"""Ordinary tests for optional treated-part assembly selection (S2C-10.3.1)."""

from __future__ import annotations

import inspect
import tempfile
import unittest
from pathlib import Path

from se2cad.catalog import load_default_catalog
from se2cad.ir import build_canonical_blueprint, component_name_from_block
from se2cad.library import EDGE_TREATMENT_CHAMFER, EDGE_TREATMENT_OFF
from se2cad.parser import parse_blueprint
from se2cad.solidworks import (
    MissingCanonicalPartError,
    generate_assembly,
    is_treated_artifact_filename,
    logical_assembly_part_filename,
    logical_part_filename,
    logical_treated_part_filename,
    placements_from_ir,
    require_canonical_part_files,
)
from se2cad.solidworks.assemble import (
    _parse_assemble_argv,
    generate_assembly_from_ir,
)
from se2cad.solidworks.placement import ComponentPlacement


REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURE_PATH = REPO_ROOT / "fixtures/acceptance/four-block-armor-asymmetric/bp.sbc"


def _fixture_ir():
    return build_canonical_blueprint(parse_blueprint(FIXTURE_PATH), load_default_catalog())


class AssemblyPartSelectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.ir = _fixture_ir()

    def test_default_and_off_keep_untreated_filenames(self) -> None:
        omitted = placements_from_ir(self.ir)
        explicit_off = placements_from_ir(self.ir, EDGE_TREATMENT_OFF)
        self.assertEqual(len(omitted), 24)
        self.assertEqual(len(explicit_off), 24)
        for left, right, block in zip(
            omitted, explicit_off, self.ir.grid.blocks, strict=True
        ):
            self.assertEqual(left.part_filename, f"{left.geometry_id}.SLDPRT")
            self.assertEqual(right.part_filename, left.part_filename)
            self.assertEqual(
                logical_assembly_part_filename(left.geometry_id),
                logical_part_filename(left.geometry_id),
            )
            self.assertFalse(is_treated_artifact_filename(left.part_filename))
            self.assertEqual(left.geometry_id, block.geometry_id)
            self.assertEqual(right.geometry_id, block.geometry_id)

    def test_explicit_chamfer_names_treated_siblings(self) -> None:
        default = placements_from_ir(self.ir)
        treated = placements_from_ir(self.ir, EDGE_TREATMENT_CHAMFER)
        self.assertEqual(len(treated), 24)
        for item, prior, block in zip(
            treated, default, self.ir.grid.blocks, strict=True
        ):
            self.assertEqual(item.geometry_id, prior.geometry_id)
            self.assertEqual(item.geometry_id, block.geometry_id)
            self.assertEqual(
                item.part_filename,
                logical_treated_part_filename(item.geometry_id, EDGE_TREATMENT_CHAMFER),
            )
            self.assertEqual(
                item.part_filename, f"{item.geometry_id}_chamfer.SLDPRT"
            )
            self.assertTrue(is_treated_artifact_filename(item.part_filename))
            self.assertNotEqual(item.part_filename, prior.part_filename)
            self.assertNotIn("_chamfer", item.geometry_id)
            self.assertNotIn("chamfer", item.subtype_id)

    def test_transforms_names_and_appearance_stay_on_the_ir_block(self) -> None:
        default = placements_from_ir(self.ir)
        treated = placements_from_ir(self.ir, EDGE_TREATMENT_CHAMFER)
        identity_fields = (
            "source_index",
            "subtype_id",
            "geometry_id",
            "component_name",
            "grid_min",
            "position_mm",
            "rotation",
            "orientation_serialized",
            "color_mask_hsv",
            "appearance_support",
            "appearance_rgb",
        )
        for item, prior, block in zip(
            treated, default, self.ir.grid.blocks, strict=True
        ):
            for field in identity_fields:
                self.assertEqual(
                    getattr(item, field),
                    getattr(prior, field),
                    msg=field,
                )
            self.assertEqual(item.component_name, component_name_from_block(block))
            self.assertNotIn("_chamfer", item.component_name)
            self.assertEqual(item.position_mm, block.position_mm.as_tuple())
            self.assertEqual(item.rotation, block.rotation)


