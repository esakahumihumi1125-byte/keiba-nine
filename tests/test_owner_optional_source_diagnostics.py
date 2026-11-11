"""Operator codes for owner JRDB source diagnostics must never leak data."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from jrdb_coverage import CoverageError
from jrdb_private import JRDBError
from jrdb_race_context import RaceContextError
from owner_optional_source_diagnostics import (
    safe_material_error_code, safe_context_error_code, CONTEXT_MESSAGES,
)

SENSITIVE = "PRIVATE_HORSE_X_API_TOKEN_1234"


class OptionalSourceDiagnosticsTests(unittest.TestCase):
    def test_material_code_never_includes_untrusted_error_message(self):
        errors = (
            CoverageError(SENSITIVE),
            ValueError(SENSITIVE),
            TypeError(SENSITIVE),
            KeyError(SENSITIVE),
            RuntimeError(SENSITIVE),
        )
        expected = ("source_coverage", "source_value", "source_type",
                    "source_missing_field", "source_other")
        self.assertEqual(tuple(map(safe_material_error_code, errors)), expected)
        for e in errors:
            self.assertNotIn(SENSITIVE, safe_material_error_code(e))
            self.assertLess(len(safe_material_error_code(e)), 50)

    def test_context_code_specific_known_schema_errors(self):
        for message, code in CONTEXT_MESSAGES.items():
            self.assertEqual(safe_context_error_code(RaceContextError(message)), code)
        self.assertEqual(safe_context_error_code(
            RaceContextError(SENSITIVE)), "context_schema_other")
        for cls, code in (
            (KeyError, "context_missing_field"),
            (TypeError, "context_type"),
            (ValueError, "context_value"),
            (RuntimeError, "context_other"),
        ):
            with self.subTest(cls=cls.__name__):
                result = safe_context_error_code(cls(SENSITIVE))
                self.assertEqual(result, code)
                self.assertNotIn(SENSITIVE, result)

    def test_provider_http_diagnosis_does_not_leak_response_text(self):
        for raw, code in (
            ("JRDB request failed (HTTP 401)", "provider_auth"),
            ("JRDB request failed (HTTP 403)", "provider_entitlement"),
            ("JRDB request failed (HTTP 429)", "provider_rate_limit"),
            ("JRDB request failed (HTTP 500)", "provider_other"),
            ("JRDB request or response failed", "provider_other"),
            ("JRDB request failed (HTTP 403) " + SENSITIVE, "provider_other"),
        ):
            with self.subTest(code=code):
                actual = safe_context_error_code(JRDBError(raw))
                self.assertEqual(actual, code)
                self.assertNotIn(SENSITIVE, actual)

    def test_same_message_untrusted_exception_subclass_never_promoted(self):
        class ForgedContext(RaceContextError):
            pass
        class ForgedMaterial(CoverageError):
            pass
        self.assertEqual(safe_context_error_code(
            ForgedContext("Invalid condition timestamp")), "context_other")
        self.assertEqual(safe_material_error_code(
            ForgedMaterial("Known error")), "source_other")


if __name__ == "__main__":
    unittest.main()
