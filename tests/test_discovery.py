"""S2C-11.1.1 operator-local definition discovery. Synthetic trees only."""

from __future__ import annotations

import io
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from se2cad.catalog import CellSize, load_default_catalog
from se2cad.discovery import (
    GAME_ROOT_ENV,
    SDK_ROOT_ENV,
    DiscoveryConfigError,
    DiscoveryParseError,
    DiscoveryPathError,
    contained_file,
    discover_cube_block_definitions,
    load_discovery_config,
    parse_cube_block_definitions_xml,
)
from se2cad.discovery.__main__ import main as discovery_main
from se2cad.ir import build_canonical_blueprint
from se2cad.parser import parse_blueprint

_FIXTURE = (
    Path(__file__).resolve().parents[1]
    / "fixtures"
    / "acceptance"
    / "four-block-armor-asymmetric"
    / "bp.sbc"
)
_SRC = Path(__file__).resolve().parents[1] / "src" / "se2cad"

_ARMOR_FACTS = {
    "LargeBlockArmorBlock": {
        "type_id": "CubeBlock",
        "cube_size": "Large",
        "size": (1, 1, 1),
        "block_topology": "Cube",
        "cube_topology": "Box",
    },
    "LargeBlockArmorSlope": {
        "type_id": "CubeBlock",
        "cube_size": "Large",
        "size": (1, 1, 1),
        "block_topology": "Cube",
        "cube_topology": "Slope",
    },
    "LargeBlockArmorCorner": {
        "type_id": "CubeBlock",
        "cube_size": "Large",
        "size": (1, 1, 1),
        "block_topology": "Cube",
        "cube_topology": "Corner",
    },
    "LargeBlockArmorCornerInv": {
        "type_id": "CubeBlock",
        "cube_size": "Large",
        "size": (1, 1, 1),
        "block_topology": "Cube",
        "cube_topology": "InvCorner",
    },
}


def _definition_xml(
    *,
    subtype: str,
    type_id: str = "CubeBlock",
    cube_size: str = "Large",
    size: tuple[int, int, int] = (1, 1, 1),
    block_topology: str = "Cube",
    cube_topology: str | None = "Box",
    include_model: bool = False,
    id_as_attributes: bool = False,
) -> str:
    if id_as_attributes:
        ident = f'<Id Type="MyObjectBuilder_{type_id}" Subtype="{subtype}" />'
    else:
        ident = (
            f"<Id><TypeId>{type_id}</TypeId><SubtypeId>{subtype}</SubtypeId></Id>"
        )
    cube_def = ""
    if cube_topology is not None:
        cube_def = f"<CubeDefinition><CubeTopology>{cube_topology}</CubeTopology></CubeDefinition>"
    model = ""
    if include_model:
        model = '<Model>Models\\Cubes\\Large\\armor.mwm</Model><Icon>Textures\\GUI\\icon.dds</Icon>'
    x, y, z = size
    return (
        f"<Definition>{ident}<CubeSize>{cube_size}</CubeSize>"
        f'<Size x="{x}" y="{y}" z="{z}" />'
        f"<BlockTopology>{block_topology}</BlockTopology>"
        f"{cube_def}{model}</Definition>"
    )


def _document(*definitions: str) -> str:
    body = "".join(definitions)
    return (
        '<?xml version="1.0"?>'
        '<Definitions xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">'
        f"<CubeBlocks>{body}</CubeBlocks></Definitions>"
    )


def _write_game_tree(root: Path, filename: str, xml_text: str) -> Path:
    cube_dir = root / "Content" / "Data" / "CubeBlocks"
    cube_dir.mkdir(parents=True, exist_ok=True)
    path = cube_dir / filename
    path.write_text(xml_text, encoding="utf-8")
    return path


def _clear_discovery_env() -> dict[str, str]:
    return {
        key: value
        for key, value in os.environ.items()
        if key
        not in {GAME_ROOT_ENV, SDK_ROOT_ENV, "SE2CAD_LOCAL_CONFIG"}
    }


