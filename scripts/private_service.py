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

from jrdb_private import (fetch_race_program, fetch_horse_entries,
                          fetch_training_analysis, fetch_recent_runs,
                          fetch_venue_conditions, JRDBError)
from jrdb_evidence_readiness import audit_evidence_coverage
from jrdb_factor_preflight import audit_assessment_preflight
from jrdb_training_hypothesis import build_training_hints, summarize_training_hints
from jrdb_recent_hypothesis import build_recent_hints, summarize_recent_hints
from jrdb_position_observations import summarize_position_observations
from jrdb_dual_factor_readiness import summarize_dual_factor_readiness
from jrdb_coverage import audit_race_coverage, CoverageError
from jrdb_program_preview import normalize_program_rows, ProgrammeFormatError
from jrdb_race_context import audit_race_context, RaceContextError
from research_planner import plan_race

MAX_BODY = 131072
HTML = '''<!doctype html><html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>KEIBA NINE｜本人用接続確認</title><link rel="stylesheet" href="/app.css"></head><body><main><h1>KEIBA NINE</h1><p>本人用・データ接続確認</p><section><h2>JRDB接続</h2><p id="status" role="status">設定を確認中…</p><label for="date">開催日</label><input id="date" type="date"><button id="load" disabled>レース情報を取得</button><button id="context" disabled>コース・距離・馬場を確認</button><button id="coverage" disabled>全場・全Rの取得状況を確認</button><button id="evidence" disabled>調教・近走の資料状況を確認</button><p id="message" role="status"></p><div id="races"></div></section><section><h2>10項目の評価 → 総合ランク → 3連単</h2>
<p class="muted">架空テスト専用の分析画面。実レース・JRDBの有料データ・購入には使用しません。計算は本人専用サーバー内だけで行い、保存や外部送信はしません。</p>
<button id="researchDemo">架空8頭で動作確認</button>
<label for="researchFile">検証用JSONファイル（任意）</label>
<input id="researchFile" type="file" accept=".json,application/json">
<label for="researchInput">検証用の根拠付き10項目JSON</label>
<textarea id="researchInput" spellcheck="false" placeholder="架空データ専用です。実データやAPIキーを貼らないでください。"></textarea>
<button id="researchRun">10項目を分析して3連単を確認</button>
<p id="researchMessage" role="status">未検証。架空8頭の動作確認ボタンから試せます。</p>
<pre id="researchOutput">研究用の検証結果だけを表示します。</pre>
</section><section><h2>接続準備の診断</h2><p class="muted">本人用の設定だけを確認します。JRDBへの通信や会員情報の確認、予想作成は行いません。</p><button id="diagnose">安全な設定診断を実行</button><p id="diagnostic" role="status">診断は未実施です。</p></section><p>この画面は接続確認用です。実データからのランク評価・買い目作成にはまだ接続していません。取得した内容は公開アプリやGoogleシートへ送信しません。</p></main><script src="/app.js" defer></script></body></html>'''
CSS = '''body{margin:0;background:#09172b;color:#edf3fa;font:16px/1.7 system-ui,sans-serif}main{max-width:680px;margin:auto;padding:24px}h1{color:#efc66b}section{background:#172d48;padding:20px;border-radius:18px;margin:12px 0}.muted{font-size:14px;color:#c5d3e5}label{display:block}input,button{box-sizing:border-box;font:inherit;padding:12px;width:100%;margin:8px 0;border-radius:10px;border:1px solid #8b9eb7}button{background:#efc66b;color:#10213b;font-weight:700}button:disabled{opacity:.5}.race{border-bottom:1px solid #415878;padding:12px 0}p{overflow-wrap:anywhere}textarea{box-sizing:border-box;width:100%;min-height:120px;background:#0a2035;color:#edf3fa;border:1px solid #829bbb;border-radius:9px;padding:12px;font:14px/1.5 ui-monospace,monospace}pre{white-space:pre-wrap;overflow-wrap:anywhere;font-size:13px;background:#0a2035;padding:12px;border-radius:9px}'''
JS = ''''use strict';
const el=id=>document.getElementById(id);
async function request(path){const r=await fetch(path,{credentials:'same-origin',cache:'no-store',headers:{'X-Keiba-Request':'private'}});const data=await r.json();if(!r.ok)throw Error(data.error||'取得できませんでした');return data;}
let enabled=false;
request('/api/status').then(s=>{enabled=s.jrdbConfigured;el('status').textContent=enabled?'接続設定あり（実際の接続は取得ボタンで確認）':'JRDBは未設定です。契約と接続設定が必要です。';el('load').disabled=!enabled;el('context').disabled=!enabled;el('coverage').disabled=!enabled;el('evidence').disabled=!enabled;}).catch(e=>el('status').textContent=e.message);
el('diagnose').onclick=async()=>{el('diagnose').disabled=true;el('diagnostic').textContent='設定だけを点検中…';try{const info=await request('/api/setup');const items=['本人認証：有効','通信：'+(info.transport==='https'?'HTTPS':'開発用ループバック'),'JRDBの接続設定：'+(info.jrdbConfigured?'あり（実通信は未検証）':'未設定'),'API利用確認：未実施','実戦予想：未接続','次の段階：'+info.nextStep];el('diagnostic').textContent=items.join('｜');}catch(e){el('diagnostic').textContent=e.message;}finally{el('diagnose').disabled=false;}};
const RESEARCH_FACTORS=['training','recent','course_distance','pace','ground','pedigree','draw_weight','jockey_stable','rotation','body_condition'];
function syntheticSample(){
 const date='2099-01-01';
 return {recordType:'test',raceId:'synthetic-2099-1',track:'架空競馬場',date,race:1,
 asOf:date+'T09:00:00+09:00',offAt:date+'T10:00:00+09:00',
 horses:Array.from({length:8},(_,i)=>{
   const grade=i<2?'S':i<4?'A':'B';
   return {number:i+1,assessments:Object.fromEntries(RESEARCH_FACTORS.map(factor=>[
     factor,{grade,winSupport:i<2&&['training','pace'].includes(factor),
       reason:'架空データを使った計算機能の確認用',
       evidence:[{sourceId:'synthetic',reference:'fake-fixture',
                   availableAt:date+'T08:00:00+09:00'}]}]))};
 })};
}
async function runResearch(){
 const button=el('researchRun');button.disabled=true;el('researchMessage').textContent='研究用データを検査しています…';el('researchOutput').textContent='';
 try{
  const raw=el('researchInput').value;
  if(raw.length>100000)throw Error('検証用JSONは100KB以内にしてください');
  const input=JSON.parse(raw);
  if(input?.recordType!=='test'||!Array.isArray(input.horses)||input.horses.length<2||input.horses.length>18)
   throw Error('架空テスト用の2〜18頭JSONだけに対応しています');
  const response=await fetch('/api/research',{
   method:'POST',credentials:'same-origin',cache:'no-store',
   headers:{'Content-Type':'application/json','X-Keiba-Request':'private'},
   body:JSON.stringify(input)
  });
  const data=await response.json();if(!response.ok)throw Error(data.error||'評価できませんでした');
  if(data.recordType!=='test'||data.publishable!==false||data.validated!==false)
   throw Error('検証用以外の予想結果は表示できません');
  const label={simulate:'参考買い目を計算',hold:'保留',skip:'見送り'}[data.researchDecision]||'要確認';
  el('researchMessage').textContent='架空テスト：'+label+'｜'+data.points+'点／1点100円なら'+data.stake+'円（実際の購入ではありません）';
  const lines=['【総合評価順：架空の評価入力に基づく計算】'];
  for(const h of data.evaluation.horses)
   lines.push((h.rank??'-')+'位  '+h.number+'番  '+h.overall+'  調教：'+h.grades.training+'／近走：'+h.grades.recent+'／コース：'+h.grades.course_distance+'  根拠 '+h.coverage+'%');
  lines.push('','【1着候補】'+(data.first.length?data.first.join('・'):'保留・見送り'),
             '【3連単参考】'+(data.tri.length?data.tri.map(t=>t.join('-')).join('、'):'買い目なし'),
             '','理由：'+data.reason,'※架空の動作確認専用。実戦予想・JRA公式との照合・購入・保存は行っていません。');
  el('researchOutput').textContent=lines.join('\\n');
 }catch(e){el('researchMessage').textContent='検証できません：'+e.message;el('researchOutput').textContent='根拠付きの架空データと日時を確認してください。';}
 finally{button.disabled=false}
}
el('researchDemo').onclick=()=>{el('researchInput').value=JSON.stringify(syntheticSample());runResearch();};
el('researchRun').onclick=runResearch;
el('researchFile').onchange=async()=>{const file=el('researchFile').files?.[0];if(!file)return;try{if(file.size>100000||!/\.json$/i.test(file.name))throw Error('100KB以内の.jsonファイルを選択してください');const contents=await file.text();JSON.parse(contents);el('researchInput').value=contents;el('researchMessage').textContent='読み込みました。まだ検証していません。';}catch(e){el('researchMessage').textContent='読み込み失敗：'+e.message;}finally{el('researchFile').value='';}};

el('date').value=new Date().toLocaleDateString('sv-SE',{timeZone:'Asia/Tokyo'});
el('load').onclick=async()=>{el('load').disabled=true;el('message').textContent='取得中…';el('races').replaceChildren();try{if(!el('date').value)throw Error('開催日を選んでください');const data=await request('/api/jrdb/program?date='+encodeURIComponent(el('date').value.replaceAll('-','')));el('message').textContent=data.rows.length+'レースの番組情報を確認。馬名・近走・調教・買い目はまだ未確認です。';for(const row of data.rows){const div=document.createElement('div');div.className='race';const name=row.race_name||'レース名未確認';const dist=row.distance_m==null?'距離未確認':row.distance_m+'m';div.textContent=row.track+row.race+'R '+name+'｜'+(row.surface||'種別未確認')+dist+'｜発走 '+(row.post_time||'未確認')+'｜予想：未作成';el('races').append(div);}}catch(e){el('message').textContent=e.message;}finally{el('load').disabled=!enabled;}};
el('context').onclick=async()=>{el('context').disabled=true;el('message').textContent='コース・馬場の取得状況を照合中…';el('races').replaceChildren();try{if(!el('date').value)throw Error('開催日を選んでください');const data=await request('/api/jrdb/context?date='+encodeURIComponent(el('date').value.replaceAll('-','')));el('message').textContent=data.raceCount+'Rのうちコース条件取得 '+data.courseInfoPresentCount+'R／馬場状態取得 '+data.goingAvailableCount+'R（馬の適性や予想は未評価）';for(const row of data.races){const div=document.createElement('div');div.className='race';div.textContent=row.track+row.race+'R｜'+(row.surface||'種別未確認')+' '+(row.distance_m==null?'距離未確認':row.distance_m+'m')+' '+(row.turn||'回り未確認')+'｜馬場 '+row.going+'｜更新記録 '+(row.conditionUpdateRecorded?'あり':'未確認')+'｜コース・馬場適性：未評価';el('races').append(div);}}catch(e){el('message').textContent=e.message;}finally{el('context').disabled=!enabled;}};
el('coverage').onclick=async()=>{el('coverage').disabled=true;el('message').textContent='全レースの照合中…';el('races').replaceChildren();try{if(!el('date').value)throw Error('開催日を選んでください');const data=await request('/api/jrdb/coverage?date='+encodeURIComponent(el('date').value.replaceAll('-','')));el('message').textContent=data.raceCount+'Rのうち出走馬件数一致 '+data.matchingEntryCounts+'R。最終確認済み0R、予想作成済み0R（取消・調教など未検証）。';for(const row of data.races){const div=document.createElement('div');div.className='race';div.textContent=row.track+row.race+'R｜発走 '+(row.post_time||'未確認')+'｜登録 '+row.observedEntries+'/'+(row.expectedRunners===null?'?':row.expectedRunners)+'頭｜'+row.status+'｜予想：未作成';el('races').append(div);}}catch(e){el('message').textContent=e.message;}finally{el('coverage').disabled=!enabled;}};
el('evidence').onclick=async()=>{el('evidence').disabled=true;el('message').textContent='資料の件数を確認中…';el('races').replaceChildren();try{if(!el('date').value)throw Error('開催日を選んでください');const data=await request('/api/jrdb/evidence?date='+encodeURIComponent(el('date').value.replaceAll('-','')));const preflight=data.assessmentPreflight;el('message').textContent=data.raceCount+'Rのうち資料不足・未対応 '+data.gapRaceCount+'R。評価済み '+preflight.gradedFactors+'/'+preflight.factorCount+'項目。実戦予想：未接続。';const labels={source_record_count_matches:'資料件数一致（内容は未評価）',partial_source_records:'一部のみ資料あり',unknown_or_not_applicable:'資料なし・対象外の可能性',not_mapped_from_provider:'自動紐付け未実装'};for(const row of data.races){const div=document.createElement('div');div.className='race';const detail=preflight.races.find(a=>a.track===row.track&&a.race===row.race);div.textContent=row.track+row.race+'R｜登録 '+row.observedEntries+'/'+(row.expectedRunners==null?'?':row.expectedRunners)+'頭｜調教未対応 '+row.trainingUnaccounted+'／1週前 '+row.lastWeekUnaccounted+'／近走 '+row.pastRunUnaccounted+'頭｜総合評価：未実施';const candidate=data.trainingHypothesis?.races?.find(a=>a.track===row.track&&a.race===row.race);if(candidate){const p=document.createElement('p');const c=candidate.gradeCounts;p.textContent='調教のみ独自暫定：S '+c.S+'／A '+c.A+'／B '+c.B+'／C '+c.C+'／未評価 '+c['未評価']+'（実戦買い目ではありません）';div.append(p)}const form=data.recentHypothesis?.races?.find(a=>a.track===row.track&&a.race===row.race);if(form){const recent=document.createElement('p');const g=form.gradeCounts;recent.textContent='近走のみ独自暫定：S '+g.S+'／A '+g.A+'／B '+g.B+'／C '+g.C+'／未評価 '+g['未評価']+'｜4角位置 '+form.fourthPositionObservations+'件／上がり3F '+form.late3fObservations+'件（相手関係・着差未評価）';div.append(recent)}const position=data.positionObservations?.races?.find(a=>a.track===row.track&&a.race===row.race);if(position){const p=document.createElement('p');const c=position.observations;p.textContent='過去4角位置：前方観測 '+c.frontObserved+'／後方観測 '+c.backObserved+'／混在 '+c.mixedObserved+'／資料不足 '+c.insufficient+'頭（展開予想ではありません）';div.append(p)}const dual=data.dualFactorReadiness?.races?.find(a=>a.track===row.track&&a.race===row.race);if(dual){const p=document.createElement('p');p.textContent='調教・近走の両方が暫定評価可能：'+dual.both+'/'+dual.runnerCount+'頭｜残り8項目未確認・買い目未作成';div.append(p)}if(detail){const exp=document.createElement('details');const head=document.createElement('summary');head.textContent='10項目の評価準備を見る';exp.append(head);const list=document.createElement('ul');for(const item of Object.values(detail.factors)){const li=document.createElement('li');li.textContent=item.label+'：'+(labels[item.sourceStatus]||'未確認')+'｜ランク未評価';list.append(li)}exp.append(list);div.append(exp)}el('races').append(div);}}catch(e){el('message').textContent=e.message;}finally{el('evidence').disabled=!enabled;}};
'''


