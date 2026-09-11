"""Ordinary tests for the S2C-11.7.1 single-identity SDK-mesh bind."""

from __future__ import annotations

import ast
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from se2cad.catalog import (
    AUTHORIZED_SDK_MESH_GEOMETRY_ID,
    AUTHORIZED_SDK_MESH_RECIPE_KIND,
    AUTHORIZED_SDK_MESH_SUBTYPE_ID,
    FILLER_GEOMETRY_ID,
    RecipeKind,
    SupportStatus,
    classify_observed,
    conversion_may_report_supported,
    evaluate_leftover_set,
    geometry_id_for_subtype,
    load_default_catalog,
    load_default_leftover_set,
    query_exception_records,
    select_catalog_recipes,
)
from se2cad.catalog.selection import GeometryClass
from se2cad.ir import build_canonical_blueprint
from se2cad.library import (
    NativeSolidRecipe,
    SdkMeshRecipe,
    all_library_records,
    geometry_supports_chamfer,
    lookup_recipe,
    lookup_record,
)
from se2cad.parser import parse_blueprint, parse_blueprint_xml
from se2cad.policy import ConversionPolicy, ConversionRefusedError, convert_blueprint
from se2cad.preflight import compute_conversion_preflight
from se2cad.solidworks import (
    GeneratedRootError,
    contained_destination,
    has_qualified_untreated_builder,
    logical_part_filename,
    placements_from_ir,
)
from se2cad.solidworks.com_validate import PartValidation
from se2cad.solidworks.config import SolidWorksBackendConfig
from se2cad.solidworks.errors import CanonicalPartValidationError, SdkSourceError
from se2cad.solidworks.sdk_convert import assert_imported_mesh_envelope
from se2cad.solidworks.materialize import (
    demanded_untreated_geometry_ids,
    ensure_untreated_canonical_parts,
)
from se2cad.solidworks.sdk_source import (
    AUTHORIZED_SDK_SOURCE_FILENAME,
    contained_sdk_file,
    load_sdk_root,
    resolve_sdk_mesh_file,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src" / "se2cad"
_ARMOR_SUBTYPES = (
    "LargeBlockArmorBlock",
    "LargeBlockArmorSlope",
    "LargeBlockArmorCorner",
    "LargeBlockArmorCornerInv",
    "LargeHeavyBlockArmorBlock",
    "LargeHeavyBlockArmorSlope",
    "LargeHeavyBlockArmorCorner",
    "LargeHeavyBlockArmorCornerInv",
)


def _document(blocks: str, identity: str = "se2cad-sdk-probe") -> str:
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


def _block(subtype: str, *, xsi_type: str = "MyObjectBuilder_CubeBlock", min_xml: str = "") -> str:
    extra = f"\n              {min_xml}" if min_xml else ""
    return (
        f'            <MyObjectBuilder_CubeBlock xsi:type="{xsi_type}">\n'
        f"              <SubtypeName>{subtype}</SubtypeName>{extra}\n"
        "            </MyObjectBuilder_CubeBlock>"
    )


def _config(root: Path) -> SolidWorksBackendConfig:
    return SolidWorksBackendConfig(
        generated_root=root.resolve(),
        part_template=None,
        visible=False,
        source="test",
    )


def _fake_generate(config, treatment=None, geometry_ids=None):
    for geometry_id in geometry_ids or ():
        name = logical_part_filename(geometry_id)
        (config.generated_root / name).write_bytes(b"generated")
    return ()


class CatalogAndLibraryBindTests(unittest.TestCase):
    def test_target_resolves_to_one_sdk_record(self) -> None:
        catalog = load_default_catalog()
        entry = catalog.lookup(AUTHORIZED_SDK_MESH_SUBTYPE_ID)
        self.assertEqual(entry.geometry_id, AUTHORIZED_SDK_MESH_GEOMETRY_ID)
        self.assertEqual(
            entry.geometry_id,
            geometry_id_for_subtype(AUTHORIZED_SDK_MESH_SUBTYPE_ID),
        )
        self.assertEqual(entry.recipe_kind, AUTHORIZED_SDK_MESH_RECIPE_KIND)
        self.assertEqual(entry.support_status, SupportStatus.SUPPORTED)
        self.assertEqual(entry.observed.type_id, "Thrust")
        self.assertEqual(entry.observed.block_topology, "TriangleMesh")
        self.assertIsNone(entry.observed.cube_topology)
        recipe = lookup_recipe(entry.geometry_id)
        self.assertIsInstance(recipe, SdkMeshRecipe)
        self.assertNotIsInstance(recipe, NativeSolidRecipe)
        self.assertEqual(recipe.subtype_id, AUTHORIZED_SDK_MESH_SUBTYPE_ID)
        self.assertEqual(recipe.source_type, "official_modsdk")
        self.assertEqual(
            recipe.relative_source_stem,
            "Models/Cubes/Large/HydrogenThrusterSmall",
        )
        record = lookup_record(entry.geometry_id)
        self.assertFalse(record.chamfer_capable)
        self.assertFalse(geometry_supports_chamfer(entry.geometry_id))
        self.assertTrue(has_qualified_untreated_builder(entry.geometry_id))

    def test_no_other_subtype_gains_support(self) -> None:
        catalog = load_default_catalog()
        supported = [entry.subtype_id for entry in catalog.entries if entry.support_status is SupportStatus.SUPPORTED]
        self.assertEqual(
            supported[:9],
            [*_ARMOR_SUBTYPES, AUTHORIZED_SDK_MESH_SUBTYPE_ID],
        )
        self.assertNotIn("LargeBlockLargeHydrogenThrust", [entry.subtype_id for entry in catalog.entries])
        self.assertEqual(len(all_library_records()), 12)
        for record in all_library_records():
            self.assertIsInstance(record.recipe, NativeSolidRecipe)
            self.assertEqual(record.recipe_kind, RecipeKind.NATIVE_PROCEDURAL)

    def test_classification_stays_long_tail_and_other_sdk_mesh_fails(self) -> None:
        catalog = load_default_catalog()
        entry = catalog.lookup(AUTHORIZED_SDK_MESH_SUBTYPE_ID)
        classification = classify_observed(entry.observed)
        self.assertEqual(classification.geometry_class, GeometryClass.LONG_TAIL)
        self.assertEqual(classification.recipe_kind, RecipeKind.UNSUPPORTED)
        leftover = load_default_leftover_set()
        self.assertTrue(conversion_may_report_supported(entry, leftover))
        self.assertEqual(query_exception_records(catalog), ())
        report = select_catalog_recipes(catalog)
        self.assertEqual(report.exceptions, ())
        from se2cad.catalog.model import CatalogEntry, CellSize, DefinitionCatalog, ObservedDefinition

        other = DefinitionCatalog(
            entries=(
                CatalogEntry(
                    subtype_id="LargeBlockLargeHydrogenThrust",
                    observed=ObservedDefinition(
                        type_id="Thrust",
                        cube_size="Large",
                        size=CellSize(1, 1, 1),
                        block_topology="TriangleMesh",
                        cube_topology=None,
                    ),
                    geometry_id="large_block_large_hydrogen_thrust",
                    recipe_kind=RecipeKind.SDK_MESH_DIRECT,
                    support_status=SupportStatus.UNSUPPORTED,
                ),
            )
        )
        from se2cad.catalog import CatalogValidationError

        with self.assertRaises(CatalogValidationError) as ctx:
            select_catalog_recipes(other)
        self.assertIn("ADR-004", str(ctx.exception))


class SdkPathSafetyTests(unittest.TestCase):
    def test_resolution_stays_inside_configured_root(self) -> None:
        recipe = lookup_recipe(AUTHORIZED_SDK_MESH_GEOMETRY_ID)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "Models" / "Cubes" / "Large" / AUTHORIZED_SDK_SOURCE_FILENAME
            source.parent.mkdir(parents=True)
            source.write_bytes(b"Kaydara FBX Binary  \x1a\x00")
            resolved = resolve_sdk_mesh_file(recipe, sdk_root=root)
            self.assertEqual(resolved, source.resolve())
            self.assertEqual(resolved.name, AUTHORIZED_SDK_SOURCE_FILENAME)

    def test_missing_sdk_root_fails_closed(self) -> None:
        with patch.dict("os.environ", {"SE2CAD_SDK_ROOT": ""}, clear=False):
            with patch("os.environ.get", side_effect=lambda name, default=None: None if name == "SE2CAD_SDK_ROOT" else __import__("os").environ.get(name, default)):
                with patch(
                    "se2cad.solidworks.sdk_source.discover_local_config",
                    return_value=None,
                ):
                    with self.assertRaises(SdkSourceError) as ctx:
                        load_sdk_root()
                    self.assertIn("SDK root is required", str(ctx.exception))

    def test_missing_target_fbx_fails_closed(self) -> None:
        recipe = lookup_recipe(AUTHORIZED_SDK_MESH_GEOMETRY_ID)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "Models" / "Cubes" / "Large").mkdir(parents=True)
            with self.assertRaises(SdkSourceError) as ctx:
                resolve_sdk_mesh_file(recipe, sdk_root=root)
            self.assertIn("is not a file", str(ctx.exception))

    def test_path_traversal_and_wrong_files_are_refused(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            outside = Path(tmp).resolve().parent / AUTHORIZED_SDK_SOURCE_FILENAME
            with self.assertRaises(SdkSourceError):
                contained_sdk_file(root, outside)
            lod = root / "Models" / "Cubes" / "Large" / "LOD" / AUTHORIZED_SDK_SOURCE_FILENAME
            lod.parent.mkdir(parents=True)
            lod.write_bytes(b"lod")
            with self.assertRaises(SdkSourceError) as ctx:
                contained_sdk_file(root, lod)
            self.assertIn("LOD", str(ctx.exception))
            construction = (
                root / "Models" / "Cubes" / "Large" / "HydrogenThrusterSmall_Construction_1.fbx"
            )
            with self.assertRaises(SdkSourceError):
                contained_sdk_file(root, construction)
            mwm = root / "Models" / "Cubes" / "Large" / "HydrogenThrusterSmall.mwm"
            mwm.parent.mkdir(parents=True, exist_ok=True)
            mwm.write_bytes(b"mwm")
            with self.assertRaises(SdkSourceError) as ctx:
                contained_sdk_file(root, mwm)
            message = str(ctx.exception)
            self.assertTrue(
                "MWM" in message or "non-authorized SDK filename" in message,
                msg=message,
            )

    def test_unrelated_fbx_is_not_authorized(self) -> None:
        recipe = lookup_recipe(AUTHORIZED_SDK_MESH_GEOMETRY_ID)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            other = root / "Models" / "Cubes" / "Large" / "HydrogenThrusterLarge.fbx"
            other.parent.mkdir(parents=True)
            other.write_bytes(b"other")
            with self.assertRaises(SdkSourceError) as ctx:
                resolve_sdk_mesh_file(recipe, sdk_root=root)
            self.assertIn("is not a file", str(ctx.exception))
            with self.assertRaises(SdkSourceError) as contained_ctx:
                contained_sdk_file(
                    root, other, expected_name=AUTHORIZED_SDK_SOURCE_FILENAME
                )
            self.assertIn("non-authorized SDK filename", str(contained_ctx.exception))


class PolicyAndProvenanceTests(unittest.TestCase):
    def test_strict_accepts_target_and_refuses_remaining_unknowns(self) -> None:
        catalog = load_default_catalog()
        xml = _document(
            "\n".join(
                [
                    _block(AUTHORIZED_SDK_MESH_SUBTYPE_ID, xsi_type="MyObjectBuilder_Thrust"),
                    _block("ModdedUnknownBlock", xsi_type="MyObjectBuilder_Gyro", min_xml='<Min x="1" y="0" z="0" />'),
                ]
            )
        )
        parsed = parse_blueprint_xml(xml, source="strict-mixed")
        report = compute_conversion_preflight(parsed, catalog)
        self.assertEqual(report.supported_count, 1)
        self.assertEqual(report.unknown_count, 1)
        with self.assertRaises(ConversionRefusedError):
            convert_blueprint(parsed, catalog, ConversionPolicy.STRICT)
        permitted = convert_blueprint(parsed, catalog, ConversionPolicy.PERMISSIVE)
        thrust, gyro = permitted.ir.grid.blocks
        self.assertEqual(thrust.geometry_id, AUTHORIZED_SDK_MESH_GEOMETRY_ID)
        self.assertEqual(thrust.support_status, SupportStatus.SUPPORTED)
        self.assertEqual(gyro.geometry_id, FILLER_GEOMETRY_ID)
        self.assertEqual(permitted.filler_count, 1)

    def test_small_grid_remains_unsupported(self) -> None:
        xml = """<?xml version="1.0"?>
<Definitions xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <ShipBlueprints>
    <ShipBlueprint>
      <Id Type="MyObjectBuilder_ShipBlueprintDefinition" Subtype="small" />
      <CubeGrids>
        <CubeGrid>
          <GridSizeEnum>Small</GridSizeEnum>
          <CubeBlocks>
            <MyObjectBuilder_CubeBlock>
              <SubtypeName>LargeBlockSmallHydrogenThrust</SubtypeName>
            </MyObjectBuilder_CubeBlock>
          </CubeBlocks>
        </CubeGrid>
      </CubeGrids>
    </ShipBlueprint>
  </ShipBlueprints>
</Definitions>
"""
        from se2cad.parser import UnsupportedBlueprintError

        with self.assertRaises(UnsupportedBlueprintError):
            parse_blueprint_xml(xml, source="small-grid")

    def test_provenance_and_leftover_honesty(self) -> None:
        leftover = evaluate_leftover_set(load_default_catalog())
        self.assertEqual(leftover.coverage_claim, "not_universal_vanilla")
        self.assertEqual(
            [item.subtype_id for item in leftover.completed_automatable],
            [
                *_ARMOR_SUBTYPES,
                "LargeBlockArmorSlope2Base",
                "LargeBlockArmorSlope2Tip",
                "LargeHalfArmorBlock",
                "LargeHeavyHalfArmorBlock",
            ],
        )
        self.assertEqual([record.cube_topology for record in leftover.leftovers], [])
        recipe = lookup_recipe(AUTHORIZED_SDK_MESH_GEOMETRY_ID)
        self.assertIsInstance(recipe, SdkMeshRecipe)
        self.assertEqual(recipe.relative_source_stem, "Models/Cubes/Large/HydrogenThrusterSmall")
        catalog_text = (SRC_ROOT / "catalog" / "large_grid_armor.json").read_text(encoding="utf-8")
        self.assertNotIn(".fbx", catalog_text.lower())
        self.assertNotIn("hydrogenthrustersmall.fbx", catalog_text.lower())


class LazyMaterializationTests(unittest.TestCase):
    def test_missing_part_generates_once_and_existing_is_reused(self) -> None:
        catalog = load_default_catalog()
        xml = _document(
            "\n".join(
                [
                    _block(AUTHORIZED_SDK_MESH_SUBTYPE_ID, xsi_type="MyObjectBuilder_Thrust"),
                    _block(
                        AUTHORIZED_SDK_MESH_SUBTYPE_ID,
                        xsi_type="MyObjectBuilder_Thrust",
                        min_xml='<Min x="1" y="0" z="0" />',
                    ),
                    _block("LargeBlockArmorBlock", min_xml='<Min x="2" y="0" z="0" />'),
                ]
            )
        )
        parsed = parse_blueprint_xml(xml, source="lazy-thrust")
        ir = convert_blueprint(parsed, catalog, ConversionPolicy.STRICT).ir
        self.assertEqual(
            demanded_untreated_geometry_ids(ir),
            (AUTHORIZED_SDK_MESH_GEOMETRY_ID, "large_armor_block"),
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = _config(root)
            with patch(
                "se2cad.solidworks.generate.generate_canonical_parts",
                side_effect=_fake_generate,
            ) as generate:
                first = ensure_untreated_canonical_parts(
                    config,
                    demanded_untreated_geometry_ids(ir),
                )
            self.assertEqual(
                first.generated,
                (AUTHORIZED_SDK_MESH_GEOMETRY_ID, "large_armor_block"),
            )
            self.assertEqual(first.reused, ())
            self.assertEqual(generate.call_count, 1)
            self.assertEqual(
                generate.call_args.kwargs["geometry_ids"],
                (AUTHORIZED_SDK_MESH_GEOMETRY_ID, "large_armor_block"),
            )
            with patch(
                "se2cad.solidworks.generate.generate_canonical_parts",
                side_effect=_fake_generate,
            ) as second_generate:
                second = ensure_untreated_canonical_parts(
                    config,
                    demanded_untreated_geometry_ids(ir),
                )
            self.assertEqual(second.generated, ())
            self.assertEqual(
                second.reused,
                (AUTHORIZED_SDK_MESH_GEOMETRY_ID, "large_armor_block"),
            )
            self.assertEqual(second_generate.call_count, 0)
            placements = placements_from_ir(ir)
            self.assertEqual(
                [item.part_filename for item in placements],
                [
                    "large_block_small_hydrogen_thrust.SLDPRT",
                    "large_block_small_hydrogen_thrust.SLDPRT",
                    "large_armor_block.SLDPRT",
                ],
            )

    def test_chamfer_is_not_applied_and_root_stays_contained(self) -> None:
        self.assertFalse(geometry_supports_chamfer(AUTHORIZED_SDK_MESH_GEOMETRY_ID))
        self.assertEqual(
            logical_part_filename(AUTHORIZED_SDK_MESH_GEOMETRY_ID),
            "large_block_small_hydrogen_thrust.SLDPRT",
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            destination = contained_destination(
                root, "large_block_small_hydrogen_thrust.SLDPRT"
            )
            destination.relative_to(root.resolve())
            with self.assertRaises(GeneratedRootError):
                contained_destination(root, "../large_block_small_hydrogen_thrust.SLDPRT")


class EnvelopeContractTests(unittest.TestCase):
    def test_sub_cell_mesh_is_accepted_and_forgotten_scale_is_not(self) -> None:
        small = PartValidation(
            solid_body_count=1,
            sheet_body_count=0,
            bounding_box_min_m=(-0.25, -0.25, -0.1),
            bounding_box_max_m=(0.25, 0.25, 0.09),
            volume_m3=0.01,
            center_of_mass_m=(0.0, 0.0, 0.0),
        )
        assert_imported_mesh_envelope(small)
        tiny = PartValidation(
            solid_body_count=1,
            sheet_body_count=0,
            bounding_box_min_m=(-0.0013, -0.0013, -0.0013),
            bounding_box_max_m=(0.0013, 0.0013, 0.0013),
            volume_m3=1e-8,
            center_of_mass_m=(0.0, 0.0, 0.0),
        )
        with self.assertRaises(CanonicalPartValidationError) as ctx:
            assert_imported_mesh_envelope(tiny)
        self.assertIn("not a coherent Large Grid cell", str(ctx.exception))


class ScanBoundaryTests(unittest.TestCase):
    def test_runtime_modules_do_not_scan_an_install(self) -> None:
        forbidden = (
            "stamp_automatable_remainder",
            "expand_catalog_identities",
            "SE2CAD_GAME_ROOT",
            "SE2CAD_SDK_ROOT",
            "SE2CAD-SE",
            "OriginalContent",
        )
        for path in (
            SRC_ROOT / "solidworks" / "materialize.py",
            SRC_ROOT / "solidworks" / "assemble.py",
        ):
            text = path.read_text(encoding="utf-8")
            for token in forbidden:
                self.assertNotIn(token, text, msg=f"{path.name} mentions {token}")
            tree = ast.parse(text, filename=str(path))
            for node in ast.walk(tree):
                modules: list[str] = []
                if isinstance(node, ast.Import):
                    modules.extend(alias.name for alias in node.names)
                elif isinstance(node, ast.ImportFrom) and node.module:
                    modules.append(node.module)
                for module in modules:
                    self.assertFalse(module.startswith("se2cad.discovery"))
                    self.assertNotEqual(module, "se2cad.solidworks.sdk_source")

    def test_library_sources_do_not_name_fbx(self) -> None:
        for path in (SRC_ROOT / "library").glob("*.py"):
            lowered = path.read_text(encoding="utf-8").lower()
            self.assertNotIn(".fbx", lowered, msg=path.name)
            self.assertNotIn(".mwm", lowered, msg=path.name)
            self.assertNotIn("c:\\", lowered, msg=path.name)


if __name__ == "__main__":
    unittest.main()
