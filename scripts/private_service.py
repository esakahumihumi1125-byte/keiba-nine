"""Owner-authenticated WSGI connection console. Deploy behind verified HTTPS only.

Never serves repository files, writes data, or calls paid AI. Live JRDB requests
remain opt-in. The local runner binds loopback only and is not a public server.
"""
import base64
import hashlib
import hmac
import json
import os
from urllib.parse import parse_qs

from jrdb_private import fetch_race_program, JRDBError
from research_planner import plan_race

MAX_BODY = 131072
HTML = '''<!doctype html><html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>KEIBA NINE｜本人用接続確認</title><link rel="stylesheet" href="/app.css"></head><body><main><h1>KEIBA NINE</h1><p>本人用・データ接続確認</p><section><h2>JRDB接続</h2><p id="status" role="status">設定を確認中…</p><label for="date">開催日</label><input id="date" type="date"><button id="load" disabled>レース情報を取得</button><p id="message" role="status"></p><div id="races"></div></section><p>この画面は接続確認用です。実データからのランク評価・買い目作成にはまだ接続していません。取得した内容は公開アプリやGoogleシートへ送信しません。</p></main><script src="/app.js" defer></script></body></html>'''
CSS = '''body{margin:0;background:#09172b;color:#edf3fa;font:16px/1.7 system-ui,sans-serif}main{max-width:680px;margin:auto;padding:24px}h1{color:#efc66b}section{background:#172d48;padding:20px;border-radius:18px}label{display:block}input,button{box-sizing:border-box;font:inherit;padding:12px;width:100%;margin:8px 0;border-radius:10px;border:1px solid #8b9eb7}button{background:#efc66b;color:#10213b;font-weight:700}button:disabled{opacity:.5}.race{border-bottom:1px solid #415878;padding:12px 0}p{overflow-wrap:anywhere}'''
JS = ''''use strict';
const el=id=>document.getElementById(id);
async function request(path){const r=await fetch(path,{credentials:'same-origin',cache:'no-store',headers:{'X-Keiba-Request':'private'}});const data=await r.json();if(!r.ok)throw Error(data.error||'取得できませんでした');return data;}
let enabled=false;
request('/api/status').then(s=>{enabled=s.jrdbConfigured;el('status').textContent=enabled?'接続設定あり（実際の接続は取得ボタンで確認）':'JRDBは未設定です。契約と接続設定が必要です。';el('load').disabled=!enabled;}).catch(e=>el('status').textContent=e.message);
el('date').value=new Date().toLocaleDateString('sv-SE',{timeZone:'Asia/Tokyo'});
el('load').onclick=async()=>{el('load').disabled=true;el('message').textContent='取得中…';el('races').replaceChildren();try{if(!el('date').value)throw Error('開催日を選んでください');const data=await request('/api/jrdb/program?date='+encodeURIComponent(el('date').value.replaceAll('-','')));el('message').textContent=data.rows.length+'件取得しました。まだ予想の評価は行っていません。';for(const row of data.rows){const div=document.createElement('div');div.className='race';div.textContent=String(row.racekey||'レース番号未取得')+' / 発走 '+String(row.post_time||'未取得');el('races').append(div);}}catch(e){el('message').textContent=e.message;}finally{el('load').disabled=!enabled;}};
'''