class MissingTreatedPartTests(unittest.TestCase):
    def test_default_lookup_still_requires_untreated_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with self.assertRaises(MissingCanonicalPartError) as ctx:
                require_canonical_part_files(root)
            self.assertIn("canonical part artifacts are missing", str(ctx.exception))
            self.assertNotIn("_chamfer", str(ctx.exception))

    def test_treated_lookup_fails_closed_when_siblings_are_absent(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for geometry_id in (
                "large_armor_block",
                "large_armor_slope",
                "large_armor_corner",
                "large_armor_corner_inv",
            ):
                (root / f"{geometry_id}.SLDPRT").write_bytes(b"untreated")
            untreated = require_canonical_part_files(root)
            self.assertEqual(
                {path.name for path in untreated.values()},
                {
                    "large_armor_block.SLDPRT",
                    "large_armor_slope.SLDPRT",
                    "large_armor_corner.SLDPRT",
                    "large_armor_corner_inv.SLDPRT",
                },
            )
            with self.assertRaises(MissingCanonicalPartError) as ctx:
                require_canonical_part_files(root, EDGE_TREATMENT_CHAMFER)
            message = str(ctx.exception)
            self.assertIn("treated part artifacts are missing", message)
            self.assertIn("large_armor_block_chamfer.SLDPRT", message)
            self.assertIn("--edge-treatment chamfer", message)

    def test_treated_lookup_does_not_fall_back_to_untreated_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "large_armor_block.SLDPRT").write_bytes(b"untreated")
            (root / "large_armor_slope.SLDPRT").write_bytes(b"untreated")
            (root / "large_armor_corner.SLDPRT").write_bytes(b"untreated")
            (root / "large_armor_corner_inv.SLDPRT").write_bytes(b"untreated")
            (root / "large_armor_block_chamfer.SLDPRT").write_bytes(b"treated")
            (root / "large_armor_slope_chamfer.SLDPRT").write_bytes(b"treated")
            with self.assertRaises(MissingCanonicalPartError) as ctx:
                require_canonical_part_files(root, EDGE_TREATMENT_CHAMFER)
            message = str(ctx.exception)
            self.assertIn("treated part artifacts are missing", message)
            self.assertIn("large_armor_corner_inv_chamfer.SLDPRT", message)
            self.assertNotIn("resolved untreated", message.lower())
            self.assertTrue((root / "large_armor_block.SLDPRT").is_file())

    def test_treated_lookup_resolves_only_siblings(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for geometry_id in (
                "large_armor_block",
                "large_armor_slope",
                "large_armor_corner",
                "large_armor_corner_inv",
            ):
                (root / f"{geometry_id}.SLDPRT").write_bytes(b"untreated")
                (root / f"{geometry_id}_chamfer.SLDPRT").write_bytes(b"treated")
            found = require_canonical_part_files(root, EDGE_TREATMENT_CHAMFER)
            self.assertEqual(len(found), 4)
            for geometry_id, path in found.items():
                self.assertEqual(path.name, f"{geometry_id}_chamfer.SLDPRT")
                self.assertEqual(path.read_bytes(), b"treated")
                path.relative_to(root.resolve())


class AssembleOperatorEntryTests(unittest.TestCase):
    def test_argv_default_is_untreated(self) -> None:
        parsed = _parse_assemble_argv([str(FIXTURE_PATH)])
        self.assertIsNotNone(parsed)
        assert parsed is not None
        blueprint, request = parsed
        self.assertEqual(blueprint, FIXTURE_PATH)
        self.assertEqual(request, EDGE_TREATMENT_OFF)

    def test_argv_explicit_chamfer_matches_part_generation_spelling(self) -> None:
        parsed = _parse_assemble_argv(
            [str(FIXTURE_PATH), "--edge-treatment", "chamfer"]
        )
        self.assertIsNotNone(parsed)
        assert parsed is not None
        blueprint, request = parsed
        self.assertEqual(blueprint, FIXTURE_PATH)
        self.assertEqual(request, EDGE_TREATMENT_CHAMFER)
        off = _parse_assemble_argv([str(FIXTURE_PATH), "--edge-treatment", "off"])
        self.assertIsNotNone(off)
        assert off is not None
        self.assertEqual(off[1], EDGE_TREATMENT_OFF)

    def test_argv_rejects_unknown_flags_and_flag_first_order(self) -> None:
        self.assertIsNone(_parse_assemble_argv([]))
        self.assertIsNone(_parse_assemble_argv(["--edge-treatment", "chamfer"]))
        self.assertIsNone(
            _parse_assemble_argv(
                [str(FIXTURE_PATH), "--edge-treatment", "fillet"]
            )
        )
        self.assertIsNone(_parse_assemble_argv([str(FIXTURE_PATH), "--help"]))

    def test_generate_assembly_signatures_default_to_untreated(self) -> None:
        public = inspect.signature(generate_assembly)
        from_ir = inspect.signature(generate_assembly_from_ir)
        self.assertIsNone(public.parameters["treatment"].default)
        self.assertIsNone(from_ir.parameters["treatment"].default)


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
        self._material: tuple[float, ...] | None = None
        self.IsFixed = False
        self.Transform2 = _FakeTransform()

    @property
    def Name2(self) -> str:
        return f"{self._short}-1"

    @Name2.setter
    def Name2(self, value: str) -> None:
        self._short = value

    @property
    def MaterialPropertyValues(self):
        return self._material

    @MaterialPropertyValues.setter
    def MaterialPropertyValues(self, value) -> None:
        self._material = tuple(float(v) for v in value)

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


class TreatedHermeticInsertionTests(unittest.TestCase):
    def test_insert_uses_treated_filenames_without_changing_names(self) -> None:
        from unittest.mock import patch

        from se2cad.solidworks.com_assemble import insert_placements

        ir = _fixture_ir()
        placements = placements_from_ir(ir, EDGE_TREATMENT_CHAMFER)[:3]
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            part_paths: dict[str, Path] = {}
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
            self.assertEqual(len(placed), 3)
            for item, placement in zip(placed, placements, strict=True):
                self.assertTrue(is_treated_artifact_filename(placement.part_filename))
                self.assertEqual(item.part_path.name, placement.part_filename)
                self.assertEqual(item.component_name, placement.component_name)
                self.assertNotIn("_chamfer", item.component_name)
                self.assertTrue(item.geometry_applied)
                self.assertTrue(item.appearance_applied)


class PlacementDataclassContractTests(unittest.TestCase):
    def test_placement_has_no_treatment_identity_field(self) -> None:
        fields = set(ComponentPlacement.__dataclass_fields__)
        self.assertNotIn("treatment", fields)
        self.assertNotIn("chamfer", fields)
        self.assertIn("geometry_id", fields)
        self.assertIn("part_filename", fields)
        self.assertIn("component_name", fields)


if __name__ == "__main__":
    unittest.main()
