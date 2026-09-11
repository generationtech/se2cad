"""S2C-11.10.1 CAD-neutral multi-cell placement foundation.

Does not grant multi-cell runtime support. Does not generate CAD.
"""

from __future__ import annotations

import ast
import csv
import dataclasses
import hashlib
import inspect
import os
import unittest
from collections import Counter
from fractions import Fraction
from pathlib import Path
from unittest.mock import patch

from se2cad.catalog import (
    FILLER_GEOMETRY_ID,
    LARGE_GRID_CELL_PITCH_MM,
    CellSize,
    RecipeKind,
    SupportStatus,
    load_default_catalog,
)
from se2cad.ir import (
    build_canonical_blueprint,
    canonical_block_from_parsed,
    placement_from_catalog_entry,
)
from se2cad.ir.model import CanonicalBlock
from se2cad.parser import (
    DEFAULT_COLOR_MASK_HSV,
    AppearanceSupport,
    Direction,
    GridCoordinate,
    parse_blueprint,
    parse_blueprint_xml,
)
from se2cad.parser.model import ParsedBlock
from se2cad.policy import ConversionPolicy, convert_blueprint
from se2cad.preflight import CatalogOutcome, compute_conversion_preflight
from se2cad.transform import (
    IDENTITY_ROTATION,
    MILLIMETRES_PER_METRE,
    QUALIFIED_ONE_BY_ONE_PLACEMENT,
    BlockPlacementDefinition,
    InvalidBlockSizeError,
    InvalidModelOffsetError,
    InvalidOrientationError,
    ModelOffset,
    TransformError,
    cell_center_mm,
    legal_orientations,
    occupied_max,
    occupancy_center_mm,
    placement_translation_mm,
    rotation_from_forward_up,
)
from se2cad.vanilla.resolve import (
    VanillaResolveKind,
    eligibility_reason,
    resolve_vanilla_geometry,
)
from se2cad.vanilla.lookup import TargetedDefinition
from se2cad.vanilla.roots import try_load_game_content_root, try_load_sdk_root

REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURE_PATH = REPO_ROOT / "fixtures/acceptance/four-block-armor-asymmetric/bp.sbc"
EXPECTED_SHA256 = "99c93d199a6dc960918ecd70dcecbb154c16e18d5638d359a279a15140a95b31"
TRANSFORM_ROOT = REPO_ROOT / "src" / "se2cad" / "transform"
IR_ROOT = REPO_ROOT / "src" / "se2cad" / "ir"
BIG_RED_CANDIDATES = (
    Path(r"C:\SE-blueprints\bigred_bp.sbc"),
    Path(os.environ["SE2CAD_BIG_RED"]) if os.environ.get("SE2CAD_BIG_RED") else None,
)
_MULTI_CELL_SUBTYPES = (
    "LargeBlockLandingGear",
    "LargeBlockLargeHydrogenThrust",
    "LargeHydrogenTank",
    "LargeBlockRadioAntenna",
    "LargeOreDetector",
)
_BIG_RED_SIZES = {
    "LargeBlockLandingGear": CellSize(1, 2, 3),
    "LargeBlockLargeHydrogenThrust": CellSize(3, 3, 3),
    "LargeHydrogenTank": CellSize(3, 3, 3),
    "LargeBlockRadioAntenna": CellSize(1, 6, 2),
    "LargeOreDetector": CellSize(1, 1, 2),
}
_PROPERTY_SIZES = (
    CellSize(1, 1, 1),
    CellSize(1, 1, 2),
    CellSize(1, 2, 3),
    CellSize(1, 6, 2),
    CellSize(3, 3, 3),
    CellSize(2, 2, 2),
    CellSize(2, 3, 4),
)
_PROPERTY_MINS = (
    GridCoordinate(0, 0, 0),
    GridCoordinate(2, 6, 4),
    GridCoordinate(-1, 7, 4),
    GridCoordinate(-3, 9, 5),
    GridCoordinate(5, -2, -4),
)
_CANONICAL_BLOCK_FIELDS = (
    "subtype_id",
    "geometry_id",
    "recipe_kind",
    "support_status",
    "grid_min",
    "min_serialized",
    "forward",
    "up",
    "orientation_serialized",
    "color_mask_hsv",
    "color_serialized",
    "appearance_support",
    "position_mm",
    "rotation",
    "source_index",
    "source",
)


def _aabb_dims(min_cell: GridCoordinate, max_cell: GridCoordinate) -> tuple[int, int, int]:
    return (
        max_cell.x - min_cell.x + 1,
        max_cell.y - min_cell.y + 1,
        max_cell.z - min_cell.z + 1,
    )


