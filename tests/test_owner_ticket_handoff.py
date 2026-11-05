"""Main app and private owner ticket handoff, no payment or private credentials."""
import sys
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from test_private_service import call, SETTINGS
from private_service import create_app


class TicketHandoffTests(unittest.TestCase):
    def test_main_app_only_transfers_explicit_manually_reviewed_formation(self):
        html=(ROOT/'keiba-nine-beta51-feed-record.html').read_text(encoding='utf-8')
        code=(ROOT/'owner-ticket-transfer.js').read_text(encoding='utf-8')
        self.assertIn('id="ownerTicketTransfer"',html)
        self.assertIn('id="ownerTicketTransferStatus"',html)
        self.assertIn('<script src="./owner-ticket-transfer.js" defer></script>',html)
        for name in ('rpDate','rpTrack','rpRace','rpFirst','rpSecond','rpThird'):
            self.assertIn("'"+name+"'",code)
        self.assertIn("recordType!=='live'",code)
        self.assertIn('unique.size>48',code)
        self.assertIn("new URLSearchParams",code)
        self.assertNotIn("localStorage.setItem",code)
        self.assertNotIn("fetch(",code)
        self.assertNotIn("KEIBA_OWNER_PASSWORD",code)
        self.assertNotIn("password:",code)

    def test_private_receiver_is_authenticated_and_never_saves_on_arrival(self):
        app=create_app(SETTINGS)
        unauthorized=call(app,'/my-tickets.js',auth='')
        self.assertEqual(unauthorized['status'],'401 Unauthorized')
        authorized=call(app,'/my-tickets.js')
        self.assertEqual(authorized['status'],'200 OK')
        source=authorized['body'].decode('utf-8')
        self.assertIn("new URLSearchParams(fragment.slice(1))",source)
        self.assertIn("window.history.replaceState",source)
        self.assertIn("first=new Set(incomingFirst)",source)
        self.assertIn("window.confirm",source)
        # The receiving segment itself never saves, purchases or transfers
        # credentials. The base notebook still has manual save buttons.
        from owner_ticket_handoff import JS
        self.assertNotIn('localStorage.setItem',JS)
        self.assertNotIn('fetch(',JS)
        self.assertNotIn('KEIBA_OWNER_PASSWORD',JS)
        self.assertNotIn('Set-Cookie',JS)
        self.assertNotIn('payout=',JS)
        self.assertNotIn('購入記録に追加',JS)


if __name__=='__main__':
    unittest.main()
