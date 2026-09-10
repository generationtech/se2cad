"""Acceptance tests against the qualified S2C-1.1.1 fixture."""

from __future__ import annotations

import hashlib
import unittest
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path

from se2cad.parser import (
    DEFAULT_COLOR_MASK_HSV,
    AppearanceSupport,
    Direction,
    GridSize,
    parse_blueprint,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURE_PATH = REPO_ROOT / "fixtures/acceptance/four-block-armor-asymmetric/bp.sbc"
EXPECTED_SHA256 = "99c93d199a6dc960918ecd70dcecbb154c16e18d5638d359a279a15140a95b31"


class AcceptanceFixtureParserTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.digest = hashlib.sha256(FIXTURE_PATH.read_bytes()).hexdigest()
        cls.parsed = parse_blueprint(FIXTURE_PATH)
        cls.raw_blocks = _raw_cube_blocks(FIXTURE_PATH)

    def test_fixture_sha256_is_the_qualified_file(self) -> None:
        self.assertEqual(self.digest, EXPECTED_SHA256)
        self.assertEqual(len(self.raw_blocks), 24)

    def test_single_large_grid_identity(self) -> None:
        self.assertEqual(self.parsed.identity_subtype, "se2cad-test1")
        self.assertEqual(self.parsed.grid.display_name, "se2cad-test1")
        self.assertEqual(self.parsed.grid.grid_size, GridSize.LARGE)
        self.assertEqual(self.parsed.grid.block_count, 24)
        self.assertEqual(len(self.parsed.grid.blocks), 24)

    def test_ship_display_name_is_preserved_exactly(self) -> None:
        self.assertEqual(self.parsed.display_name, "\ue030Kolyma")

    def test_subtype_counts_and_exact_identities(self) -> None:
        counts = Counter(block.subtype_id for block in self.parsed.grid.blocks)
        self.assertEqual(
            dict(counts),
            {
                "LargeBlockArmorBlock": 9,
                "LargeBlockArmorSlope": 12,
                "LargeBlockArmorCorner": 2,
                "LargeBlockArmorCornerInv": 1,
            },
        )
        self.assertNotIn("LargeBlockArmor", counts)
        raw_counts = Counter(_raw_subtype(block) for block in self.raw_blocks)
        self.assertEqual(dict(counts), dict(raw_counts))

    def test_coordinates_match_source_xml_semantics(self) -> None:
        parsed_positions = []
        for parsed, raw in zip(self.parsed.grid.blocks, self.raw_blocks, strict=True):
            raw_min = raw.find("Min")
            if raw_min is None:
                self.assertFalse(parsed.min_serialized)
                self.assertEqual((parsed.min.x, parsed.min.y, parsed.min.z), (0, 0, 0))
            else:
                self.assertTrue(parsed.min_serialized)
                self.assertEqual(parsed.min.x, int(raw_min.attrib["x"]))
                self.assertEqual(parsed.min.y, int(raw_min.attrib["y"]))
                self.assertEqual(parsed.min.z, int(raw_min.attrib["z"]))
            parsed_positions.append((parsed.min.x, parsed.min.y, parsed.min.z))

        self.assertEqual(len(set(parsed_positions)), 24)
        xs, ys, zs = zip(*parsed_positions)
        self.assertEqual((min(xs), max(xs)), (0, 5))
        self.assertEqual((min(ys), max(ys)), (0, 2))
        self.assertEqual((min(zs), max(zs)), (-2, 1))

    def test_explicit_and_omitted_orientations_match_source_semantics(self) -> None:
        omitted = 0
        explicit_pairs: Counter[tuple[str, str]] = Counter()
        for parsed, raw in zip(self.parsed.grid.blocks, self.raw_blocks, strict=True):
            raw_orientation = raw.find("BlockOrientation")
            if raw_orientation is None:
                omitted += 1
                self.assertFalse(parsed.orientation_serialized)
                self.assertEqual(parsed.forward, Direction.FORWARD)
                self.assertEqual(parsed.up, Direction.UP)
            else:
                self.assertTrue(parsed.orientation_serialized)
                self.assertEqual(parsed.forward.value, raw_orientation.attrib["Forward"])
                self.assertEqual(parsed.up.value, raw_orientation.attrib["Up"])
                explicit_pairs[(parsed.forward.value, parsed.up.value)] += 1

        self.assertEqual(omitted, 15)
        self.assertEqual(
            dict(explicit_pairs),
            {
                ("Down", "Forward"): 5,
                ("Down", "Right"): 1,
                ("Forward", "Right"): 1,
                ("Down", "Left"): 1,
                ("Backward", "Down"): 1,
            },
        )

    def test_omitted_colormaskhsv_is_default_on_every_fixture_block(self) -> None:
        for parsed, raw in zip(self.parsed.grid.blocks, self.raw_blocks, strict=True):
            self.assertIsNone(raw.find("ColorMaskHSV"))
            self.assertFalse(parsed.color_serialized)
            self.assertEqual(parsed.appearance_support, AppearanceSupport.DEFAULT)
            self.assertEqual(parsed.color_mask_hsv, DEFAULT_COLOR_MASK_HSV)

    def test_block_order_and_source_context(self) -> None:
        for index, block in enumerate(self.parsed.grid.blocks):
            self.assertEqual(block.source_index, index)
            self.assertEqual(block.source, str(FIXTURE_PATH))
            self.assertEqual(block.subtype_id, _raw_subtype(self.raw_blocks[index]))
            self.assertEqual(block.object_builder_type, "MyObjectBuilder_CubeBlock")


def _raw_cube_blocks(path: Path) -> list[ET.Element]:
    root = ET.fromstring(path.read_text(encoding="utf-8"))
    blocks = []
    for el in root.iter():
        tag = el.tag.rsplit("}", 1)[-1]
        if tag == "MyObjectBuilder_CubeBlock":
            blocks.append(el)
    return blocks


def _raw_subtype(block: ET.Element) -> str:
    subtype = block.find("SubtypeName")
    if subtype is None or subtype.text is None:
        raise AssertionError("fixture block missing SubtypeName")
    return subtype.text


if __name__ == "__main__":
    unittest.main()
