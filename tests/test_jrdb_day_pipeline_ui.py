"""Static authenticated iPhone day-readiness page; no provider requests on load."""
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from private_service import create_app
from test_private_service import SETTINGS, call
from jrdb_day_pipeline_ui import HTML, CSS, JS


class DayPipelinePageTests(unittest.TestCase):
    def setUp(self):
        self.app=create_app(SETTINGS)

    def test_login_redirect_and_protected_scripts(self):
        anonymous=call(self.app,'/day-pipeline',auth='')
        self.assertEqual(anonymous['status'],'303 See Other')
        self.assertEqual(anonymous['headers']['Location'],'/login')
        for path in ('/day-pipeline.css','/day-pipeline.js'):
            with self.subTest(path=path):
                out=call(self.app,path,auth='')
                self.assertEqual(out['status'],'401 Unauthorized')
                self.assertIn('no-store',out['headers']['Cache-Control'])

    def test_live_page_is_only_a_gateway_no_paid_fetch_or_storage(self):
        with (patch('private_service.fetch_race_program') as pro,
              patch('private_service.fetch_horse_entries') as entries,
              patch('private_service.fetch_training_analysis') as training):
            page=call(self.app,'/day-pipeline')
            style=call(self.app,'/day-pipeline.css')
            script=call(self.app,'/day-pipeline.js')
        self.assertEqual(page['status'],'200 OK')
        self.assertEqual(style['status'],'200 OK')
        self.assertEqual(script['status'],'200 OK')
        self.assertIn('text/html',page['headers']['Content-Type'])
        self.assertIn('text/javascript',script['headers']['Content-Type'])
        self.assertIn('text/css',style['headers']['Content-Type'])
        self.assertIn(b'/day-pipeline.js',page['body'])
        self.assertIn(b'id="run" type="button" disabled',page['body'])
        self.assertIn('認証',HTML)
        self.assertIn("async function init()",JS)
        self.assertIn("'/api/setup'",JS)
        self.assertIn("'/api/jrdb/day-pipeline?date='",JS)
        self.assertNotIn('localStorage',HTML+CSS+JS)
        self.assertNotIn('JRDB_API_KEY',HTML+CSS+JS)
        self.assertNotIn('innerHTML',JS)
        self.assertNotIn('setInterval',JS)
        pro.assert_not_called()
        entries.assert_not_called()
        training.assert_not_called()

    def test_owner_home_links_to_day_pipeline(self):
        home=call(self.app,'/')
        self.assertIn(b'href="/day-pipeline"',home['body'])


if __name__=='__main__':
    unittest.main()
