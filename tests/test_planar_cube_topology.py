"""S2C-11.13.1 planar CubeTopology native constructions.

Ordinary tests cover definition mapping, CAD-neutral geometry, and
fail-closed boundaries. Live SolidWorks generation lives in the
integration module.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from se2cad.catalog import (
    RecipeKind,
    SupportStatus,
    expand_catalog_identities,
    geometry_id_for_subtype,
    load_default_catalog,
)
from se2cad.catalog.errors import CatalogValidationError
from se2cad.catalog.model import CellSize, ObservedDefinition, ObservedIdentity
from se2cad.ir import build_canonical_blueprint, component_name_from_block
from se2cad.library import (
    AUTOMATABLE_CUBE_TOPOLOGIES,
    CANONICAL_CELL_ENVELOPE,
    PLANAR_CUBE_TOPOLOGY_BINDINGS,
    PrismConstruction,
    SolidKind,
    TrapezoidalPrismConstruction,
    UnsupportedTopologyError,
    all_library_records,
    apply_edge_treatment,
    cell_half_extent_mm,
    geometry_supports_chamfer,
    lookup_recipe,
    lookup_record,
    original_library_geometry_ids,
    planar_cube_topology_geometry_ids,
    recipe_for_topology,
    signed_volume_times_6,
    solid_from_recipe,
)
from se2cad.library.treatment import EDGE_TREATMENT_CHAMFER
from se2cad.parser import parse_blueprint_xml
from se2cad.policy import ConversionPolicy, ConversionRefusedError, convert_blueprint
from se2cad.preflight import CatalogOutcome, compute_conversion_preflight
from se2cad.solidworks.artifacts import canonical_geometry_ids
from se2cad.solidworks.materialize import has_qualified_untreated_builder
from se2cad.solidworks.recipe_plan import plan_from_recipe
from se2cad.transform import IDENTITY_ROTATION, rotation_from_forward_up
from se2cad.parser.model import Direction
from se2cad.vanilla import VanillaResolveKind, resolve_vanilla_geometry
from se2cad.vanilla.resolve import eligibility_reason


_QUALIFIED = (
    (
        "LargeBlockArmorSlope2Base",
        "large_block_armor_slope2_base",
        "Slope2Base",
    ),
    (
        "LargeBlockArmorSlope2Tip",
        "large_block_armor_slope2_tip",
        "Slope2Tip",
    ),
    ("LargeHalfArmorBlock", "large_half_armor_block", "HalfBox"),
    (
        "LargeHeavyHalfArmorBlock",
        "large_heavy_half_armor_block",
        "HalfBox",
    ),
)

_UNRESOLVED_INVESTIGATED = (
    "LargeBlockArmorHalfSlopeInverted",
    "LargeBlockArmorHalfCorner",
    "LargeBlockArmorHalfSlopedCorner",
    "LargeBlockArmorSlopedCornerBase",
    "LargeBlockArmorSlopedCornerTip",
    "LargeBlockHeavyArmorHalfSlopeInverted",
    "LargeBlockArmorSlopedCorner",
    "LargeBlockArmorSquareSlopedCornerBase",
    "LargeHeavyHalfSlopeArmorBlock",
    "LargeBlockInteriorWall",
    "LargeHalfSlopeArmorBlock",
    "LargeBlockArmorSlopeTransitionTip",
    "LargeBlockArmorSlopeTransitionTipMirrored",
    "LargeBlockArmorRoundSlope",
    "LargeBlockArmorRoundCorner",
)


def _half() -> int:
    return cell_half_extent_mm()


def _scale(signs: tuple[int, int, int]) -> tuple[int, int, int]:
    half = _half()
    return (signs[0] * half, signs[1] * half, signs[2] * half)


def _ship_xml(blocks: str, identity: str = "planar-probe") -> str:
    return f"""<?xml version="1.0"?>
<Definitions xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <ShipBlueprints>
    <ShipBlueprint>
      <Id Type="MyObjectBuilder_ShipBlueprintDefinition" Subtype="{identity}" />
      <CubeGrids>
        <CubeGrid>
          <GridSizeEnum>Large</GridSizeEnum>
          <CubeBlocks>
{blocks}
          </CubeBlocks>
        </CubeGrid>
      </CubeGrids>
    </ShipBlueprint>
  </ShipBlueprints>
