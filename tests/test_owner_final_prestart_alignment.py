"""Final-delivery gate regression: signed receipt must match its exact race.

All inputs are synthetic structures. A well-shaped signature here is NOT an
authenticated HMAC; that independent check remains elsewhere in the app.
No JRDB reads, JRA requests, purchases, or persistent records.
"""
import copy
import sys
import unittest
from datetime import datetime, timezone, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from jrdb_coverage import CoverageError
from owner_last_prestart_gate import expire_undelivered_drafts

JST = timezone(timedelta(hours=9))
DAY = "20990101"
MORNING = datetime(2099, 1, 1, 9, 30, tzinfo=JST)
LATE = datetime(2099, 1, 1, 10, 0, tzinfo=JST)


def fixture():
    races, receipts = [], []
    for number, hour in ((1, 10), (2, 11)):
        ticket = [[1, 2, number + 2]]
        races.append({
            "track": "東京", "race": number, "status": "provisional_draft",
            "reason": "two_factor_only", "postTime": f"{hour:02d}:00",
            "runners": [], "first": [1, 2], "second": [1, 2, 3],
            "third": [1, 2, 3, 4], "tickets": ticket,
            "points": 1, "amountYen": 100,
        })
        receipts.append({
            "snapshot": {
                "date": "2099-01-01", "track": "東京", "race": number,
                "sourceKind": "prestart-locked", "actualPurchase": False,
                "lockedAt": "2099-01-01T09:00:00+09:00",
                "scheduledOffAt": f"2099-01-01T{hour:02d}:00:00+09:00",
                "trifectaTickets": ticket, "trioTickets": [],
                "scheduleVerified": False, "predictionVerified": False,
            },
            "signature": "a" * 64,
        })
    return {
        "date": DAY, "races": races, "raceCount": 2,
        "draftCount": 2, "holdCount": 0, "holdReasons": {},
        "researchReceipts": receipts, "researchReceiptCount": 2,
    }


class FinalPrestartReceiptIdentityTests(unittest.TestCase):
    def test_before_off_no_mutation_and_no_provider_calls(self):
        report = fixture()
        original = copy.deepcopy(report)
        self.assertEqual(expire_undelivered_drafts(report, MORNING), 0)
        self.assertEqual(report, original)

    def test_exact_boundary_expires_only_that_race_and_keeps_other_receipt(self):
        report = fixture()
        second_receipt = copy.deepcopy(report["researchReceipts"][1])
        self.assertEqual(expire_undelivered_drafts(report, LATE), 1)
        self.assertEqual((report["draftCount"], report["holdCount"]), (1, 1))
        self.assertEqual(report["holdReasons"], {"after_provisional_off": 1})
        self.assertEqual(report["researchReceiptCount"], 1)
        self.assertEqual(report["researchReceipts"], [second_receipt])
        first = report["races"][0]
        self.assertEqual((first["status"], first["points"]), ("hold", 0))
        self.assertEqual(first["tickets"], [])

    def test_bijection_and_ticket_integrity_fail_closed(self):
        changes = {
            "duplicate_receipt": lambda x: x["researchReceipts"].__setitem__(
                1, copy.deepcopy(x["researchReceipts"][0])),
            "other_race_receipt": lambda x: x["researchReceipts"][1][
                "snapshot"].__setitem__("race", 3),
            "other_day_receipt": lambda x: x["researchReceipts"][1][
                "snapshot"].__setitem__("date", "2099-01-02"),
            "wrong_off": lambda x: x["researchReceipts"][1][
                "snapshot"].__setitem__("scheduledOffAt", "2099-01-01T11:01:00+09:00"),
            "wrong_ticket": lambda x: x["researchReceipts"][1][
                "snapshot"].__setitem__("trifectaTickets", [[2, 1, 4]]),
            "wrong_signature": lambda x: x["researchReceipts"][1].__setitem__(
                "signature", "not-an-hmac"),
            "future_lock": lambda x: x["researchReceipts"][1][
                "snapshot"].__setitem__("lockedAt", "2099-01-01T09:40:00+09:00"),
            "naive_lock": lambda x: x["researchReceipts"][1][
                "snapshot"].__setitem__("lockedAt", "2099-01-01T09:00:00"),
            "missing_receipt": lambda x: x["researchReceipts"].pop(),
            "duplicate_race": lambda x: x["races"][1].__setitem__("race", 1),
        }
        for name, mutate in changes.items():
            with self.subTest(name=name):
                report = fixture()
                mutate(report)
                original = copy.deepcopy(report)
                with self.assertRaises(CoverageError):
                    expire_undelivered_drafts(report, MORNING)
                self.assertEqual(report, original, "Bad input must not mutate prior state")

    def test_failure_precedes_late_race_redaction(self):
        report = fixture()
        report["researchReceipts"][1]["snapshot"]["race"] = 3
        previous = copy.deepcopy(report)
        with self.assertRaises(CoverageError):
            expire_undelivered_drafts(report, LATE)
        self.assertEqual(report, previous)

    def test_held_race_cannot_carry_tickets(self):
        report = fixture()
        report["races"][0].update(status="hold", reason="missing_factors",
                                  points=0, amountYen=0, tickets=[])
        report["researchReceipts"].pop(0)
        report.update(draftCount=1, holdCount=1,
                      researchReceiptCount=1,
                      holdReasons={"missing_factors": 1})
        self.assertEqual(expire_undelivered_drafts(report, MORNING), 0)
        report["races"][0]["tickets"] = [[1, 2, 3]]
        with self.assertRaises(CoverageError):
            expire_undelivered_drafts(report, MORNING)


if __name__ == "__main__":
    unittest.main()
