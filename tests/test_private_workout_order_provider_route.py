"""Owner-only, postrace opt-in workout index study route tests."""
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from private_service import create_app
from test_private_service import call, SETTINGS
from owner_workout_order_receipts import issue_workout_locks
from test_owner_workout_order_receipts import source, BEFORE, DAY
from test_owner_workout_order_provider_pairs import rows


def authorized():
    return create_app({
        **SETTINGS, "KEIBA_RENDER_PRIVATE_ONLY":"1",
        "KEIBA_RENDER_PREVIEW_ONLY":"0",
        "JRDB_PRIVATE_ENABLED":"1",
        "JRDB_API_KEY":"TEST-ONLY",
        "JRDB_AUTH_KEY":"TEST-ONLY",
    })


class WorkoutOrderProviderRouteTests(unittest.TestCase):
    def receipts(self):
        return issue_workout_locks(
            source(), SETTINGS["KEIBA_OWNER_PASSWORD"], BEFORE)

    def test_result_requested_once_after_off_only(self):
        app=authorized()
        data={"date":DAY, "receipts":self.receipts()}
        with (patch("private_service._now_in_jst",
                    return_value="2099-01-01T10:30:00+09:00"),
              patch("private_service.fetch_finished_race_results",
                    return_value=rows()) as fetched):
            out=call(app,"/api/owner-workout-order-provider-check",
                     method="POST",data=data)
            fetched.assert_called_once_with(DAY)
        self.assertEqual(out["status"],"200 OK")
        parsed=json.loads(out["body"])
        self.assertEqual(parsed["studiedRaceCount"],1)
        self.assertEqual(parsed["observedPairsByTrainingBand"]["S"]["discordant"],1)
        self.assertFalse(parsed["accuracyVerified"])
        self.assertFalse(parsed["calibrationReady"])
        self.assertIsNone(parsed["roiPercent"])
        self.assertNotIn("horse_number",repr(parsed))
        self.assertNotIn("oikirisisu",repr(parsed))

    def test_before_off_never_calls_chargeable_result_provider(self):
        app=authorized()
        with (patch("private_service._now_in_jst",
                    return_value="2099-01-01T09:30:00+09:00"),
              patch("private_service.fetch_finished_race_results") as fetched):
            out=call(app,"/api/owner-workout-order-provider-check",
                     method="POST",
                     data={"date":DAY,"receipts":self.receipts()})
            fetched.assert_not_called()
        self.assertEqual(out["status"],"200 OK")
        parsed=json.loads(out["body"])
        self.assertEqual(parsed["sourceReadCount"],0)
        self.assertEqual(parsed["studiedRaceCount"],0)
        self.assertEqual(parsed["races"][0]["providerStatus"],"pending")

    def test_invalid_receipt_or_injected_result_does_not_call_provider(self):
        app=authorized()
        receipt=self.receipts()
        for payload in (
            {"date":DAY,"receipts":[{**receipt[0],"signature":"0"*64}]},
            {"date":DAY,"receipts":receipt,"results":rows()},
            {"date":DAY,"receipts":receipt,"officialJraVerified":True},
            {"date":DAY,"receipts":[]},
        ):
            with self.subTest(payload=repr(payload)[:60]), patch(
                 "private_service.fetch_finished_race_results") as fetched:
                out=call(app,"/api/owner-workout-order-provider-check",
                         method="POST",data=payload)
                self.assertEqual(out["status"],"400 Bad Request")
                fetched.assert_not_called()
        self.assertEqual(call(
            app,"/api/owner-workout-order-provider-check",method="POST",
            auth="",data={"date":DAY,"receipts":receipt}
        )["status"],"401 Unauthorized")
        self.assertEqual(call(
            create_app(SETTINGS),"/api/owner-workout-order-provider-check",
            method="POST",data={"date":DAY,"receipts":receipt}
        )["status"],"404 Not Found")


if __name__=="__main__":
    unittest.main()
