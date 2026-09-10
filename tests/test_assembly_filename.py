"""S2C-12.4.1 safe assembly filename derivation."""

from __future__ import annotations

import hashlib
import tempfile
import unittest
from pathlib import Path

from se2cad.catalog import FILLER_GEOMETRY_ID, load_default_catalog
from se2cad.ir import component_name_from_block
from se2cad.parser import parse_blueprint_xml
from se2cad.policy import ConversionPolicy, convert_blueprint_from_xml
from se2cad.solidworks import (
    AssemblyIdentityError,
    GeneratedRootError,
    assembly_path_for,
    logical_assembly_filename,
    logical_part_filename,
)
from se2cad.solidworks.artifacts import (
    assert_overwrite_is_canonical,
    assembly_filename_stem,
    contained_destination,
    is_assembly_artifact_filename,
)
from se2cad.solidworks.placement import placements_from_ir

DIGEST_LENGTH = 12


def _digest(identity: str) -> str:
    return hashlib.sha256(identity.encode("utf-8")).hexdigest()[:DIGEST_LENGTH]


def _derived_name(prefix: str, identity: str) -> str:
    return f"{prefix}+{_digest(identity)}.SLDASM"


def _ship_xml(identity: str, unknown: bool = False) -> str:
    second = ""
    if unknown:
        second = """
            <MyObjectBuilder_CubeBlock>
              <SubtypeName>NotACatalogSubtype</SubtypeName>
              <Min x="1" y="0" z="0" />
            </MyObjectBuilder_CubeBlock>"""
    return f"""<?xml version="1.0"?>
<Definitions xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <ShipBlueprints>
    <ShipBlueprint>
      <Id Type="MyObjectBuilder_ShipBlueprintDefinition" Subtype="{identity}" />
      <CubeGrids>
        <CubeGrid>
          <GridSizeEnum>Large</GridSizeEnum>
          <CubeBlocks>
            <MyObjectBuilder_CubeBlock>
              <SubtypeName>LargeBlockArmorBlock</SubtypeName>
            </MyObjectBuilder_CubeBlock>{second}
          </CubeBlocks>
        </CubeGrid>
      </CubeGrids>
    </ShipBlueprint>
  </ShipBlueprints>
</Definitions>
"""


