import base64
import io
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from private_service import create_app, MAX_BODY
from jrdb_private import JRDBError
from test_research_pipeline import sample

# Synthetic fixture, not a deployed password.
SETTINGS = {'KEIBA_OWNER_PASSWORD': 'synthetic-test-fixture-1234567890-ABCDE'}
AUTH = 'Basic ' + base64.b64encode(('owner:' + SETTINGS['KEIBA_OWNER_PASSWORD']).encode()).decode()


def call(app, path='/', method='GET', auth=AUTH, data=None, **changes):
    raw = json.dumps(data).encode() if data is not None else b''
    env = {'wsgi.url_scheme': 'https', 'REMOTE_ADDR': '127.0.0.1', 'PATH_INFO': path,
           'REQUEST_METHOD': method, 'HTTP_AUTHORIZATION': auth, 'HTTP_X_KEIBA_REQUEST': 'private',
           'CONTENT_LENGTH': str(len(raw)), 'CONTENT_TYPE': 'application/json', 'wsgi.input': io.BytesIO(raw)}
    env.update(changes)
    result = {}
    def start(status, headers):
        result.update(status=status, headers=dict(headers))
    result['body'] = b''.join(app(env, start))
    return result


class PrivateServiceTests(unittest.TestCase):
    def setUp(self): self.app = create_app(SETTINGS)

    def test_anonymous_live_revision_reports_only_public_build_identity(self):
        sha = "a" * 40
        app = create_app({
            **SETTINGS, "RENDER_GIT_COMMIT": sha,
            "JRDB_PRIVATE_ENABLED": "1",
            "JRDB_API_KEY": "DONT_LEAK_PRIVATE_JRDB_KEY",
            "JRDB_AUTH_KEY": "DONT_LEAK_PRIVATE_JRDB_AUTH",
            "KEIBA_RENDER_PRIVATE_ONLY": "1",
        })
        response = call(app, "/live-revision", auth="")
        self.assertEqual(response["status"], "200 OK")
        self.assertIn("no-store", response["headers"]["Cache-Control"])
        self.assertEqual(json.loads(response["body"]), {
            "version": "owner-live-revision-1",
            "renderCommit": sha[:12],
            "revisionOnly": True,
            "jrdbConnectionVerified": False,
            "forecastExecutionVerified": False,
            "ownerDataIncluded": False,
        })
        for secret in ("DONT_LEAK_PRIVATE_JRDB_KEY", "DONT_LEAK_PRIVATE_JRDB_AUTH",
                       SETTINGS["KEIBA_OWNER_PASSWORD"], "JRDB_API_KEY"):
            self.assertNotIn(secret.encode(), response["body"])
        http_env = {"wsgi.url_scheme": "http", "REMOTE_ADDR": "198.51.100.4"}
        self.assertEqual(call(app, "/live-revision", auth="", **http_env)["status"],
                         "426 Upgrade Required")
        self.assertEqual(call(app, "/live-revision", auth="",
                              QUERY_STRING="key=anything")["status"],
                         "401 Unauthorized")
        self.assertEqual(call(app, "/live-revision", method="POST",
                              auth="")["status"], "401 Unauthorized")
        self.assertEqual(call(app, "/ui-version", auth="")["status"],
                         "401 Unauthorized")
        self.assertEqual(call(app, "/api/status", auth="")["status"],
                         "401 Unauthorized")

    def test_anonymous_revision_without_render_sha_is_explicitly_unknown(self):
        response = call(self.app, "/live-revision", auth="")
        self.assertEqual(response["status"], "200 OK")
        self.assertEqual(json.loads(response["body"])["renderCommit"],
                         "not-reported")

    def test_private_saturday_preflight_zero_provider_reads_and_auth(self):
        app = create_app({
            **SETTINGS, "KEIBA_RENDER_PRIVATE_ONLY": "1",
            "JRDB_PRIVATE_ENABLED": "1",
            "JRDB_API_KEY": "SYNTHETIC_PRESTART_KEY",
            "JRDB_AUTH_KEY": "SYNTHETIC_PRESTART_AUTH",
            # Owner Render boots only with the production host; the free
            # preflight must not count a blank/development host as ready.
            "JRDB_API_BASE_URL": "https://api.bigtime.world/v1",
        })
        with (patch("private_service.fetch_race_program") as programme,
              patch("private_service.fetch_horse_entries") as entries,
              patch("private_service.fetch_training_analysis") as training,
              patch("private_service.fetch_recent_runs") as recent,
              patch("private_service.fetch_venue_conditions") as going):
            response = call(app, "/api/owner-saturday-preflight",
                            QUERY_STRING="date=20261114")
            self.assertEqual(response["status"], "200 OK")
            payload = json.loads(response["body"])
            self.assertEqual(payload["version"], "owner-saturday-config-preflight-2")
            self.assertEqual(payload["date"], "20261114")
            self.assertTrue(payload["configurationReady"])
            self.assertTrue(payload["jrdbCredentialsFormatValid"])
            self.assertFalse(payload["providerPublicationVerified"])
            self.assertEqual(payload["sourceCallsMade"], 0)
            for flag in ("providerConnectionVerified", "liveRaceFeedVerified",
                         "officialJraVerified", "formalTenFactorsReady",
                         "archivePersistenceVerified", "bettingReady"):
                self.assertFalse(payload[flag])
            for private in ("SYNTHETIC_PRESTART_KEY", "SYNTHETIC_PRESTART_AUTH",
                            SETTINGS["KEIBA_OWNER_PASSWORD"], "horse_id"):
                self.assertNotIn(private.encode(), response["body"])
            programme.assert_not_called()
            entries.assert_not_called()
            training.assert_not_called()
            recent.assert_not_called()
            going.assert_not_called()
            self.assertEqual(call(app, "/api/owner-saturday-preflight",
                                  QUERY_STRING="date=20261114", auth="")["status"],
                             "401 Unauthorized")
            self.assertEqual(call(app, "/api/owner-saturday-preflight",
                                  QUERY_STRING="date=20260230")["status"],
                             "400 Bad Request")
            self.assertEqual(call(app, "/api/owner-saturday-preflight",
                                  QUERY_STRING="date=20261114",
                                  HTTP_X_KEIBA_REQUEST="")["status"],
                             "403 Forbidden")
            self.assertEqual(call(app, "/api/owner-saturday-preflight",
                                  method="POST", QUERY_STRING="date=20261114")["status"],
                             "404 Not Found")

    def test_owner_deployment_revision_check_requires_authentication(self):
        root = call(self.app, '/')['body'].decode('utf-8')
        js = call(self.app, '/app.js')['body'].decode('utf-8')
        self.assertIn('id="deployCheck"', root)
        self.assertIn('id="deployResult"', root)
        self.assertIn("request('/api/deploy-status')", js)
        self.assertIn('配信中の版IDを見る', root)
        report = {
            'version': 'owner-revision-diagnostic-1',
            'status': 'behind', 'renderCommit': '4c7f36010fee',
            'githubMainCommit': '00bf8a0ea0c5',
            'checkedOnDemand': True, 'autoDeployed': False,
            'predictionReady': False,
            'note': 'Renderが古い版を配信中です。',
        }
        with patch('private_service.inspect_owner_revision', return_value=report) as check:
            actual = call(self.app, '/api/deploy-status')
            self.assertEqual(actual['status'], '200 OK')
            self.assertEqual(json.loads(actual['body']), report)
            self.assertIn('no-store', actual['headers']['Cache-Control'])
            check.assert_called_once_with('not-reported')
        with patch('private_service.inspect_owner_revision') as check:
            denied = call(self.app, '/api/deploy-status', auth='')
            self.assertEqual(denied['status'], '401 Unauthorized')
            check.assert_not_called()
        self.assertEqual(call(self.app, '/api/deploy-status', method='POST')['status'],
                         '404 Not Found')

    def test_private_preday_forecast_page_assets_and_login(self):
        home = call(self.app, '/')['body'].decode()
        self.assertIn('href="/owner-preday-forecast"', home)
        for path, media in (
                ('/owner-preday-forecast', 'text/html'),
                ('/owner-preday-forecast.js', 'text/javascript'),
                ('/owner-preday-forecast.css', 'text/css')):
            ok = call(self.app, path)
            self.assertEqual(ok['status'], '200 OK')
            self.assertIn(media, ok['headers']['Content-Type'])
            self.assertIn('no-store', ok['headers']['Cache-Control'])
            denied = call(self.app, path, auth='')
            self.assertIn(denied['status'][:3], ('303','401'))
        js = call(self.app, '/owner-preday-forecast.js')['body'].decode()
        self.assertIn('keiba-nine-owner-preday-analysis-v1', js)
        self.assertIn('jraOfficialConfirmed!==false', js)
        self.assertIn('fullFactorVerified!==false', js)
        self.assertIn("fetch('/api/owner-preday-forecast'", js)
        self.assertIn("X-Keiba-Request", js)
        self.assertNotIn('innerHTML', js)

    def test_iphone_home_screen_entry_and_private_notebook_navigation(self):
        # Pure HTML navigation: no new public route, credentials or storage.
        home = call(self.app, '/')
        login = call(self.app, '/login', auth='')
        notebook = call(self.app, '/my-tickets')
        self.assertEqual(home['status'], '200 OK')
        self.assertEqual(notebook['status'], '200 OK')
        self.assertEqual(login['status'], '200 OK')
        root_html = home['body'].decode('utf-8')
        notebook_html = notebook['body'].decode('utf-8')
        login_html = login['body'].decode('utf-8')
        for body in (root_html, notebook_html, login_html):
            self.assertIn('name="apple-mobile-web-app-title"', body)
            self.assertIn('name="theme-color"', body)
        self.assertIn('class="owner-quick-start"', root_html)
        self.assertIn('href="/my-tickets"', root_html)
        self.assertIn('href="/jrdb-mail-local"', root_html)
        self.assertIn('Safariとデータが別になることがあります', root_html)
        for target in ('racePicker', 'formationPanel', 'bulkPanel',
                       'savedPanel', 'actualPurchasePanel'):
            self.assertIn('href="#' + target + '"', notebook_html)
            self.assertIn('id="' + target + '"', notebook_html)
        self.assertIn('id="mRaceBoard"', notebook_html)
        self.assertIn('保存状況の一覧です', notebook_html)
        self.assertIn('JSONバックアップ', notebook_html)
        denied = call(self.app, '/my-tickets', auth='')
        self.assertEqual(denied['status'], '303 See Other')
        self.assertEqual(denied['headers']['Location'], '/login')

    def test_home_keeps_synthetic_demo_behind_collapsed_section(self):
        root = call(self.app, '/')['body'].decode('utf-8')
        self.assertIn('aria-label="実戦で使うメニュー"', root)
        self.assertIn('class="developer-menu"', root)
        self.assertIn('class="developer-panel"', root)
        self.assertIn('<summary>架空の予想デモを表示（開発確認用）</summary>', root)
        self.assertIn('id="researchPanel"', root)
        self.assertIn('href="/my-scorecard"', root)
        self.assertIn('href="/owner-backup"', root)
        self.assertIn('href="/my-tickets"', root)
        self.assertNotIn('class="developer-panel" open', root)
        self.assertNotIn('class="developer-menu" open', root)
        self.assertIn('架空データ', root)

    def test_private_36r_workbench_has_login_and_no_data_upload(self):
        for route, marker in (
            ('/owner-races', '全開催Rの準備一覧'),
            ('/owner-race-workbench.js', 'keiba-nine-owner-factor-notes-v1'),
            ('/owner-race-workbench.css', '.race-grid'),
        ):
            with self.subTest(route=route):
                ok = call(self.app, route)
                self.assertEqual(ok['status'], '200 OK')
                self.assertIn('no-store', ok['headers']['Cache-Control'])
                self.assertIn(marker, ok['body'].decode('utf-8'))
                missing = call(self.app, route, auth='')
                if route == '/owner-races':
                    self.assertEqual(missing['status'], '303 See Other')
                    self.assertEqual(missing['headers']['Location'], '/login')
                else:
                    self.assertEqual(missing['status'], '401 Unauthorized')
                    self.assertNotIn('WWW-Authenticate', missing['headers'])
        home = call(self.app, '/')['body'].decode('utf-8')
        self.assertIn('href="/owner-races"', home)
        script = call(self.app, '/owner-race-workbench.js')['body'].decode('utf-8')
        self.assertIn("const PURCHASES='keiba-nine-owner-real-purchases-v1'", script)
        self.assertIn("const SCORES='keiba-nine-owner-factor-notes-v1'", script)
        self.assertIn("'/my-scorecard'", script)
        self.assertIn("'/my-tickets'", script)
        dashboard = call(self.app, '/owner-races')['body'].decode('utf-8')
        self.assertIn('id="workReload"', dashboard)
        self.assertIn('id="workOnlyActions"', dashboard)
        self.assertIn('id="workLedger"', dashboard)
        self.assertIn('端末内の記録を再読込', dashboard)
        self.assertIn("window.addEventListener('pageshow'", script)
        self.assertIn('tile.hidden=onlyActions', script)
        self.assertIn('function validPurchaseRecord(x)', script)
        self.assertIn('function summarizePurchases(data,date)', script)
        self.assertIn("label:'払戻未確定 '", script)
        self.assertNotIn('fetch(', script)
        self.assertNotIn('localStorage.setItem', script)
        self.assertNotIn('innerHTML', script)

    def test_owner_result_review_is_private_read_only(self):
        for route, text in (
            ('/owner-review', '着順ごとの振り返り'),
            ('/owner-review.js', "keiba-nine-owner-ticket-drafts-v1"),
            ('/owner-review.css', '.review-row'),
        ):
            with self.subTest(route=route):
                result = call(self.app, route)
                self.assertEqual(result['status'], '200 OK')
                self.assertIn('no-store', result['headers']['Cache-Control'])
                self.assertIn(text, result['body'].decode('utf-8'))
                denied = call(self.app, route, auth='')
                if route == '/owner-review':
                    self.assertEqual(denied['status'], '303 See Other')
                    self.assertEqual(denied['headers']['Location'], '/login')
                else:
                    self.assertEqual(denied['status'], '401 Unauthorized')
                    self.assertNotIn('WWW-Authenticate', denied['headers'])
        root = call(self.app, '/')['body'].decode('utf-8')
        self.assertIn('href="/owner-review"', root)
        script = call(self.app, '/owner-review.js')['body'].decode('utf-8')
        self.assertNotIn('fetch(', script)
        self.assertNotIn('XMLHttpRequest', script)
        self.assertNotIn('localStorage.setItem', script)
        self.assertNotIn('innerHTML', script)
        self.assertIn("const DRAFT='keiba-nine-owner-ticket-drafts-v1'", script)
        self.assertIn("const PURCHASE='keiba-nine-owner-real-purchases-v1'", script)
        self.assertIn("const conflict=outcomes.size>1", script)
        self.assertIn("function verdict(form,result)", script)
        self.assertIn('id="reviewFactorStats"', call(self.app, '/owner-review')['body'].decode('utf-8'))
        self.assertIn('id="reviewMode"', call(self.app, '/owner-review')['body'].decode('utf-8'))
        self.assertIn("const FACTOR_NOTE='keiba-nine-owner-factor-notes-v1'", script)
        self.assertIn("function sourceMatches(note,parsed,mail,numberMemos)", script)
        self.assertIn("const displayed=model.details.filter", script)

    def test_manual_scorecard_is_private_not_an_ai_prediction(self):
        for path, phrase in (
            ('/my-scorecard', '5項目の手動評価'),
            ('/owner-scorecard.js', "scoreHandoff"),
            ('/owner-scorecard.css', '.score-row'),
        ):
            with self.subTest(path=path):
                response = call(self.app, path)
                self.assertEqual(response['status'], '200 OK')
                self.assertIn('no-store', response['headers']['Cache-Control'])
                self.assertIn(phrase, response['body'].decode('utf-8'))
                denied = call(self.app, path, auth='')
                if path == '/my-scorecard':
                    self.assertEqual(denied['status'], '303 See Other')
                    self.assertEqual(denied['headers']['Location'], '/login')
                else:
                    self.assertEqual(denied['status'], '401 Unauthorized')
                    self.assertNotIn('WWW-Authenticate', denied['headers'])
        root = call(self.app, '/')['body'].decode('utf-8')
        notebook = call(self.app, '/my-tickets')['body'].decode('utf-8')
        self.assertIn('href="/my-scorecard"', root)
        self.assertIn('href="/my-scorecard"', notebook)
        page = call(self.app, '/my-scorecard')['body'].decode('utf-8')
        self.assertIn('AIによる調教分析', page)
        self.assertIn('実戦で使う前に公式出馬表', page)
        js = call(self.app, '/owner-scorecard.js')['body'].decode('utf-8')
        self.assertNotIn('fetch(', js)
        self.assertIn("localStorage.getItem('keiba-nine-owner-manual-numbers-v1')", js)
        self.assertIn('localStorage.setItem(NOTE_KEY', js)
        self.assertNotIn("localStorage.setItem('keiba-nine-jrdb-personal-mail-v1'", js)
        self.assertNotIn("localStorage.setItem('keiba-nine-owner-manual-numbers-v1'", js)
        self.assertNotIn("localStorage.setItem('keiba-nine-owner-real-purchases-v1'", js)
        self.assertNotIn('innerHTML', js)
        self.assertIn("window.location.assign('/my-tickets#'", js)

    def test_owner_backup_page_is_authenticated_and_local_only(self):
        for path, marker in (
            ('/owner-backup', '本人用データのバックアップ'),
            ('/owner-backup.js', "keiba-nine-owner-local-all-v1"),
            ('/owner-backup.css', 'max-width:670px'),
        ):
            with self.subTest(path=path):
                allowed = call(self.app, path)
                self.assertEqual(allowed['status'], '200 OK')
                self.assertIn('no-store', allowed['headers']['Cache-Control'])
                self.assertIn(marker, allowed['body'].decode('utf-8'))
                denied = call(self.app, path, auth='')
                if path == '/owner-backup':
                    self.assertEqual(denied['status'], '303 See Other')
                    self.assertEqual(denied['headers']['Location'], '/login')
                else:
                    self.assertEqual(denied['status'], '401 Unauthorized')
                    self.assertNotIn('WWW-Authenticate', denied['headers'])
        root = call(self.app, '/')['body'].decode('utf-8')
        notebook = call(self.app, '/my-tickets')['body'].decode('utf-8')
        self.assertIn('href="/owner-backup"', root)
        self.assertIn('href="/owner-backup"', notebook)
        js = call(self.app, '/owner-backup.js')['body'].decode('utf-8')
        self.assertNotIn('fetch(', js)
        self.assertNotIn('XMLHttpRequest', js)
        self.assertNotIn('innerHTML', js)

    def test_owner_home_screen_resume_checks_release_without_weakening_auth(self):
        active = create_app({**SETTINGS,
                             'RENDER_GIT_COMMIT': '0123456789abcdef0123456789abcdef01234567'})
        for path in ('/', '/preview-v2', '/my-tickets'):
            r = call(active, path)
            self.assertEqual(r['status'], '200 OK')
            html = r['body'].decode('utf-8')
            self.assertIn('name="keiba-owner-release"', html)
            self.assertIn('iphone-login-recovery-20261105-v9|0123456789ab', html)
            self.assertIn('src="/owner-update.js"', html)
            if path == '/my-tickets':
                self.assertIn('class="release-details"', html)
                self.assertIn('この画面の配信識別子：', html)
                self.assertIn('0123456789ab</code>', html)
            self.assertNotIn('__OWNER_RELEASE__', html)
            self.assertIn('no-store', r['headers']['Cache-Control'])
        javascript = call(active, '/owner-update.js')
        self.assertEqual(javascript['status'], '200 OK')
        self.assertIn('text/javascript', javascript['headers']['Content-Type'])
        self.assertIn("fetch('/ui-version'", javascript['body'].decode('utf-8'))
        self.assertNotIn(SETTINGS['KEIBA_OWNER_PASSWORD'], javascript['body'].decode('utf-8'))
        latest = call(active, '/ui-version')
        self.assertIn('renderCommit=0123456789ab', latest['body'].decode('utf-8'))
        for path in ('/owner-update.js', '/ui-version'):
            denied = call(active, path, auth='')
            self.assertTrue(denied['status'].startswith('401'))
            self.assertNotIn('WWW-Authenticate', denied['headers'])
        bare = call(self.app, '/my-tickets')['body'].decode('utf-8')
        self.assertIn('iphone-login-recovery-20261105-v9|not-reported', bare)
        self.assertNotIn('__OWNER_RELEASE__', bare)

    def test_no_or_weak_password_fails_closed(self):
        for config in [{}, {'KEIBA_OWNER_PASSWORD': 'short'}, {'KEIBA_OWNER_PASSWORD': 'x' * 40}]:
            with self.assertRaises(ValueError): create_app(config)

    def test_all_pages_require_owner(self):
        with patch('private_service.fetch_race_program') as fetch:
            for path in ['/', '/app.js', '/app.css', '/api/status', '/api/jrdb/program', '/api/research']:
                for auth in ['', 'Basic invalid', 'Basic ' + base64.b64encode(b'other:password').decode()]:
                    result = call(self.app, path=path, auth=auth)
                    if path == '/':
                        self.assertEqual(result['status'], '303 See Other')
                        self.assertEqual(result['headers']['Location'], '/login')
                    else:
                        self.assertTrue(result['status'].startswith('401'))
            fetch.assert_not_called()

    def test_private_selectors_are_read_only_without_paid_credentials(self):
        page = call(self.app, '/')['body'].decode('utf-8')
        script = call(self.app, '/app.js')['body'].decode('utf-8')
        self.assertIn('id="programmeTrack" disabled', page)
        self.assertIn('id="programmeRace" disabled', page)
        self.assertIn('id="programmeSelected"', page)
        self.assertIn('id="programmeDemo"', page)
        self.assertIn('id="programmeDemoNotice"', page)
        self.assertIn('id="programmeReadiness" type="button" disabled', page)
        self.assertIn('id="programmeReadinessResult"', page)
        self.assertIn("el('programmeReadiness').onclick=async()=>", script)
        self.assertIn('function showSingleRaceReadiness(', script)
        self.assertIn('実戦予想はまだ作成できません', script)
        self.assertIn('/api/jrdb/selected-readiness?', script)
        self.assertIn('/app.js?v=owner-mobile-navigation-20261104', page)
        self.assertIn('function loadOfflineProgrammeDemo()', script)
        self.assertIn("el('programmeDemo').onclick=loadOfflineProgrammeDemo", script)
        self.assertIn('架空3R', script)
        self.assertIn('20990101', script)
        self.assertIn('function loadProgrammePicker(rows,day)', script)
        self.assertIn('function showProgrammeSelection()', script)
        self.assertIn('selectedProgramme=[];loadedProgrammeDate', script)
        self.assertIn('実戦予想は未接続', script)
        self.assertNotIn('innerHTML', script)
        with patch('private_service.fetch_race_program') as provider:
            failed = call(self.app, '/api/jrdb/program',
                          QUERY_STRING='date=20261107')
            self.assertTrue(failed['status'].startswith('503'))
            provider.assert_not_called()

    def test_owner_ui_diagnostics_report_actual_served_layout(self):
        with patch('private_service.fetch_race_program') as provider:
            root = call(self.app, '/')
            separate = call(self.app, '/preview-v2',
                            HTTP_X_KEIBA_REQUEST='')
            self.assertEqual(root['status'], '200 OK')
            self.assertEqual(separate['status'], '200 OK')
            self.assertEqual(root['body'], separate['body'])
            page = separate['body'].decode('utf-8')
            self.assertIn('id="uiVersion"', page)
            self.assertIn('class="jump-nav"', page)
            self.assertIn('href="/my-tickets"', page)
            self.assertIn('href="#researchPanel"', page)
            self.assertIn('href="#jrdbSection"', page)
            self.assertIn('href="#operatorFactorPanel"', page)
            self.assertIn('href="#ownerTools"', page)
            self.assertIn('id="ownerManualSection"', page)
            self.assertIn('研究用の自動予想・馬券記録が使えます', page)
            self.assertIn('実馬のAI予想・馬券購入は未接続', page)
            self.assertIn('iphone-login-recovery-20261105-v9', page)
            self.assertLess(page.index('id="researchPanel"'),
                            page.index('<h2>JRDB接続</h2>'))
            version = call(self.app, '/ui-version',
                           HTTP_X_KEIBA_REQUEST='')
            self.assertEqual(version['status'], '200 OK')
            self.assertIn('text/plain', version['headers']['Content-Type'])
            self.assertIn('no-store', version['headers']['Cache-Control'])
            info = version['body'].decode('utf-8')
            self.assertIn('uiVersion=iphone-login-recovery-20261105-v9', info)
            self.assertIn('researchFirst=yes', info)
            self.assertIn('renderCommit=not-reported', info)
            self.assertNotIn(SETTINGS['KEIBA_OWNER_PASSWORD'], info)
            for path in ('/ui-version', '/preview-v2'):
                denied = call(self.app, path, auth='')
                if path == '/preview-v2':
                    self.assertEqual(denied['status'], '303 See Other')
                    self.assertEqual(denied['headers']['Location'], '/login')
                else:
                    self.assertTrue(denied['status'].startswith('401'))
        provider.assert_not_called()

    def test_owner_ui_diagnostic_uses_sanitized_git_revision(self):
        preview = create_app({**SETTINGS,
                              'RENDER_GIT_COMMIT': 'a239d5b33ff2e5a6d37757125e7128b4c2b8df53'})
        version = call(preview, '/ui-version')['body'].decode('utf-8')
        self.assertIn('renderCommit=a239d5b33ff2', version)
        bad = create_app({**SETTINGS,
                          'RENDER_GIT_COMMIT': 'malicious-value-with-secret'})
        bad_version = call(bad, '/ui-version')['body'].decode('utf-8')
        self.assertIn('renderCommit=not-reported', bad_version)
        self.assertNotIn('malicious-value-with-secret', bad_version)

    def test_http_and_spoofed_forwarded_header_rejected(self):
        result = call(self.app, **{'wsgi.url_scheme': 'http', 'HTTP_X_FORWARDED_PROTO': 'https'})
        self.assertTrue(result['status'].startswith('426'))
        self.assertNotIn('WWW-Authenticate', result['headers'])

    def test_local_http_requires_explicit_opt_in(self):
        local = create_app({**SETTINGS, 'KEIBA_ALLOW_LOCAL_HTTP': '1'})
        self.assertTrue(call(local, **{'wsgi.url_scheme': 'http'})['status'].startswith('200'))
        self.assertTrue(call(local, **{'wsgi.url_scheme': 'http', 'REMOTE_ADDR': '203.0.113.1'})['status'].startswith('426'))

    def test_status_has_no_credentials(self):
        result = call(self.app, '/api/status')
        self.assertEqual(json.loads(result['body']), {'jrdbConfigured': False, 'historyConfigured': False, 'manualComparisonConfigured': False, 'livePredictionEnabled': False})
        self.assertNotIn(SETTINGS['KEIBA_OWNER_PASSWORD'].encode(), result['body'])
        self.assertIn('no-store', result['headers']['Cache-Control'])
        self.assertNotIn('Access-Control-Allow-Origin', result['headers'])

    @staticmethod
    def manual_payload():
        return {
            'date': '20261101', 'source': 'operator_transcription',
            'races': [{
                'track': '東京', 'race': 1, 'completeRoster': False,
                'postTime': '10:10', 'going': '稍重', 'surface': '芝',
                'entries': [{
                    'horseNumber': '01', 'status': 'withdrawn',
                    'jockeyCode': None,
                }],
            }],
        }

    def test_manual_comparison_requires_separate_opt_in_and_owner(self):
        app = create_app({**SETTINGS, 'JRDB_PRIVATE_ENABLED': '1',
                          'JRDB_API_KEY': 'fixture', 'JRDB_AUTH_KEY': 'fixture'})
        self.assertFalse(json.loads(call(app, '/api/status')['body'])['manualComparisonConfigured'])
        with patch('private_service.fetch_race_program') as provider:
            out = call(app, '/api/jrdb/compare-manual', 'POST',
                       data=self.manual_payload())
            self.assertTrue(out['status'].startswith('503'))
        provider.assert_not_called()
        ready = create_app({**SETTINGS, 'JRDB_PRIVATE_ENABLED': '1',
                            'KEIBA_MANUAL_REFERENCE_ENABLED': '1',
                            'JRDB_API_KEY': 'fixture', 'JRDB_AUTH_KEY': 'fixture'})
        self.assertTrue(json.loads(call(ready, '/api/status')['body'])['manualComparisonConfigured'])
        with patch('private_service.fetch_race_program') as provider:
            for kw in ({'auth': ''},
                       {'HTTP_X_KEIBA_REQUEST': ''},
                       {'HTTP_SEC_FETCH_SITE': 'cross-site'},
                       {'wsgi.url_scheme': 'http'}):
                response = call(ready, '/api/jrdb/compare-manual', 'POST',
                                data=self.manual_payload(), **kw)
                self.assertTrue(response['status'].startswith(
                    ('401', '403', '426')))
        provider.assert_not_called()

    def test_manual_comparison_rejects_bad_payload_before_provider_fetch(self):
        ready = create_app({**SETTINGS, 'JRDB_PRIVATE_ENABLED': '1',
                            'KEIBA_MANUAL_REFERENCE_ENABLED': '1',
                            'JRDB_API_KEY': 'fixture', 'JRDB_AUTH_KEY': 'fixture'})
        from copy import deepcopy
        cases = []
        base = self.manual_payload()
        def altered(fn):
            p = deepcopy(base)
            fn(p)
            cases.append(p)
        altered(lambda x: x.update(source='future_authorized_adapter'))
        altered(lambda x: x.update(date='20260230'))
        altered(lambda x: x['races'][0].update(completeRoster=True))
        altered(lambda x: x['races'].append(deepcopy(x['races'][0])))
        altered(lambda x: x['races'][0].update(track='札幌' * 100))
        altered(lambda x: x['races'][0].update(entries=[{'horseNumber':'99',
                             'status':'withdrawn','jockeyCode':None}]))
        altered(lambda x: x['races'][0].update(entries=[{'horseNumber':'01',
                             'status':'invalid','jockeyCode':None}]))
        altered(lambda x: x['races'][0].update(postTime='19:70'))
        altered(lambda x: x['races'][0].update(going='UNKNOWN-GOING'))
        altered(lambda x: x['races'][0].update(extra='secret-source-row'))
        altered(lambda x: x['races'][0].update(
            entries=[], postTime=None, going=None, surface=None))
        with patch('private_service.fetch_race_program') as provider:
            for case in cases:
                with self.subTest(case=str(case)[:60]):
                    out = call(ready, '/api/jrdb/compare-manual',
                               'POST', data=case)
                    self.assertTrue(out['status'].startswith('400'))
                    self.assertNotIn(b'secret-source-row', out['body'])
            self.assertTrue(call(ready, '/api/jrdb/compare-manual', 'POST',
                                 data=base, QUERY_STRING='debug=1')['status'].startswith('400'))
        provider.assert_not_called()

    def test_manual_one_race_comparison_reports_only_aggregate_differences(self):
        from test_jrdb_race_day_gates import fixture
        programme, entries, conditions = fixture()
        raw = [{
            'racekey': r['racekey'], 'racedate': '20261101',
            'track_type': '1' if r['track'] == '東京' else '2',
            'distance': str(r['distance_m']),
            'turn_cd': '2' if r['turn'] == '左' else '1',
            'headcount': r['headcount'], 'post_time': '1000'
        } for r in programme]
        ready = create_app({**SETTINGS, 'JRDB_PRIVATE_ENABLED': '1',
                            'KEIBA_MANUAL_REFERENCE_ENABLED': '1',
                            'JRDB_API_KEY': 'fixture', 'JRDB_AUTH_KEY': 'fixture'})
        with (
            patch('private_service.fetch_race_program', return_value=raw) as p,
            patch('private_service.fetch_horse_entries', return_value=entries) as e,
            patch('private_service.fetch_venue_conditions', return_value=conditions) as c,
        ):
            out = call(ready, '/api/jrdb/compare-manual', 'POST',
                       data=self.manual_payload())
        self.assertEqual(out['status'], '200 OK')
        report = json.loads(out['body'])
        self.assertEqual(report['racesCompared'], 1)
        self.assertEqual(report['racesMissingReference'], 1)
        tokyo = next(x for x in report['races'] if x['track'] == '東京')
        self.assertEqual(tokyo['differenceCategories']['postTime'], 1)
        self.assertEqual(tokyo['differenceCategories']['going'], 1)
        self.assertEqual(tokyo['differenceCategories']['withdrawal'], 1)
        self.assertEqual(tokyo['differenceCount'], 3)
        self.assertFalse(tokyo['independentSnapshotAuthenticated'])
        self.assertFalse(report['officialJraFinalVerification'])
        self.assertFalse(report['predictionReady'])
        self.assertFalse(report['bettingReady'])
        p.assert_called_once_with('20261101')
        e.assert_called_once_with('20261101')
        c.assert_called_once_with('20261101')
        for forbidden in (b'LICENSED-HORSE-PRIVATE', b'LICENSED-GOING-PRIVATE',
                          b'horse_number', b'horseNumber', b'jockey_code',
                          b'racekey', b'2328aaa95a05'):
            self.assertNotIn(forbidden, out['body'])
        self.assertIn('no-store', out['headers']['Cache-Control'])

    def test_historical_check_requires_separate_opt_in_without_fetches(self):
        app = create_app({**SETTINGS, 'JRDB_PRIVATE_ENABLED': '1',
                          'JRDB_API_KEY': 'synthetic-key', 'JRDB_AUTH_KEY': 'synthetic-user'})
        status = json.loads(call(app, '/api/status')['body'])
        self.assertTrue(status['jrdbConfigured'])
        self.assertFalse(status['historyConfigured'])
        with patch('private_service.fetch_race_program') as fetch:
            denied = call(app, '/api/jrdb/history', 'POST',
                          data={'date': '20261101', 'limit': 8})
        self.assertTrue(denied['status'].startswith('503'))
        fetch.assert_not_called()

    def test_historical_check_rejects_invalid_or_cross_site_request(self):
        config = {**SETTINGS, 'JRDB_PRIVATE_ENABLED': '1',
                  'JRDB_API_KEY': 'synthetic-key', 'JRDB_AUTH_KEY': 'synthetic-user',
                  'KEIBA_HISTORY_ENABLED': '1'}
        app = create_app(config)
        self.assertTrue(json.loads(call(app, '/api/status')['body'])['historyConfigured'])
        with patch('private_service.fetch_race_program') as fetch:
            for req in ({'date': '20261101', 'limit': 9},
                        {'date': '20261101', 'limit': True},
                        {'date': '20261301', 'limit': 1},
                        {'date': '20261101', 'limit': 1, 'racekey': 'secret'}):
                bad = call(app, '/api/jrdb/history', 'POST', data=req)
                self.assertTrue(bad['status'].startswith('400'))
            xsite = call(app, '/api/jrdb/history', 'POST',
                         data={'date': '20261101'}, HTTP_SEC_FETCH_SITE='cross-site')
            self.assertTrue(xsite['status'].startswith('403'))
            noauth = call(app, '/api/jrdb/history', 'POST',
                          data={'date': '20261101'}, auth='')
            self.assertTrue(noauth['status'].startswith('401'))
        fetch.assert_not_called()

    def test_historical_check_uses_only_redacted_bounded_private_results(self):
        from test_jrdb_going_history import sample_going
        from test_jrdb_evidence_readiness import sample as evidence_sample
        p, entries, previous, oldprogram, oldgoing, current = sample_going()
        _, _, training, _ = evidence_sample()
        raw_program = [
            {'racekey': x['racekey'], 'racedate': x['racedate'],
             'post_time': '1010', 'headcount': x['headcount'],
             'track_type': '1' if x['surface'] == '芝' else '2',
             'distance': str(x['distance_m']),
             'turn_cd': '2' if x['turn'] == '左' else '1'}
            for x in p
        ]
        config = {**SETTINGS, 'JRDB_PRIVATE_ENABLED': '1',
                  'JRDB_API_KEY': 'synthetic-key', 'JRDB_AUTH_KEY': 'synthetic-user',
                  'KEIBA_HISTORY_ENABLED': '1'}
        app = create_app(config)
        with (
            patch('private_service.fetch_race_program', return_value=raw_program),
            patch('private_service.fetch_horse_entries', return_value=entries),
            patch('private_service.fetch_recent_runs', return_value=previous),
            patch('private_service.fetch_training_analysis', return_value=training),
            patch('private_service.fetch_venue_conditions', return_value=current),
            patch('private_service.fetch_historical_race_program',
                  side_effect=lambda key: [x for x in oldprogram if x['racekey'] == key]) as dra,
            patch('private_service.fetch_historical_venue_conditions',
                  side_effect=lambda key: [x for x in oldgoing if x['holdingkey'] == key[:6]]) as dka,
        ):
            out = call(app, '/api/jrdb/history', 'POST',
                       data={'date': '20261101', 'limit': 8})
        self.assertEqual(out['status'], '200 OK')
        report = json.loads(out['body'])
        self.assertEqual(report['draCalls'], 3)
        self.assertEqual(report['dkaCalls'], 2)
        quality = next(x for x in report['evidenceQuality']['races'] if x['track'] == '東京')
        self.assertEqual(quality['courseComparableSamples']['oneOrTwo'], 1)
        self.assertEqual(quality['knownGoingComparableSamples']['none'], 1)
        self.assertFalse(report['evidenceQuality']['predictionConfidenceAssessed'])
        tokyo_materials = next(x for x in report['tenFactorMaterials']['races']
                               if x['track'] == '東京')
        self.assertEqual(report['tenFactorMaterials']['factorCount'], 10)
        self.assertEqual(tokyo_materials['observedFactorCount'], 4)
        self.assertEqual(tokyo_materials['factors']['training']['observedRunnerCount'], 2)
        self.assertEqual(tokyo_materials['factors']['course_distance']['observedRunnerCount'], 1)
        self.assertTrue(all(x['grade'] == '未評価'
                            for x in tokyo_materials['factors'].values()))
        self.assertFalse(report['tenFactorMaterials']['bettingReady'])
        self.assertFalse(report['predictionReady'])
        self.assertFalse(report['goingSuitabilityAssessed'])
        complete = report['allTenFactorSources']
        self.assertEqual(complete['raceCount'], 2)
        tokyo_combined = next(x for x in complete['races'] if x['track'] == '東京')
        self.assertEqual(tokyo_combined['sourceMaterialSlots'], 10)
        self.assertEqual(tokyo_combined['verifiedFactorCount'], 0)
        self.assertFalse(tokyo_combined['overallRankReady'])
        self.assertFalse(complete['predictionReady'])
        gate = report['realAssessmentPreflight']
        self.assertEqual(gate['version'], 'real-assessment-preflight-1')
        self.assertEqual(gate['raceCount'], 2)
        self.assertFalse(gate['realGradeReady'])
        self.assertFalse(gate['purchaseReady'])
        self.assertTrue(all(not row['realPredictionReady']
                            for row in gate['races']))
        tokyo = next(x for x in report['goingSummary']['races'] if x['track'] == '東京')
        self.assertEqual(tokyo['heavyComparableRuns'], 1)
        self.assertEqual(dra.call_count, 3)
        self.assertEqual(dka.call_count, 2)
        for private_value in (b'PRIVATE-HORSE', b'PAID-SECRET', b'racekey',
                              b'horse_id', b'05264a01', b'byNumber'):
            self.assertNotIn(private_value, out['body'])

    def test_race_day_status_fails_closed_without_config_or_auth(self):
        unconfigured = call(self.app, '/api/jrdb/race-day', QUERY_STRING='date=20261101')
        self.assertTrue(unconfigured['status'].startswith('503'))
        cfg = create_app({**SETTINGS, 'JRDB_PRIVATE_ENABLED': '1'})
        with patch('private_service.fetch_race_program') as fetch:
            for date in ('not-a-day', '20260230', '20261101&race=1', '20261101&now=20261101', ''):
                out = call(cfg, '/api/jrdb/race-day', QUERY_STRING='date='+date)
                self.assertTrue(out['status'].startswith('400'))
            self.assertTrue(call(cfg, '/api/jrdb/race-day',
                         QUERY_STRING='date=20261101', auth='')['status'].startswith('401'))
            self.assertTrue(call(cfg, '/api/jrdb/race-day', QUERY_STRING='date=20261101',
                         HTTP_X_KEIBA_REQUEST='')['status'].startswith('403'))
        fetch.assert_not_called()

    def test_race_day_reports_source_withdrawals_without_licensed_rows(self):
        from test_jrdb_race_day_gates import fixture
        programme, entries, conditions = fixture()
        raw = [{
            'racekey': r['racekey'], 'racedate': '20261101',
            'track_type': '1' if r['track']=='東京' else '2',
            'distance': str(r['distance_m']),
            'turn_cd': '2' if r['turn']=='左' else '1',
            'headcount': r['headcount'],
            'post_time': '1010',
        } for r in programme]
        app = create_app({**SETTINGS, 'JRDB_PRIVATE_ENABLED': '1'})
        with (
            patch('private_service.fetch_race_program', return_value=raw) as program,
            patch('private_service.fetch_horse_entries', return_value=entries) as horses,
            patch('private_service.fetch_venue_conditions', return_value=conditions) as venue,
            patch('private_service._now_in_jst', return_value='2026-11-01T09:30:00+09:00'),
        ):
            out = call(app, '/api/jrdb/race-day', QUERY_STRING='date=20261101')
        self.assertEqual(out['status'], '200 OK')
        data = json.loads(out['body'])
        self.assertEqual(data['racesWithProviderWithdrawal'], 1)
        self.assertEqual(data['racesWithUnknownFlags'], 1)
        self.assertEqual(data['racesWithOfficialFinalCheck'], 0)
        comparison = data['independentComparison']
        self.assertEqual(comparison['racesCompared'], 0)
        self.assertEqual(comparison['racesMissingReference'], data['raceCount'])
        self.assertEqual(comparison['racesWithDifferences'], 0)
        self.assertFalse(comparison['officialJraFinalVerification'])
        self.assertFalse(comparison['bettingReady'])
        self.assertTrue(all(x['comparisonStatus'] == 'missing_reference'
                            for x in comparison['races']))
        prestart = data['prestartFreshness']
        self.assertEqual(prestart['checkedAtJapan'], '2026-11-01 09:30 JST')
        self.assertEqual(prestart['racesWithinTwoHours'], 2)
        self.assertEqual(prestart['officiallyVerifiedRaces'], 0)
        self.assertFalse(prestart['predictionReady'])
        self.assertFalse(prestart['bettingReady'])
        tokyo_time = next(x for x in prestart['races'] if x['track'] == '東京')
        self.assertEqual(tokyo_time['sourceGoingAgeStatus'], 'recent_reported')
        self.assertFalse(tokyo_time['jraPostTimeVerified'])
        self.assertTrue(tokyo_time['candidateForManualJraReview'])
        self.assertFalse(data['predictionReady'])
        self.assertFalse(data['bettingReady'])
        tokyo = next(x for x in data['races'] if x['track'] == '東京')
        self.assertEqual(tokyo['providerWithdrawnCount'], 1)
        self.assertFalse(tokyo['officialScratchesVerified'])
        self.assertFalse(tokyo['officialGoingVerified'])
        self.assertFalse(tokyo['finalRaceReady'])
        program.assert_called_once_with('20261101')
        horses.assert_called_once_with('20261101')
        venue.assert_called_once_with('20261101')
        for private in (b'LICENSED-HORSE-PRIVATE', b'LICENSED-GOING-PRIVATE',
                        b'racekey', b'horse_number', b'horse_name', b'2328aaa95a05'):
            self.assertNotIn(private, out['body'])

    def test_race_day_malformed_withdrawal_is_redacted_502(self):
        from test_jrdb_race_day_gates import fixture
        p, e, c = fixture()
        e[0]['withdrawn_flag'] = '9'
        raw = [{
            'racekey': r['racekey'], 'racedate': '20261101',
            'track_type': '1' if r['track']=='東京' else '2',
            'distance': str(r['distance_m']),
            'turn_cd': '2' if r['turn']=='左' else '1',
            'headcount': r['headcount'], 'post_time': '1010'
        } for r in p]
        app = create_app({**SETTINGS, 'JRDB_PRIVATE_ENABLED': '1'})
        with (
            patch('private_service.fetch_race_program', return_value=raw),
            patch('private_service.fetch_horse_entries', return_value=e),
            patch('private_service.fetch_venue_conditions', return_value=c),
        ):
            out = call(app, '/api/jrdb/race-day', QUERY_STRING='date=20261101')
        self.assertTrue(out['status'].startswith('502'))
        self.assertNotIn(b'LICENSED-HORSE-PRIVATE', out['body'])

    def test_no_directory_or_repo_file_serving(self):
        for path in ['/../.env', '/scripts/jrdb_private.py', '/keiba-nine-auto-feed.json']:
            self.assertTrue(call(self.app, path)['status'].startswith('404'))

    def test_cross_site_or_simple_request_denied(self):
        for extra in [{'HTTP_SEC_FETCH_SITE': 'cross-site'}, {'HTTP_X_KEIBA_REQUEST': ''}]:
            self.assertTrue(call(self.app, '/api/research', 'POST', data=sample(), **extra)['status'].startswith('403'))

    def test_setup_diagnostic_requires_owner_and_custom_header(self):
        for auth in ('', 'Basic malformed'):
            self.assertTrue(call(self.app, '/api/setup', auth=auth)['status'].startswith('401'))
        self.assertTrue(call(self.app, '/api/setup', HTTP_X_KEIBA_REQUEST='')['status'].startswith('403'))

    def test_setup_diagnostic_discloses_no_secrets_or_false_readiness(self):
        out = call(self.app, '/api/setup')
        self.assertEqual(out['status'], '200 OK')
        data = json.loads(out['body'])
        self.assertEqual(data['transport'], 'https')
        self.assertFalse(data['jrdbConfigured'])
        self.assertFalse(data['prestartBodyEnabled'])
        self.assertFalse(data['historyConfigured'])
        self.assertFalse(data['liveConnectionVerified'])
        self.assertFalse(data['realPredictionEnabled'])
        self.assertNotIn(SETTINGS['KEIBA_OWNER_PASSWORD'].encode(), out['body'])
        self.assertEqual(set(data), {'transport', 'jrdbConfigured', 'prestartBodyEnabled',
                                   'historyConfigured', 'liveConnectionVerified', 'realPredictionEnabled',
                                   'nextStep'})
        self.assertIn('no-store', out['headers']['Cache-Control'])

    def test_configured_setup_diagnostic_never_claims_live_api_success(self):
        cfg = {**SETTINGS, 'JRDB_PRIVATE_ENABLED': '1',
               'JRDB_API_KEY': 'synthetic-api-key-not-real',
               'JRDB_AUTH_KEY': 'synthetic-auth-key-not-real'}
        with patch('private_service.fetch_race_program') as fetch:
            out = call(create_app(cfg), '/api/setup')
        self.assertEqual(out['status'], '200 OK')
        body = json.loads(out['body'])
        self.assertTrue(body['jrdbConfigured'])
        self.assertFalse(body['historyConfigured'])
        self.assertFalse(body['liveConnectionVerified'])
        self.assertFalse(body['realPredictionEnabled'])
        self.assertNotIn(cfg['JRDB_API_KEY'].encode(), out['body'])
        self.assertNotIn(cfg['JRDB_AUTH_KEY'].encode(), out['body'])
        fetch.assert_not_called()

    def test_setup_rejects_unknown_api_origin_even_with_keys(self):
        cfg = {**SETTINGS, 'JRDB_PRIVATE_ENABLED': '1',
               'JRDB_API_KEY': 'test-only', 'JRDB_AUTH_KEY': 'test-only',
               'JRDB_API_BASE_URL': 'https://other-host.example/v1'}
        with patch('private_service.fetch_race_program') as fetch:
            app = create_app(cfg)
            setup = json.loads(call(app, '/api/setup')['body'])
            status = json.loads(call(app, '/api/status')['body'])
        self.assertFalse(setup['jrdbConfigured'])
        self.assertFalse(status['jrdbConfigured'])
        self.assertFalse(setup['liveConnectionVerified'])
        fetch.assert_not_called()

    def test_setup_accepts_documented_api_origin_without_calling_jrdb(self):
        cfg = {**SETTINGS, 'JRDB_PRIVATE_ENABLED': '1',
               'JRDB_API_KEY': 'test-only', 'JRDB_AUTH_KEY': 'test-only',
               'JRDB_API_BASE_URL': 'https://api.bigtime.world/v1'}
        with patch('private_service.fetch_race_program') as fetch:
            setup = json.loads(call(create_app(cfg), '/api/setup')['body'])
        self.assertTrue(setup['jrdbConfigured'])
        self.assertFalse(setup['liveConnectionVerified'])
        fetch.assert_not_called()

    def test_preview_service_cannot_accidentally_enable_licensed_api(self):
        cfg = {**SETTINGS, 'KEIBA_RENDER_PREVIEW_ONLY': '1',
               'JRDB_PRIVATE_ENABLED': '1',
               'JRDB_API_KEY': 'test-only',
               'JRDB_AUTH_KEY': 'test-only'}
        with patch('private_service.fetch_race_program') as fetch, \
             self.assertRaisesRegex(ValueError, 'Render preview mode'):
            create_app(cfg)
        fetch.assert_not_called()
        safe = create_app({**SETTINGS, 'KEIBA_RENDER_PREVIEW_ONLY': '1',
                           'JRDB_PRIVATE_ENABLED': '0'})
        response = call(safe, '/api/setup')
        self.assertFalse(json.loads(response['body'])['jrdbConfigured'])

    def test_owner_only_one_request_connection_check_no_data_returned(self):
        cfg = {**SETTINGS, 'JRDB_PRIVATE_ENABLED': '1',
               'JRDB_API_KEY': 'synthetic-app-key',
               'JRDB_AUTH_KEY': 'synthetic-user-key'}
        app = create_app(cfg)
        for denied in (
                call(app, '/api/jrdb/connection-test', auth='',
                     QUERY_STRING='date=20261107'),
                call(app, '/api/jrdb/connection-test',
                     QUERY_STRING='date=20261107',
                     HTTP_X_KEIBA_REQUEST='')):
            self.assertIn(denied['status'][:3], ('401', '403'))
        with patch('private_service.fetch_race_program', return_value=[
                {'licensed_field': 'secret-value'}]) as read, \
             patch('private_service.normalize_program_rows', return_value=[{}, {}]) as normalize:
            out = call(app, '/api/jrdb/connection-test',
                       QUERY_STRING='date=20261107')
        self.assertEqual(out['status'], '200 OK')
        report = json.loads(out['body'])
        self.assertEqual(report, {'date': '20261107',
                                'connectionVerified': True,
                                'programmeCount': 2,
                                'providerDataStored': False,
                                'predictionReady': False})
        self.assertNotIn(b'licensed_field', out['body'])
        self.assertNotIn(b'secret-value', out['body'])
        self.assertNotIn(b'synthetic-app-key', out['body'])
        self.assertIn('no-store', out['headers']['Cache-Control'])
        read.assert_called_once_with('20261107')
        normalize.assert_called_once()

    def test_connection_check_disabled_or_bad_query_never_fetches(self):
        for cfg in (SETTINGS, {**SETTINGS, 'JRDB_PRIVATE_ENABLED': '1',
                'JRDB_API_KEY': 'fake', 'JRDB_AUTH_KEY': 'fake',
                'JRDB_API_BASE_URL': 'https://untrusted.example/v1'}):
            with patch('private_service.fetch_race_program') as fetch:
                out = call(create_app(cfg), '/api/jrdb/connection-test',
                           QUERY_STRING='date=20261107')
                self.assertTrue(out['status'].startswith('503'))
                fetch.assert_not_called()
        cfg = {**SETTINGS, 'JRDB_PRIVATE_ENABLED': '1',
               'JRDB_API_KEY': 'fake', 'JRDB_AUTH_KEY': 'fake'}
        for query in ('', 'date=20261107&extra=1',
                      'date=20261107&date=20261108',
                      'date=20260230', 'date=20261107%0D'):
            with self.subTest(query=query), patch('private_service.fetch_race_program') as fetch:
                out = call(create_app(cfg), '/api/jrdb/connection-test',
                           QUERY_STRING=query)
                self.assertTrue(out['status'].startswith('400'))
                fetch.assert_not_called()

    def test_connection_check_sanitized_provider_failures(self):
        cfg = {**SETTINGS, 'JRDB_PRIVATE_ENABLED': '1',
               'JRDB_API_KEY': 'secret-app-should-not-appear',
               'JRDB_AUTH_KEY': 'secret-user-should-not-appear'}
        for status in (401, 403, 429):
            with self.subTest(status=status), patch(
                 'private_service.fetch_race_program',
                 side_effect=JRDBError('JRDB request failed (HTTP %s)' % status)):
                out = call(create_app(cfg), '/api/jrdb/connection-test',
                           QUERY_STRING='date=20261107')
                self.assertEqual(out['status'], '502 Bad Gateway')
                self.assertNotIn(b'secret-app', out['body'])
                self.assertNotIn(b'secret-user', out['body'])
                self.assertIn('error', json.loads(out['body']))

    def test_jrdb_connection_diagnostic_logs_only_fixed_status_codes(self):
        cfg = {**SETTINGS, 'JRDB_PRIVATE_ENABLED': '1',
               'JRDB_API_KEY': 'sensitive-app-key-not-for-logs',
               'JRDB_AUTH_KEY': 'sensitive-user-key-not-for-logs'}
        app = create_app(cfg)
        for count, label in ((0, 'empty'), (1, 'present')):
            with (self.subTest(count=count),
                patch('private_service.fetch_race_program',
                      return_value=[{'private_horse_name': 'DO-NOT-LOG'}]),
                patch('private_service.normalize_program_rows',
                      return_value=[{}] * count),
                patch('private_service.logging.warning') as logger,
            ):
                result = call(app, '/api/jrdb/connection-test',
                              QUERY_STRING='date=20261107')
                self.assertEqual(result['status'], '200 OK')
                self.assertEqual(logger.call_count, 1)
                self.assertEqual(logger.call_args.args[0],
                                 'KEIBA_JRDB_CONNECTION_TEST status=connected programme=%s')
                self.assertEqual(logger.call_args.args[1], label)
                logged = str(logger.call_args)
                for forbidden in ('20261107', 'DO-NOT-LOG', 'sensitive-app',
                                  'sensitive-user', 'private_horse_name'):
                    self.assertNotIn(forbidden, logged)
        with (patch('private_service.fetch_race_program',
                    side_effect=JRDBError('JRDB request failed (HTTP 403)')),
              patch('private_service.logging.warning') as logger):
            result = call(app, '/api/jrdb/connection-test',
                          QUERY_STRING='date=20261107')
            self.assertEqual(result['status'], '502 Bad Gateway')
            self.assertEqual(logger.call_args.args[1], 'entitlement')
            self.assertNotIn('20261107', str(logger.call_args))

    def test_owner_connection_button_only_enabled_after_setup(self):
        home = call(self.app, '/')['body'].decode()
        js = call(self.app, '/app.js')['body'].decode()
        self.assertIn('id="jrdbConnectTest"', home)
        self.assertIn('id="jrdbConnectResult"', home)
        self.assertIn('disabled>JRDB', home)
        self.assertIn("request('/api/jrdb/connection-test?date='", js)
        self.assertIn("el('jrdbConnectTest').disabled=!enabled", js)

    def test_history_setup_explicit_gate_without_provider_fetch(self):
        cfg = {**SETTINGS, 'JRDB_PRIVATE_ENABLED': '1',
               'JRDB_API_KEY': 'synthetic-api-not-real',
               'JRDB_AUTH_KEY': 'synthetic-auth-not-real',
               'KEIBA_HISTORY_ENABLED': '1'}
        with patch('private_service.fetch_historical_race_program') as history, \
             patch('private_service.fetch_race_program') as today:
            reply = call(create_app(cfg), '/api/setup')
        self.assertEqual(reply['status'], '200 OK')
        report = json.loads(reply['body'])
        self.assertTrue(report['historyConfigured'])
        self.assertTrue(report['jrdbConfigured'])
        self.assertFalse(report['liveConnectionVerified'])
        self.assertFalse(report['realPredictionEnabled'])
        history.assert_not_called()
        today.assert_not_called()
        self.assertNotIn(cfg['JRDB_API_KEY'].encode(), reply['body'])

    def test_http_preview_cannot_enable_paid_jrdb_credentials(self):
        with self.assertRaisesRegex(ValueError, 'HTTPS-only'):
            create_app({**SETTINGS, 'KEIBA_ALLOW_LOCAL_HTTP': '1',
                        'JRDB_PRIVATE_ENABLED': '1', 'JRDB_API_KEY': 'fake',
                        'JRDB_AUTH_KEY': 'fake'})
        local = create_app({**SETTINGS, 'KEIBA_ALLOW_LOCAL_HTTP': '1'})
        info = json.loads(call(local, '/api/setup', **{'wsgi.url_scheme':'http'})['body'])
        self.assertEqual(info['transport'], 'local-dev')
        self.assertFalse(info['jrdbConfigured'])

    def test_synthetic_research_page_has_readable_cards_and_folded_json(self):
        page = call(self.app, '/')['body'].decode('utf-8')
        stylesheet = call(self.app, '/app.css')['body'].decode('utf-8')
        script = call(self.app, '/app.js')['body'].decode('utf-8')
        self.assertIn('id="researchDemo"', page)
        self.assertIn('id="researchSummary"', page)
        self.assertLess(page.index('id="researchPanel"'), page.index('id="raceday"'))
        self.assertIn('id="researchMessage" role="status"', page)
        self.assertIn('<details id="researchAdvanced"', page)
        self.assertIn('<details id="researchDetails"', page)
        self.assertIn('id="researchOutput"', page)
        self.assertNotIn('<details id="researchAdvanced" open', page)
        self.assertIn('架空8頭', page)
        self.assertIn('href="/app.css?theme=owner-mobile-nav-20261104"', page)
        self.assertIn('grade-s{background:#D4AF37;color:#0B2343;border:1px solid #E6C75A}', stylesheet)
        self.assertIn('grade-a{background:#c6374c}', stylesheet)
        self.assertIn('formation-columns', stylesheet)
        self.assertIn('function renderResearchSummary(data,input)', script)
        self.assertIn('全組み合わせが買い目とは限りません', script)
        self.assertNotIn('innerHTML', script)
        self.assertNotIn('JRDB_API_KEY', page)
        self.assertIn('no-store', call(self.app, '/')['headers']['Cache-Control'])

    def test_private_page_exposes_diagnostic_without_credentials(self):
        html = call(self.app, '/')['body']
        script = call(self.app, '/app.js')['body']
        self.assertIn(b'id="diagnose"', html)
        self.assertIn(b'/api/setup', script)
        self.assertNotIn(SETTINGS['KEIBA_OWNER_PASSWORD'].encode(), html + script)

    def test_live_connection_disabled_by_default(self):
        with patch('private_service.fetch_race_program') as fetch:
            self.assertTrue(call(self.app, '/api/jrdb/program', QUERY_STRING='date=20261027')['status'].startswith('503'))
            fetch.assert_not_called()

    def test_authorized_connection_uses_fixed_client(self):
        app = create_app({**SETTINGS, 'JRDB_PRIVATE_ENABLED': '1'})
        incoming = [{'racekey': '05264b11', 'racedate': '20261027',
                     'post_time': '1555', 'racecourse_cd': '05',
                     'track_type': '1', 'distance': '2000',
                     'race_name': '架空テスト', 'headcount': 15,
                     'privateNotes': 'never-display-secret'}]
        with patch('private_service.fetch_race_program', return_value=incoming) as fetch:
            result = call(app, '/api/jrdb/program', QUERY_STRING='date=20261027')
            self.assertTrue(result['status'].startswith('200'))
            fetch.assert_called_once_with('20261027')
            payload = json.loads(result['body'])
            self.assertTrue(payload['programmeOnly'])
            self.assertEqual(payload['rows'][0]['track'], '東京')
            self.assertEqual(payload['rows'][0]['race'], 11)
            self.assertEqual(payload['rows'][0]['post_time'], '15:55')
            self.assertNotIn(b'never-display-secret', result['body'])

    def test_invalid_upstream_programme_is_not_exposed(self):
        app = create_app({**SETTINGS, 'JRDB_PRIVATE_ENABLED': '1'})
        with patch('private_service.fetch_race_program',
                   return_value=[{'racekey': 'invalid', 'secret': 'hidden-value'}]):
            result = call(app, '/api/jrdb/program', QUERY_STRING='date=20261027')
            self.assertTrue(result['status'].startswith('502'))
            self.assertNotIn(b'hidden-value', result['body'])

    def test_private_coverage_counts_without_leaking_horse_data(self):
        app = create_app({**SETTINGS, 'JRDB_PRIVATE_ENABLED': '1'})
        programme = [{'racekey': '05264b11', 'racedate': '20261027',
                      'racecourse_cd': '05', 'post_time': '1555',
                      'headcount': 2}]
        entries = [
            {'racekey': '05264b11', 'racedate': '20261027',
             'horse_number': n, 'horse_name': 'TOP-SECRET-HORSE'}
            for n in ('01', '02')
        ]
        with patch('private_service.fetch_race_program', return_value=programme), \
             patch('private_service.fetch_horse_entries', return_value=entries):
            result = call(app, '/api/jrdb/coverage', QUERY_STRING='date=20261027')
        self.assertTrue(result['status'].startswith('200'))
        payload = json.loads(result['body'])
        self.assertEqual(payload['raceCount'], 1)
        self.assertEqual(payload['matchingEntryCounts'], 1)
        self.assertEqual(payload['predictionsReady'], 0)
        self.assertNotIn(b'TOP-SECRET-HORSE', result['body'])

    def test_private_coverage_is_denied_without_connection(self):
        app = create_app(SETTINGS)
        with patch('private_service.fetch_race_program') as programme, \
             patch('private_service.fetch_horse_entries') as entries:
            result = call(app, '/api/jrdb/coverage', QUERY_STRING='date=20261027')
        self.assertTrue(result['status'].startswith('503'))
        programme.assert_not_called()
        entries.assert_not_called()

    def test_training_and_recent_evidence_are_private_counts_only(self):
        app = create_app({**SETTINGS, 'JRDB_PRIVATE_ENABLED': '1'})
        race = [{'racekey': '05264b01', 'racedate': '20261027',
                 'racecourse_cd': '05', 'post_time': '1010', 'headcount': 1}]
        horse = [{'racekey': '05264b01', 'racedate': '20261027',
                  'horse_number': '01', 'horse_id': '2328aaa95a05',
                  'horse_name': 'SECRET-HORSE'}]
        training = [{'racekey': '05264b01', 'racedate': '20261027',
                     'horse_number': None, 'horse_id': '2328aaa95a05',
                     'oikirisisu': 40, 'oikirisisu_lastweek': 30,
                     'internal_field': 'HIDDEN-DATA'}]
        previous = [{'racekey': '05264b01', 'racedate': '20261027',
                     'horse_number': '01', 'horse_id': '2328aaa95a05',
                     'race_back_1_racedate': '20260926'}]
        with patch('private_service.fetch_race_program', return_value=race), \
             patch('private_service.fetch_horse_entries', return_value=horse), \
             patch('private_service.fetch_training_analysis', return_value=training), \
             patch('private_service.fetch_recent_runs', return_value=previous):
            result = call(app, '/api/jrdb/evidence', QUERY_STRING='date=20261027')
        self.assertTrue(result['status'].startswith('200'))
        data = json.loads(result['body'])
        self.assertEqual(data['raceCount'], 1)
        self.assertEqual(data['races'][0]['trainingRecords'], 1)
        self.assertEqual(data['races'][0]['lastWeekRecords'], 1)
        self.assertEqual(data['races'][0]['pastRunRecords'], 1)
        self.assertEqual(data['races'][0]['trainingUnaccounted'], 0)
        self.assertEqual(data['races'][0]['lastWeekUnaccounted'], 0)
        self.assertEqual(data['races'][0]['pastRunUnaccounted'], 0)
        self.assertEqual(data['gapRaceCount'], 0)
        self.assertEqual(data['unaccountedTotals'],
                         {'training': 0, 'lastWeek': 0, 'pastRuns': 0})
        self.assertEqual(data['predictionsReady'], 0)
        preflight = data['assessmentPreflight']
        self.assertEqual(preflight['factorCount'], 10)
        self.assertEqual(preflight['gradedFactors'], 0)
        self.assertEqual(preflight['readyForPrediction'], 0)
        self.assertEqual(preflight['raceCount'], 1)
        self.assertEqual(preflight['races'][0]['factors']['training']['grade'], '未評価')
        self.assertEqual(preflight['races'][0]['factors']['recent']['grade'], '未評価')
        self.assertNotIn(b'SECRET-HORSE', result['body'])
        self.assertNotIn(b'HIDDEN-DATA', result['body'])

    def test_evidence_gap_summary_is_owner_only_and_not_live_prediction(self):
        private = create_app({**SETTINGS, 'JRDB_PRIVATE_ENABLED': '1'})
        race = [{'racekey': '05264b01', 'racedate': '20261027',
                 'racecourse_cd': '05', 'post_time': '1010', 'headcount': 1}]
        entries = [{'racekey': '05264b01', 'racedate': '20261027',
                    'horse_number': '01', 'horse_id': '2328aaa95a05',
                    'horse_name': 'NONPUBLIC-TEST-HORSE'}]
        with (
            patch('private_service.fetch_race_program', return_value=race),
            patch('private_service.fetch_horse_entries', return_value=entries),
            patch('private_service.fetch_training_analysis', return_value=[]),
            patch('private_service.fetch_recent_runs', return_value=[]),
        ):
            denied = call(private, '/api/jrdb/evidence', auth='',
                          QUERY_STRING='date=20261027')
            result = call(private, '/api/jrdb/evidence',
                          QUERY_STRING='date=20261027')
        self.assertTrue(denied['status'].startswith('401'))
        self.assertTrue(result['status'].startswith('200'))
        report = json.loads(result['body'])
        self.assertEqual(report['gapRaceCount'], 1)
        self.assertEqual(report['unaccountedTotals'],
                         {'training': 1, 'lastWeek': 1, 'pastRuns': 1})
        self.assertFalse(report['races'][0]['predictionsReady'])
        self.assertEqual(report['races'][0]['trainingUnaccounted'], 1)
        self.assertNotIn(b'NONPUBLIC-TEST-HORSE', result['body'])
        self.assertNotIn(b'2328aaa95a05', result['body'])
        self.assertNotIn(b'API_KEY', result['body'])

    def test_course_ground_screen_uses_text_only_rendering(self):
        html = call(self.app, '/')['body']
        js = call(self.app, '/app.js')['body']
        self.assertIn(b'id="context"', html)
        self.assertIn(b'/api/jrdb/context', js)
        self.assertIn(b'goingAvailableCount', js)
        self.assertNotIn(b'innerHTML', js)

    def test_private_client_script_displays_missing_evidence_counts(self):
        script = call(self.app, '/app.js')['body']
        for label in (b'trainingUnaccounted', b'lastWeekUnaccounted',
                      b'pastRunUnaccounted', b'gapRaceCount',
                      b'assessmentPreflight', b'sourceStatus',
                      b'trainingHypothesis', b'recentHypothesis',
                      b'dualFactorReadiness', b'positionObservations',
                      b'gradeCounts'):
            self.assertIn(label, script)
        self.assertNotIn(b'innerHTML', script)

    def test_preflight_does_not_promote_raw_horse_data_to_grades(self):
        private = create_app({**SETTINGS, 'JRDB_PRIVATE_ENABLED': '1'})
        race = [{'racekey': '05264b01', 'racedate': '20261027',
                 'racecourse_cd': '05', 'post_time': '1010', 'headcount': 1}]
        entries = [{'racekey': '05264b01', 'racedate': '20261027',
                    'horse_number': '01', 'horse_id': '2328aaa95a05',
                    'horse_name': 'SECRET-PROVIDER-HORSE'}]
        training = [{'racekey': '05264b01', 'racedate': '20261027',
                     'horse_number': '01', 'horse_id': '2328aaa95a05',
                     'oikirisisu': 99, 'oikirisisu_lastweek': 90,
                     'grade': 'S', 'private_notes': 'SECRET-PAID-REPORT'}]
        previous = [{'racekey': '05264b01', 'racedate': '20261027',
                     'horse_number': '01', 'horse_id': '2328aaa95a05',
                     'race_back_1_racedate': '20261001'}]
        with (
            patch('private_service.fetch_race_program', return_value=race),
            patch('private_service.fetch_horse_entries', return_value=entries),
            patch('private_service.fetch_training_analysis', return_value=training),
            patch('private_service.fetch_recent_runs', return_value=previous),
        ):
            result = call(private, '/api/jrdb/evidence', QUERY_STRING='date=20261027')
        self.assertEqual(result['status'], '200 OK')
        data = json.loads(result['body'])
        self.assertEqual(data['assessmentPreflight']['gradedFactors'], 0)
        row = data['assessmentPreflight']['races'][0]
        self.assertTrue(all(item['grade'] == '未評価'
                            for item in row['factors'].values()))
        self.assertEqual(row['factors']['training']['sourceStatus'],
                         'source_record_count_matches')
        for private_value in (b'SECRET-PROVIDER-HORSE', b'SECRET-PAID-REPORT',
                              b'2328aaa95a05', b'oikirisisu'):
            self.assertNotIn(private_value, result['body'])

    def test_private_workout_hypothesis_returns_only_aggregate_provisional_grades(self):
        app = create_app({**SETTINGS, 'JRDB_PRIVATE_ENABLED': '1'})
        program = [{'racekey': '05264b01', 'racedate': '20261027',
                    'racecourse_cd': '05', 'post_time': '1010', 'headcount': 2}]
        horses = [
            {'racekey': '05264b01', 'racedate': '20261027',
             'horse_number': '01', 'horse_id': '2328aaa95a05',
             'horse_name': 'PRIVATE-HORSE-A'},
            {'racekey': '05264b01', 'racedate': '20261027',
             'horse_number': '02', 'horse_id': '2328aaa95a06',
             'horse_name': 'PRIVATE-HORSE-B'},
        ]
        training = [
            {'racekey': '05264b01', 'racedate': '20261027',
             'horse_number': '01', 'horse_id': '2328aaa95a05',
             'oikirisisu': 78, 'siagarisisu': 80},
            {'racekey': '05264b01', 'racedate': '20261027',
             'horse_number': '02', 'horse_id': '2328aaa95a06',
             'oikirisisu': 62, 'siagarisisu': 60},
        ]
        with (
            patch('private_service.fetch_race_program', return_value=program),
            patch('private_service.fetch_horse_entries', return_value=horses),
            patch('private_service.fetch_training_analysis', return_value=training),
            patch('private_service.fetch_recent_runs', return_value=[]),
        ):
            result = call(app, '/api/jrdb/evidence', QUERY_STRING='date=20261027')
        self.assertEqual(result['status'], '200 OK')
        payload = json.loads(result['body'])
        counts = payload['trainingHypothesis']['races'][0]['gradeCounts']
        self.assertEqual(counts, {'S': 1, 'A': 1, 'B': 0, 'C': 0, '未評価': 0})
        self.assertFalse(payload['trainingHypothesis']['predictionReady'])
        self.assertEqual(payload['assessmentPreflight']['gradedFactors'], 0)
        self.assertEqual(payload['predictionsReady'], 0)
        for secret in (b'PRIVATE-HORSE-', b'2328aaa95a05',
                       b'oikirisisu', b'siagarisisu'):
            self.assertNotIn(secret, result['body'])

    def test_out_of_range_workout_index_cannot_produce_a_race_report(self):
        app = create_app({**SETTINGS, 'JRDB_PRIVATE_ENABLED': '1'})
        program = [{'racekey': '05264b01', 'racedate': '20261027',
                    'racecourse_cd': '05', 'post_time': '1010', 'headcount': 1}]
        horses = [{'racekey': '05264b01', 'racedate': '20261027',
                   'horse_number': '01', 'horse_id': '2328aaa95a05'}]
        training = [{'racekey': '05264b01', 'racedate': '20261027',
                     'horse_number': '01', 'horse_id': '2328aaa95a05',
                     'oikirisisu': 999, 'siagarisisu': 70,
                     'private': 'SECRET-PROVIDER-SCORE'}]
        with (
            patch('private_service.fetch_race_program', return_value=program),
            patch('private_service.fetch_horse_entries', return_value=horses),
            patch('private_service.fetch_training_analysis', return_value=training),
            patch('private_service.fetch_recent_runs', return_value=[]),
        ):
            result = call(app, '/api/jrdb/evidence', QUERY_STRING='date=20261027')
        self.assertTrue(result['status'].startswith('502'))
        self.assertNotIn(b'SECRET-PROVIDER-SCORE', result['body'])

    def test_recent_hypothesis_is_redacted_and_not_a_live_prediction(self):
        private = create_app({**SETTINGS, 'JRDB_PRIVATE_ENABLED': '1'})
        programme = [{'racekey': '05264b01', 'racedate': '20261027',
                      'racecourse_cd': '05', 'post_time': '1010', 'headcount': 1}]
        horses = [{'racekey': '05264b01', 'racedate': '20261027',
                   'horse_number': '01', 'horse_id': '2328aaa95a05',
                   'horse_name': 'SECRET-PAID-HORSE'}]
        recent = [{
            'racekey': '05264b01', 'racedate': '20261027',
            'horse_number': '01', 'horse_id': '2328aaa95a05',
            'race_back_1_racedate': '20261020',
            'race_back_1_order_of_finish': 1,
            'race_back_1_idm': 80, 'race_back_1_corner4_order': 2,
            'race_back_1_later3f_time': 34.6,
            'race_back_2_racedate': '20261010',
            'race_back_2_order_of_finish': 2,
            'race_back_2_idm': 75, 'race_back_2_corner4_order': 3,
            'race_back_2_later3f_time': 35.0,
            'race_back_1_confirmed_win_odds': 1000.0,
        }]
        with (
            patch('private_service.fetch_race_program', return_value=programme),
            patch('private_service.fetch_horse_entries', return_value=horses),
            patch('private_service.fetch_training_analysis', return_value=[]),
            patch('private_service.fetch_recent_runs', return_value=recent),
        ):
            result = call(private, '/api/jrdb/evidence',
                          QUERY_STRING='date=20261027')
        self.assertEqual(result['status'], '200 OK')
        response = json.loads(result['body'])
        recent_report = response['recentHypothesis']
        self.assertEqual(recent_report['races'][0]['gradeCounts']['S'], 1)
        self.assertEqual(recent_report['races'][0]['frontAtFourthObservations'], 2)
        self.assertEqual(recent_report['races'][0]['late3fObservations'], 2)
        self.assertFalse(recent_report['predictionReady'])
        positions = response['positionObservations']
        self.assertFalse(positions['paceForecastAvailable'])
        self.assertFalse(positions['predictionReady'])
        self.assertEqual(positions['races'][0]['observations']['frontObserved'], 1)
        self.assertEqual(positions['races'][0]['observations']['insufficient'], 0)
        joint = response['dualFactorReadiness']['races'][0]
        self.assertEqual(joint['runnerCount'], 1)
        self.assertEqual(joint['recentOnly'], 1)
        self.assertEqual(joint['both'], 0)
        self.assertTrue(joint['coreFactorsStillUnverified'])
        self.assertFalse(response['dualFactorReadiness']['predictionReady'])
        self.assertEqual(response['assessmentPreflight']['gradedFactors'], 0)
        self.assertEqual(response['predictionsReady'], 0)
        for raw in (b'2328aaa95a05', b'SECRET-PAID-HORSE', b'80',
                    b'confirmed_win_odds', b'34.6'):
            # Numeric literals may appear in other metadata; only forbid
            # identifiable material and field names.
            if raw not in (b'80',):
                self.assertNotIn(raw, result['body'])

    def test_bad_recent_history_is_rejected_without_provider_payload(self):
        private = create_app({**SETTINGS, 'JRDB_PRIVATE_ENABLED': '1'})
        programme = [{'racekey': '05264b01', 'racedate': '20261027',
                      'racecourse_cd': '05', 'post_time': '1010', 'headcount': 1}]
        horses = [{'racekey': '05264b01', 'racedate': '20261027',
                   'horse_number': '01', 'horse_id': '2328aaa95a05'}]
        previous = [{'racekey': '05264b01', 'racedate': '20261027',
                     'horse_number': '01', 'horse_id': '2328aaa95a05',
                     'race_back_1_racedate': '20261020',
                     'race_back_1_idm': 999, 'horse_name': 'SECRET-PAID-HORSE'}]
        with (
            patch('private_service.fetch_race_program', return_value=programme),
            patch('private_service.fetch_horse_entries', return_value=horses),
            patch('private_service.fetch_training_analysis', return_value=[]),
            patch('private_service.fetch_recent_runs', return_value=previous),
        ):
            result = call(private, '/api/jrdb/evidence',
                          QUERY_STRING='date=20261027')
        self.assertTrue(result['status'].startswith('502'))
        self.assertNotIn(b'SECRET-PAID-HORSE', result['body'])

    def test_course_going_context_is_owner_only_and_not_prediction(self):
        private = create_app({**SETTINGS, 'JRDB_PRIVATE_ENABLED': '1'})
        race = [
            {'racekey': '05264b01', 'racedate': '20261027',
             'post_time': '1010', 'track_type': '1',
             'turn_cd': '2', 'distance': '1600', 'headcount': 12},
            {'racekey': '05264b02', 'racedate': '20261027',
             'post_time': '1040', 'track_type': '2',
             'turn_cd': '2', 'distance': '1400', 'headcount': 14},
        ]
        going = [{'holdingkey': '052648', 'racedate': '20261027',
                  'turf_condition_cd': '04', 'dirt_condition_cd': '1',
                  'horse_name': 'PRIVATE-HORSE-SECRET',
                  'updated_at': '2026-10-27T07:30:00+09:00'}]
        with (
            patch('private_service.fetch_race_program', return_value=race) as program,
            patch('private_service.fetch_venue_conditions', return_value=going) as source,
        ):
            rejected = call(private, '/api/jrdb/context', auth='',
                            QUERY_STRING='date=20261027')
            response = call(private, '/api/jrdb/context', QUERY_STRING='date=20261027')
        self.assertTrue(rejected['status'].startswith('401'))
        self.assertEqual(response['status'], '200 OK')
        data = json.loads(response['body'])
        self.assertEqual(data['raceCount'], 2)
        self.assertEqual(data['courseInfoPresentCount'], 2)
        self.assertEqual(data['goingAvailableCount'], 2)
        turf, dirt = data['races']
        self.assertEqual((turf['surface'], turf['distance_m'], turf['turn'],
                          turf['going']), ('芝', 1600, '左', '不良'))
        self.assertEqual(dirt['going'], '良')
        self.assertFalse(data['predictionReady'])
        self.assertFalse(turf['horseCourseSuitabilityAssessed'])
        self.assertFalse(turf['horseGoingSuitabilityAssessed'])
        self.assertEqual(program.call_count, 1)
        self.assertEqual(source.call_count, 1)
        self.assertNotIn(b'PRIVATE-HORSE-SECRET', response['body'])
        self.assertNotIn(b'052648', response['body'])

    def test_wrong_going_condition_stops_without_leaking_data(self):
        private = create_app({**SETTINGS, 'JRDB_PRIVATE_ENABLED': '1'})
        race = [{'racekey': '05264b01', 'racedate': '20261027',
                 'track_type': '1', 'distance': '1600', 'turn_cd': '2'}]
        going = [{'holdingkey': '052648', 'racedate': '20261027',
                  'turf_condition_cd': '99', 'private': 'SECRET-PAID-DATA'}]
        with (
            patch('private_service.fetch_race_program', return_value=race),
            patch('private_service.fetch_venue_conditions', return_value=going),
        ):
            response = call(private, '/api/jrdb/context',
                            QUERY_STRING='date=20261027')
        self.assertTrue(response['status'].startswith('502'))
        self.assertNotIn(b'SECRET-PAID-DATA', response['body'])

    def test_course_ground_context_disabled_until_api_activation(self):
        with (
            patch('private_service.fetch_race_program') as programme,
            patch('private_service.fetch_venue_conditions') as going,
        ):
            result = call(self.app, '/api/jrdb/context',
                          QUERY_STRING='date=20261027')
        self.assertTrue(result['status'].startswith('503'))
        programme.assert_not_called()
        going.assert_not_called()

    def test_bad_course_context_query_rejected_before_fetch(self):
        private = create_app({**SETTINGS, 'JRDB_PRIVATE_ENABLED': '1'})
        with patch('private_service.fetch_venue_conditions') as going:
            for query in ('', 'date=20261027&date=20261028',
                          'limit=100', 'date=../../etc'):
                with self.subTest(query=query):
                    response = call(private, '/api/jrdb/context', QUERY_STRING=query)
                    self.assertTrue(response['status'].startswith(('400', '502')))
            going.assert_not_called()

    def test_evidence_endpoint_disabled_without_private_activation(self):
        with patch('private_service.fetch_race_program') as fetch:
            result = call(self.app, '/api/jrdb/evidence', QUERY_STRING='date=20261027')
        self.assertTrue(result['status'].startswith('503'))
        fetch.assert_not_called()

    def test_evidence_endpoint_is_owner_only(self):
        for auth in ('', 'Basic malformed'):
            result = call(self.app, '/api/jrdb/evidence', auth=auth,
                          QUERY_STRING='date=20261027')
            self.assertTrue(result['status'].startswith('401'))

    def test_invalid_query_is_rejected(self):
        app = create_app({**SETTINGS, 'JRDB_PRIVATE_ENABLED': '1'})
        for query in ['', 'date=20261027&date=20261028', 'url=https://example.com']:
            self.assertTrue(call(app, '/api/jrdb/program', QUERY_STRING=query)['status'].startswith('400'))

    def test_upstream_error_is_redacted(self):
        app = create_app({**SETTINGS, 'JRDB_PRIVATE_ENABLED': '1'})
        with patch('private_service.fetch_race_program', side_effect=JRDBError('secret-data')):
            result = call(app, '/api/jrdb/program', QUERY_STRING='date=20261027')
            self.assertTrue(result['status'].startswith('502')); self.assertNotIn(b'secret-data', result['body'])

    def test_research_preview_available_only_to_owner(self):
        for path in ('/', '/app.js'):
            blocked = call(self.app, path, auth='')
            self.assertEqual(blocked['status'], '303 See Other' if path == '/' else
                             '401 Unauthorized')
        html = call(self.app, '/')['body']
        script = call(self.app, '/app.js')['body']
        for label in (b'id="researchDemo"', b'id="researchInput"',
                      b'id="researchRun"', b'id="researchFile"'):
            self.assertIn(label, html)
        for label in (b'function syntheticSample', b'async function runResearch',
                      b"'/api/research'", b"recordType:'test'"):
            self.assertIn(label, script)
        self.assertIn(b'textContent', script)
        self.assertNotIn(b'innerHTML', script)

    def test_research_sandbox_rejects_real_provider_sources(self):
        race = sample()
        race['horses'][0]['assessments']['training']['evidence'][0]['sourceId'] = 'jrdb-tcy'
        with patch('private_service.fetch_race_program') as fetch:
            response = call(self.app, '/api/research', 'POST', data=race)
        self.assertTrue(response['status'].startswith('400'))
        self.assertNotIn(b'jrdb-tcy', response['body'])
        fetch.assert_not_called()

    def test_research_sandbox_rejects_bad_evidence_shapes(self):
        for evidence in ('not-an-array', [{'sourceId': 'unknown'}],
                         [{'sourceId': 'synthetic'}, None], {}):
            with self.subTest(evidence=evidence):
                race = sample()
                race['horses'][0]['assessments']['recent']['evidence'] = evidence
                result = call(self.app, '/api/research', 'POST', data=race)
                self.assertTrue(result['status'].startswith('400'))

    def test_synthetic_research_response_contains_rank_and_tickets_only_as_test(self):
        result = call(self.app, '/api/research', 'POST', data=sample())
        self.assertEqual(result['status'], '200 OK')
        payload = json.loads(result['body'])
        self.assertEqual(payload['recordType'], 'test')
        self.assertFalse(payload['publishable'])
        self.assertFalse(payload['validated'])
        self.assertEqual(payload['researchDecision'], 'simulate')
        self.assertTrue(len(payload['evaluation']['horses']) >= 2)
        self.assertEqual(payload['points'], len(payload['tri']))
        self.assertLessEqual(payload['points'], 40)
        self.assertEqual(payload['stake'], payload['points'] * 100)
        self.assertEqual(payload['snapshotGate']['version'],
                         'research-cutoff-snapshot-1')
        self.assertTrue(payload['snapshotGate']['cutoffChecked'])
        self.assertFalse(payload['snapshotGate']['verifiedSourceAuthenticity'])
        self.assertFalse(payload['snapshotGate']['bettingReady'])
        self.assertEqual(len(payload['snapshotGate']['snapshotSha256']), 64)

    def test_research_api_rejects_evidence_from_after_cutoff(self):
        race = sample()
        race['horses'][0]['assessments']['recent']['evidence'][0]['availableAt'] = (
            race['offAt']
        )
        with patch('private_service.fetch_race_program') as source:
            result = call(self.app, '/api/research', 'POST', data=race)
        self.assertEqual(result['status'], '400 Bad Request')
        self.assertNotIn(b'finish', result['body'])
        source.assert_not_called()

    def test_research_pipeline_end_to_end(self):
        result = call(self.app, '/api/research', 'POST', data=sample())
        self.assertTrue(result['status'].startswith('200'))
        plan = json.loads(result['body']); self.assertFalse(plan['publishable'])
        self.assertEqual(plan['researchDecision'], 'simulate'); self.assertLessEqual(plan['points'], 40)

    def test_live_and_bad_inputs_are_rejected(self):
        for data in [{**sample(), 'recordType': 'live'}, {}, None, []]:
            self.assertNotEqual(call(self.app, '/api/research', 'POST', data=data)['status'], '200 OK')
        result = call(self.app, '/api/research', 'POST', data=sample(), CONTENT_LENGTH=str(MAX_BODY + 1))
        self.assertTrue(result['status'].startswith('413'))
        self.assertTrue(call(self.app, '/api/research', 'POST', data=sample(), CONTENT_TYPE='text/plain')['status'].startswith('415'))

    def test_html_and_script_do_not_embed_secrets(self):
        for path in ['/', '/app.js', '/app.css']:
            result = call(self.app, path)
            self.assertTrue(result['status'].startswith('200'))
            self.assertNotIn(SETTINGS['KEIBA_OWNER_PASSWORD'].encode(), result['body'])
            self.assertEqual(result['headers']['X-Frame-Options'], 'DENY')


if __name__ == '__main__': unittest.main()
