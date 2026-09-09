"""Backend-independent tests for S2C-5.1.1 assembly placement."""

from __future__ import annotations

import tempfile
import unittest
from collections import Counter
from pathlib import Path

from se2cad.catalog import LARGE_GRID_CELL_PITCH_MM, load_default_catalog
from se2cad.ir import build_canonical_blueprint, component_name_from_block
from se2cad.parser import Direction, parse_blueprint
from se2cad.solidworks import (
    AssemblyIdentityError,
    GeneratedRootError,
    MissingCanonicalPartError,
    UnknownCanonicalPartError,
    assembly_path_for,
    logical_assembly_filename,
    placements_from_ir,
    require_canonical_part_files,
    solidworks_arraydata,
)
from se2cad.solidworks.artifacts import (
    assert_overwrite_is_canonical,
    is_assembly_artifact_filename,
)
from se2cad.solidworks.transform_pack import arraydata_axes, arraydata_translation_m
from se2cad.transform import IDENTITY_ROTATION, rotation_from_forward_up

REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURE_PATH = REPO_ROOT / "fixtures/acceptance/four-block-armor-asymmetric/bp.sbc"


class AssemblyNamingTests(unittest.TestCase):
    def test_identity_becomes_sldasm_filename(self) -> None:
        self.assertEqual(
            logical_assembly_filename("se2cad-test1"), "se2cad-test1.SLDASM"
        )
        self.assertTrue(is_assembly_artifact_filename("se2cad-test1.SLDASM"))

    def test_unsafe_identity_is_rejected(self) -> None:
        for identity in ("", "../escape", "a/b", r"a\b", "has space", "ünicode"):
            with self.subTest(identity=identity):
                with self.assertRaises(AssemblyIdentityError):
                    logical_assembly_filename(identity)

    def test_assembly_stays_inside_generated_root(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            dest = assembly_path_for(Path(tmp), "se2cad-test1")
            dest.relative_to(Path(tmp).resolve())
            self.assertEqual(dest.name, "se2cad-test1.SLDASM")

    def test_overwrite_of_owned_assembly_is_allowed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            owned = Path(tmp) / "se2cad-test1.SLDASM"
            owned.write_bytes(b"stub")
            assert_overwrite_is_canonical(owned)

    def test_overwrite_of_unrelated_assembly_name_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            foreign = Path(tmp) / "notes.txt"
            foreign.write_text("no", encoding="utf-8")
            with self.assertRaises(GeneratedRootError):
                assert_overwrite_is_canonical(foreign)


class MissingPartTests(unittest.TestCase):
    def test_missing_canonical_parts_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(MissingCanonicalPartError):
                require_canonical_part_files(Path(tmp))

    def test_all_four_parts_resolve(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for name in (
                "large_armor_block.SLDPRT",
                "large_armor_slope.SLDPRT",
                "large_armor_corner.SLDPRT",
                "large_armor_corner_inv.SLDPRT",
            ):
                (root / name).write_bytes(b"stub")
            found = require_canonical_part_files(root)
            self.assertEqual(len(found), 4)
            for path in found.values():
                path.relative_to(root.resolve())


class FixturePlacementTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        parsed = parse_blueprint(FIXTURE_PATH)
        cls.ir = build_canonical_blueprint(parsed, load_default_catalog())
        cls.placements = placements_from_ir(cls.ir)

    def test_preserves_multiplicity_and_order(self) -> None:
        self.assertEqual(len(self.placements), 24)
        self.assertEqual(len(self.placements), self.ir.grid.block_count)
        self.assertEqual(
            [item.source_index for item in self.placements],
            [block.source_index for block in self.ir.grid.blocks],
        )
        self.assertEqual(
            Counter(item.geometry_id for item in self.placements),
            Counter(
                {
                    "large_armor_block": 9,
                    "large_armor_slope": 12,
                    "large_armor_corner": 2,
                    "large_armor_corner_inv": 1,
                }
            ),
        )
        self.assertEqual(
            [item.part_filename for item in self.placements],
            [f"{item.geometry_id}.SLDPRT" for item in self.placements],
        )
        self.assertEqual(
            [item.component_name for item in self.placements],
            [component_name_from_block(block) for block in self.ir.grid.blocks],
        )
        self.assertEqual(
            len({item.component_name for item in self.placements}),
            24,
        )

    def test_subtype_maps_to_canonical_part(self) -> None:
        expected = {
            "LargeBlockArmorBlock": "large_armor_block.SLDPRT",
            "LargeBlockArmorSlope": "large_armor_slope.SLDPRT",
            "LargeBlockArmorCorner": "large_armor_corner.SLDPRT",
            "LargeBlockArmorCornerInv": "large_armor_corner_inv.SLDPRT",
        }
        for placement, block in zip(self.placements, self.ir.grid.blocks, strict=True):
            self.assertEqual(placement.subtype_id, block.subtype_id)
            self.assertEqual(placement.geometry_id, block.geometry_id)
            self.assertEqual(placement.part_filename, expected[block.subtype_id])
            self.assertEqual(
                placement.component_name, component_name_from_block(block)
            )
            self.assertEqual(placement.position_mm, block.position_mm.as_tuple())
            self.assertEqual(placement.rotation, block.rotation)

    def test_unknown_geometry_id_fails_closed(self) -> None:
        from dataclasses import replace

        bad = replace(self.ir.grid.blocks[0], geometry_id="not_a_canonical_part")
        grid = replace(self.ir.grid, blocks=(bad,) + self.ir.grid.blocks[1:])
        ir = replace(self.ir, grid=grid)
        with self.assertRaises(UnknownCanonicalPartError):
            placements_from_ir(ir)

    def test_representative_translations_match_ir(self) -> None:
        pitch = LARGE_GRID_CELL_PITCH_MM
        by_min = {item.grid_min: item for item in self.placements}
        self.assertEqual(by_min[(0, 0, 0)].position_mm, (0, 0, 0))
        self.assertEqual(by_min[(1, 0, 0)].position_mm, (pitch, 0, 0))
        self.assertEqual(by_min[(0, 0, 1)].position_mm, (0, 0, pitch))
        self.assertEqual(by_min[(0, 0, -1)].position_mm, (0, 0, -pitch))
        self.assertEqual(
            by_min[(5, 2, -2)].position_mm, (5 * pitch, 2 * pitch, -2 * pitch)
        )

    def test_omitted_orientation_is_identity(self) -> None:
        omitted = [item for item in self.placements if not item.orientation_serialized]
        self.assertEqual(len(omitted), 15)
        for item in omitted:
            self.assertTrue(item.rotation.is_identity())
            self.assertEqual(item.rotation, IDENTITY_ROTATION)


class TransformPackTests(unittest.TestCase):
    def test_identity_at_origin_is_identity_arraydata(self) -> None:
        data = solidworks_arraydata(IDENTITY_ROTATION, (0, 0, 0))
        self.assertEqual(len(data), 16)
        self.assertEqual(
            data,
            (1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0),
        )

    def test_translation_is_metres_with_no_half_cell(self) -> None:
        data = solidworks_arraydata(IDENTITY_ROTATION, (2500, 0, -2500))
        self.assertEqual(arraydata_translation_m(data), (2.5, 0.0, -2.5))
        self.assertEqual(arraydata_axes(data), ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0)))
        self.assertEqual(data[12], 1.0)

    def test_down_right_uses_column_axes_not_row_major(self) -> None:
        rotation = rotation_from_forward_up(Direction.DOWN, Direction.RIGHT)
        data = solidworks_arraydata(rotation, (2500, 2500, 0))
        # Columns of R are the SolidWorks X/Y/Z axes (official ArrayData rows).
        self.assertEqual(arraydata_axes(data), (rotation.c0, rotation.c1, rotation.c2))
        self.assertEqual(arraydata_translation_m(data), (2.5, 2.5, 0.0))
        row_major = (
            float(rotation.rows[0][0]),
            float(rotation.rows[0][1]),
            float(rotation.rows[0][2]),
            float(rotation.rows[1][0]),
            float(rotation.rows[1][1]),
            float(rotation.rows[1][2]),
            float(rotation.rows[2][0]),
            float(rotation.rows[2][1]),
            float(rotation.rows[2][2]),
        )
        self.assertNotEqual(data[:9], row_major)
        self.assertEqual(rotation.determinant(), 1)

    def test_down_forward_matches_qualified_columns(self) -> None:
        rotation = rotation_from_forward_up(Direction.DOWN, Direction.FORWARD)
        data = solidworks_arraydata(rotation, (0, 0, -2500))
        self.assertEqual(arraydata_axes(data), rotation.columns)
        self.assertEqual(data[:9], (1.0, 0.0, 0.0, 0.0, 0.0, -1.0, 0.0, 1.0, 0.0))
        self.assertEqual(arraydata_translation_m(data), (0.0, 0.0, -2.5))

    def test_scale_is_one_and_unused_are_zero(self) -> None:
        rotation = rotation_from_forward_up(Direction.BACKWARD, Direction.DOWN)
        data = solidworks_arraydata(rotation, (12500, 0, 0))
        self.assertEqual(data[12:], (1.0, 0.0, 0.0, 0.0))
        self.assertEqual(rotation.determinant(), 1)

    def test_no_sign_inversion_or_reflection_in_legal_rotations(self) -> None:
        parsed = parse_blueprint(FIXTURE_PATH)
        ir = build_canonical_blueprint(parsed, load_default_catalog())
        for block in ir.grid.blocks:
            data = solidworks_arraydata(block.rotation, block.position_mm.as_tuple())
            self.assertEqual(arraydata_axes(data), block.rotation.columns)
            self.assertEqual(block.rotation.determinant(), 1)
            self.assertAlmostEqual(
                arraydata_translation_m(data)[0] * 1000, block.position_mm.x
            )