class SyntheticDiscoveryTests(unittest.TestCase):
    def test_discovers_catalog_modeled_fields_from_synthetic_game_tree(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "SpaceEngineers"
            defs = [
                _definition_xml(subtype=subtype, cube_topology=facts["cube_topology"])
                for subtype, facts in _ARMOR_FACTS.items()
            ]
            _write_game_tree(root, "CubeBlocks_Armor.sbc", _document(*defs))
            report = discover_cube_block_definitions(game_root=root)
        self.assertTrue(report.game_root_configured)
        self.assertFalse(report.sdk_root_configured)
        self.assertEqual(len(report.definitions), 4)
        self.assertEqual(
            report.files_read,
            ("game:Content/Data/CubeBlocks/CubeBlocks_Armor.sbc",),
        )
        by_subtype = {item.subtype_id: item for item in report.definitions}
        self.assertEqual(set(by_subtype), set(_ARMOR_FACTS))
        for subtype, facts in _ARMOR_FACTS.items():
            item = by_subtype[subtype]
            self.assertEqual(item.type_id, facts["type_id"])
            self.assertEqual(item.cube_size, facts["cube_size"])
            self.assertEqual(item.size, CellSize(*facts["size"]))
            self.assertEqual(item.block_topology, facts["block_topology"])
            self.assertEqual(item.cube_topology, facts["cube_topology"])
            self.assertEqual(item.source_kind, "game")
            self.assertEqual(
                item.source_relative,
                "Content/Data/CubeBlocks/CubeBlocks_Armor.sbc",
            )
            dumped = repr(item)
            self.assertNotIn(str(root), dumped)
            self.assertNotIn(".mwm", dumped.lower())
            self.assertNotIn(".fbx", dumped.lower())
            self.assertNotIn(".dds", dumped.lower())

    def test_small_grid_and_triangle_mesh_are_observed_facts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "game"
            xml = _document(
                _definition_xml(
                    subtype="SmallBlockArmorBlock",
                    cube_size="Small",
                    cube_topology="Box",
                ),
                _definition_xml(
                    subtype="LargeBlockCockpit",
                    type_id="Cockpit",
                    block_topology="TriangleMesh",
                    cube_topology=None,
                    include_model=True,
                ),
            )
            _write_game_tree(root, "CubeBlocks_Mix.sbc", xml)
            report = discover_cube_block_definitions(game_root=root)
        small = next(
            item
            for item in report.definitions
            if item.subtype_id == "SmallBlockArmorBlock"
        )
        mesh = next(
            item
            for item in report.definitions
            if item.subtype_id == "LargeBlockCockpit"
        )
        self.assertEqual(small.cube_size, "Small")
        self.assertEqual(small.cube_topology, "Box")
        self.assertEqual(mesh.block_topology, "TriangleMesh")
        self.assertIsNone(mesh.cube_topology)
        self.assertEqual(mesh.type_id, "Cockpit")
        dumped = repr(report)
        self.assertNotIn(".mwm", dumped.lower())
        self.assertNotIn(".dds", dumped.lower())

    def test_attribute_id_normalizes_type_prefix(self) -> None:
        xml = _document(
            _definition_xml(
                subtype="LargeBlockArmorBlock",
                id_as_attributes=True,
            )
        )
        parsed = parse_cube_block_definitions_xml(
            xml, source="attr", source_kind="game", source_relative="attr.sbc"
        )
        self.assertEqual(parsed[0].type_id, "CubeBlock")
        self.assertEqual(parsed[0].subtype_id, "LargeBlockArmorBlock")

    def test_sdk_root_uses_data_cubeblocks(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "ModSDK"
            cube_dir = root / "Data" / "CubeBlocks"
            cube_dir.mkdir(parents=True)
            (cube_dir / "CubeBlocks_Armor.sbc").write_text(
                _document(_definition_xml(subtype="LargeBlockArmorBlock")),
                encoding="utf-8",
            )
            report = discover_cube_block_definitions(sdk_root=root)
        self.assertTrue(report.sdk_root_configured)
        self.assertEqual(report.definitions[0].source_kind, "sdk")
        self.assertEqual(
            report.definitions[0].source_relative,
            "Data/CubeBlocks/CubeBlocks_Armor.sbc",
        )

    def test_identical_facts_from_game_and_sdk_are_not_duplicated(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            game = Path(tmp) / "game"
            sdk = Path(tmp) / "sdk"
            xml = _document(_definition_xml(subtype="LargeBlockArmorBlock"))
            _write_game_tree(game, "a.sbc", xml)
            sdk_dir = sdk / "Content" / "Data" / "CubeBlocks"
            sdk_dir.mkdir(parents=True)
            (sdk_dir / "a.sbc").write_text(xml, encoding="utf-8")
            report = discover_cube_block_definitions(game_root=game, sdk_root=sdk)
        self.assertEqual(len(report.definitions), 1)
        self.assertEqual(report.definitions[0].source_kind, "game")

    def test_conflicting_facts_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            game = Path(tmp) / "game"
            sdk = Path(tmp) / "sdk"
            _write_game_tree(
                game,
                "a.sbc",
                _document(_definition_xml(subtype="LargeBlockArmorBlock")),
            )
            sdk_dir = sdk / "Content" / "Data" / "CubeBlocks"
            sdk_dir.mkdir(parents=True)
            (sdk_dir / "a.sbc").write_text(
                _document(
                    _definition_xml(
                        subtype="LargeBlockArmorBlock", cube_topology="Slope"
                    )
                ),
                encoding="utf-8",
            )
            with self.assertRaises(DiscoveryParseError) as ctx:
                discover_cube_block_definitions(game_root=game, sdk_root=sdk)
        self.assertIn("conflicting observed facts", str(ctx.exception))


class DiscoveryFailureTests(unittest.TestCase):
    def test_missing_root_fails_closed(self) -> None:
        missing = Path(__file__).resolve().parent / "no-such-se-install"
        with self.assertRaises(DiscoveryPathError) as ctx:
            discover_cube_block_definitions(game_root=missing)
        self.assertIn("does not exist", str(ctx.exception))

    def test_root_that_is_a_file_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "not-a-dir"
            path.write_text("x", encoding="utf-8")
            with self.assertRaises(DiscoveryPathError):
                discover_cube_block_definitions(game_root=path)

    def test_root_without_cubeblocks_tree_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "empty-install"
            root.mkdir()
            (root / "Bin64").mkdir()
            with self.assertRaises(DiscoveryPathError) as ctx:
                discover_cube_block_definitions(game_root=root)
        self.assertIn("no cube-block definition directory", str(ctx.exception))

    def test_path_escape_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "game"
            outside = Path(tmp) / "outside.sbc"
            outside.write_text(
                _document(_definition_xml(subtype="LargeBlockArmorBlock")),
                encoding="utf-8",
            )
            _write_game_tree(
                root, "ok.sbc", _document(_definition_xml(subtype="LargeBlockArmorBlock"))
            )
            with self.assertRaises(DiscoveryPathError) as ctx:
                contained_file(root, outside)
            self.assertIn("escapes", str(ctx.exception))

    def test_malformed_xml_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "game"
            _write_game_tree(root, "bad.sbc", "<Definitions><CubeBlocks>")
            with self.assertRaises(DiscoveryParseError) as ctx:
                discover_cube_block_definitions(game_root=root)
        self.assertIn("malformed XML", str(ctx.exception))

    def test_doctype_and_entity_are_rejected(self) -> None:
        xml = (
            '<!DOCTYPE Definitions [<!ENTITY xxe "boom">]>'
            "<Definitions><CubeBlocks>&xxe;</CubeBlocks></Definitions>"
        )
        with self.assertRaises(DiscoveryParseError) as ctx:
            parse_cube_block_definitions_xml(
                xml, source="xxe", source_kind="game", source_relative="xxe.sbc"
            )
        self.assertIn("<!doctype", str(ctx.exception).lower())

    def test_xinclude_is_rejected(self) -> None:
        xml = (
            "<Definitions xmlns:xi='http://www.w3.org/2001/XInclude'>"
            "<CubeBlocks><xi:include href='secret.xml'/></CubeBlocks>"
            "</Definitions>"
        )
        with self.assertRaises(DiscoveryParseError):
            parse_cube_block_definitions_xml(
                xml,
                source="xinclude",
                source_kind="game",
                source_relative="xinclude.sbc",
            )

    def test_missing_required_fields_fail_closed(self) -> None:
        xml = (
            "<Definitions><CubeBlocks><Definition>"
            "<Id><TypeId>CubeBlock</TypeId></Id>"
            "<CubeSize>Large</CubeSize>"
            '<Size x="1" y="1" z="1" />'
            "<BlockTopology>Cube</BlockTopology>"
            "</Definition></CubeBlocks></Definitions>"
        )
        with self.assertRaises(DiscoveryParseError) as ctx:
            parse_cube_block_definitions_xml(
                xml, source="noid", source_kind="game", source_relative="noid.sbc"
            )
        self.assertIn("SubtypeId", str(ctx.exception))

    def test_non_sbc_and_mesh_files_are_not_read(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "game"
            cube_dir = root / "Content" / "Data" / "CubeBlocks"
            cube_dir.mkdir(parents=True)
            (cube_dir / "secret.mwm").write_bytes(b"not-xml")
            (cube_dir / "notes.txt").write_text("ignore", encoding="utf-8")
            (cube_dir / "CubeBlocks_Armor.sbc").write_text(
                _document(_definition_xml(subtype="LargeBlockArmorBlock")),
                encoding="utf-8",
            )
            report = discover_cube_block_definitions(game_root=root)
        self.assertEqual(len(report.definitions), 1)
        self.assertEqual(len(report.files_read), 1)
        self.assertTrue(report.files_read[0].endswith(".sbc"))


class DiscoveryConfigTests(unittest.TestCase):
    def test_missing_roots_fail_closed(self) -> None:
        env = _clear_discovery_env()
        with tempfile.TemporaryDirectory() as tmp:
            with patch.dict(os.environ, env, clear=True):
                with patch("se2cad.local_config.Path.cwd", return_value=Path(tmp)):
                    with self.assertRaises(DiscoveryConfigError):
                        load_discovery_config()

    def test_environment_game_root_wins(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "game"
            _write_game_tree(
                root,
                "a.sbc",
                _document(_definition_xml(subtype="LargeBlockArmorBlock")),
            )
            env = _clear_discovery_env()
            env[GAME_ROOT_ENV] = str(root)
            with patch.dict(os.environ, env, clear=True):
                config = load_discovery_config()
                report = discover_cube_block_definitions()
            self.assertEqual(config.game_root, root.resolve())
            self.assertEqual(config.source, GAME_ROOT_ENV)
            self.assertEqual(len(report.definitions), 1)

    def test_local_json_game_root_is_accepted(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "game"
            _write_game_tree(
                root,
                "a.sbc",
                _document(_definition_xml(subtype="LargeBlockArmorBlock")),
            )
            local = Path(tmp) / "se2cad.local.json"
            local.write_text(
                json.dumps({"game_root": str(root), "generated_root": str(tmp)}),
                encoding="utf-8",
            )
            env = _clear_discovery_env()
            env["SE2CAD_LOCAL_CONFIG"] = str(local)
            with patch.dict(os.environ, env, clear=True):
                report = discover_cube_block_definitions()
            self.assertEqual(len(report.definitions), 1)

    def test_operator_entry_prints_observed_facts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "game"
            _write_game_tree(
                root,
                "a.sbc",
                _document(_definition_xml(subtype="LargeBlockArmorBlock")),
            )
            env = _clear_discovery_env()
            env[GAME_ROOT_ENV] = str(root)
            stdout = io.StringIO()
            with patch.dict(os.environ, env, clear=True):
                with patch("sys.stdout", stdout):
                    code = discovery_main([])
            self.assertEqual(code, 0)
            text = stdout.getvalue()
            self.assertIn("definition_count=1", text)
            self.assertIn("LargeBlockArmorBlock", text)
            self.assertIn("Cube\tBox", text)
            self.assertNotIn(str(root), text)

    def test_operator_entry_usage_and_config_failure(self) -> None:
        stdout = io.StringIO()
        with patch("sys.stdout", stdout):
            self.assertEqual(discovery_main(["extra"]), 2)
        self.assertIn("usage: python -m se2cad.discovery", stdout.getvalue())
        env = _clear_discovery_env()
        with tempfile.TemporaryDirectory() as tmp:
            stdout = io.StringIO()
            with patch.dict(os.environ, env, clear=True):
                with patch("se2cad.local_config.Path.cwd", return_value=Path(tmp)):
                    with patch("sys.stdout", stdout):
                        self.assertEqual(discovery_main([]), 2)
        self.assertIn("game or SDK root is required", stdout.getvalue())


class RuntimeIndependenceTests(unittest.TestCase):
    def test_conversion_stays_install_free(self) -> None:
        env = _clear_discovery_env()
        with tempfile.TemporaryDirectory() as tmp:
            with patch.dict(os.environ, env, clear=True):
                with patch("se2cad.local_config.Path.cwd", return_value=Path(tmp)):
                    catalog = load_default_catalog()
                    parsed = parse_blueprint(_FIXTURE)
                    ir = build_canonical_blueprint(parsed, catalog)
        self.assertEqual(ir.identity_subtype, "se2cad-test1")
        self.assertEqual(len(ir.grid.blocks), 24)

    def test_public_se2cad_surface_does_not_import_discovery(self) -> None:
        text = (_SRC / "__init__.py").read_text(encoding="utf-8")
        self.assertNotIn("se2cad.discovery", text)
        self.assertNotIn("GAME_ROOT", text)

    def test_runtime_modules_do_not_import_discovery(self) -> None:
        forbidden = ("se2cad.discovery", "SE2CAD_GAME_ROOT", "SE2CAD_SDK_ROOT")
        runtime_dirs = (
            _SRC / "parser",
            _SRC / "catalog",
            _SRC / "ir",
            _SRC / "library",
            _SRC / "transform",
            _SRC / "statistics",
            _SRC / "solidworks",
        )
        generation_only = {
            "sdk_source.py",
            "sdk_convert.py",
            "blender_fbx_to_stl.py",
        }
        for directory in runtime_dirs:
            for path in directory.glob("*.py"):
                if path.name in generation_only:
                    continue
                text = path.read_text(encoding="utf-8")
                for token in forbidden:
                    self.assertNotIn(
                        token, text, msg=f"{path.name} mentions {token}"
                    )

    def test_discovery_does_not_import_solidworks_or_write_catalog(self) -> None:
        discovery_root = _SRC / "discovery"
        forbidden = (
            "se2cad.solidworks",
            "win32com",
            "blender",
            "subprocess",
            "large_grid_armor.json",
        )
        for path in discovery_root.glob("*.py"):
            text = path.read_text(encoding="utf-8")
            for token in forbidden:
                self.assertNotIn(token, text, msg=f"{path.name} mentions {token}")

    def test_packaged_catalog_unchanged_and_path_free(self) -> None:
        from se2cad.catalog import default_catalog_path

        path = default_catalog_path()
        raw = path.read_text(encoding="utf-8")
        data = json.loads(raw)
        serialized = json.dumps(data)
        self.assertGreaterEqual(len(data["entries"]), 4)
        self.assertEqual(
            [entry["subtype_id"] for entry in data["entries"][:4]],
            [
                "LargeBlockArmorBlock",
                "LargeBlockArmorSlope",
                "LargeBlockArmorCorner",
                "LargeBlockArmorCornerInv",
            ],
        )
        self.assertNotIn("/home/", serialized)
        self.assertNotIn("C:\\\\", serialized)
        self.assertNotIn(".mwm", serialized.lower())
        self.assertNotIn("game_root", serialized)


if __name__ == "__main__":
    unittest.main()