</Definitions>
"""


def _block(
    subtype: str,
    *,
    x: int = 0,
    y: int = 0,
    z: int = 0,
    forward: str = "Forward",
    up: str = "Up",
) -> str:
    return f"""            <MyObjectBuilder_CubeBlock xsi:type="MyObjectBuilder_CubeBlock">
              <SubtypeName>{subtype}</SubtypeName>
              <Min x="{x}" y="{y}" z="{z}" />
              <BlockOrientation Forward="{forward}" Up="{up}" />
              <ColorMaskHSV x="0.0" y="0.0" z="0.0" />
            </MyObjectBuilder_CubeBlock>"""


class QualifiedIdentityMappingTests(unittest.TestCase):
    def test_packaged_observed_facts_match_vanilla_definition_record(self) -> None:
        catalog = load_default_catalog()
        for subtype_id, geometry_id, topology in _QUALIFIED:
            entry = catalog.lookup(subtype_id)
            self.assertEqual(entry.geometry_id, geometry_id)
            self.assertEqual(entry.observed.type_id, "CubeBlock")
            self.assertEqual(entry.observed.cube_size, "Large")
            self.assertEqual(entry.observed.size, CellSize(1, 1, 1))
            self.assertEqual(entry.observed.block_topology, "Cube")
            self.assertEqual(entry.observed.cube_topology, topology)
            self.assertEqual(entry.recipe_kind, RecipeKind.NATIVE_PROCEDURAL)
            self.assertEqual(entry.support_status, SupportStatus.SUPPORTED)
            self.assertEqual(geometry_id_for_subtype(subtype_id), geometry_id)

    def test_identity_mapping_is_deterministic(self) -> None:
        first = tuple(
            (subtype, geometry_id_for_subtype(subtype), topology)
            for subtype, _geometry_id, topology in _QUALIFIED
        )
        second = tuple(
            (subtype, geometry_id_for_subtype(subtype), topology)
            for subtype, _geometry_id, topology in _QUALIFIED
        )
        self.assertEqual(first, second)
        self.assertEqual(first, _QUALIFIED)

    def test_heavy_light_halfbox_share_construction_not_geometry_id(self) -> None:
        light = lookup_recipe("large_half_armor_block")
        heavy = lookup_recipe("large_heavy_half_armor_block")
        self.assertNotEqual(light.geometry_id, heavy.geometry_id)
        self.assertEqual(light.vertices_mm, heavy.vertices_mm)
        self.assertEqual(light.faces, heavy.faces)
        self.assertEqual(light.construction, heavy.construction)
        self.assertEqual(
            light.validation.volume_times_6_mm3,
            heavy.validation.volume_times_6_mm3,
        )
        self.assertEqual(light.orientation.observed_cube_topology, "HalfBox")
        self.assertEqual(heavy.orientation.observed_cube_topology, "HalfBox")

    def test_packaged_geometry_id_collision_fails_closed(self) -> None:
        catalog = load_default_catalog()
        colliding = ObservedIdentity(
            "LargeArmorBlock",
            ObservedDefinition(
                type_id="CubeBlock",
                cube_size="Large",
                size=CellSize(1, 1, 1),
                block_topology="Cube",
                cube_topology="Box",
            ),
        )
        with self.assertRaises(CatalogValidationError) as ctx:
            expand_catalog_identities((colliding,), existing=catalog)
        self.assertIn("geometry_id", str(ctx.exception).lower())

    def test_curved_and_unqualified_planar_remain_unknown(self) -> None:
        catalog = load_default_catalog()
        for subtype_id in _UNRESOLVED_INVESTIGATED:
            with self.subTest(subtype_id=subtype_id):
                with self.assertRaises(Exception):
                    catalog.lookup(subtype_id)

    def test_round_slope_and_corner_have_no_construction(self) -> None:
        for topology in ("RoundSlope", "RoundCorner"):
            with self.subTest(topology=topology):
                with self.assertRaises(UnsupportedTopologyError) as ctx:
                    recipe_for_topology("synthetic_curved", topology)
                self.assertIn(topology, str(ctx.exception))
                self.assertNotIn(topology, AUTOMATABLE_CUBE_TOPOLOGIES)

    def test_small_grid_counterpart_is_not_catalogued(self) -> None:
        catalog = load_default_catalog()
        for subtype_id in (
            "SmallBlockArmorSlope2Base",
            "SmallBlockArmorSlope2Tip",
            "SmallHalfArmorBlock",
        ):
            with self.assertRaises(Exception):
                catalog.lookup(subtype_id)
        for entry in catalog.entries:
            self.assertEqual(entry.observed.cube_size, "Large")

    def test_unsupported_and_malformed_topology_fail_closed(self) -> None:
        with self.assertRaises(UnsupportedTopologyError):
            recipe_for_topology("synthetic_unknown_token", "NotATopology")
        with self.assertRaises(UnsupportedTopologyError):
            recipe_for_topology("synthetic_empty_token", "")
        with self.assertRaises(UnsupportedTopologyError):
            recipe_for_topology("synthetic_slope_transition", "SlopeTransitionTip")

    def test_omitted_block_topology_does_not_grant_support(self) -> None:
        catalog = load_default_catalog()
        with self.assertRaises(Exception):
            catalog.lookup("LargeBlockInteriorWall")
        parsed = parse_blueprint_xml(
            _ship_xml(_block("LargeBlockInteriorWall")),
            source="interior-wall",
        )
        preflight = compute_conversion_preflight(parsed, catalog)
        self.assertEqual(preflight.unknown_count, 1)
        self.assertEqual(preflight.blocks[0].catalog_outcome, CatalogOutcome.UNKNOWN)

    def test_cube_topology_with_model_or_subparts_stays_off_trianglemesh_path(
        self,
    ) -> None:
        catalog = load_default_catalog()
        definition = """<?xml version="1.0"?>
