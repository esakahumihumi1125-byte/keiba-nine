"""Synthetic only: owner live briefs never expose raw licensed source."""
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from owner_live_notes import parse_live_notes, LiveNoteError, ENV_KEY, SCHEMA
from private_service import create_app
from test_private_service import call, SETTINGS


def sample():
    return {"schema":SCHEMA, "date":"2026-11-07", "races":[{
        "track":"京都", "race":1, "time":"10:05", "observedAt":"09:47",
        "ground":"良", "paddock":[1,9,5], "note":"京都1Rの短い観察メモ",
        "rawProviderScore":"NEVER_EXPOSE", "credential":"DO_NOT_PRINT"
    }]}


class OwnerLiveNoteTests(unittest.TestCase):
    def test_private_same_origin_only_and_strips_unapproved_fields(self):
        app = create_app({**SETTINGS, ENV_KEY:json.dumps(sample(), ensure_ascii=False)})
        self.assertEqual(call(app,"/api/owner-live-notes",auth="")["status"],"401 Unauthorized")
        self.assertEqual(call(app,"/api/owner-live-notes",HTTP_X_KEIBA_REQUEST="")["status"],"403 Forbidden")
        self.assertEqual(call(app,"/api/owner-live-notes",method="POST")["status"],"404 Not Found")
        response=call(app,"/api/owner-live-notes")
        self.assertEqual(response["status"],"200 OK")
        self.assertIn("no-store",response["headers"]["Cache-Control"])
        payload=json.loads(response["body"])
        self.assertTrue(payload["available"])
        self.assertEqual(payload["notes"]["races"][0]["paddock"],[1,9,5])
        self.assertFalse(payload["notes"]["officialJraVerified"])
        self.assertFalse(payload["notes"]["predictionReady"])
        self.assertNotIn("NEVER_EXPOSE",str(payload))
        self.assertNotIn("DO_NOT_PRINT",str(payload))

    def test_missing_notices_and_malformed_data_fail_closed(self):
        plain=call(create_app(SETTINGS),"/api/owner-live-notes")
        self.assertEqual(json.loads(plain["body"]),{"available":False,"notes":None})
        for value in ("not-json",json.dumps({**sample(),"date":"2026-11-99"}),
                      json.dumps({**sample(),"races":[{**sample()["races"][0],"paddock":[1,1]}]}),
                      json.dumps({**sample(),"races":[{**sample()["races"][0],"note":"<script>"}]})):
            with self.subTest(value=value[:40]):
                bad=call(create_app({**SETTINGS, ENV_KEY:value}),"/api/owner-live-notes")
                self.assertEqual(bad["status"],"503 Service Unavailable")

    def test_parse_preserves_only_safe_editorial_data(self):
        record=parse_live_notes(json.dumps(sample(), ensure_ascii=False))
        self.assertEqual(record["races"][0]["track"],"京都")
        self.assertEqual(record["races"][0]["time"],"10:05")
        self.assertNotIn("rawProviderScore", record["races"][0])


if __name__=="__main__":
    unittest.main()
