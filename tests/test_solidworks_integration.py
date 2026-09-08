"""Windows/SolidWorks 2026 integration tests.

Skipped tests are not qualification evidence. Set
SE2CAD_SOLIDWORKS_INTEGRATION=1 in the Windows VM to require a real run.
"""

from __future__ import annotations

import os
import unittest
from pathlib import Path

INTEGRATION_ENV = "SE2CAD_SOLIDWORKS_INTEGRATION"
FIXTURE_PATH = (
    Path(__file__).resolve().parents[1]
    / "fixtures/acceptance/four-block-armor-asymmetric/bp.sbc"
)


def _integration_requested() -> bool:
    return os.environ.get(INTEGRATION_ENV, "").strip() in {"1", "true", "yes"}


@unittest.skipUnless(
    _integration_requested(),
    "set SE2CAD_SOLIDWORKS_INTEGRATION=1 in the Windows SolidWorks VM",
)
class SolidWorksIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        from se2cad.solidworks.availability import require_solidworks_backend
        from se2cad.solidworks.config import load_solidworks_backend_config

        require_solidworks_backend()
        cls.config = load_solidworks_backend_config()

    def test_four_canonical_parts_generate_validate_save_and_reopen(self) -> None:
        from se2cad.solidworks.com_session import (
            SolidWorksSession,
            session_environment_report,
        )
        from se2cad.solidworks.generate import generate_canonical_parts
        from se2cad.solidworks.pipeline import resolve_recipes_from_blueprint

        resolved = resolve_recipes_from_blueprint(FIXTURE_PATH)
        self.assertEqual(len(resolved.geometry_ids), 4)

        with SolidWorksSession(self.config) as session:
            report = session_environment_report(session)
            self.assertTrue(report["solidworks_revision"])
            if not report["solidworks_revision"].startswith("34"):
                # SW 2026 is revision 34 (year - 1992). Record but do not
                # invent a second product; fail if this is clearly not 2026.
                self.assertIn(
                    "2026",
                    report["solidworks_revision"],
                    msg=f"expected SolidWorks 2026, got {report}",
                )

        results = generate_canonical_parts(self.config)
        self.assertEqual(len(results), 4)
        for result in results:
            self.assertTrue(result.locator.path.is_file())
            self.assertTrue(result.locator.path.is_relative_to(self.config.generated_root))
            self.assertEqual(result.after_save.solid_body_count, 1)
            self.assertEqual(result.after_reopen.solid_body_count, 1)
            self.assertEqual(result.after_reopen.sheet_body_count, 0)
            self.assertEqual(result.locator.identity.filename, result.locator.path.name)


if __name__ == "__main__":
    unittest.main()