class AssemblyFilenameDerivationTests(unittest.TestCase):
    def test_already_safe_identities_keep_stable_filenames(self) -> None:
        for identity, filename in (
            ("se2cad-test1", "se2cad-test1.SLDASM"),
            ("se2cad-filler-probe", "se2cad-filler-probe.SLDASM"),
            ("se2cad-ob-probe", "se2cad-ob-probe.SLDASM"),
            ("se2cad-color1", "se2cad-color1.SLDASM"),
            ("Big_Red", "Big_Red.SLDASM"),
        ):
            with self.subTest(identity=identity):
                self.assertEqual(logical_assembly_filename(identity), filename)
                self.assertTrue(is_assembly_artifact_filename(filename))
                self.assertEqual(assembly_filename_stem(identity), identity)

    def test_big_red_derives_safe_filename_and_keeps_logical_identity(self) -> None:
        identity = "Big Red"
        expected = _derived_name("Big_Red", identity)
        self.assertEqual(logical_assembly_filename(identity), expected)
        self.assertEqual(logical_assembly_filename(identity), expected)
        parsed = parse_blueprint_xml(_ship_xml(identity), source="big-red-name")
        self.assertEqual(parsed.identity_subtype, identity)
        result = convert_blueprint_from_xml(
            _ship_xml(identity),
            policy=ConversionPolicy.STRICT,
            source="big-red-name",
        )
        self.assertEqual(result.ir.identity_subtype, identity)
        self.assertEqual(logical_assembly_filename(result.ir.identity_subtype), expected)
        self.assertTrue(is_assembly_artifact_filename(expected))
        self.assertFalse(is_assembly_artifact_filename("Big Red.SLDASM"))
        self.assertTrue(is_assembly_artifact_filename("Big_Red.SLDASM"))

    def test_naive_normalization_does_not_collide(self) -> None:
        spaced = logical_assembly_filename("Big Red")
        underscored = logical_assembly_filename("Big_Red")
        self.assertEqual(underscored, "Big_Red.SLDASM")
        self.assertEqual(spaced, _derived_name("Big_Red", "Big Red"))
        self.assertNotEqual(spaced, underscored)
        self.assertNotEqual(assembly_filename_stem("Big Red"), assembly_filename_stem("Big_Red"))

    def test_path_like_identities_stay_single_segment_inside_root(self) -> None:
        cases = (
            "../evil",
            r"..\evil",
            r"C:\evil",
            r"\\server\share",
            "a/b",
            r"a\b",
            "C:evil",
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for identity in cases:
                with self.subTest(identity=identity):
                    filename = logical_assembly_filename(identity)
                    self.assertEqual(Path(filename).name, filename)
                    self.assertNotIn("/", filename)
                    self.assertNotIn("\\", filename)
                    dest = assembly_path_for(root, identity)
                    dest.relative_to(root.resolve())
                    self.assertEqual(dest.parent, root.resolve())
                    self.assertEqual(dest.name, filename)

    def test_windows_invalid_and_reserved_identities_are_safe(self) -> None:
        cases = (
            ("has space", "has_space"),
            ("ünicode", "nicode"),
            ("foo.", "foo"),
            ("foo ", "foo"),
            ("CON", "CON"),
            ("con", "con"),
            ("PRN", "PRN"),
            ("AUX", "AUX"),
            ("NUL", "NUL"),
            ("COM1", "COM1"),
            ("lpt9", "lpt9"),
            ("CON.txt", "CON_txt"),
            ('name*?"<>|', "name"),
            ("trail.", "trail"),
        )
        for identity, prefix in cases:
            with self.subTest(identity=identity):
                filename = logical_assembly_filename(identity)
                self.assertEqual(filename, _derived_name(prefix, identity))
                self.assertTrue(is_assembly_artifact_filename(filename))
                self.assertFalse(filename.upper().startswith("CON.SLDASM"))

    def test_empty_identity_fails_closed(self) -> None:
        with self.assertRaises(AssemblyIdentityError):
            logical_assembly_filename("")
        with self.assertRaises(AssemblyIdentityError):
            assembly_filename_stem("")

    def test_generated_root_containment_stays_authoritative(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            dest = assembly_path_for(root, "Big Red")
            dest.relative_to(root.resolve())
            with self.assertRaises(GeneratedRootError):
                contained_destination(root, "../escape.SLDASM")
            with self.assertRaises(GeneratedRootError):
                contained_destination(root, r"..\escape.SLDASM")
            with self.assertRaises(GeneratedRootError):
                contained_destination(root, "sub/dir.SLDASM")
            owned = dest
            owned.write_bytes(b"stub")
            assert_overwrite_is_canonical(owned)
            foreign = root / "notes.txt"
            foreign.write_text("no", encoding="utf-8")
            with self.assertRaises(GeneratedRootError):
                assert_overwrite_is_canonical(foreign)

    def test_component_and_part_names_are_unchanged(self) -> None:
        result = convert_blueprint_from_xml(
            _ship_xml("Big Red", unknown=True),
            policy=ConversionPolicy.PERMISSIVE,
            source="name-isolation",
        )
        self.assertEqual(result.ir.identity_subtype, "Big Red")
        self.assertEqual(result.ir.grid.block_count, 2)
        self.assertEqual(result.filler_count, 1)
        placements = placements_from_ir(result.ir)
        self.assertEqual(placements[0].part_filename, "large_armor_block.SLDPRT")
        self.assertEqual(placements[1].part_filename, "se2cad_unknown_filler.SLDPRT")
        self.assertEqual(placements[1].geometry_id, FILLER_GEOMETRY_ID)
        self.assertEqual(
            [item.component_name for item in placements],
            [component_name_from_block(block) for block in result.ir.grid.blocks],
        )
        self.assertEqual(
            logical_part_filename("large_armor_block"), "large_armor_block.SLDPRT"
        )
        catalog = load_default_catalog()
        self.assertEqual(len(catalog.entries), 9)
        self.assertFalse(
            any(entry.subtype_id == "SmallBlockArmorBlock" for entry in catalog.entries)
        )


if __name__ == "__main__":
    unittest.main()