def _center_cells(
    min_cell: GridCoordinate, max_cell: GridCoordinate
) -> tuple[Fraction, Fraction, Fraction]:
    return (
        Fraction(min_cell.x + max_cell.x, 2),
        Fraction(min_cell.y + max_cell.y, 2),
        Fraction(min_cell.z + max_cell.z, 2),
    )


def _placement(size: CellSize, offset: ModelOffset | None = None) -> BlockPlacementDefinition:
    return BlockPlacementDefinition(
        size=size, model_offset=offset or ModelOffset.zero()
    )


def _parsed(
    *,
    subtype: str = "LargeBlockArmorBlock",
    min_cell: GridCoordinate = GridCoordinate(0, 0, 0),
    forward: Direction = Direction.FORWARD,
    up: Direction = Direction.UP,
    source_index: int = 0,
) -> ParsedBlock:
    return ParsedBlock(
        subtype_id=subtype,
        object_builder_type="MyObjectBuilder_CubeBlock",
        min=min_cell,
        min_serialized=True,
        forward=forward,
        up=up,
        orientation_serialized=True,
        color_mask_hsv=DEFAULT_COLOR_MASK_HSV,
        color_serialized=False,
        appearance_support=AppearanceSupport.DEFAULT,
        source_index=source_index,
        source="placement-test",
    )


def _one_block_xml(
    subtype: str = "LargeBlockArmorBlock",
    min_xml: str = '<Min x="2" y="1" z="-1" />',
    orientation_xml: str = "",
) -> str:
    return f"""<?xml version="1.0"?>
<Definitions xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <ShipBlueprints>
    <ShipBlueprint>
      <Id Type="MyObjectBuilder_ShipBlueprintDefinition" Subtype="place-test" />
      <CubeGrids>
        <CubeGrid>
          <GridSizeEnum>Large</GridSizeEnum>
          <CubeBlocks>
            <MyObjectBuilder_CubeBlock>
              <SubtypeName>{subtype}</SubtypeName>
              {min_xml}
              {orientation_xml}
            </MyObjectBuilder_CubeBlock>
          </CubeBlocks>
        </CubeGrid>
      </CubeGrids>
    </ShipBlueprint>
  </ShipBlueprints>
</Definitions>
"""


def _big_red_path() -> Path | None:
    for candidate in BIG_RED_CANDIDATES:
        if candidate is not None and candidate.is_file():
            return candidate
    return None