def create_app(settings=None):
    settings = dict(os.environ if settings is None else settings)
    password = settings.get('KEIBA_OWNER_PASSWORD', '')
    username = settings.get('KEIBA_OWNER_USERNAME', 'owner')
    if not isinstance(password, str) or len(password) < 32 or len(set(password)) < 12:
        raise ValueError('Configure a generated owner password of at least 32 characters')
    if not isinstance(username, str) or not username or ':' in username:
        raise ValueError('Invalid owner username')
    expected = hashlib.sha256((username + ':' + password).encode()).digest()

    def app(environ, start_response):
        def response(code, data, content_type='application/json; charset=utf-8', extra=()):
            raw = json.dumps(data, ensure_ascii=False).encode() if content_type.startswith('application/json') else data.encode()
            headers = [('Content-Type', content_type), ('Content-Length', str(len(raw))),
                       ('Cache-Control', 'no-store, private'), ('Pragma', 'no-cache'),
                       ('X-Content-Type-Options', 'nosniff'), ('X-Frame-Options', 'DENY'),
                       ('Referrer-Policy', 'no-referrer'),
                       ('Content-Security-Policy', "default-src 'none'; script-src 'self'; style-src 'self'; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'")]
            if environ.get('wsgi.url_scheme') == 'https':
                headers.append(('Strict-Transport-Security', 'max-age=31536000'))
            start_response(code, headers + list(extra))
            return [raw]

        secure = environ.get('wsgi.url_scheme') == 'https'
        local = settings.get('KEIBA_ALLOW_LOCAL_HTTP') == '1' and environ.get('REMOTE_ADDR') in ('127.0.0.1', '::1')
        if not secure and not local:
            return response('426 Upgrade Required', {'error': 'HTTPS接続が必要です。'})
        auth = environ.get('HTTP_AUTHORIZATION', '')
        try:
            scheme, value = auth.split(' ', 1)
            if scheme.lower() != 'basic' or len(value) > 2048:
                raise ValueError()
            credentials = base64.b64decode(value, validate=True)
            valid = hmac.compare_digest(hashlib.sha256(credentials).digest(), expected)
        except (ValueError, TypeError):
            valid = False
        if not valid:
            return response('401 Unauthorized', {'error': '本人認証が必要です。'}, extra=[('WWW-Authenticate', 'Basic realm="KEIBA NINE private", charset="UTF-8"')])
        path, method = environ.get('PATH_INFO', '/'), environ.get('REQUEST_METHOD', 'GET')
        if path.startswith('/api/'):
            # Custom header stops cross-origin form submissions; no CORS is granted.
            if environ.get('HTTP_X_KEIBA_REQUEST') != 'private' or environ.get('HTTP_SEC_FETCH_SITE') == 'cross-site':
                return response('403 Forbidden', {'error': '本人用画面から操作してください。'})
        if method == 'GET' and path in ('/', '/app.js', '/app.css'):
            text, mime = {'/': (HTML, 'text/html; charset=utf-8'), '/app.js': (JS, 'text/javascript; charset=utf-8'), '/app.css': (CSS, 'text/css; charset=utf-8')}[path]
            return response('200 OK', text, mime)
        if method == 'GET' and path == '/api/status':
            ready = settings.get('JRDB_PRIVATE_ENABLED') == '1' and all(settings.get(k) for k in ('JRDB_API_KEY', 'JRDB_AUTH_KEY')) and settings.get('GITHUB_ACTIONS') != 'true'
            return response('200 OK', {'jrdbConfigured': ready, 'livePredictionEnabled': False})
        if method == 'GET' and path == '/api/jrdb/program':
            if settings.get('JRDB_PRIVATE_ENABLED') != '1' or settings.get('GITHUB_ACTIONS') == 'true':
                return response('503 Service Unavailable', {'error': 'JRDB接続はまだ有効になっていません。'})
            query = parse_qs(environ.get('QUERY_STRING', ''), keep_blank_values=True)
            if set(query) != {'date'} or len(query['date']) != 1:
                return response('400 Bad Request', {'error': '開催日を1つ指定してください。'})
            try:
                rows = fetch_race_program(query['date'][0])
            except JRDBError:
                return response('502 Bad Gateway', {'error': 'JRDBから取得できませんでした。契約・接続設定・開催日を確認してください。'})
            return response('200 OK', {'rows': rows})
        if method == 'POST' and path == '/api/research':
            if environ.get('CONTENT_TYPE', '').split(';')[0].strip().lower() != 'application/json':
                return response('415 Unsupported Media Type', {'error': 'JSON形式が必要です。'})
            try:
                length = int(environ.get('CONTENT_LENGTH', '0'))
            except ValueError:
                length = -1
            if length <= 0 or length > MAX_BODY:
                return response('413 Content Too Large', {'error': '入力サイズが範囲外です。'})
            try:
                raw = environ['wsgi.input'].read(length)
                if len(raw) != length:
                    raise ValueError()
                race = json.loads(raw)
                plan = plan_race(race)
            except (ValueError, TypeError, KeyError):
                return response('400 Bad Request', {'error': '架空検証用の入力形式・根拠・時刻を確認してください。'})
            return response('200 OK', plan)
        return response('404 Not Found', {'error': '対象がありません。'})

    return app


if __name__ == '__main__':
    from wsgiref.simple_server import make_server, WSGIRequestHandler

    class QuietHandler(WSGIRequestHandler):
        def log_message(self, format, *args):
            pass

    # Local development only. A production HTTPS WSGI host is not configured here.
    with make_server('127.0.0.1', 8765, create_app(), handler_class=QuietHandler) as server:
        server.serve_forever()