class ComAssembleContractTests(unittest.TestCase):
    def test_create_transform_is_not_called(self) -> None:
        import ast

        path = (
            Path(__file__).resolve().parents[1]
            / "src"
            / "se2cad"
            / "solidworks"
            / "com_assemble.py"
        )
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                self.assertNotEqual(node.func.attr, "CreateTransform")
        source = path.read_text(encoding="utf-8")
        self.assertIn("AddComponent5", source)
        self.assertIn("UnfixComponent", source)
        self.assertIn("apply_component_name", source)
        self.assertIn("Name2", source)
        self.assertIn("swExtRefUpdateCompNames", source)
        self.assertIn("Select", source)
        self.assertIn("VT_ARRAY", source)
        self.assertIn("VT_R8", source)

    def test_no_mate_creation_calls(self) -> None:
        source = (
            Path(__file__).resolve().parents[1]
            / "src"
            / "se2cad"
            / "solidworks"
            / "com_assemble.py"
        ).read_text(encoding="utf-8")
        for token in ("AddMate", "CreateMate", "MateFeature", "InsertMate"):
            self.assertNotIn(token, source)


class _FakeTransform:
    def __init__(self) -> None:
        self.ArrayData = (
            1.0, 0.0, 0.0,
            0.0, 1.0, 0.0,
            0.0, 0.0, 1.0,
            0.0, 0.0, 0.0,
            1.0, 0.0, 0.0, 0.0,
        )