class OccupiedMaxTests(unittest.TestCase):
    def test_one_by_one_max_equals_min(self) -> None:
        min_cell = GridCoordinate(3, 1, -2)
        for forward, up in legal_orientations():
            rotation = rotation_from_forward_up(forward, up)
            maximum = occupied_max(min_cell, CellSize(1, 1, 1), rotation)
            self.assertEqual(maximum, min_cell)
            self.assertTrue(all(isinstance(v, int) for v in (maximum.x, maximum.y, maximum.z)))

    def test_default_one_by_one_by_two(self) -> None:
        maximum = occupied_max(
            GridCoordinate(0, 0, 0),
            CellSize(1, 1, 2),
            rotation_from_forward_up(Direction.FORWARD, Direction.UP),
        )
        self.assertEqual(maximum, GridCoordinate(0, 0, 1))

    def test_rotated_one_by_one_by_two(self) -> None:
        maximum = occupied_max(
            GridCoordinate(2, 9, 3),
            CellSize(1, 1, 2),
            rotation_from_forward_up(Direction.UP, Direction.FORWARD),
        )
        self.assertEqual(maximum, GridCoordinate(2, 10, 3))

    def test_default_one_by_two_by_three(self) -> None:
        maximum = occupied_max(
            GridCoordinate(0, 0, 0),
            CellSize(1, 2, 3),
            IDENTITY_ROTATION,
        )
        self.assertEqual(maximum, GridCoordinate(0, 1, 2))

    def test_rotated_one_by_two_by_three(self) -> None:
        maximum = occupied_max(
            GridCoordinate(2, 6, 4),
            CellSize(1, 2, 3),
            rotation_from_forward_up(Direction.BACKWARD, Direction.UP),
        )
        self.assertEqual(maximum, GridCoordinate(2, 7, 6))

    def test_one_by_six_by_two(self) -> None:
        maximum = occupied_max(
            GridCoordinate(-3, 9, 5),
            CellSize(1, 6, 2),
            rotation_from_forward_up(Direction.BACKWARD, Direction.UP),
        )
        self.assertEqual(maximum, GridCoordinate(-3, 14, 6))

    def test_three_by_three_by_three(self) -> None:
        maximum = occupied_max(
            GridCoordinate(-1, 7, 4),
            CellSize(3, 3, 3),
            rotation_from_forward_up(Direction.DOWN, Direction.RIGHT),
        )
        self.assertEqual(maximum, GridCoordinate(1, 9, 6))

    def test_negative_min(self) -> None:
        maximum = occupied_max(
            GridCoordinate(-4, -3, -8),
            CellSize(2, 2, 2),
            IDENTITY_ROTATION,
        )
        self.assertEqual(maximum, GridCoordinate(-3, -2, -7))

    def test_size_axes_rotate_before_aabb(self) -> None:
        # Local +Z extent (Back) becomes world +Y when Forward=Down, Up=Forward.
        maximum = occupied_max(
            GridCoordinate(0, 0, 0),
            CellSize(1, 1, 4),
            rotation_from_forward_up(Direction.DOWN, Direction.FORWARD),
        )
        self.assertEqual(maximum, GridCoordinate(0, 3, 0))

    def test_componentwise_abs_after_orientation(self) -> None:
        mapped = rotation_from_forward_up(Direction.BACKWARD, Direction.DOWN).apply(
            (0, 1, 2)
        )
        self.assertEqual(mapped, (0, -1, -2))
        maximum = occupied_max(
            GridCoordinate(2, 14, 4),
            CellSize(1, 2, 3),
            rotation_from_forward_up(Direction.BACKWARD, Direction.DOWN),
        )
        self.assertEqual(maximum, GridCoordinate(2, 15, 6))

    def test_occupied_max_is_integer(self) -> None:
        for size in _PROPERTY_SIZES:
            for min_cell in _PROPERTY_MINS:
                for forward, up in legal_orientations():
                    maximum = occupied_max(
                        min_cell, size, rotation_from_forward_up(forward, up)
                    )
                    self.assertIsInstance(maximum.x, int)
                    self.assertIsInstance(maximum.y, int)
                    self.assertIsInstance(maximum.z, int)
                    self.assertNotIsInstance(maximum.x, bool)


