"""JRDB provisional mail parser is owner-only, browser-local and does not publish data."""
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from private_service import create_app
from jrdb_mail_local_import import HTML, CSS, JS
from test_private_service import SETTINGS, call


class LocalJRDBMailPageTests(unittest.TestCase):
    def setUp(self):
        self.app=create_app(SETTINGS)

    def test_owner_route_and_static_assets_are_login_protected(self):
        for path, content_type in (
            ('/jrdb-mail-local','text/html'),
            ('/jrdb-mail-local.js','text/javascript'),
            ('/jrdb-mail-local.css','text/css'),
        ):
            with self.subTest(path=path):
                access=call(self.app,path)
                self.assertEqual(access['status'],'200 OK')
                self.assertIn(content_type,access['headers']['Content-Type'])
                self.assertIn('no-store',access['headers']['Cache-Control'])
                no_auth=call(self.app,path,auth='')
                self.assertEqual(no_auth['status'],
                                 '303 See Other' if path=='/jrdb-mail-local'
                                 else '401 Unauthorized')
                self.assertNotIn(b'keiba-nine-jrdb-personal-mail-v1',no_auth['body'])
        self.assertIn(b'/jrdb-mail-local',call(self.app,'/')["body"])

    def test_no_server_mail_ingest_or_provider_or_paid_calls(self):
        with (
            patch('private_service.fetch_race_program') as programme,
            patch('private_service.fetch_horse_entries') as horses,
            patch('private_service.fetch_training_analysis') as training,
            patch('private_service.fetch_recent_runs') as recent,
        ):
            out=call(self.app,'/jrdb-mail-local')
            js=call(self.app,'/jrdb-mail-local.js')
        self.assertEqual(out['status'],'200 OK')
        self.assertEqual(js['status'],'200 OK')
        for provider in (programme,horses,training,recent):
            provider.assert_not_called()
        for path in ('/jrdb-mail-local','/jrdb-mail-local.js'):
            denied=call(self.app,path,method='POST')
            self.assertEqual(denied['status'],'404 Not Found')
        self.assertIn('本人用・端末内のみ',HTML)
        self.assertIn('■想定確定',JS)
        self.assertIn('localStorage',JS)
        self.assertIn('horse',JS)
        self.assertNotIn('fetch(',JS)
        self.assertNotIn('XMLHttpRequest',JS)
        self.assertNotIn('innerHTML',JS)
        self.assertNotIn('gmail.googleapis.com',JS)
        self.assertNotIn('JRDB_API_KEY',JS)
        self.assertNotIn('onrender.com',JS)
        self.assertIn('/jrdb-mail-local.js',HTML)
        self.assertNotIn('<script>',HTML)


if __name__=='__main__':
    unittest.main()