<Definitions xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <CubeBlocks>
    <Definition>
      <Id Type="MyObjectBuilder_CubeBlock" Subtype="LargeBlockArmorRoundSlope" />
      <CubeSize>Large</CubeSize>
      <Size x="1" y="1" z="1" />
      <BlockTopology>Cube</BlockTopology>
      <Model>Models\\Cubes\\Large\\round.mwm</Model>
      <CubeDefinition>
        <CubeTopology>RoundSlope</CubeTopology>
      </CubeDefinition>
      <Subparts><Subpart><Name>x</Name></Subpart></Subparts>
    </Definition>
  </CubeBlocks>
</Definitions>
"""
        with tempfile.TemporaryDirectory() as tmp:
            game = Path(tmp) / "game"
            cube_dir = game / "Data" / "CubeBlocks"
            cube_dir.mkdir(parents=True)
            (cube_dir / "CubeBlocks_Armor.sbc").write_text(definition, encoding="utf-8")
            resolved = resolve_vanilla_geometry(
                "LargeBlockArmorRoundSlope",
                catalog,
                game_root=game,
                sdk_root=Path(tmp) / "sdk",
            )
        self.assertEqual(resolved.kind, VanillaResolveKind.UNRESOLVED)
        self.assertIsNotNone(resolved.unresolved_reason)
        self.assertTrue(callable(eligibility_reason))
        self.assertIn("TriangleMesh", resolved.unresolved_reason or "")


class CadNeutralGeometryTests(unittest.TestCase):
    def test_slope2_base_is_not_a_box(self) -> None:
        half = _half()
        h3 = half * half * half
        recipe = lookup_recipe("large_block_armor_slope2_base")
        box = lookup_recipe("large_armor_block")
        self.assertEqual(recipe.solid_kind, SolidKind.TRAPEZOIDAL_PRISM)
        self.assertIsInstance(recipe.construction, TrapezoidalPrismConstruction)
        self.assertEqual(recipe.validation.vertex_count, 8)
        self.assertEqual(recipe.validation.face_count, 6)
        self.assertEqual(recipe.validation.volume_times_6_mm3, 36 * h3)
        self.assertNotEqual(
            recipe.validation.volume_times_6_mm3,
            box.validation.volume_times_6_mm3,
        )
        self.assertNotEqual(frozenset(recipe.vertices_mm), frozenset(box.vertices_mm))
        self.assertIn(_scale((-1, 1, -1)), recipe.vertices_mm)
        self.assertIn(_scale((1, 0, 1)), recipe.vertices_mm)
        self.assertNotIn(_scale((-1, 1, 1)), recipe.vertices_mm)
        for _x, y, z in recipe.vertices_mm:
            self.assertLessEqual(2 * y + z, half)
        self.assertEqual(
            recipe.validation.bounding_box.min_mm, (-half, -half, -half)
        )
        self.assertEqual(
            recipe.validation.bounding_box.max_mm, (half, half, half)
        )
        assert isinstance(recipe.construction, TrapezoidalPrismConstruction)
        self.assertEqual(recipe.construction.profile_plane, "YZ")
        self.assertEqual(recipe.construction.extrusion_axis, "X")

    def test_slope2_tip_complements_base_and_is_not_a_box(self) -> None:
        half = _half()
        h3 = half * half * half
        tip = lookup_recipe("large_block_armor_slope2_tip")
        base = lookup_recipe("large_block_armor_slope2_base")
        box = lookup_recipe("large_armor_block")
        slope = lookup_recipe("large_armor_slope")
        self.assertEqual(tip.solid_kind, SolidKind.RIGHT_TRIANGULAR_PRISM)
        self.assertIsInstance(tip.construction, PrismConstruction)
        self.assertEqual(tip.validation.vertex_count, 6)
        self.assertEqual(tip.validation.face_count, 5)
        self.assertEqual(tip.validation.volume_times_6_mm3, 12 * h3)
        self.assertEqual(
            tip.validation.volume_times_6_mm3 + base.validation.volume_times_6_mm3,
            box.validation.volume_times_6_mm3,
        )
        self.assertNotEqual(
            tip.validation.volume_times_6_mm3,
            slope.validation.volume_times_6_mm3,
        )
        self.assertNotEqual(frozenset(tip.vertices_mm), frozenset(box.vertices_mm))
        self.assertIn(_scale((-1, 0, -1)), tip.vertices_mm)
        self.assertIn(_scale((1, -1, 1)), tip.vertices_mm)
        self.assertNotIn(_scale((-1, 1, -1)), tip.vertices_mm)
        for _x, y, z in tip.vertices_mm:
            self.assertLessEqual(2 * y + z, -half)
        self.assertEqual(tip.validation.bounding_box.max_mm, (half, 0, half))
        assert isinstance(tip.construction, PrismConstruction)
        self.assertEqual(
            tip.construction.profile_yz_mm,
            ((-half, -half), (0, -half), (-half, half)),
        )

    def test_halfbox_is_lower_half_cell_not_a_full_box(self) -> None:
        half = _half()
        h3 = half * half * half
        recipe = lookup_recipe("large_half_armor_block")
        box = lookup_recipe("large_armor_block")
        tip = lookup_recipe("large_block_armor_slope2_tip")
        self.assertEqual(recipe.solid_kind, SolidKind.AXIS_ALIGNED_BOX)
        self.assertEqual(recipe.validation.vertex_count, 8)
        self.assertEqual(recipe.validation.face_count, 6)
        self.assertEqual(recipe.validation.volume_times_6_mm3, 24 * h3)
        self.assertEqual(
            recipe.validation.volume_times_6_mm3 * 2,
            box.validation.volume_times_6_mm3,
        )
        self.assertNotEqual(frozenset(recipe.vertices_mm), frozenset(box.vertices_mm))
        self.assertNotEqual(frozenset(recipe.vertices_mm), frozenset(tip.vertices_mm))
        self.assertEqual(recipe.validation.bounding_box.max_mm, (half, 0, half))
        for _x, y, _z in recipe.vertices_mm:
            self.assertLessEqual(y, 0)
        self.assertEqual(recipe.construction.min_mm, (-half, -half, -half))
        self.assertEqual(recipe.construction.max_mm, (half, 0, half))

    def test_geometry_ids_are_stable_and_orientation_independent(self) -> None:
        self.assertEqual(
            planar_cube_topology_geometry_ids(),
            tuple(geometry_id for geometry_id, _topology in PLANAR_CUBE_TOPOLOGY_BINDINGS),
        )
        for geometry_id, topology in PLANAR_CUBE_TOPOLOGY_BINDINGS:
            recipe = lookup_recipe(geometry_id)
            stamped = recipe_for_topology("synthetic_" + geometry_id, topology)
            self.assertEqual(stamped.vertices_mm, recipe.vertices_mm)
            self.assertEqual(stamped.faces, recipe.faces)
            self.assertEqual(stamped.construction, recipe.construction)
            self.assertEqual(stamped.validation, recipe.validation)
            for vertex in recipe.vertices_mm:
                self.assertTrue(CANONICAL_CELL_ENVELOPE.contains(vertex))
            recomputed = signed_volume_times_6(recipe.vertices_mm, recipe.faces)
            self.assertEqual(recomputed, recipe.validation.volume_times_6_mm3)
            self.assertGreater(recomputed, 0)
            plan = plan_from_recipe(recipe)
            self.assertEqual(plan.geometry_id, geometry_id)
            self.assertGreater(plan.expected.volume_m3, 0.0)

    def test_no_subtype_specific_world_placement(self) -> None:
        for geometry_id, _topology in PLANAR_CUBE_TOPOLOGY_BINDINGS:
            record = lookup_record(geometry_id)
            self.assertEqual(record.placement.additional_offset_mm, (0, 0, 0))
            self.assertTrue(record.placement.insert_at_cell_center)
            self.assertIsNone(record.placement.part_locator)
            self.assertTrue(has_qualified_untreated_builder(geometry_id))
            self.assertTrue(geometry_supports_chamfer(geometry_id))

    def test_legal_rotations_remain_determinant_plus_one(self) -> None:
        recipe = lookup_recipe("large_block_armor_slope2_base")
        vertex = recipe.vertices_mm[0]
        self.assertEqual(IDENTITY_ROTATION.determinant(), 1)
        for forward in Direction:
            for up in Direction:
                try:
                    rotation = rotation_from_forward_up(forward, up)
                except Exception:
                    continue
                self.assertEqual(rotation.determinant(), 1)
                image = rotation.apply(vertex)
                self.assertTrue(all(isinstance(coord, int) for coord in image))

    def test_chamfer_is_valid_on_new_convex_solids(self) -> None:
        for geometry_id, _topology in PLANAR_CUBE_TOPOLOGY_BINDINGS:
            recipe = lookup_recipe(geometry_id)
            untreated = solid_from_recipe(recipe)
            result = apply_edge_treatment(untreated, EDGE_TREATMENT_CHAMFER)
            with self.subTest(geometry_id=geometry_id):
                self.assertTrue(result.applied)
                self.assertLess(
                    result.volume_times_6, recipe.validation.volume_times_6_mm3
                )


class RuntimeAndDefaultGenerationTests(unittest.TestCase):
    def test_default_generation_set_stays_original_four(self) -> None:
        self.assertEqual(canonical_geometry_ids(), original_library_geometry_ids())
        self.assertEqual(len(all_library_records()), 12)

    def test_strict_conversion_uses_generic_ir_transforms(self) -> None:
        xml = _ship_xml(
            "\n".join(
                [
                    _block("LargeBlockArmorSlope2Base", x=0, y=0, z=0),
                    _block(
                        "LargeBlockArmorSlope2Base",
                        x=1,
                        y=0,
                        z=0,
                        forward="Right",
                        up="Up",
                    ),
                    _block("LargeBlockArmorSlope2Tip", x=-2, y=0, z=3),
                    _block("LargeHalfArmorBlock", x=0, y=-1, z=0),
                    _block("LargeHeavyHalfArmorBlock", x=0, y=-1, z=1),
                    _block(
                        "LargeBlockArmorSlope2Tip",
                        x=-2,
                        y=1,
                        z=3,
                        forward="Down",
                        up="Forward",
                    ),
                ]
            )
        )
        parsed = parse_blueprint_xml(xml, source="planar-fixture")
        catalog = load_default_catalog()
        preflight = compute_conversion_preflight(parsed, catalog)
        self.assertTrue(preflight.all_supported)
        self.assertEqual(preflight.supported_count, 6)
        result = convert_blueprint(parsed, catalog, ConversionPolicy.STRICT)
        self.assertEqual(result.filler_count, 0)
        self.assertEqual(len(result.ir.grid.blocks), 6)
        geometry_ids = [block.geometry_id for block in result.ir.grid.blocks]
        self.assertEqual(geometry_ids.count("large_block_armor_slope2_base"), 2)
        self.assertEqual(geometry_ids.count("large_block_armor_slope2_tip"), 2)
        self.assertEqual(geometry_ids.count("large_half_armor_block"), 1)
        self.assertEqual(geometry_ids.count("large_heavy_half_armor_block"), 1)
        first = result.ir.grid.blocks[0]
        self.assertEqual((first.grid_min.x, first.grid_min.y, first.grid_min.z), (0, 0, 0))
        self.assertEqual(first.position_mm.as_tuple(), (0, 0, 0))
        negative = result.ir.grid.blocks[2]
        self.assertEqual(
            (negative.grid_min.x, negative.grid_min.y, negative.grid_min.z),
            (-2, 0, 3),
        )
        self.assertEqual(negative.position_mm.as_tuple(), (-5000, 0, 7500))
        names = [component_name_from_block(block) for block in result.ir.grid.blocks]
        self.assertEqual(len(names), len(set(names)))
        for block, name in zip(result.ir.grid.blocks, names, strict=True):
            self.assertIn(block.subtype_id, name)
            self.assertNotIn(block.geometry_id, name)
            self.assertNotIn("trapezoidal", name)
            self.assertNotIn("HalfBox", name)
        ir = build_canonical_blueprint(parsed, catalog)
        self.assertEqual(
            [block.geometry_id for block in ir.grid.blocks],
            geometry_ids,
        )

    def test_unresolved_identities_do_not_enter_strict_conversion(self) -> None:
        parsed = parse_blueprint_xml(
            _ship_xml(
                "\n".join(
                    [
                        _block("LargeBlockArmorRoundSlope"),
                        _block("LargeBlockArmorRoundCorner"),
                        _block("LargeBlockInteriorWall"),
                    ]
                )
            ),
            source="unresolved-planar",
        )
        catalog = load_default_catalog()
        preflight = compute_conversion_preflight(parsed, catalog)
        self.assertEqual(preflight.unknown_count, 3)
        with self.assertRaises(ConversionRefusedError):
            convert_blueprint(parsed, catalog, ConversionPolicy.STRICT)


class LiveDefinitionEvidenceTests(unittest.TestCase):
    def test_operator_game_root_matches_packaged_facts_when_configured(self) -> None:
        from se2cad.vanilla.lookup import lookup_exact_subtype
        from se2cad.vanilla.roots import try_load_game_content_root

        game = try_load_game_content_root()
        if game is None:
            self.skipTest("SE2CAD_GAME_ROOT is not configured")
        catalog = load_default_catalog()
        for subtype_id, _geometry_id, topology in _QUALIFIED:
            hit = lookup_exact_subtype(subtype_id, game)
            self.assertIsNotNone(hit)
            assert hit is not None
            self.assertIsNotNone(hit.definition)
            assert hit.definition is not None
            entry = catalog.lookup(subtype_id)
            self.assertEqual(hit.definition.cube_size, "Large")
            self.assertEqual(hit.definition.size, entry.observed.size)
            self.assertEqual(hit.definition.block_topology, "Cube")
            self.assertEqual(hit.definition.cube_topology, topology)
            self.assertFalse(hit.definition.has_subparts)
            self.assertEqual(hit.definition.primary_model, "")
        for subtype_id in (
            "LargeBlockArmorRoundSlope",
            "LargeBlockArmorRoundCorner",
            "SmallBlockArmorSlope2Base",
        ):
            hit = lookup_exact_subtype(subtype_id, game)
            self.assertIsNotNone(hit)
            assert hit is not None and hit.definition is not None
            if subtype_id.startswith("Small"):
                self.assertEqual(hit.definition.cube_size, "Small")
            else:
                self.assertIn(
                    hit.definition.cube_topology, {"RoundSlope", "RoundCorner"}
                )


if __name__ == "__main__":
    unittest.main()