class OccupancyCenterAndTranslationTests(unittest.TestCase):
    def test_one_by_one_min_remains_cell_center(self) -> None:
        min_cell = GridCoordinate(4, -2, 7)
        translation = placement_translation_mm(
            min_cell,
            QUALIFIED_ONE_BY_ONE_PLACEMENT,
            IDENTITY_ROTATION,
        )
        self.assertEqual(translation, cell_center_mm(min_cell))
        pitch = LARGE_GRID_CELL_PITCH_MM
        self.assertEqual(translation.as_tuple(), (4 * pitch, -2 * pitch, 7 * pitch))

    def test_one_by_one_all_twenty_four_preserve_translation(self) -> None:
        min_cell = GridCoordinate(-3, 5, -1)
        expected = cell_center_mm(min_cell).as_tuple()
        for forward, up in legal_orientations():
            rotation = rotation_from_forward_up(forward, up)
            translation = placement_translation_mm(
                min_cell, QUALIFIED_ONE_BY_ONE_PLACEMENT, rotation
            )
            self.assertEqual(translation.as_tuple(), expected)
            self.assertEqual(rotation.determinant(), 1)

    def test_even_size_creates_half_cell_center(self) -> None:
        min_cell = GridCoordinate(2, 6, 4)
        maximum = occupied_max(
            min_cell,
            CellSize(1, 2, 3),
            rotation_from_forward_up(Direction.BACKWARD, Direction.UP),
        )
        self.assertEqual(maximum, GridCoordinate(2, 7, 6))
        center = _center_cells(min_cell, maximum)
        self.assertEqual(center, (Fraction(2), Fraction(13, 2), Fraction(5)))
        translation = occupancy_center_mm(min_cell, maximum)
        self.assertEqual(translation.as_tuple(), (5000, 16250, 12500))
        self.assertTrue(all(isinstance(v, int) for v in translation.as_tuple()))

    def test_odd_size_creates_integer_cell_center(self) -> None:
        min_cell = GridCoordinate(-1, 7, 4)
        maximum = occupied_max(
            min_cell,
            CellSize(3, 3, 3),
            rotation_from_forward_up(Direction.DOWN, Direction.RIGHT),
        )
        self.assertEqual(_center_cells(min_cell, maximum), (Fraction(0), Fraction(8), Fraction(5)))
        translation = occupancy_center_mm(min_cell, maximum)
        self.assertEqual(translation.as_tuple(), (0, 8 * 2500, 5 * 2500))

    def test_mixed_even_odd_size(self) -> None:
        min_cell = GridCoordinate(0, 0, 0)
        maximum = occupied_max(min_cell, CellSize(2, 3, 4), IDENTITY_ROTATION)
        self.assertEqual(maximum, GridCoordinate(1, 2, 3))
        center = _center_cells(min_cell, maximum)
        self.assertEqual(center, (Fraction(1, 2), Fraction(1), Fraction(3, 2)))
        translation = occupancy_center_mm(min_cell, maximum)
        pitch = LARGE_GRID_CELL_PITCH_MM
        self.assertEqual(
            translation.as_tuple(),
            (pitch // 2, pitch, (3 * pitch) // 2),
        )

    def test_zero_model_offset_is_occupancy_center(self) -> None:
        min_cell = GridCoordinate(2, 6, 4)
        placement = _placement(CellSize(1, 2, 3))
        rotation = rotation_from_forward_up(Direction.BACKWARD, Direction.UP)
        maximum = occupied_max(min_cell, placement.size, rotation)
        self.assertEqual(
            placement_translation_mm(min_cell, placement, rotation),
            occupancy_center_mm(min_cell, maximum),
        )

    def test_center_is_not_a_translation_input(self) -> None:
        parameters = inspect.signature(placement_translation_mm).parameters
        self.assertNotIn("center", parameters)
        self.assertNotIn("definition_center", parameters)
        min_cell = GridCoordinate(-1, 7, 4)
        rotation = rotation_from_forward_up(Direction.DOWN, Direction.RIGHT)
        translation = placement_translation_mm(
            min_cell, _placement(CellSize(3, 3, 3)), rotation
        )
        self.assertEqual(translation.as_tuple(), (0, 8 * 2500, 5 * 2500))
        # Wrong Center-based guess for LargeBlockLargeHydrogenThrust Center (1,1,2).
        wrong = rotation.apply((1, 1, 2))
        wrong_t = (
            (min_cell.x + wrong[0]) * LARGE_GRID_CELL_PITCH_MM,
            (min_cell.y + wrong[1]) * LARGE_GRID_CELL_PITCH_MM,
            (min_cell.z + wrong[2]) * LARGE_GRID_CELL_PITCH_MM,
        )
        self.assertNotEqual(translation.as_tuple(), wrong_t)

    def test_synthetic_nonzero_model_offset_rotates(self) -> None:
        min_cell = GridCoordinate(0, 0, 0)
        offset = ModelOffset.from_metres("0.1", 0, 0)
        identity_t = placement_translation_mm(
            min_cell, _placement(CellSize(3, 3, 3), offset), IDENTITY_ROTATION
        )
        # Occupancy center of 3×3×3 at Min=(0,0,0) is cell (1,1,1).
        pitch = LARGE_GRID_CELL_PITCH_MM
        self.assertEqual(identity_t.as_tuple(), (pitch + 100, pitch, pitch))
        rotated = placement_translation_mm(
            min_cell,
            _placement(CellSize(1, 1, 1), offset),
            rotation_from_forward_up(Direction.FORWARD, Direction.RIGHT),
        )
        # local +X (Right) maps to world -Y.
        self.assertEqual(rotated.as_tuple(), (0, -100, 0))

    def test_model_offset_units_convert_metres_to_mm(self) -> None:
        self.assertEqual(MILLIMETRES_PER_METRE, 1000)
        offset = ModelOffset.from_metres(1, "-1/2", Fraction(3, 10))
        translation = placement_translation_mm(
            GridCoordinate(0, 0, 0),
            _placement(CellSize(1, 1, 1), offset),
            IDENTITY_ROTATION,
        )
        self.assertEqual(translation.as_tuple(), (1000, -500, 300))

    def test_model_offset_is_not_multiplied_by_size(self) -> None:
        offset = ModelOffset.from_metres("0.25", 0, 0)
        origin = GridCoordinate(0, 0, 0)
        one = placement_translation_mm(
            origin,
            _placement(CellSize(1, 1, 1), offset),
            IDENTITY_ROTATION,
        )
        large = placement_translation_mm(
            origin,
            _placement(CellSize(3, 3, 3), offset),
            IDENTITY_ROTATION,
        )
        one_center = occupancy_center_mm(origin, occupied_max(origin, CellSize(1, 1, 1), IDENTITY_ROTATION))
        large_center = occupancy_center_mm(origin, occupied_max(origin, CellSize(3, 3, 3), IDENTITY_ROTATION))
        self.assertEqual(one.x - one_center.x, 250)
        self.assertEqual(large.x - large_center.x, 250)
        self.assertEqual(one.x - one_center.x, large.x - large_center.x)

    def test_model_offset_is_not_applied_twice(self) -> None:
        min_cell = GridCoordinate(1, 2, 3)
        offset = ModelOffset.from_metres(0, "0.2", 0)
        placement = _placement(CellSize(1, 1, 2), offset)
        rotation = rotation_from_forward_up(Direction.RIGHT, Direction.UP)
        once = placement_translation_mm(min_cell, placement, rotation)
        maximum = occupied_max(min_cell, placement.size, rotation)
        center = occupancy_center_mm(min_cell, maximum)
        extra = rotation.apply((0, 200, 0))
        self.assertEqual(
            once.as_tuple(),
            (center.x + extra[0], center.y + extra[1], center.z + extra[2]),
        )

    def test_float_model_offset_is_rejected(self) -> None:
        with self.assertRaises(InvalidModelOffsetError):
            ModelOffset.from_metres(0.1, 0, 0)


class InvalidInputTests(unittest.TestCase):
    def test_size_x_zero_fails(self) -> None:
        with self.assertRaises(InvalidBlockSizeError):
            occupied_max(GridCoordinate(0, 0, 0), CellSize(0, 1, 1), IDENTITY_ROTATION)

    def test_negative_size_fails(self) -> None:
        with self.assertRaises(InvalidBlockSizeError):
            BlockPlacementDefinition(CellSize(1, -2, 1), ModelOffset.zero())

    def test_non_cell_size_fails_closed(self) -> None:
        with self.assertRaises(InvalidBlockSizeError):
            occupied_max(GridCoordinate(0, 0, 0), (1, 1, 1), IDENTITY_ROTATION)  # type: ignore[arg-type]

    def test_invalid_pitch_fails_closed(self) -> None:
        with self.assertRaises(TransformError):
            occupancy_center_mm(GridCoordinate(0, 0, 0), GridCoordinate(0, 0, 0), 0)

    def test_invalid_orientation_still_fails(self) -> None:
        with self.assertRaises(InvalidOrientationError):
            rotation_from_forward_up(Direction.FORWARD, Direction.BACKWARD)


class BigRedReferenceVectorTests(unittest.TestCase):
    def _expect(
        self,
        min_xyz: tuple[int, int, int],
        forward: Direction,
        up: Direction,
        size: CellSize,
        max_xyz: tuple[int, int, int],
        center_xyz: tuple[float, float, float],
    ) -> None:
        min_cell = GridCoordinate(*min_xyz)
        rotation = rotation_from_forward_up(forward, up)
        maximum = occupied_max(min_cell, size, rotation)
        self.assertEqual((maximum.x, maximum.y, maximum.z), max_xyz)
        center = _center_cells(min_cell, maximum)
        self.assertEqual(
            tuple(float(component) for component in center),
            center_xyz,
        )
        translation = placement_translation_mm(
            min_cell, _placement(size), rotation
        )
        self.assertEqual(
            translation.as_tuple(),
            tuple(int(component * LARGE_GRID_CELL_PITCH_MM) for component in center),
        )
        self.assertEqual(rotation.determinant(), 1)

    def test_landing_gear_vector_one(self) -> None:
        self._expect(
            (2, 14, 4),
            Direction.BACKWARD,
            Direction.DOWN,
            CellSize(1, 2, 3),
            (2, 15, 6),
            (2.0, 14.5, 5.0),
        )

    def test_landing_gear_vector_two(self) -> None:
        self._expect(
            (2, 6, 4),
            Direction.BACKWARD,
            Direction.UP,
            CellSize(1, 2, 3),
            (2, 7, 6),
            (2.0, 6.5, 5.0),
        )

    def test_large_thrust_vector(self) -> None:
        self._expect(
            (-1, 7, 4),
            Direction.DOWN,
            Direction.RIGHT,
            CellSize(3, 3, 3),
            (1, 9, 6),
            (0.0, 8.0, 5.0),
        )

    def test_hydrogen_tank_vector(self) -> None:
        self._expect(
            (-1, 10, 4),
            Direction.LEFT,
            Direction.UP,
            CellSize(3, 3, 3),
            (1, 12, 6),
            (0.0, 11.0, 5.0),
        )

    def test_antenna_vector(self) -> None:
        self._expect(
            (-3, 9, 5),
            Direction.BACKWARD,
            Direction.UP,
            CellSize(1, 6, 2),
            (-3, 14, 6),
            (-3.0, 11.5, 5.5),
        )

    def test_ore_detector_vector(self) -> None:
        self._expect(
            (2, 9, 3),
            Direction.UP,
            Direction.FORWARD,
            CellSize(1, 1, 2),
            (2, 10, 3),
            (2.0, 9.5, 3.0),
        )


class PropertyOrientationTests(unittest.TestCase):
    def test_all_orientations_and_sizes_are_permutations(self) -> None:
        for size in _PROPERTY_SIZES:
            product = size.x * size.y * size.z
            local = (size.x, size.y, size.z)
            for min_cell in _PROPERTY_MINS:
                for forward, up in legal_orientations():
                    rotation = rotation_from_forward_up(forward, up)
                    self.assertEqual(rotation.determinant(), 1)
                    maximum = occupied_max(min_cell, size, rotation)
                    dims = _aabb_dims(min_cell, maximum)
                    self.assertEqual(sorted(dims), sorted(local))
                    self.assertEqual(dims[0] * dims[1] * dims[2], product)
                    translation = placement_translation_mm(
                        min_cell, _placement(size), rotation
                    )
                    self.assertTrue(
                        all(isinstance(v, int) for v in translation.as_tuple())
                    )


class OneByOneRegressionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.digest = hashlib.sha256(FIXTURE_PATH.read_bytes()).hexdigest()
        cls.catalog = load_default_catalog()
        cls.parsed = parse_blueprint(FIXTURE_PATH)
        cls.ir = build_canonical_blueprint(cls.parsed, cls.catalog)

    def test_fixture_sha256_unchanged(self) -> None:
        self.assertEqual(self.digest, EXPECTED_SHA256)

    def test_acceptance_fixture_transforms_unchanged(self) -> None:
        pitch = LARGE_GRID_CELL_PITCH_MM
        for parsed, block in zip(
            self.parsed.grid.blocks, self.ir.grid.blocks, strict=True
        ):
            self.assertEqual(
                block.position_mm,
                cell_center_mm(parsed.min, pitch),
            )
            self.assertEqual(
                block.rotation,
                rotation_from_forward_up(parsed.forward, parsed.up),
            )
            self.assertEqual(block.rotation.determinant(), 1)

    def test_catalog_one_by_one_equals_legacy_cell_center(self) -> None:
        parsed = parse_blueprint_xml(_one_block_xml())
        ir = build_canonical_blueprint(parsed, self.catalog)
        block = ir.grid.blocks[0]
        self.assertEqual(
            block.position_mm,
            cell_center_mm(parsed.grid.blocks[0].min),
        )
        self.assertEqual(self.catalog.lookup(block.subtype_id).observed.size, CellSize(1, 1, 1))

    def test_existing_rotation_matrices_unchanged(self) -> None:
        self.assertEqual(
            rotation_from_forward_up(Direction.FORWARD, Direction.UP),
            IDENTITY_ROTATION,
        )
        self.assertEqual(
            rotation_from_forward_up(Direction.DOWN, Direction.FORWARD).columns,
            ((1, 0, 0), (0, 0, -1), (0, 1, 0)),
        )
        self.assertEqual(
            rotation_from_forward_up(Direction.BACKWARD, Direction.DOWN).columns,
            ((1, 0, 0), (0, -1, 0), (0, 0, -1)),
        )


class RuntimeEligibilityUnchangedTests(unittest.TestCase):
    def test_multi_cell_vanilla_identities_remain_unresolved(self) -> None:
        catalog = load_default_catalog()
        for subtype, size in _BIG_RED_SIZES.items():
            definition = TargetedDefinition(
                subtype_id=subtype,
                type_id="CubeBlock",
                cube_size="Large",
                size=size,
                block_topology="TriangleMesh",
                cube_topology=None,
                primary_model="Models\\Cubes\\Large\\probe.mwm",
                has_subparts=False,
                model_count=1,
                source_relative="Data/CubeBlocks/probe.sbc",
            )
            reason = eligibility_reason(definition)
            self.assertIsNotNone(reason)
            self.assertIn("1x1x1", reason or "")
            result = resolve_vanilla_geometry(subtype, catalog)
            self.assertNotEqual(result.kind, VanillaResolveKind.RUNTIME_VANILLA)

    def test_install_free_packaged_armor_works_without_game_root(self) -> None:
        catalog = load_default_catalog()
        parsed = parse_blueprint_xml(_one_block_xml())
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("SE2CAD_GAME_ROOT", None)
            os.environ.pop("SE2CAD_SDK_ROOT", None)
            with patch(
                "se2cad.vanilla.roots.discover_local_config", return_value=None
            ):
                ir = build_canonical_blueprint(parsed, catalog)
                preflight = compute_conversion_preflight(parsed, catalog)
        self.assertEqual(ir.grid.blocks[0].geometry_id, "large_armor_block")
        self.assertEqual(preflight.supported_count, 1)
        self.assertEqual(preflight.unknown_count, 0)

    def test_permissive_filler_keeps_one_by_one_min_center(self) -> None:
        parsed = parse_blueprint_xml(
            _one_block_xml(subtype="LargeBlockLandingGear")
        )
        result = convert_blueprint(
            parsed, load_default_catalog(), ConversionPolicy.PERMISSIVE
        )
        block = result.ir.grid.blocks[0]
        self.assertEqual(block.geometry_id, FILLER_GEOMETRY_ID)
        self.assertEqual(block.position_mm, cell_center_mm(block.grid_min))
        self.assertEqual(result.filler_count, 1)


class IrContractTests(unittest.TestCase):
    def test_canonical_block_fields_are_unchanged(self) -> None:
        names = tuple(field.name for field in dataclasses.fields(CanonicalBlock))
        self.assertEqual(names, _CANONICAL_BLOCK_FIELDS)

    def test_serialization_remains_deterministic(self) -> None:
        catalog = load_default_catalog()
        parsed = parse_blueprint(FIXTURE_PATH)
        first = build_canonical_blueprint(parsed, catalog)
        second = build_canonical_blueprint(parsed, catalog)
        payload = [
            (
                block.subtype_id,
                block.geometry_id,
                block.grid_min,
                block.position_mm.as_tuple(),
                block.rotation.columns,
                block.source_index,
            )
            for block in first.grid.blocks
        ]
        again = [
            (
                block.subtype_id,
                block.geometry_id,
                block.grid_min,
                block.position_mm.as_tuple(),
                block.rotation.columns,
                block.source_index,
            )
            for block in second.grid.blocks
        ]
        self.assertEqual(payload, again)
        self.assertEqual(
            [item[5] for item in payload],
            list(range(24)),
        )

    def test_ir_can_compute_multicell_without_granting_support(self) -> None:
        parsed = _parsed(
            subtype="LargeBlockLandingGear",
            min_cell=GridCoordinate(2, 6, 4),
            forward=Direction.BACKWARD,
            up=Direction.UP,
        )
        block = canonical_block_from_parsed(
            parsed,
            geometry_id=FILLER_GEOMETRY_ID,
            recipe_kind=RecipeKind.UNSUPPORTED,
            support_status=SupportStatus.UNSUPPORTED,
            pitch_mm=LARGE_GRID_CELL_PITCH_MM,
            placement=_placement(CellSize(1, 2, 3)),
        )
        self.assertEqual(block.position_mm.as_tuple(), (5000, 16250, 12500))
        self.assertEqual(block.support_status, SupportStatus.UNSUPPORTED)

    def test_placement_from_catalog_entry_uses_observed_size(self) -> None:
        entry = load_default_catalog().lookup("LargeBlockArmorBlock")
        placement = placement_from_catalog_entry(entry)
        self.assertEqual(placement.size, CellSize(1, 1, 1))
        self.assertTrue(placement.model_offset.is_zero())


class NeutralityAndBoundaryTests(unittest.TestCase):
    def test_no_solidworks_types_in_transform_or_ir(self) -> None:
        forbidden = (
            r"(?m)^\s*(?:import|from)\s+(?:solidworks|win32com|pythoncom|blender|bpy)\b",
            r"(?m)^\s*(?:import|from)\s+se2cad\.(?:vanilla|discovery|solidworks)\b",
        )
        for root in (TRANSFORM_ROOT, IR_ROOT):
            for path in root.glob("*.py"):
                text = path.read_text(encoding="utf-8")
                for pattern in forbidden:
                    self.assertNotRegex(text, pattern, msg=f"{path} {pattern}")
                self.assertNotIn("SE2CAD_GAME_ROOT", text)
                self.assertNotIn("game_root", text)
                if path.name != "__init__.py":
                    self.assertNotRegex(text, r"\b2500\b")

    def test_no_subtype_specific_placement_branch(self) -> None:
        for path in list(TRANSFORM_ROOT.glob("*.py")) + list(IR_ROOT.glob("*.py")):
            text = path.read_text(encoding="utf-8")
            for subtype in _MULTI_CELL_SUBTYPES:
                self.assertNotIn(subtype, text, msg=f"{path.name} mentions {subtype}")
        tree = ast.parse((TRANSFORM_ROOT / "placement.py").read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.If):
                snippet = ast.dump(node.test)
                self.assertNotIn("LandingGear", snippet)
                self.assertNotIn("subtype", snippet.lower())

    def test_unknown_blocks_are_not_silently_sized(self) -> None:
        source = (REPO_ROOT / "src/se2cad/ir/convert.py").read_text(encoding="utf-8")
        self.assertIn("QUALIFIED_ONE_BY_ONE_PLACEMENT", source)
        self.assertIn("designated 1×1×1 filler placement contract", source)
        self.assertNotIn("Size(1, 1, 1)", (REPO_ROOT / "src/se2cad/policy/convert.py").read_text(encoding="utf-8"))


class BigRedReadOnlyVerificationTests(unittest.TestCase):
    def test_big_red_policy_counts_and_expected_table(self) -> None:
        blueprint = _big_red_path()
        if blueprint is None:
            self.skipTest("Big Red blueprint is not present")
        parsed = parse_blueprint(blueprint)
        catalog = load_default_catalog()
        rows = []
        for block in parsed.grid.blocks:
            if block.subtype_id not in _BIG_RED_SIZES:
                continue
            size = _BIG_RED_SIZES[block.subtype_id]
            rotation = rotation_from_forward_up(block.forward, block.up)
            maximum = occupied_max(block.min, size, rotation)
            center = _center_cells(block.min, maximum)
            translation = placement_translation_mm(
                block.min, _placement(size), rotation
            )
            rows.append(
                {
                    "subtype": block.subtype_id,
                    "source_index": block.source_index,
                    "min": (block.min.x, block.min.y, block.min.z),
                    "max": (maximum.x, maximum.y, maximum.z),
                    "forward": block.forward.value,
                    "up": block.up.value,
                    "occupancy_center": tuple(float(c) for c in center),
                    "translation_mm": translation.as_tuple(),
                }
            )
        self.assertEqual(len(rows), 10)
        counts = Counter(row["subtype"] for row in rows)
        self.assertEqual(counts["LargeBlockLandingGear"], 4)
        self.assertEqual(counts["LargeBlockLargeHydrogenThrust"], 3)
        self.assertEqual(counts["LargeHydrogenTank"], 1)
        self.assertEqual(counts["LargeBlockRadioAntenna"], 1)
        self.assertEqual(counts["LargeOreDetector"], 1)
        dest_dir = REPO_ROOT / "tmp" / "generated" / "s2c-11.10.1"
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest = dest_dir / "bigred_multicell_expected_transforms.csv"
        with dest.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerow(
                [
                    "subtype",
                    "source_index",
                    "min",
                    "max",
                    "forward",
                    "up",
                    "occupancy_center",
                    "translation_mm",
                ]
            )
            for row in rows:
                writer.writerow(
                    [
                        row["subtype"],
                        row["source_index"],
                        row["min"],
                        row["max"],
                        row["forward"],
                        row["up"],
                        row["occupancy_center"],
                        row["translation_mm"],
                    ]
                )

        game = try_load_game_content_root()
        sdk = try_load_sdk_root()
        if game is None or sdk is None:
            self.skipTest("game/SDK roots are not configured for Big Red policy counts")
        result = convert_blueprint(parsed, catalog, ConversionPolicy.PERMISSIVE)
        preflight = result.preflight
        self.assertEqual(preflight.block_count, 136)
        self.assertEqual(preflight.supported_count, 126)
        self.assertEqual(preflight.unknown_count, 10)
        self.assertEqual(preflight.unsupported_count, 0)
        self.assertEqual(result.filler_count, 10)
        unknown = {item.subtype_id for item in preflight.blocks if item.catalog_outcome is CatalogOutcome.UNKNOWN}
        self.assertTrue(set(_MULTI_CELL_SUBTYPES) <= unknown)
        for block in result.ir.grid.blocks:
            if block.subtype_id in _BIG_RED_SIZES:
                self.assertEqual(block.geometry_id, FILLER_GEOMETRY_ID)
                self.assertEqual(block.position_mm, cell_center_mm(block.grid_min))


if __name__ == "__main__":
    unittest.main()