def create_app(settings=None):
    settings = dict(os.environ if settings is None else settings)
    password = settings.get('KEIBA_OWNER_PASSWORD', '')
    username = settings.get('KEIBA_OWNER_USERNAME', 'owner')
    if not isinstance(password, str) or len(password) < 32 or len(set(password)) < 12:
        raise ValueError('Configure a generated owner password of at least 32 characters')
    if not isinstance(username, str) or not username or ':' in username:
        raise ValueError('Invalid owner username')
    # A dev-only HTTP exception must never run with real JRDB access enabled.
    # Codespaces synthetic previews intentionally use this exception but disable JRDB.
    if settings.get("KEIBA_ALLOW_LOCAL_HTTP") == "1" and settings.get("JRDB_PRIVATE_ENABLED") == "1":
        raise ValueError("Private JRDB integration requires HTTPS-only service mode")
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
        if method == 'GET' and path == '/api/setup':
            # Strictly coarse, owner-only flags. This endpoint never pings JRDB,
            # discloses credentials, claims entitlement, or authorizes predictions.
            configured = settings.get('JRDB_PRIVATE_ENABLED') == '1' and all(
                isinstance(settings.get(k), str) and bool(settings.get(k).strip())
                for k in ('JRDB_API_KEY', 'JRDB_AUTH_KEY')) and settings.get('GITHUB_ACTIONS') != 'true'
            return response('200 OK', {
                'transport': 'https' if secure else 'local-dev',
                'jrdbConfigured': configured,
                'liveConnectionVerified': False,
                'realPredictionEnabled': False,
                'nextStep': ('本人専用のHTTPS環境でJRDB実接続を検証する' if configured
                             else 'β版の専用API認証情報と本人専用HTTPS環境を準備する'),
            })
        if method == 'GET' and path == '/api/jrdb/program':
            if settings.get('JRDB_PRIVATE_ENABLED') != '1' or settings.get('GITHUB_ACTIONS') == 'true':
                return response('503 Service Unavailable', {'error': 'JRDB接続はまだ有効になっていません。'})
            query = parse_qs(environ.get('QUERY_STRING', ''), keep_blank_values=True)
            if set(query) != {'date'} or len(query['date']) != 1:
                return response('400 Bad Request', {'error': '開催日を1つ指定してください。'})
            try:
                rows = fetch_race_program(query['date'][0])
                preview = normalize_program_rows(rows, query['date'][0])
            except (JRDBError, ProgrammeFormatError):
                return response('502 Bad Gateway', {'error': 'JRDB番組データを安全に確認できませんでした。API接続・開催日・応答形式を確認してください。'})
            return response('200 OK', {'rows': preview, 'programmeOnly': True})
        if method == 'GET' and path == '/api/jrdb/context':
            if settings.get('JRDB_PRIVATE_ENABLED') != '1' or settings.get('GITHUB_ACTIONS') == 'true':
                return response('503 Service Unavailable', {'error': 'JRDB接続はまだ有効になっていません。'})
            query = parse_qs(environ.get('QUERY_STRING', ''), keep_blank_values=True)
            if set(query) != {'date'} or len(query['date']) != 1:
                return response('400 Bad Request', {'error': '開催日を1つ指定してください。'})
            try:
                date = query['date'][0]
                programme = normalize_program_rows(fetch_race_program(date), date)
                conditions = fetch_venue_conditions(date)
                audit = audit_race_context(programme, conditions, date)
            except (JRDBError, ProgrammeFormatError, RaceContextError):
                return response('502 Bad Gateway', {
                    'error': 'コース・馬場の照合に失敗しました。開催日・応答形式を確認してください。'})
            return response('200 OK', audit)
        if method == 'GET' and path == '/api/jrdb/coverage':
            if settings.get('JRDB_PRIVATE_ENABLED') != '1' or settings.get('GITHUB_ACTIONS') == 'true':
                return response('503 Service Unavailable', {'error': 'JRDB接続はまだ有効になっていません。'})
            query = parse_qs(environ.get('QUERY_STRING', ''), keep_blank_values=True)
            if set(query) != {'date'} or len(query['date']) != 1:
                return response('400 Bad Request', {'error': '開催日を1つ指定してください。'})
            try:
                date = query['date'][0]
                programme = normalize_program_rows(fetch_race_program(date), date)
                entries = fetch_horse_entries(date)
                coverage = audit_race_coverage(programme, entries, date)
            except (JRDBError, ProgrammeFormatError, CoverageError):
                return response('502 Bad Gateway', {'error': '全レースの照合ができませんでした。API接続・開催日・データ形式を確認してください。'})
            return response('200 OK', coverage)
        if method == 'GET' and path == '/api/jrdb/evidence':
            if settings.get('JRDB_PRIVATE_ENABLED') != '1' or settings.get('GITHUB_ACTIONS') == 'true':
                return response('503 Service Unavailable', {'error': 'JRDB接続はまだ有効になっていません。'})
            query = parse_qs(environ.get('QUERY_STRING', ''), keep_blank_values=True)
            if set(query) != {'date'} or len(query['date']) != 1:
                return response('400 Bad Request', {'error': '開催日を1つ指定してください。'})
            try:
                date = query['date'][0]
                programme = normalize_program_rows(fetch_race_program(date), date)
                entries = fetch_horse_entries(date)
                training = fetch_training_analysis(date)
                previous = fetch_recent_runs(date)
                coverage = audit_evidence_coverage(programme, entries, training, previous, date)
                coverage['assessmentPreflight'] = audit_assessment_preflight(coverage)
                training_hints = build_training_hints(programme, entries, training, date)
                recent_hints = build_recent_hints(programme, entries, previous, date)
                coverage['trainingHypothesis'] = summarize_training_hints(training_hints)
                coverage['recentHypothesis'] = summarize_recent_hints(recent_hints)
                coverage['positionObservations'] = summarize_position_observations(recent_hints)
                coverage['dualFactorReadiness'] = summarize_dual_factor_readiness(
                    training_hints, recent_hints)
            except (JRDBError, ProgrammeFormatError, CoverageError, ValueError):
                return response('502 Bad Gateway', {'error': '資料件数や評価準備の照合ができませんでした。接続や応答形式を確認してください。'})
            return response('200 OK', coverage)
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
                # This sandbox must not accept JRDB or real provider records
                # disguised with the ordinary "test" flag.
                if not isinstance(race, dict) or race.get('recordType') != 'test':
                    raise ValueError()
                for horse in race.get('horses', []):
                    if not isinstance(horse, dict):
                        raise ValueError()
                    assessments = horse.get('assessments') or {}
                    if not isinstance(assessments, dict):
                        raise ValueError()
                    for assessment in assessments.values():
                        if not isinstance(assessment, dict):
                            raise ValueError()
                        sources = assessment.get('evidence', [])
                        if not isinstance(sources, list):
                            raise ValueError()
                        for evidence in sources:
                            if not isinstance(evidence, dict) or evidence.get('sourceId') != 'synthetic':
                                raise ValueError()
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