class _FakeComponent:
    def __init__(self, part_path: Path) -> None:
        self._short = part_path.stem
        self._path = part_path
        self.IsFixed = False
        self.Transform2 = _FakeTransform()

    @property
    def Name2(self) -> str:
        return f"{self._short}-1"

    @Name2.setter
    def Name2(self, value: str) -> None:
        self._short = value

    def GetPathName(self) -> str:
        return str(self._path)

    def GetMates(self):
        return None

    def Select(self, _flag: bool) -> bool:
        return True


class _FakeAssembly:
    def __init__(self) -> None:
        self.components: list[_FakeComponent] = []
        self.FirstFeature = None

    def AddComponent5(self, path: str, *_args):
        component = _FakeComponent(Path(path))
        self.components.append(component)
        return component

    def UnfixComponent(self) -> None:
        return None

    def ClearSelection2(self, _flag: bool) -> None:
        return None

    def EditRebuild3(self) -> bool:
        return True

    def GetComponents(self, _top_level: bool) -> list[_FakeComponent]:
        return list(self.components)

    def GetType(self) -> int:
        return 2


class _FakeApp:
    def __init__(self) -> None:
        self.update_comp_names = True

    def GetUserPreferenceToggle(self, _pref: int) -> bool:
        return self.update_comp_names

    def SetUserPreferenceToggle(self, _pref: int, value: bool) -> None:
        self.update_comp_names = bool(value)


class _FakeSession:
    def __init__(self) -> None:
        self.app = _FakeApp()
        self.constants = type("C", (), {"swExtRefUpdateCompNames": 18})()


class HermeticInsertionNameTests(unittest.TestCase):
    def test_insert_requests_ir_derived_names(self) -> None:
        from unittest.mock import patch

        from se2cad.solidworks.com_assemble import (
            apply_component_name,
            assert_assembly_matches,
            feature_manager_short_name,
            insert_placements,
        )

        parsed = parse_blueprint(FIXTURE_PATH)
        ir = build_canonical_blueprint(parsed, load_default_catalog())
        placements = placements_from_ir(ir)[:3]
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            part_paths = {}
            for item in placements:
                dest = root / item.part_filename
                dest.write_bytes(b"stub")
                part_paths[item.geometry_id] = dest
            assembly = _FakeAssembly()
            session = _FakeSession()
            with patch(
                "se2cad.solidworks.com_assemble.variant_r8",
                side_effect=lambda values: tuple(float(v) for v in values),
            ):
                placed = insert_placements(session, assembly, placements, part_paths)
            self.assertFalse(session.app.update_comp_names)
            self.assertEqual(len(placed), 3)
            for item, component in zip(placed, assembly.components, strict=True):
                self.assertEqual(item.component_name, item.placement.component_name)
                self.assertEqual(
                    feature_manager_short_name(component.Name2),
                    item.placement.component_name,
                )
                self.assertEqual(
                    apply_component_name(
                        assembly, component, item.placement.component_name
                    ),
                    f"{item.placement.component_name}-1",
                )
            matched = assert_assembly_matches(assembly, placements, root)
            self.assertEqual(
                [item.component_name for item in matched],
                [item.component_name for item in placements],
            )


if __name__ == "__main__":
    unittest.main()
