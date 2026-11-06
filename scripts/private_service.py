"""Owner-authenticated WSGI connection console. Deploy behind verified HTTPS only.

Never serves repository files, writes data, or calls paid AI. Live JRDB requests
remain opt-in. The local runner binds loopback only and is not a public server.
"""
import base64
import hashlib
import hmac
import json
import os
import re
from datetime import datetime
from zoneinfo import ZoneInfo
from urllib.parse import parse_qs
from owner_session_auth import (owner_credentials_match, session_cookie, session_cookie_valid,
                                new_login_form_csrf, login_form_csrf_valid)

from jrdb_private import (fetch_race_program, fetch_horse_entries,
                          fetch_training_analysis, fetch_recent_runs,
                          fetch_venue_conditions, fetch_prestart_body, fetch_historical_race_program,
                          fetch_historical_venue_conditions, JRDBError)
from jrdb_evidence_readiness import audit_evidence_coverage, _valid_date
from jrdb_day_pipeline import inspect_day
from jrdb_day_review_gate import build_day_review_queue
from jrdb_day_factor_progress import summarize_day_factor_progress
from jrdb_day_materials_progress import summarize_day_materials
from jrdb_prestart_body import audit_prestart_body
from jrdb_day_pipeline_ui import HTML as DAY_PIPELINE_HTML, JS as DAY_PIPELINE_JS, CSS as DAY_PIPELINE_CSS
from jrdb_selected_race_readiness import selected_race_readiness
from jrdb_history_pipeline import run_bounded_history_audit, HistoryFetchError
from jrdb_factor_preflight import audit_assessment_preflight
from jrdb_training_hypothesis import build_training_hints, summarize_training_hints
from jrdb_recent_hypothesis import build_recent_hints, summarize_recent_hints
from jrdb_position_observations import summarize_position_observations
from jrdb_dual_factor_readiness import summarize_dual_factor_readiness
from jrdb_coverage import audit_race_coverage, CoverageError
from jrdb_program_preview import normalize_program_rows, ProgrammeFormatError
from jrdb_race_context import audit_race_context, RaceContextError
from jrdb_race_day_gates import audit_race_day_checks
from jrdb_prestart_freshness import audit_prestart_freshness, FreshnessError
from jra_reference_compare import (compare_independent_race_snapshot,
                                   validate_single_manual_reference, ReferenceCompareError)
from research_planner import plan_race
from owner_revision_diagnostic import inspect_owner_revision
from research_batch_demo import build_demo_batch, render_batch_html, CSS as BATCH_DEMO_CSS
from research_validation_demo import build_validation_review, render_validation_html
from operator_factor_intake import validate_operator_factor_note
from manual_ticket_book import HTML as TICKET_HTML, JS as TICKET_JS, CSS as TICKET_CSS
from jrdb_mail_local_import import HTML as MAIL_HTML, JS as MAIL_JS, CSS as MAIL_CSS
from jrdb_final_numbers_manual import HTML as NUMBERS_HTML, JS as NUMBERS_JS, CSS as NUMBERS_CSS
from jra_official_pdf_ui import HTML as JRA_PDF_HTML, JS as JRA_PDF_JS, CSS as JRA_PDF_CSS
from jra_web_card_workflow import HTML as WEB_CARD_HTML, JS as WEB_CARD_JS, CSS as WEB_CARD_CSS
from jra_official_pdf_discovery import discover_official_pdf_links, JRAIndexError
from owner_ticket_handoff import JS as TICKET_HANDOFF_JS
from manual_purchase_book import HTML as PURCHASE_HTML, JS as PURCHASE_JS, CSS as PURCHASE_CSS
from owner_backup import HTML as BACKUP_HTML, JS as BACKUP_JS, CSS as BACKUP_CSS
from owner_factor_scorecard import HTML as SCORE_HTML, JS as SCORE_JS, CSS as SCORE_CSS
from owner_race_workbench import HTML as WORKBENCH_HTML, JS as WORKBENCH_JS, CSS as WORKBENCH_CSS
from owner_result_review import HTML as REVIEW_HTML, JS as REVIEW_JS, CSS as REVIEW_CSS
from jrdb_one_race_trial import build_one_race_trial
from jrdb_day_trial import build_day_trial
from owner_one_race_trial_ui import HTML as AUTO_HTML, JS as AUTO_JS, CSS as AUTO_CSS

def _now_in_jst():
    """Server-side time only; browser timestamps cannot claim freshness."""
    return datetime.now(ZoneInfo('Asia/Tokyo')).isoformat(timespec='seconds')


UI_VERSION = 'iphone-login-recovery-20261105-v9'
MAX_BODY = 131072
LOGIN_HTML = '''<!doctype html><html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>競馬ナイン｜本人ログイン</title><meta name="theme-color" content="#09172b"><meta name="apple-mobile-web-app-capable" content="yes"><meta name="apple-mobile-web-app-status-bar-style" content="default"><meta name="apple-mobile-web-app-title" content="競馬ナイン本人用"><link rel="stylesheet" href="/login.css"></head><body><main><h1>KEIBA NINE</h1><p class="subtitle">本人用プレビューへのログイン</p><p class="notice">予想デモは架空データ用です。実戦予想・馬券購入は未接続。</p><form action="/login" method="post"><label for="loginUser">ユーザー名</label><input id="loginUser" name="username" autocomplete="username" value="owner" maxlength="128" required><label for="loginPassword">パスワード</label><input id="loginPassword" name="password" type="password" autocomplete="current-password" required><input type="hidden" name="login_csrf" value="__CSRF__"><button type="submit">ログイン</button></form><p id="loginError" class="error">__ERROR__</p><p class="help">ログイン後に同じ画面へ戻る場合は、ChatGPT内のブラウザーではなくSafariでこのURLを直接開いてください。アプリのパスワードはRenderのEnvironmentに設定した値です。</p><p class="help">Renderのサービス <strong>keiba-nine-owner-preview</strong> の Environment にある <code>KEIBA_OWNER_PASSWORD</code> を使います。RenderやGitHubのログインパスワードとは別です。</p><p class="help">正しくログインできると、このiPhoneでは最長7日間ログイン状態を保持します。パスワードを変更すると再ログインが必要です。</p><p class="help">パスワードはこのチャットやGitHubに貼らないでください。</p></main></body></html>'''
LOGIN_CSS = '''body{margin:0;background:#09172b;color:#edf3fa;font:16px/1.65 system-ui,sans-serif}main{max-width:440px;padding:28px 22px;margin:36px auto}h1{color:#edca70;margin:0;font-size:32px}.subtitle{color:#d6e1f0;margin:0 0 24px}.notice,.help{color:#d0deee;font-size:14px}.notice{background:#142e48;border-radius:10px;padding:12px}form{background:#172d48;border:1px solid #405e7b;border-radius:16px;padding:20px}label{display:block;font-weight:700;margin:14px 0 5px}input,button{box-sizing:border-box;width:100%;padding:13px;border-radius:10px;font:inherit}input{background:#f8fbff;color:#10213b;border:1px solid #8b9eb7}button{margin-top:23px;background:#edca70;border:0;color:#12243a;font-weight:800;min-height:50px}.error{color:#ffbec4;font-weight:700}.error:empty{display:none}code{overflow-wrap:anywhere}'''
HTML = '''<!doctype html><html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>KEIBA NINE｜本人用接続確認</title><meta name="keiba-owner-release" content="__OWNER_RELEASE__"><meta name="theme-color" content="#09172b"><meta name="apple-mobile-web-app-capable" content="yes"><meta name="apple-mobile-web-app-status-bar-style" content="default"><meta name="apple-mobile-web-app-title" content="競馬ナイン本人用"><link rel="stylesheet" href="/app.css?theme=owner-mobile-nav-20261104"></head><body><main><h1>KEIBA NINE</h1><p class="top-lead">競馬ナイン｜本人用プレビュー</p><div class="preview-mode"><strong>本人用：手動の3連単下書きが使えます</strong><span>実馬のAI予想・馬券購入は未接続</span></div><section class="owner-quick-start" aria-label="本人用の実戦メニュー"><h2>本人用の実戦メニュー</h2><p class="muted">実レースのAI自動予想は未接続。まずは3連単の下書きと購入記録を本人の端末で管理できます。</p><a class="owner-main-action" href="/owner-auto-trial">全場・全RをJRDB資料からまとめて自動試算（2項目・研究用）</a><a class="owner-main-action" href="/owner-races">全開催36Rの準備状況・レース選択</a><a class="owner-main-action" href="/my-tickets">3連単・全R下書き・購入記録を開く</a><a class="owner-sub-action" href="/owner-review">1・2・3着別の取りこぼしを振り返る</a><a class="owner-sub-action" href="/my-scorecard">5項目の手入力評価・総合S/A/B/C（手動）</a><a class="owner-sub-action" href="/jrdb-mail-local">JRDB想定メールと馬番メモを確認</a><a class="owner-sub-action" href="/owner-backup">端末内の5種類の記録をまとめてバックアップ</a><p class="muted">ホーム画面から開いた場合、Safariとデータが別になることがあります。重要な記録はJSONでバックアップしてください。</p></section><section class="owner-release-panel"><h2>最新版の配信確認</h2><p class="muted">GitHubの最新版と、現在Renderで稼働しているコードを照合します。自動更新・デプロイは実行しません。</p><button id="deployCheck" type="button">配信中の版を照合</button><p id="deployResult" class="muted" role="status">必要なときだけ確認できます。買い目やJRDBデータは送信しません。</p><a href="/ui-version" target="_blank" rel="noopener noreferrer">配信中の版IDを見る</a></section><nav class="jump-nav" aria-label="実戦で使うメニュー"><a href="/owner-auto-trial">JRDBから1R自動試算</a><a href="/owner-races">全開催36R一覧</a><a href="/my-tickets">3連単・購入記録</a><a href="/owner-review">着順別の予想振り返り</a><a href="/my-scorecard">5項目の手動評価</a><a href="/jrdb-mail-local">JRDB資料・馬番メモ</a><a href="/owner-backup">バックアップ・復元</a><a href="#ownerTools">接続・設定</a></nav><details class="developer-menu"><summary>開発用テスト・詳細画面を開く（架空データ）</summary><nav class="jump-nav" aria-label="開発用の詳細メニュー"><a href="/research-batch-demo">全36R一括テスト（架空）</a><a href="/research-validation-demo">1着候補の振り返り（架空）</a><a href="/day-pipeline">全R資料の一括準備（API待ち）</a><a href="#researchPanel">予想デモ</a><a href="#jrdbSection">レース選択</a><a href="#operatorFactorPanel">資料チェック</a></nav></details><p class="muted" id="uiVersion">画面版：iphone-login-recovery-20261105-v9</p><details class="developer-panel"><summary>架空の予想デモを表示（開発確認用）</summary><section id="researchPanel" class="research-panel"><p class="research-kicker">KEIBA NINE • OWNER TEST</p><h2>総合評価と3連単</h2>
<p class="research-intro">見やすい予想画面の動作確認。<strong>架空8頭のテスト専用</strong>です。実レース・JRDB有料データ・購入には使えません。</p>
<button id="researchDemo" class="primary-run">架空8頭で予想画面を確認</button>
<p id="researchMessage" role="status">未検証。上のボタンで架空8頭の画面を表示できます。</p>
<div id="researchSummary" class="research-summary" role="region" aria-label="架空の評価結果"><p class="muted">動作確認後、総合評価順・各着順候補・点数・金額がここに表示されます。</p></div>
<details id="researchDetails" class="research-expand"><summary>全買い目・評価の詳細を見る</summary><pre id="researchOutput">架空8頭を実行すると詳細が表示されます。</pre></details>
<details id="researchAdvanced" class="research-expand"><summary>開発者向け：検証用JSONの入力・読み込み</summary>
<p class="muted">架空データの研究用。実データやAPIキーを貼らないでください。</p>
<label for="researchFile">検証用JSONファイル（任意）</label>
<input id="researchFile" type="file" accept=".json,application/json">
<label for="researchInput">検証用の根拠付き10項目JSON</label>
<textarea id="researchInput" spellcheck="false" placeholder="架空データ専用です。実データやAPIキーを貼らないでください。"></textarea>
<button id="researchRun">入力した架空データで分析する</button></details>
<p class="muted research-disclaimer">画面・データは研究用。保存・公開・外部送信・馬券購入は行いません。将来の本番予想とは完全に分離しています。</p>
</section></details><section id="jrdbSection"><h2>JRDB接続</h2><p class="muted">開催日からレース選択（実レースはJRDB接続後に利用可能）</p><p id="status" role="status">設定を確認中…</p><label for="date">開催日</label><input id="date" type="date"><button id="load" disabled>開催日の出走表を取得</button><div id="programmePicker" class="programme-picker"><p class="muted">実データ接続前でも、架空レースで競馬場・レースの選択操作を試せます。実際の出走馬・予想・買い目は表示しません。</p><button id="programmeDemo" type="button">架空レースで選択操作を試す</button><p id="programmeDemoNotice" class="muted" role="status">架空テストは実在しない2099年の日付を使用します。</p><label for="programmeTrack">競馬場</label><select id="programmeTrack" disabled><option value="">出走表を取得してください</option></select><label for="programmeRace">レース</label><select id="programmeRace" disabled><option value="">競馬場を選択してください</option></select><p id="programmeSelected" class="muted" role="status">未選択・実戦予想は未接続</p><button id="programmeReadiness" type="button" disabled>選んだ1Rの資料をまとめて確認</button><p id="programmeReadinessResult" class="muted" role="status">出走表とレースを選ぶと、調教・近走・出走取消・馬場の確認状況をまとめて表示します。実データ未接続の間は利用できません。</p></div><button id="context" disabled>コース・距離・馬場を確認</button><button id="raceday" disabled>出走取消・当日馬場・発走前の情報を確認</button><p class="muted">JRA公式の変更・出馬表・馬場は<a href="https://www.jra.go.jp/keiba/" target="_blank" rel="noopener noreferrer">JRA公式競馬メニュー</a>で別途確認（自動照合は未接続）。</p><button id="coverage" disabled>全場・全Rの取得状況を確認</button><button id="evidence" disabled>調教・近走の資料状況を確認</button><button id="history" disabled>過去の重・不良馬場を照合（最大8レース）</button><p class="muted">本人が実行した時だけ過去APIを最大16回照会します。実データ接続前は無効です。</p><p id="message" role="status"></p><div id="races"></div></section><section id="operatorFactorPanel"><h2>本人用・評価資料の入力チェック</h2><p class="muted">上の「開催日」を選び、馬番と資料項目を選択。JRDB契約前でも利用できます。記録があるかの自己申告を形式確認するだけで、能力評価やJRA公式照合は行いません。画面を閉じると入力件数は消えます。</p><label for="noteTrack">競馬場</label><select id="noteTrack"><option value="">競馬場を選ぶ</option><option value="札幌">札幌</option><option value="函館">函館</option><option value="福島">福島</option><option value="新潟">新潟</option><option value="東京">東京</option><option value="中山">中山</option><option value="中京">中京</option><option value="京都">京都</option><option value="阪神">阪神</option><option value="小倉">小倉</option></select><label for="noteRace">レース</label><select id="noteRace"><option value="1">1R</option><option value="2">2R</option><option value="3">3R</option><option value="4">4R</option><option value="5">5R</option><option value="6">6R</option><option value="7">7R</option><option value="8">8R</option><option value="9">9R</option><option value="10">10R</option><option value="11">11R</option><option value="12">12R</option></select><label for="noteHorse">馬番</label><select id="noteHorse"><option value="01">1番</option><option value="02">2番</option><option value="03">3番</option><option value="04">4番</option><option value="05">5番</option><option value="06">6番</option><option value="07">7番</option><option value="08">8番</option><option value="09">9番</option><option value="10">10番</option><option value="11">11番</option><option value="12">12番</option><option value="13">13番</option><option value="14">14番</option><option value="15">15番</option><option value="16">16番</option><option value="17">17番</option><option value="18">18番</option></select><label for="noteFactor">確認する項目</label><select id="noteFactor"><option value="training">調教</option><option value="recent">近走</option><option value="course_distance">コース・距離</option><option value="pace">展開・脚質</option><option value="ground">馬場</option><option value="pedigree">血統</option><option value="draw_weight">枠・斤量</option><option value="jockey_stable">騎手・厩舎</option><option value="rotation">ローテ</option><option value="body_condition">馬体・状態</option></select><label for="noteState">資料の状態</label><select id="noteState"><option value="unknown">未確認</option><option value="noted">自分で資料を見た</option></select><label for="noteSource">資料の種類</label><select id="noteSource"><option value="none">未選択</option><option value="jra_page_viewed_by_operator">JRAページを自分で確認</option><option value="operator_observation">自分自身の観察</option></select><button id="noteRun" type="button">この1項目を入力チェック</button><p id="noteResult" class="muted" role="status">未実行。本人用画面の中だけで数え、保存・公開・予想生成はしません。</p><p class="muted">馬名・指数・有料資料の原文やパスワードは入力しないでください。ここでの「見た」は正式な資料検証ではありません。</p></section><section id="ownerManualSection"><h2>JRA画面を見ながら1レースを手入力照合</h2><p class="muted">本人専用。上の開催日を選んで、JRA公式サイトで確認した項目だけ入力します。入力はこの照合で一度だけ使用し、保存しません。データの出所を自動認証できないため、差分ゼロでも「公式確認済み」にはなりません。</p><label for="manualTrack">競馬場</label><select id="manualTrack"><option value="">競馬場を選ぶ</option><option value="札幌">札幌</option><option value="函館">函館</option><option value="福島">福島</option><option value="新潟">新潟</option><option value="東京">東京</option><option value="中山">中山</option><option value="中京">中京</option><option value="京都">京都</option><option value="阪神">阪神</option><option value="小倉">小倉</option></select><label for="manualRace">レース</label><select id="manualRace"><option value="1">1R</option><option value="2">2R</option><option value="3">3R</option><option value="4">4R</option><option value="5">5R</option><option value="6">6R</option><option value="7">7R</option><option value="8">8R</option><option value="9">9R</option><option value="10">10R</option><option value="11">11R</option><option value="12">12R</option></select><label for="manualTime">JRAサイトで見た発走時刻（任意、HH:MM）</label><input id="manualTime" type="text" maxlength="5" inputmode="numeric" placeholder="例 10:05"><label for="manualSurface">芝・ダート（任意）</label><select id="manualSurface"><option value="">未入力</option><option>芝</option><option>ダート</option><option>障害</option></select><label for="manualGoing">馬場状態（任意）</label><select id="manualGoing"><option value="">未入力</option><option>良</option><option>稍重</option><option>重</option><option>不良</option></select><label for="manualHorse">取消を確認した馬番（任意・1頭ずつ）</label><select id="manualHorse"><option value="">対象馬なし</option><option value="01">1番</option><option value="02">2番</option><option value="03">3番</option><option value="04">4番</option><option value="05">5番</option><option value="06">6番</option><option value="07">7番</option><option value="08">8番</option><option value="09">9番</option><option value="10">10番</option><option value="11">11番</option><option value="12">12番</option><option value="13">13番</option><option value="14">14番</option><option value="15">15番</option><option value="16">16番</option><option value="17">17番</option><option value="18">18番</option></select><label for="manualStatus">その馬の状態</label><select id="manualStatus"><option value="unknown">未確認</option><option value="active">出走予定</option><option value="withdrawn">取消</option></select><button id="manualCompare" disabled>入力内容とJRDB資料を1回比較</button><p id="manualMessage" role="status">未実行。本人専用HTTPSとJRDB接続の設定が必要です。</p><div id="manualResults"></div><p class="muted">比較対象は最大1レース。JRA公式からの自動取得ではありません。再実行するとその時点の資料を取り直し、前回の差分件数と比較します（画面を閉じれば前回値は消えます）。</p></section><section id="ownerTools"><h2>接続準備の診断</h2><p class="muted">本人用の設定だけを確認します。JRDBへの通信や会員情報の確認、予想作成は行いません。</p><button id="diagnose">安全な設定診断を実行</button><p id="diagnostic" role="status">診断は未実施です。</p></section><p>この画面は接続確認用です。実データからのランク評価・買い目作成にはまだ接続していません。取得した内容は公開アプリやGoogleシートへ送信しません。</p></main><script src="/app.js?v=owner-mobile-navigation-20261104" defer></script><script src="/owner-update.js" defer></script></body></html>'''
CSS = '''body{margin:0;background:#09172b;color:#edf3fa;font:16px/1.7 system-ui,sans-serif}main{max-width:680px;margin:auto;padding:24px}h1{color:#efc66b}section{background:#172d48;padding:20px;border-radius:18px;margin:12px 0}.muted{font-size:14px;color:#c5d3e5}label{display:block}input,button,select{box-sizing:border-box;font:inherit;padding:12px;width:100%;margin:8px 0;border-radius:10px;border:1px solid #8b9eb7}button{background:#efc66b;color:#10213b;font-weight:700}button:disabled{opacity:.5}.race{border-bottom:1px solid #415878;padding:12px 0}p{overflow-wrap:anywhere}textarea{box-sizing:border-box;width:100%;min-height:120px;background:#0a2035;color:#edf3fa;border:1px solid #829bbb;border-radius:9px;padding:12px;font:14px/1.5 ui-monospace,monospace}pre{white-space:pre-wrap;overflow-wrap:anywhere;font-size:13px;background:#0a2035;padding:12px;border-radius:9px}
.top-lead{color:#b9cee4;font-size:14px;margin:0 0 10px}
.preview-mode{background:#0e2339;border:1px solid #7e6d42;border-radius:12px;padding:12px 14px;margin:8px 0 12px;display:flex;flex-direction:column;gap:3px}
.preview-mode strong{font-size:14px;color:#efc66b}
.preview-mode span{font-size:12px;color:#c8d7e7}
.owner-release-panel{padding:14px;background:#112b41;border:1px solid #486984;border-radius:14px;margin:12px 0}.owner-release-panel h2{font-size:19px;margin:0}.owner-release-panel button{width:100%;min-height:47px;margin:8px 0;background:#edca70;color:#12253b}.owner-release-panel a{color:#f2cd76;font-size:13px}.owner-release-panel p{font-size:13px;line-height:1.6;margin:6px 0}.owner-quick-start{background:#122d44;border:1px solid #806e42;padding:16px;margin:12px 0;border-radius:14px}.owner-quick-start h2{font-size:20px;margin:0 0 5px;color:#edca70}.owner-quick-start .muted{font-size:13px}.owner-quick-start a{display:block;margin:9px 0;padding:12px;border-radius:10px;text-align:center;text-decoration:none;font-weight:800;font-size:15px}.owner-main-action{background:#edca70;color:#10213b}.owner-sub-action{background:#2c4c67;color:#f8e9b0;border:1px solid #657d94}.owner-update-notice{position:sticky;top:0;z-index:30;margin:0 auto;max-width:680px;background:#2e291a;border:2px solid #dcbf73;color:#fff0b8;padding:12px;border-radius:0 0 12px 12px;font-size:14px}.owner-update-notice p{margin:0 0 5px}.owner-update-notice button{display:inline-block;width:auto;min-height:44px;background:#edca70;color:#17253a;font-size:14px;font-weight:800;border:0;border-radius:8px;padding:9px 16px}.developer-menu{margin:12px 0;padding:12px;border:1px solid #52697f;border-radius:12px;background:#172b3f}.developer-menu summary{cursor:pointer;color:#d5e2ed;font-size:14px;font-weight:700}.developer-menu nav{margin:12px 0 0}.developer-panel{border:1px solid #46617a;border-radius:12px;padding:12px;margin:12px 0}.developer-panel>summary{font-size:15px;font-weight:750;color:#d4e3f2;cursor:pointer}.jump-nav{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:8px;margin:12px 0 18px}
.jump-nav a{display:block;text-decoration:none;color:#f1f6fb;background:#183550;border:1px solid #52718e;border-radius:11px;padding:12px 6px;text-align:center;font-size:14px;font-weight:800;line-height:1.5}
.jump-nav a:first-child{grid-column:1/-1;background:#edca70;color:#10213b;border-color:#e1b95f}.jump-nav a:focus-visible{outline:3px solid #efc66b;outline-offset:2px}
#researchPanel,#jrdbSection,#operatorFactorPanel,#ownerManualSection,#ownerTools{scroll-margin-top:16px}
.research-panel{background:linear-gradient(170deg,#1b3552,#10263f 72%);border:1px solid #4c6b8d}
.research-panel h2{font-size:26px;line-height:1.25;margin:8px 0 12px}
.research-kicker{font-size:11px;letter-spacing:.13em;font-weight:800;color:#f3d18a;margin:0}
.research-intro{color:#dbe6f4;font-size:14px;line-height:1.6;margin:0 0 15px}
.research-intro strong{color:#f6d07d}
.primary-run{background:#edc86f;min-height:55px;font-size:17px;letter-spacing:.02em}
.research-summary{margin:15px 0}
.research-summary:empty{display:none}
.preview-race-head{padding:15px 14px;border:1px solid #587490;border-radius:12px;margin-bottom:13px;background:#0e2339}
.preview-kicker{font-weight:800;font-size:11px;letter-spacing:.1em;color:#f4d17a}
.preview-race-name{font-size:19px;font-weight:800;line-height:1.4;margin-top:5px}
.preview-race-meta{font-size:12px;color:#c5d3e5;margin-top:5px}
.research-card{background:#112b46;border:1px solid #45637f;border-radius:13px;padding:14px;margin-top:12px}
.research-card h3{font-size:17px;margin:0 0 11px;line-height:1.35;color:#f1f6ff}
.stake-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:9px}
.stake-cell{background:#0b2035;border:1px solid #47637c;border-radius:10px;padding:11px 9px}
.stake-label{font-size:12px;color:#c3d0df}
.stake-value{font-size:25px;line-height:1.35;font-weight:800;font-variant-numeric:tabular-nums}
.horse-row{display:flex;gap:10px;align-items:center;padding:10px 0;border-bottom:1px solid #354d66}
.horse-row:last-child{border-bottom:0}
.horse-rank{font-size:13px;color:#cad7e6;flex:0 0 31px;text-align:center}
.horse-number{font-size:23px;font-weight:800;flex:0 0 50px;text-align:center}
.grade-tag{font-size:14px;font-weight:900;border-radius:7px;padding:4px 10px;min-width:27px;text-align:center;color:white}
.grade-s{background:#D4AF37;color:#0B2343;border:1px solid #E6C75A}.grade-a{background:#c6374c}.grade-b{background:#385cbd}.grade-c{background:#5a6270}.grade-unknown{background:#59677b}
.horse-meta{font-size:11px;color:#c5d3e5;line-height:1.5;min-width:0;overflow-wrap:anywhere;flex:1}
.formation-columns{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:6px}
.formation-col{min-width:0;background:#0a2034;border:1px solid #45627c;padding:9px 6px;border-radius:10px;text-align:center}
.formation-title{font-size:12px;color:#cad8e8}
.formation-numbers{font-size:18px;font-weight:800;line-height:1.7;overflow-wrap:anywhere;margin-top:5px}
.research-note{font-size:12px;color:#ccdaeb;margin-top:10px;line-height:1.6}
.research-expand{border:1px solid #506e8b;border-radius:10px;margin-top:12px;padding:11px 13px;background:#10253c}
.research-expand summary{font-size:14px;font-weight:750;cursor:pointer;min-height:27px}
.research-expand pre{margin:10px 0 0;max-height:360px;overflow:auto;white-space:pre-wrap;font-size:12px;line-height:1.6}
.research-expand textarea{margin-top:7px}
.research-disclaimer{margin:14px 0 0}
.programme-picker{background:#0c2239;border:1px solid #496784;border-radius:13px;margin:12px 0;padding:13px}
.programme-picker label{font-weight:700;font-size:14px;margin:8px 0 2px}
.programme-picker select{background:#f4f7fc;color:#11263e;min-height:47px}
#programmeSelected{margin:10px 0 0;font-size:13px;line-height:1.7}
#programmeReadiness{margin-top:12px}
#programmeReadinessResult{white-space:pre-line;font-size:13px;line-height:1.7}

@media(max-width:380px){.research-card{padding:11px}.horse-row{gap:7px}.horse-number{flex-basis:40px}.grade-tag{padding:4px 7px}.formation-numbers{font-size:16px}.stake-value{font-size:22px}}
'''
JS = ''''use strict';
const el=id=>document.getElementById(id);
async function request(path){const r=await fetch(path,{credentials:'same-origin',cache:'no-store',headers:{'X-Keiba-Request':'private'}});const data=await r.json();if(!r.ok)throw Error(data.error||'取得できませんでした');return data;}
el('deployCheck').onclick=async()=>{
 const button=el('deployCheck'),out=el('deployResult');
 button.disabled=true;out.textContent='GitHub mainとRenderの版を照合中…';
 try{
  const data=await request('/api/deploy-status');
  const status=data.status==='current'?'最新版を配信中':data.status==='behind'?'Renderが古い版を配信中':'照合できません';
  out.textContent=status+'｜Render '+data.renderCommit+'／GitHub '+data.githubMainCommit+'。'+data.note;
 }catch(_){out.textContent='配信状態を取得できません。ログインと通信状況を確認してな。'}
 finally{button.disabled=false}
};
let enabled=false,historyEnabled=false,manualEnabled=false;
request('/api/status').then(s=>{enabled=s.jrdbConfigured===true;historyEnabled=enabled&&s.historyConfigured===true;manualEnabled=enabled&&s.manualComparisonConfigured===true;el('status').textContent=enabled?'接続設定あり（実際の接続は取得ボタンで確認）':'JRDBは未設定です。契約と接続設定が必要です。';el('load').disabled=!enabled;el('context').disabled=!enabled;el('raceday').disabled=!enabled;el('manualCompare').disabled=!manualEnabled;el('coverage').disabled=!enabled;el('evidence').disabled=!enabled;el('history').disabled=!historyEnabled;}).catch(e=>el('status').textContent=e.message);
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
const RESEARCH_AXIS_JP={training:'調教',recent:'近走',course_distance:'コース',pace:'展開',ground:'馬場',pedigree:'血統',draw_weight:'枠斤量',jockey_stable:'騎手厩舎',rotation:'ローテ',body_condition:'馬体'};
function researchNode(tag,cls,value){
 const node=document.createElement(tag);node.className=cls||'';
 if(value!==undefined)node.textContent=String(value);
 return node;
}
function researchSection(label){
 const card=researchNode('div','research-card');
 card.append(researchNode('h3','',label));return card;
}
function renderResearchSummary(data,input){
 // Keep all untrusted strings in textContent; do not interpret as HTML.
 const host=el('researchSummary');host.replaceChildren();
 const rows=data.evaluation?.horses;
 if(!Array.isArray(rows)||!Array.isArray(data.tri)
    ||!Number.isInteger(data.points)||data.points<0||data.points>40
    ||data.points!==data.tri.length
    ||!Number.isInteger(data.stake)||data.stake!==data.points*100
    ||!data.tri.every(t=>Array.isArray(t)&&t.length===3
       &&t.every(x=>Number.isInteger(x)&&x>0&&x<=18)
       &&new Set(t).size===3))
  throw Error('架空テストの買い目データが不正です');
 const unique=new Set(data.tri.map(t=>t.join('-')));
 if(unique.size!==data.tri.length)throw Error('買い目が重複しています');
 const head=researchNode('div','preview-race-head');
 head.append(researchNode('div','preview-kicker','架空テスト • 実際のレースではありません'));
 head.append(researchNode('div','preview-race-name','架空8頭｜分析結果'));
 head.append(researchNode('div','preview-race-meta','総合評価は架空の根拠入力から計算・データ保存なし'));
 host.append(head);
 const stats=researchSection('3連単参考買い目');
 const statgrid=researchNode('div','stake-grid');
 for(const item of [['買い目',data.points+'点'],['1点100円の場合',data.stake.toLocaleString('ja-JP')+'円']]){
  const cell=researchNode('div','stake-cell');
  cell.append(researchNode('div','stake-label',item[0]));
  cell.append(researchNode('div','stake-value',item[1]));statgrid.append(cell);
 }
 stats.append(statgrid);
 const label={simulate:'参考買い目を生成',hold:'保留',skip:'見送り'}[data.researchDecision]||'判定要確認';
 stats.append(researchNode('p','research-note',label+'（実際の購入・投票はできません）'));
 host.append(stats);
 const rankings=researchSection('総合評価順');
 for(const h of rows){
  if(!h||!Number.isInteger(h.number)||h.number<1||h.number>18)
   throw Error('馬番の形式が不正です');
  const row=researchNode('div','horse-row');
  row.append(researchNode('span','horse-rank',(h.rank??'-')+'位'));
  row.append(researchNode('span','horse-number',h.number+'番'));
  const grade=['S','A','B','C'].includes(h.overall)?h.overall:'—';
  row.append(researchNode('span','grade-tag grade-'+(grade==='—'?'unknown':grade.toLowerCase()),grade));
  const grades=h.grades||{};
  const labels=['training','recent','course_distance'].map(k=>RESEARCH_AXIS_JP[k]+' '+(grades[k]||'—'));
  row.append(researchNode('span','horse-meta',labels.join(' / ')+' ｜ 根拠 '+(h.coverage??'—')+'%'));
  rankings.append(row);
 }
 host.append(rankings);
 const formation=researchSection('各着順の候補');
 const opts=[0,1,2].map(k=>[...new Set(data.tri.map(t=>t[k]))].sort((a,b)=>a-b));
 const cols=researchNode('div','formation-columns');
 for(let i=0;i<3;i++){
  const col=researchNode('div','formation-col');
  col.append(researchNode('div','formation-title',(i+1)+'着'));
  col.append(researchNode('div','formation-numbers',opts[i].length?opts[i].map(x=>x+'番').join(' ') : '—'));
  cols.append(col);
 }
 formation.append(cols);
 formation.append(researchNode('p','research-note','着順ごとの候補です。全組み合わせが買い目とは限りません。実際に生成した全'+data.points+'点は「全買い目・評価の詳細」を確認してください。'));
 host.append(formation);
}
async function runResearch(){
 const button=el('researchRun');button.disabled=true;el('researchMessage').textContent='研究用データを検査しています…';el('researchOutput').textContent='';el('researchSummary').replaceChildren();
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
  renderResearchSummary(data,input);
  const label={simulate:'参考買い目を計算',hold:'保留',skip:'見送り'}[data.researchDecision]||'要確認';
  el('researchMessage').textContent='架空テスト成功：'+label+'｜'+data.points+'点・'+data.stake.toLocaleString('ja-JP')+'円（実レース・購入には使えません）';
  const snapshot=data.snapshotGate;
  if(snapshot&&(snapshot.version!=='research-cutoff-snapshot-1'
     ||snapshot.cutoffChecked!==true||snapshot.futureEvidenceRejected!==true
     ||snapshot.predictionReady!==false||snapshot.bettingReady!==false
     ||snapshot.verifiedSourceAuthenticity!==false
     ||snapshot.immutableExternalRecord!==false
     ||!/^[0-9a-f]{64}$/.test(snapshot.snapshotSha256)))
    throw Error('予想前の資料時刻検査の状態が不正です');
  const lines=['【総合評価順：架空の評価入力に基づく計算】'];
  for(const h of data.evaluation.horses)
   lines.push((h.rank??'-')+'位  '+h.number+'番  '+h.overall+'  調教：'+h.grades.training+'／近走：'+h.grades.recent+'／コース：'+h.grades.course_distance+'  根拠 '+h.coverage+'%');
  if(snapshot)lines.push('','【資料時刻検査：架空テスト】','予想時刻以前の根拠のみ・入力の指紋 '+snapshot.snapshotSha256.slice(0,12)+'…','※時刻は自己申告で、実際の記録時刻や提供元の真正性を証明しません');
  lines.push('','【1着候補】'+(data.first.length?data.first.join('・'):'保留・見送り'),
             '【3連単参考】'+(data.tri.length?data.tri.map(t=>t.join('-')).join('、'):'買い目なし'),
             '','理由：'+data.reason,'※架空の動作確認専用。実戦予想・JRA公式との照合・購入・保存は行っていません。');
  el('researchOutput').textContent=lines.join('\\n');
 }catch(e){el('researchSummary').replaceChildren();el('researchMessage').textContent='検証できません：'+e.message;el('researchOutput').textContent='根拠付きの架空データと日時を確認してください。';}
 finally{button.disabled=false}
}
el('researchDemo').onclick=()=>{el('researchInput').value=JSON.stringify(syntheticSample());runResearch();};
el('researchRun').onclick=runResearch;
el('researchFile').onchange=async()=>{const file=el('researchFile').files?.[0];if(!file)return;try{if(file.size>100000||!/\.json$/i.test(file.name))throw Error('100KB以内の.jsonファイルを選択してください');const contents=await file.text();JSON.parse(contents);el('researchInput').value=contents;el('researchMessage').textContent='読み込みました。まだ検証していません。';}catch(e){el('researchMessage').textContent='読み込み失敗：'+e.message;}finally{el('researchFile').value='';}};

const VALID_RACE_TRACKS=['札幌','函館','福島','新潟','東京','中山','中京','京都','阪神','小倉'];
let selectedProgramme=[],loadedProgrammeDate='',programmeDemoActive=false;
let readinessSerial=0;
function chosenProgramme(){
 const day=el('date').value.replaceAll('-',''),track=el('programmeTrack').value;
 const n=Number(el('programmeRace').value);
 return loadedProgrammeDate===day&&track&&n>=1&&n<=12
  ?selectedProgramme.find(x=>x.track===track&&x.race===n):null;
}
function updateReadinessAction(){
 el('programmeReadiness').disabled=!enabled||programmeDemoActive||!chosenProgramme();
}
function clearReadiness(){
 readinessSerial++;
 el('programmeReadinessResult').textContent='未確認：選んだレースの資料をまとめて確認できます。実戦予想は未接続です。';
 updateReadinessAction();
}
function makeOption(value,label){const o=document.createElement('option');o.value=String(value);o.textContent=String(label);return o;}
function resetProgramme(){
 selectedProgramme=[];loadedProgrammeDate='';programmeDemoActive=false;
 el('programmeDemoNotice').textContent='架空テストは実在しない2099年の日付を使用します。';
 el('programmeTrack').disabled=true;el('programmeTrack').replaceChildren(makeOption('','出走表を取得してください'));el('programmeTrack').value='';
 el('programmeRace').disabled=true;el('programmeRace').replaceChildren(makeOption('','競馬場を選択してください'));el('programmeRace').value='';
 el('programmeSelected').textContent='未選択・実戦予想は未接続';
 clearReadiness();
}
function showProgrammeSelection(){
 const track=el('programmeTrack').value;
 const race=Number(el('programmeRace').value);
 const currentDay=el('date').value.replaceAll('-','');
 const found=loadedProgrammeDate===currentDay&&selectedProgramme.find(x=>x.track===track&&x.race===race);
 el('races').replaceChildren();
 clearReadiness();
 if(!found){
  el('programmeSelected').textContent='開催日・競馬場・レースを選んでください。実戦予想は未接続';
  return;
 }
 const name=found.race_name||'レース名未確認',distance=found.distance_m==null?'距離未確認':found.distance_m+'m';
 const info=(programmeDemoActive?'【架空テスト】':'【番組のみ・実出走未確認】')+track+race+'R｜'+name+'｜'+(found.surface||'種別未確認')+' '+distance
  +'｜発走予定 '+(found.post_time||'未確認')
  +'｜頭数 '+(found.headcount==null?'未確認':found.headcount+'頭');
 el('programmeSelected').textContent=info+'｜出走取消・近走・調教・JRA公式の最終確認は未実施';
 const div=document.createElement('div');div.className='race';
 div.textContent=info+'｜総合評価：未作成／3連単：未作成（実戦データ連携前）';
 el('races').append(div);
 updateReadinessAction();
}
function selectProgrammeTrack(){
 const track=el('programmeTrack').value;
 const races=selectedProgramme.filter(x=>x.track===track).sort((a,b)=>a.race-b.race);
 const dropdown=el('programmeRace');
 dropdown.replaceChildren(makeOption('','レースを選択'));
 for(const race of races)dropdown.append(makeOption(race.race,race.race+'R'+(race.post_time?'　'+race.post_time:'')));
 dropdown.disabled=!races.length;
 dropdown.value='';
 showProgrammeSelection();
}
function loadProgrammePicker(rows,day){
 if(!Array.isArray(rows)||rows.length>120||rows.some(x=>!x
   ||!VALID_RACE_TRACKS.includes(x.track)||!Number.isInteger(x.race)
   ||x.race<1||x.race>12||x.racedate!==day
   ||x.programmeOnly!==true||x.horsesVerified!==false))
  throw Error('番組データが正しく照合できませんでした');
 const seen=new Set();
 for(const x of rows){
  const k=x.track+'|'+x.race;
  if(seen.has(k))throw Error('重複したレース情報が含まれています');
  seen.add(k);
 }
 selectedProgramme=rows;loadedProgrammeDate=day;
 const tracks=VALID_RACE_TRACKS.filter(t=>rows.some(x=>x.track===t));
 const dropdown=el('programmeTrack');
 dropdown.replaceChildren(makeOption('','競馬場を選択'));
 for(const track of tracks)dropdown.append(makeOption(track,track+(programmeDemoActive?'（架空）':'')));
 dropdown.value='';dropdown.disabled=!tracks.length;
 el('programmeSelected').textContent=tracks.length?'競馬場を選択してください。予想・馬券は未接続':'この開催日に取得できたレースはありません';
 clearReadiness();
}
function loadOfflineProgrammeDemo(){
 resetProgramme();
 const day='20990101';
 const rows=[
  {racedate:day,track:'東京',race:1,race_name:'架空の東京1R',post_time:'10:05',
   surface:'芝',distance_m:1600,headcount:8,programmeOnly:true,horsesVerified:false},
  {racedate:day,track:'東京',race:2,race_name:'架空の東京2R',post_time:'10:35',
   surface:'ダート',distance_m:1400,headcount:9,programmeOnly:true,horsesVerified:false},
  {racedate:day,track:'京都',race:1,race_name:'架空の京都1R',post_time:'10:00',
   surface:'芝',distance_m:1200,headcount:10,programmeOnly:true,horsesVerified:false}
 ];
 el('date').value='2099-01-01';
 // Only local, invented values. No request, recording, real horse name or betting signal.
 programmeDemoActive=true;
 loadProgrammePicker(rows,day);
 el('programmeDemoNotice').textContent='【架空テスト中】2099年1月1日（実在しない開催日）・実レースではありません。';
 el('programmeSelected').textContent='【架空テスト中】競馬場とレースを選択してください。実戦予想には使用できません。';
 el('message').textContent='架空3Rを画面内で用意しました。競馬場→レースの順に選んでください。JRDBへの通信はありません。';
 el('races').replaceChildren();
}
function safeReadinessCount(n,max){
 if(!Number.isInteger(n)||n<0||n>max)throw Error('資料件数が正しくありません');
 return n;
}
function showSingleRaceReadiness(data,selected,day){
 if(!data||data.version!=='selected-race-readiness-5'
    ||data.date!==day||data.track!==selected.track||data.race!==selected.race
    ||data.sourceSnapshotNotOfficial!==true||data.independentJraConnected!==false
    ||data.officialJraFinalVerification!==false||data.predictionReady!==false
    ||data.bettingReady!==false||data.gradedFactors!==0)
  throw Error('資料が未確認のままかを安全に確認できません');
 const n=safeReadinessCount(data.observedEntries,18);
 const train=safeReadinessCount(data.trainingUnaccounted,n),
       last=safeReadinessCount(data.lastWeekUnaccounted,n),
       past=safeReadinessCount(data.pastRunUnaccounted,n);
 const withdrawn=safeReadinessCount(data.providerWithdrawnCount,n),
       unknown=safeReadinessCount(data.withdrawalFlagUnknownCount,n);
 const research=data.factorResearch;
 if(!research||research.experimental!==true||research.predictionReady!==false
    ||research.remainingFactors!==8)
  throw Error('調教・近走の仮評価に未確認情報があります');
 const pair=['bothGraded','trainingOnly','recentOnly','neither',
             'sameGrade','trainingHigher','recentHigher',
             'largeDisagreement','bothHigh'].map(k=>safeReadinessCount(research[k],n));
 const [both,trainingOnly,recentOnly,neither,same,trainHigh,recentHigh,large,bothHigh]=pair;
 if(both+trainingOnly+recentOnly+neither!==n
    ||same+trainHigh+recentHigh!==both||large>both||bothHigh>both)
  throw Error('調教・近走の暫定評価が一致しません');
 const materials=data.factorMaterials;
 if(!materials||materials.observedFactors!==3
    ||materials.verifiedFactorCount!==0||materials.unmappedFactors!==7
    ||materials.paceForecastAvailable!==false
    ||materials.overallRankReady!==false||materials.predictionReady!==false
    ||materials.trainingProvisional!==both+trainingOnly
    ||materials.recentProvisional!==both+recentOnly)
  throw Error('10項目の資料の確認状態が不正です');
 const fourth=materials.pastFourthCorner;
 if(!fourth||Object.keys(fourth).length!==4
    ||!['frontObserved','backObserved','mixedObserved','insufficient']
        .every(k=>Object.prototype.hasOwnProperty.call(fourth,k)))
  throw Error('4角位置の資料の内容が不正です');
 const [front,back,mixed,insufficient]=['frontObserved','backObserved',
  'mixedObserved','insufficient'].map(k=>safeReadinessCount(fourth[k],n));
 if(front+back+mixed+insufficient!==n)
  throw Error('4角位置の資料件数が一致しません');
 const entry=data.entryMaterials;
 if(!entry||entry.observedFactorSlots!==6||entry.unmappedFactors!==4
    ||entry.verifiedFactorCount!==0||entry.predictionReady!==false
    ||entry.overallRankReady!==false
    ||entry.pedigreeAptitudeAssessed!==false
    ||entry.drawWeightEffectAssessed!==false
    ||entry.rotationEffectAssessed!==false)
  throw Error('血統・枠・斤量・ローテの資料状態が不正です');
 const ec=entry.entryObservations,ri=entry.rotationIntervals;
 if(!ec||!ri
    ||Object.keys(ec).length!==6||Object.keys(ri).length!==4
    ||!['sireRecorded','maternalSireRecorded','bothPedigreeRecorded',
         'bracketRecorded','weightRecorded','drawAndWeightRecorded']
        .every(k=>Object.prototype.hasOwnProperty.call(ec,k))
    ||!['under14Days','days14to55','days56plus','unknown']
        .every(k=>Object.prototype.hasOwnProperty.call(ri,k)))
  throw Error('血統・枠・斤量・ローテの件数情報が不足しています');
 const [sire,maternal,bothParent,bracket,weight,bothDraw]=[
  'sireRecorded','maternalSireRecorded','bothPedigreeRecorded',
  'bracketRecorded','weightRecorded','drawAndWeightRecorded'
 ].map(k=>safeReadinessCount(ec[k],n));
 const [under14,days14to55,days56plus,intervalUnknown]=[
  'under14Days','days14to55','days56plus','unknown'
 ].map(k=>safeReadinessCount(ri[k],n));
 if(bothParent>Math.min(sire,maternal)||bothDraw>Math.min(bracket,weight)
    ||under14+days14to55+days56plus+intervalUnknown!==n)
  throw Error('血統・枠・斤量・ローテの資料件数が一致しません');
 const personnel=data.personnelBodyMaterials;
 if(!personnel||personnel.observedFactorSlots!==8
    ||personnel.unmappedFactors!==2||personnel.verifiedFactorCount!==0
    ||personnel.jockeyTrainerPerformanceAssessed!==false
    ||personnel.bodyConditionAssessed!==false
    ||personnel.raceDayBodyWeightFetched!==false
    ||personnel.overallRankReady!==false
    ||personnel.predictionReady!==false)
   throw Error('騎手・厩舎・馬体資料の確認状態が不正です');
 const pr=personnel.recorded,pk=[
   'jockeyNameRecorded','jockeyCodeRecorded','trainerNameRecorded',
   'trainerCodeRecorded','bothPersonnelNamesRecorded','bodyTypeRecorded',
   'integrationCodeRecorded','anyConformationRecorded'
 ];
 if(!pr||Object.keys(pr).length!==pk.length
    ||!pk.every(k=>Object.prototype.hasOwnProperty.call(pr,k)))
   throw Error('騎手・厩舎・馬体資料の件数情報が不足しています');
 const [jockeyName,jockeyCode,trainerName,trainerCode,bothPeople,
    bodyType,bodyCode,anyBody]=pk.map(k=>safeReadinessCount(pr[k],n));
 if(bothPeople>Math.min(jockeyName,trainerName)
    ||anyBody<Math.max(bodyType,bodyCode)
    ||anyBody>bodyType+bodyCode)
   throw Error('騎手・厩舎・馬体資料の件数が一致しません');
 if(withdrawn+unknown>n||typeof data.entryCountMatchesSource!=='boolean'
    ||!['良','稍重','重','不良','未確認'].includes(data.sourceGoing)
    ||!['post_time_unknown','other_date','post_time_passed',
         'within_two_hours','more_than_two_hours'].includes(data.prestartWindow))
  throw Error('資料照合結果が不正です');
 const source=data.entryCountMatchesSource?'頭数のみ一致（取消未確定）':'頭数に差異・未確認';
 const timing={
  post_time_unknown:'発走予定未確認',other_date:'別日',
  post_time_passed:'発走予定時刻経過',within_two_hours:'発走2時間以内',
  more_than_two_hours:'発走まで2時間超'
 }[data.prestartWindow];
 return '【実戦予想はまだ作成できません】'+selected.track+selected.race+'R'
  +'\\n出走馬の資料 '+n+'頭｜'+source
  +'\\n調教不足・未対応 '+train+'頭／1週前 '+last+'頭／近走 '+past+'頭'
  +'\\n提供元の取消報告 '+withdrawn+'頭・取消状態不明 '+unknown+'頭'
  +'\\n提供元の馬場 '+data.sourceGoing+'｜'+timing
  +'\\n調教と近走の暫定評価：両方あり '+both+'頭／片方のみ '+(trainingOnly+recentOnly)+'頭／両方なし '+neither+'頭'
  +'\\n評価差が大きい馬 '+large+'頭（独自仮基準・要再検討）｜どちらも高評価 '+bothHigh+'頭（勝ち馬候補ではありません）'
  +'\\n過去4角位置（展開の材料のみ）：前方観測 '+front+'頭／後方 '+back+'頭／混在 '+mixed+'頭／資料不足 '+insufficient+'頭'
  +'\\n血統資料：父 '+sire+'頭／母父 '+maternal+'頭／両方 '+bothParent+'頭（適性未評価）'
  +'\\n枠・斤量：枠 '+bracket+'頭／斤量 '+weight+'頭／両方 '+bothDraw+'頭（有利不利は未評価）'
  +'\\n前走間隔：14日未満 '+under14+'頭／14〜55日 '+days14to55+'頭／56日以上 '+days56plus+'頭／不明 '+intervalUnknown+'頭'
  +'\\n騎手・厩舎資料：騎手名 '+jockeyName+'頭／騎手コード '+jockeyCode+'頭／調教師名 '+trainerName+'頭／調教師コード '+trainerCode+'頭／両名 '+bothPeople+'頭'
  +'\\n馬体形状資料：体型コード '+bodyType+'頭／総合コード '+bodyCode+'頭／どちらか '+anyBody+'頭（当日の馬体重・増減は未取得）'
  +'\\n10項目の資料：調教・近走の仮評価＋6項目の観測に接続、残り2項目（距離・馬場）はこの確認では未接続（総合ランク未完成）'
  +'\\n10項目評価：未実施｜JRA公式の取消・馬場・発走時刻：未照合'
  +'\\n独立したJRAデータ取得：未接続｜総合評価・3連単：未作成';
}
el('programmeReadiness').onclick=async()=>{
 const selected=chosenProgramme(),day=loadedProgrammeDate;
 if(!enabled||programmeDemoActive||!selected||!/^[0-9]{8}$/.test(day)){
  el('programmeReadinessResult').textContent='資料確認不可：実データ接続済みのレースを選んでください。架空テストは対象外です。';
  return;
 }
 const key=selected.track+'|'+selected.race,serial=++readinessSerial,
       button=el('programmeReadiness');
 button.disabled=true;
 el('programmeReadinessResult').textContent='選んだ1レースの資料を一括確認中…（読取専用）';
 try{
  // A single deliberately-triggered owner request, no background polling.
  const data=await request('/api/jrdb/selected-readiness?date='+encodeURIComponent(day)
    +'&track='+encodeURIComponent(selected.track)+'&race='+selected.race);
  if(serial!==readinessSerial||day!==loadedProgrammeDate||!chosenProgramme()
     ||key!==chosenProgramme().track+'|'+chosenProgramme().race||programmeDemoActive)return;
  el('programmeReadinessResult').textContent=showSingleRaceReadiness(data,selected,day);
 }catch(error){
  if(serial===readinessSerial)
   el('programmeReadinessResult').textContent='資料を照合できません：'+error.message+'。実戦予想・買い目は作成しません。';
 }finally{
  if(serial===readinessSerial)updateReadinessAction();
 }
};
el('programmeDemo').onclick=loadOfflineProgrammeDemo;
el('programmeTrack').onchange=selectProgrammeTrack;
el('programmeRace').onchange=showProgrammeSelection;
el('date').value=new Date().toLocaleDateString('sv-SE',{timeZone:'Asia/Tokyo'});
el('date').onchange=()=>{resetProgramme();el('races').replaceChildren();el('message').textContent='開催日を変更しました。出走表を再取得してください。';};
el('load').onclick=async()=>{
 const button=el('load');button.disabled=true;resetProgramme();el('races').replaceChildren();el('message').textContent='開催日の出走表を確認中…';
 try{
  if(!enabled)throw Error('JRDBの実データ連携は未接続です');
  const date=el('date').value.replaceAll('-','');
  if(!/^[0-9]{8}$/.test(date))throw Error('開催日を選んでください');
  const data=await request('/api/jrdb/program?date='+encodeURIComponent(date));
  if(data.programmeOnly!==true||!Array.isArray(data.rows))throw Error('番組以外のデータは表示できません');
  // A response to a previous day must never repopulate a newly selected date.
  if(el('date').value.replaceAll('-','')!==date)throw Error('開催日が変わりました。取得し直してください');
  loadProgrammePicker(data.rows,date);
  el('message').textContent=data.rows.length+'Rを取得。競馬場とレースを選択してください。調教・近走・評価・買い目は未確認です。';
 }catch(e){resetProgramme();el('message').textContent='出走表を表示できません：'+e.message;}
 finally{button.disabled=!enabled;}
};
el('history').onclick=async()=>{
 const b=el('history');b.disabled=true;el('message').textContent='上限8レースの過去馬場を照合中…';el('races').replaceChildren();
 try{
  if(!historyEnabled)throw Error('過去履歴の実行は無効です');
  if(!el('date').value)throw Error('開催日を選んでください');
  const date=el('date').value.replaceAll('-','');
  const reply=await fetch('/api/jrdb/history',{
   method:'POST',credentials:'same-origin',cache:'no-store',
   headers:{'Content-Type':'application/json','X-Keiba-Request':'private'},
   body:JSON.stringify({date,limit:8})
  });
  const data=await reply.json();if(!reply.ok)throw Error(data.error||'照合できませんでした');
  if(data.predictionReady!==false||data.goingSuitabilityAssessed!==false
     ||data.evidenceQuality?.predictionReady!==false
     ||data.evidenceQuality?.predictionConfidenceAssessed!==false
     ||data.tenFactorMaterials?.predictionReady!==false
     ||data.tenFactorMaterials?.bettingReady!==false
     ||data.tenFactorMaterials?.gradedFactors!==0
     ||data.privateHistoryFactors?.version!=='private-course-ground-materials-1'
     ||data.privateHistoryFactors?.predictionReady!==false
     ||data.privateHistoryFactors?.bettingReady!==false
     ||data.privateHistoryFactors?.raceCount!==data.goingSummary?.races?.length
     ||data.allTenFactorSources?.version!=='combined-ten-factor-observations-1'
     ||data.allTenFactorSources?.raceCount!==data.goingSummary?.races?.length
     ||data.allTenFactorSources?.predictionReady!==false
     ||data.allTenFactorSources?.bettingReady!==false
     ||data.realAssessmentPreflight?.version!=='real-assessment-preflight-1'
     ||data.realAssessmentPreflight?.raceCount!==data.goingSummary?.races?.length
     ||data.realAssessmentPreflight?.realGradeReady!==false
     ||data.realAssessmentPreflight?.realPredictionReady!==false
     ||data.realAssessmentPreflight?.purchaseReady!==false)
   throw Error('安全な資料集計以外は表示できません');
  el('message').textContent='照合 '+data.selectedPastRaces+'件／残り '+data.deferredPastRaces
   +'件｜過去番組未取得 '+data.unavailablePastProgrammes
   +'件｜過去馬場未取得 '+data.unavailablePastConditions+'件（適性評価・予想は未実施）';
  for(const race of data.goingSummary.races){
   const quality=data.evidenceQuality.races.find(r=>r.track===race.track&&r.race===race.race);
   if(!quality)throw Error('資料充足度の照合結果が一致しません');
   const materials=data.tenFactorMaterials.races.find(r=>r.track===race.track&&r.race===race.race);
   if(!materials||materials.runnerCount!==quality.runnerCount
      ||materials.predictionReady!==false||materials.bettingReady!==false
      ||materials.gradedFactors!==0)throw Error('10項目の資料確認が一致しません');
   const factors=materials.factors;
   if(!factors||Object.keys(factors).length!==10
      ||!Object.values(factors).every(x=>x.grade==='未評価'&&x.assessmentComplete===false))
     throw Error('未評価以外の資料情報は表示できません');
   const privateFactors=data.privateHistoryFactors.races.filter(
     r=>r.track===race.track&&r.race===race.race);
   if(privateFactors.length!==1)throw Error('コース・馬場の評価資料が一致しません');
   const linked=privateFactors[0];
   const combined=data.allTenFactorSources.races.filter(
     r=>r.track===race.track&&r.race===race.race);
   if(combined.length!==1)throw Error('10項目の資料結合が一致しません');
   const total=combined[0];
   const gateList=data.realAssessmentPreflight.races.filter(
     r=>r.track===race.track&&r.race===race.race);
   if(gateList.length!==1)throw Error('実馬評価の前提条件が一致しません');
   const gate=gateList[0];
   const n=quality.runnerCount;
   const headcounts=['runnerCount','runnersWithComparableCourse',
     'runnersWithKnownGoingComparable','runnersWithWetComparable',
     'runnersMatchingCurrentGoing','runnersWithIncompleteHistory',
     'runnersWithCurrentGoingUnknown'].map(k=>linked[k]);
   if(!headcounts.every(v=>Number.isInteger(v)&&v>=0&&v<=n)
      ||linked.runnerCount!==n
      ||linked.observationOnlyFactors?.join(',')!=='pace,course_distance,ground'
      ||linked.unmappedFactorCount!==5
      ||linked.verifiedFactorCount!==0
      ||linked.suitabilityAssessed!==false
      ||linked.overallRankReady!==false
      ||linked.predictionReady!==false||linked.bettingReady!==false
      ||!Number.isInteger(linked.unknownComparableGoingRuns)
      ||linked.unknownComparableGoingRuns<0
      ||linked.unknownComparableGoingRuns>5*n
      ||linked.runnersWithKnownGoingComparable>linked.runnersWithComparableCourse)
     throw Error('コース・馬場の資料件数が一致しません');
   if(total.runnerCount!==n||total.sourceMaterialSlots!==10
      ||total.provisionalFactorSlots!==2||total.observationOnlySlots!==8
      ||total.unmappedFactorCount!==0||total.verifiedFactorCount!==0
      ||total.raceDayBodyWeightFetched!==false
      ||total.historySuitabilityAssessed!==false
      ||total.jockeyTrainerPerformanceAssessed!==false
      ||total.bodyConditionAssessed!==false
      ||total.officialJraFinalVerification!==false
      ||total.overallRankReady!==false||total.predictionReady!==false
      ||total.bettingReady!==false
      ||!['runnersWithComparableCourse','runnersWithKnownGoingComparable',
           'runnersWithIncompleteHistory','runnersWithBothPersonnelNames',
           'runnersWithConformationCodes'].every(k=>
              Number.isInteger(total[k])&&total[k]>=0&&total[k]<=n)
      ||total.runnersWithComparableCourse!==linked.runnersWithComparableCourse
      ||total.runnersWithKnownGoingComparable!==linked.runnersWithKnownGoingComparable
      ||total.runnersWithIncompleteHistory!==linked.runnersWithIncompleteHistory)
     throw Error('10項目の資料結合に未確認の状態があります');
   const always=[
     'source_use_rights_not_verified',
     'independent_jra_final_not_verified',
     'real_factor_assessments_not_validated',
     'race_day_body_condition_not_verified'
   ];
   const allowed=[
     ...always,'history_lookup_incomplete','course_comparables_missing',
     'going_comparables_missing','personnel_records_partial',
     'conformation_codes_partial','past_run_records_absent','empty_runner_list'
   ];
   const blockers=gate.blockerCodes;
   if(!Array.isArray(blockers)||blockers.length<always.length
      ||blockers.length>allowed.length
      ||new Set(blockers).size!==blockers.length
      ||always.some((code,i)=>blockers[i]!==code)
      ||blockers.some(code=>!allowed.includes(code))
      ||gate.runnerCount!==n||gate.observedTenSlotStructure!==true
      ||gate.verifiedFactorCount!==0
      ||gate.realGradeReady!==false||gate.realPredictionReady!==false
      ||gate.purchaseReady!==false)
     throw Error('実馬評価の未完了条件を確認できません');
   const pendingCounts=[
     'unverifiedRunnerHistory','runnersWithoutCourseComparables',
     'runnersWithoutGoingComparables','runnersWithoutPersonnelNames',
     'runnersWithoutConformationCodes','runnersWithoutRecordedPast'
   ];
   if(!pendingCounts.every(k=>Number.isInteger(gate[k])&&gate[k]>=0&&gate[k]<=n)
      ||gate.unverifiedRunnerHistory!==total.runnersWithIncompleteHistory
      ||gate.runnersWithoutCourseComparables!==n-total.runnersWithComparableCourse
      ||gate.runnersWithoutGoingComparables!==n-total.runnersWithKnownGoingComparable
      ||gate.runnersWithoutPersonnelNames!==n-total.runnersWithBothPersonnelNames
      ||gate.runnersWithoutConformationCodes!==n-total.runnersWithConformationCodes
      ||!Number.isInteger(quality.runnersNoRecordedPast)
      ||gate.runnersWithoutRecordedPast!==quality.runnersNoRecordedPast
      ||((!data.historyComplete||gate.unverifiedRunnerHistory>0
             ||quality.unlinkedPastRuns>0)
          !==blockers.includes('history_lookup_incomplete'))
      ||(gate.runnersWithoutCourseComparables>0)
          !==blockers.includes('course_comparables_missing')
      ||(gate.runnersWithoutGoingComparables>0)
          !==blockers.includes('going_comparables_missing')
      ||(gate.runnersWithoutPersonnelNames>0)
          !==blockers.includes('personnel_records_partial')
      ||(gate.runnersWithoutConformationCodes>0)
          !==blockers.includes('conformation_codes_partial')
      ||(gate.runnersWithoutRecordedPast>0)
          !==blockers.includes('past_run_records_absent')
      ||(n===0)!==blockers.includes('empty_runner_list'))
     throw Error('実馬評価の不足資料件数が一致しません');
   const c=quality.courseComparableSamples,g=quality.knownGoingComparableSamples;
   const counts=[c.none,c.oneOrTwo,c.threePlus,g.none,g.oneOrTwo,g.threePlus];
   if(!counts.every(n=>Number.isInteger(n)&&n>=0)
      ||c.none+c.oneOrTwo+c.threePlus!==quality.runnerCount
      ||g.none+g.oneOrTwo+g.threePlus!==quality.runnerCount)
     throw Error('資料充足度の件数が一致しません');
   if(linked.runnersWithComparableCourse!==c.oneOrTwo+c.threePlus
      ||linked.runnersWithKnownGoingComparable!==g.oneOrTwo+g.threePlus)
     throw Error('比較履歴の頭数が一致しません');
   const div=document.createElement('div');div.className='race';
   div.textContent=race.track+race.race+'R｜重 '+race.heavyComparableRuns
      +'走（3着以内 '+race.heavyTopThreeRuns+'）／不良 '+race.poorComparableRuns
      +'走（3着以内 '+race.poorTopThreeRuns+'）／馬場未照合 '+race.unknownComparableRuns
      +'走｜距離比較 3走以上 '+c.threePlus+'頭・1〜2走 '+c.oneOrTwo+'頭・0走 '+c.none
      +'頭｜馬場比較 3走以上 '+g.threePlus+'頭・1〜2走 '+g.oneOrTwo+'頭・0走 '+g.none
      +'頭｜過去番組の未照合 '+quality.unlinkedPastRuns+'走'
      +'｜10項目の資料：調教 '+factors.training.observedRunnerCount+'/'+materials.runnerCount
      +'頭、近走 '+factors.recent.observedRunnerCount+'/'+materials.runnerCount
      +'頭、距離 '+factors.course_distance.observedRunnerCount+'/'+materials.runnerCount
      +'頭、馬場 '+factors.ground.observedRunnerCount+'/'+materials.runnerCount
      +'頭、残り6項目は未接続'
      +'｜10項目の内部資料：コース比較あり '+linked.runnersWithComparableCourse+'頭'
      +'・馬場比較あり '+linked.runnersWithKnownGoingComparable+'頭'
      +'・履歴未完成 '+linked.runnersWithIncompleteHistory+'頭'
      +'・馬場未確認 '+linked.runnersWithCurrentGoingUnknown+'頭'
      +'｜10項目の資料枠：10/10接続（調教・近走は未検証の暫定基準、残り8項目は観測のみ）'
      +'・騎手・厩舎の両名あり '+total.runnersWithBothPersonnelNames+'頭'
      +'・馬体形状コードあり '+total.runnersWithConformationCodes+'頭（当日の馬体重・増減は未取得）'
      +'｜確定評価 0項目／総合S/A/B/C未作成／予想信頼度：未算定'
      +'｜実馬評価前の必須確認：利用権限・JRA公式・項目別評価基準・当日の馬体状態'
      +'｜不足資料：履歴 '+gate.unverifiedRunnerHistory+'頭'
      +'／距離 '+gate.runnersWithoutCourseComparables+'頭'
      +'／馬場 '+gate.runnersWithoutGoingComparables+'頭'
      +'／騎手厩舎 '+gate.runnersWithoutPersonnelNames+'頭'
      +'／馬体形状 '+gate.runnersWithoutConformationCodes+'頭'
      +'／過去走 '+gate.runnersWithoutRecordedPast+'頭（評価未着手・予想不可）';
   el('races').append(div);
  }
 }catch(e){el('message').textContent=e.message;}
 finally{b.disabled=!historyEnabled;}
};
const operatorNotes=new Map();
el('noteRun').onclick=async()=>{
 const b=el('noteRun');b.disabled=true;
 try{
  if(!el('date').value)throw Error('開催日を選んでください');
  const date=el('date').value.replaceAll('-',''),track=el('noteTrack').value;
  if(!track)throw Error('競馬場を選んでください');
  const race=Number(el('noteRace').value),horseNumber=el('noteHorse').value;
  const factor=el('noteFactor').value,state=el('noteState').value,source=el('noteSource').value;
  if(state==='noted'&&source==='none')
   throw Error('見た資料の種類を選んでください');
  if(state==='unknown'&&source!=='none')
   throw Error('未確認のときは資料の種類を「未選択」にしてください');
  const payload={recordType:'operator_factor_note',date,track,race,
                 horseNumber,factor,state,source};
  const r=await fetch('/api/operator/factor-note',{
   method:'POST',credentials:'same-origin',cache:'no-store',
   headers:{'Content-Type':'application/json','X-Keiba-Request':'private'},
   body:JSON.stringify(payload)
  });
  const data=await r.json();
  if(!r.ok)throw Error(data.error||'入力の確認に失敗しました');
  if(data.version!=='operator-factor-intake-1'
     ||data.recordType!=='operator_factor_note'
     ||data.date!==date||data.track!==track||data.race!==race
     ||data.factor!==factor||data.state!==state||data.sourceKind!==source
     ||data.submittedByOperator!==true||data.saved!==false
     ||data.sourceAuthenticated!==false||data.verifiedBeforePostTime!==false
     ||data.jraOfficialFinalVerification!==false
     ||data.grade!=='未評価'||data.gradedFactorCount!==0
     ||data.predictionReady!==false||data.bettingReady!==false)
    throw Error('未検証の入力として確認できません');
  const key=[date,track,race,horseNumber].join('|');
  const notes=operatorNotes.get(key)||new Map();
  notes.set(factor,state);
  operatorNotes.set(key,notes);
  const viewed=[...notes.values()].filter(v=>v==='noted').length;
  el('noteResult').textContent=track+race+'R・'+Number(horseNumber)+'番｜'
      +'本人が入力した項目 '+notes.size+'/10（資料を見た '+viewed+'／未確認 '
      +(notes.size-viewed)+'）｜保存なし／能力ランク未評価／公式照合未実施';
 }catch(e){el('noteResult').textContent=e.message;}
 finally{b.disabled=false;}
};
let previousManualComparison=null;
el('manualCompare').onclick=async()=>{
 const button=el('manualCompare');button.disabled=true;
 el('manualResults').replaceChildren();
 el('manualMessage').textContent='本人入力の1Rだけを照合中…';
 try{
  if(!manualEnabled)throw Error('本人専用の手入力照合は無効です');
  if(!el('date').value)throw Error('開催日を選んでください');
  const date=el('date').value.replaceAll('-','');
  const track=el('manualTrack').value;
  if(!track)throw Error('競馬場を選んでください');
  const race=Number(el('manualRace').value);
  const horse=el('manualHorse').value;
  const status=el('manualStatus').value;
  if(!horse&&status!=='unknown')throw Error('取消状態を入力する場合は馬番を選んでください');
  const manual={
   date,source:'operator_transcription',
   races:[{track,race,completeRoster:false,
    postTime:el('manualTime').value.trim()||null,
    going:el('manualGoing').value||null,
    surface:el('manualSurface').value||null,
    entries:horse?[{horseNumber:horse,status,jockeyCode:null}]:[]
   }]
  };
  const response=await fetch('/api/jrdb/compare-manual',{
   method:'POST',credentials:'same-origin',cache:'no-store',
   headers:{'Content-Type':'application/json','X-Keiba-Request':'private'},
   body:JSON.stringify(manual)
  });
  const data=await response.json();
  if(!response.ok)throw Error(data.error||'照合できませんでした');
  if(data.officialJraFinalVerification!==false
     ||data.predictionReady!==false||data.bettingReady!==false
     ||data.racesCompared!==1)throw Error('公式確認の状態が不正です');
  const row=data.races.find(x=>x.track===track&&x.race===race);
  if(!row||row.independentSnapshotAuthenticated!==false
     ||row.referenceCollectionFreshnessVerified!==false
     ||row.officialJraFinalVerification!==false
     ||row.predictionReady!==false||row.bettingReady!==false
     ||!Number.isInteger(row.differenceCount)||row.differenceCount<0
     ||!Number.isInteger(row.unknownComparisons)||row.unknownComparisons<0)
    throw Error('照合件数または確認状態が不正です');
  const category={withdrawal:'取消',jockey:'騎手コード',going:'馬場',
    postTime:'発走予定時刻',surface:'芝・ダート',roster:'出走馬一覧'};
  if(!row.differenceCategories
     ||Object.keys(category).some(key=>!Number.isInteger(row.differenceCategories[key])
                                       ||row.differenceCategories[key]<0))
    throw Error('差分項目が不正です');
  const details=Object.keys(category)
    .filter(key=>row.differenceCategories[key]>0)
    .map(key=>category[key]+row.differenceCategories[key]+'件');
  const key=date+'|'+track+'|'+race;
  const before=previousManualComparison&&previousManualComparison.key===key
    ?previousManualComparison.count:null;
  const diff=before===null?'':('｜前回との差分件数 '+before+'→'+row.differenceCount);
  el('manualMessage').textContent=track+race+'R｜入力した範囲の差分 '
    +row.differenceCount+'件'+(details.length?'（'+details.join('、')+'）':'')
    +'｜比較できない項目 '+row.unknownComparisons+'件'+diff
    +'｜出所・最新性の独立認証なし／JRA公式の最終確認：未実施／予想・購入：未接続';
  previousManualComparison={key,count:row.differenceCount};
 }catch(err){el('manualMessage').textContent=err.message;}
 finally{button.disabled=!manualEnabled;}
};
el('raceday').onclick=async()=>{
 const button=el('raceday');button.disabled=true;
 el('message').textContent='出走取消フラグ・馬場の資料を照合中…';
 el('races').replaceChildren();
 try{
  if(!enabled)throw Error('本人用データ接続は無効です');
  if(!el('date').value)throw Error('開催日を選んでください');
  const date=el('date').value.replaceAll('-','');
  const data=await request('/api/jrdb/race-day?date='+encodeURIComponent(date));
  const fresh=data.prestartFreshness;
  const independent=data.independentComparison;
  if(data.predictionReady!==false||data.bettingReady!==false
     ||independent?.predictionReady!==false
     ||independent?.bettingReady!==false
     ||independent?.officialJraFinalVerification!==false
     ||independent?.racesCompared!==0
     ||independent?.racesMissingReference!==data.raceCount
     ||data.racesWithOfficialFinalCheck!==0
     ||fresh?.predictionReady!==false||fresh?.bettingReady!==false
     ||fresh?.officiallyVerifiedRaces!==0)
    throw Error('資料確認の状態が不正です');
  el('message').textContent='JRDB資料：出走取消報告あり '+data.racesWithProviderWithdrawal
   +'R／取消フラグ不明あり '+data.racesWithUnknownFlags
   +'R｜発走2時間以内 '+fresh.racesWithinTwoHours
   +'R（'+fresh.checkedAtJapan+'時点）｜独立JRA参照：未接続｜JRA公式での最終確認：全R未完了';
  for(const race of data.races){
   if(race.finalRaceReady!==false||race.predictionReady!==false
      ||race.officialScratchesVerified!==false||race.officialGoingVerified!==false)
     throw Error('最終確認の状態が不正です');
   const cross=independent.races.find(x=>x.track===race.track&&x.race===race.race);
   if(!cross||cross.independentReferenceProvided!==false
      ||cross.comparisonStatus!=='missing_reference'
      ||cross.officialJraFinalVerification!==false
      ||cross.bettingReady!==false)
     throw Error('独立参照の未接続状態が一致しません');
   const timing=fresh.races.find(x=>x.track===race.track&&x.race===race.race);
   if(!timing||timing.jraOfficialDataFetched!==false
      ||timing.jraScratchesVerified!==false||timing.jraGoingVerified!==false
      ||timing.jraPostTimeVerified!==false||timing.bettingReady!==false)
     throw Error('発走時刻と公式資料の確認が一致しません');
   const windows={post_time_unknown:'発走予定不明',other_date:'別開催日',
     post_time_passed:'発走予定時刻経過',within_two_hours:'発走2時間以内',
     more_than_two_hours:'発走まで2時間超'};
   const ages={no_going_report:'馬場未確認',no_update_timestamp:'更新時刻未確認',
     timestamp_in_future:'更新時刻が未来',recent_reported:'更新記録60分以内',
     old_or_other_date_reported:'更新記録60分超または別日'};
   if(!windows[timing.prestartWindow]||!ages[timing.sourceGoingAgeStatus])
     throw Error('発走前情報の状態が不明です');
   const div=document.createElement('div');div.className='race';
   div.textContent=race.track+race.race+'R｜提供元の取消報告 '+race.providerWithdrawnCount
    +'頭／フラグ不明 '+race.withdrawalFlagUnknownCount
    +'頭｜馬場 '+race.sourceGoing
    +'（'+(ages[timing.sourceGoingAgeStatus]||'更新状況不明')+'）'
    +'｜発走前：'+(windows[timing.prestartWindow]||'時刻未確認')
    +'｜独立照合：未接続／公式の取消・馬場・発走時刻：未確認｜馬券予想：未作成';
   el('races').append(div);
  }
 }catch(e){el('message').textContent=e.message;}
 finally{button.disabled=!enabled;}
};
el('context').onclick=async()=>{el('context').disabled=true;el('message').textContent='コース・馬場の取得状況を照合中…';el('races').replaceChildren();try{if(!el('date').value)throw Error('開催日を選んでください');const data=await request('/api/jrdb/context?date='+encodeURIComponent(el('date').value.replaceAll('-','')));el('message').textContent=data.raceCount+'Rのうちコース条件取得 '+data.courseInfoPresentCount+'R／馬場状態取得 '+data.goingAvailableCount+'R（馬の適性や予想は未評価）';for(const row of data.races){const div=document.createElement('div');div.className='race';div.textContent=row.track+row.race+'R｜'+(row.surface||'種別未確認')+' '+(row.distance_m==null?'距離未確認':row.distance_m+'m')+' '+(row.turn||'回り未確認')+'｜馬場 '+row.going+'｜更新記録 '+(row.conditionUpdateRecorded?'あり':'未確認')+'｜コース・馬場適性：未評価';el('races').append(div);}}catch(e){el('message').textContent=e.message;}finally{el('context').disabled=!enabled;}};
el('coverage').onclick=async()=>{el('coverage').disabled=true;el('message').textContent='全レースの照合中…';el('races').replaceChildren();try{if(!el('date').value)throw Error('開催日を選んでください');const data=await request('/api/jrdb/coverage?date='+encodeURIComponent(el('date').value.replaceAll('-','')));el('message').textContent=data.raceCount+'Rのうち出走馬件数一致 '+data.matchingEntryCounts+'R。最終確認済み0R、予想作成済み0R（取消・調教など未検証）。';for(const row of data.races){const div=document.createElement('div');div.className='race';div.textContent=row.track+row.race+'R｜発走 '+(row.post_time||'未確認')+'｜登録 '+row.observedEntries+'/'+(row.expectedRunners===null?'?':row.expectedRunners)+'頭｜'+row.status+'｜予想：未作成';el('races').append(div);}}catch(e){el('message').textContent=e.message;}finally{el('coverage').disabled=!enabled;}};
el('evidence').onclick=async()=>{el('evidence').disabled=true;el('message').textContent='資料の件数を確認中…';el('races').replaceChildren();try{if(!el('date').value)throw Error('開催日を選んでください');const data=await request('/api/jrdb/evidence?date='+encodeURIComponent(el('date').value.replaceAll('-','')));const preflight=data.assessmentPreflight;el('message').textContent=data.raceCount+'Rのうち資料不足・未対応 '+data.gapRaceCount+'R。評価済み '+preflight.gradedFactors+'/'+preflight.factorCount+'項目。実戦予想：未接続。';const labels={source_record_count_matches:'資料件数一致（内容は未評価）',partial_source_records:'一部のみ資料あり',unknown_or_not_applicable:'資料なし・対象外の可能性',not_mapped_from_provider:'自動紐付け未実装'};for(const row of data.races){const div=document.createElement('div');div.className='race';const detail=preflight.races.find(a=>a.track===row.track&&a.race===row.race);div.textContent=row.track+row.race+'R｜登録 '+row.observedEntries+'/'+(row.expectedRunners==null?'?':row.expectedRunners)+'頭｜調教未対応 '+row.trainingUnaccounted+'／1週前 '+row.lastWeekUnaccounted+'／近走 '+row.pastRunUnaccounted+'頭｜総合評価：未実施';const candidate=data.trainingHypothesis?.races?.find(a=>a.track===row.track&&a.race===row.race);if(candidate){const p=document.createElement('p');const c=candidate.gradeCounts;p.textContent='調教のみ独自暫定：S '+c.S+'／A '+c.A+'／B '+c.B+'／C '+c.C+'／未評価 '+c['未評価']+'（実戦買い目ではありません）';div.append(p)}const form=data.recentHypothesis?.races?.find(a=>a.track===row.track&&a.race===row.race);if(form){const recent=document.createElement('p');const g=form.gradeCounts;recent.textContent='近走のみ独自暫定：S '+g.S+'／A '+g.A+'／B '+g.B+'／C '+g.C+'／未評価 '+g['未評価']+'｜4角位置 '+form.fourthPositionObservations+'件／上がり3F '+form.late3fObservations+'件（相手関係・着差未評価）';div.append(recent)}const position=data.positionObservations?.races?.find(a=>a.track===row.track&&a.race===row.race);if(position){const p=document.createElement('p');const c=position.observations;p.textContent='過去4角位置：前方観測 '+c.frontObserved+'／後方観測 '+c.backObserved+'／混在 '+c.mixedObserved+'／資料不足 '+c.insufficient+'頭（展開予想ではありません）';div.append(p)}const dual=data.dualFactorReadiness?.races?.find(a=>a.track===row.track&&a.race===row.race);if(dual){const p=document.createElement('p');p.textContent='調教・近走の両方が暫定評価可能：'+dual.both+'/'+dual.runnerCount+'頭｜残り8項目未確認・買い目未作成';div.append(p)}if(detail){const exp=document.createElement('details');const head=document.createElement('summary');head.textContent='10項目の評価準備を見る';exp.append(head);const list=document.createElement('ul');for(const item of Object.values(detail.factors)){const li=document.createElement('li');li.textContent=item.label+'：'+(labels[item.sourceStatus]||'未確認')+'｜ランク未評価';list.append(li)}exp.append(list);div.append(exp)}el('races').append(div);}}catch(e){el('message').textContent=e.message;}finally{el('evidence').disabled=!enabled;}};
'''



OWNER_UPDATE_JS = r"""(()=>{'use strict';
/* Authenticated, no-store update detection for iPhone home-screen Web app.
   Only auto-reload the untouched landing page; never discard notebook input. */
const meta=document.querySelector('meta[name="keiba-owner-release"]');
if(!meta||typeof meta.content!=='string'||!meta.content.includes('|'))return;
const loaded=meta.content,landing=location.pathname==='/'||location.pathname==='/preview-v2';
let busy=false,changed=false,notified=false;
document.addEventListener('input',()=>{changed=true},true);
document.addEventListener('change',()=>{changed=true},true);
document.addEventListener('click',e=>{if(e.target&&typeof e.target.closest==='function'&&e.target.closest('button'))changed=true},true);
function offerUpdate(){
 if(notified)return;
 notified=true;
 const bar=document.createElement('aside');bar.className='owner-update-notice';
 bar.setAttribute('role','status');
 const line=document.createElement('p');
 line.textContent='競馬ナインの新しい版があります。編集中の入力が消えないよう、自動更新を止めています。';
 const button=document.createElement('button');
 button.type='button';button.textContent='確認して最新版を開く';
 button.onclick=()=>location.reload();
 bar.append(line,button);document.body.prepend(bar);
}
async function inspectRelease(){
 if(busy||notified||document.visibilityState==='hidden')return;
 busy=true;
 try{
  const r=await fetch('/ui-version',{
   cache:'no-store',credentials:'same-origin',redirect:'manual',
   headers:{'X-Keiba-Request':'private'}
  });
  if(!r.ok)return;
  const txt=await r.text();
  const v=/^uiVersion=([a-zA-Z0-9._-]+)$/m.exec(txt);
  const c=/^renderCommit=([0-9a-fA-F]{12}|not-reported)$/m.exec(txt);
  if(!v||!c)return;
  const latest=v[1]+'|'+c[1];
  if(latest===loaded)return;
  if(landing&&!changed){location.reload();return;}
  offerUpdate();
 }catch(_){
  // Offline, sleeping instance or invalid login: preserve current input.
 }finally{busy=false}
}
window.addEventListener('pageshow',inspectRelease);
document.addEventListener('visibilitychange',()=>{if(document.visibilityState==='visible')inspectRelease()});
})();"""

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
    raw_sha = settings.get('RENDER_GIT_COMMIT', '')
    release_sha = raw_sha[:12] if isinstance(raw_sha, str) and re.fullmatch(
        r'[0-9a-fA-F]{7,64}', raw_sha) else 'not-reported'
    release_tag = UI_VERSION + '|' + release_sha

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
        path, method = environ.get('PATH_INFO', '/'), environ.get('REQUEST_METHOD', 'GET')
        auth = environ.get('HTTP_AUTHORIZATION', '')
        try:
            scheme, value = auth.split(' ', 1)
            if scheme.lower() != 'basic' or len(value) > 2048:
                raise ValueError()
            credentials = base64.b64decode(value, validate=True)
            valid_basic = hmac.compare_digest(hashlib.sha256(credentials).digest(), expected)
        except (ValueError, TypeError):
            valid_basic = False
        # Signed HttpOnly cookie is derived from the existing strong owner
        # password. It is not a second password and never reaches JavaScript.
        valid_cookie = session_cookie_valid(environ.get('HTTP_COOKIE', ''), expected)
        valid = valid_basic or valid_cookie
        if method == 'GET' and path == '/login.css':
            return response('200 OK', LOGIN_CSS, 'text/css; charset=utf-8')
        def login_page(error='', status='200 OK'):
            # Fresh token for each login page; never expose the password or
            # session secret. The token must match a host-only HttpOnly cookie.
            csrf_token, csrf_cookie = new_login_form_csrf()
            html = LOGIN_HTML.replace('__ERROR__', error).replace('__CSRF__', csrf_token)
            return response(status, html, 'text/html; charset=utf-8',
                            extra=[('Set-Cookie', csrf_cookie)])

        if method == 'GET' and path == '/login':
            if valid:
                return response('303 See Other', '', 'text/plain; charset=utf-8',
                                extra=[('Location', '/')])
            # If the password was accepted but this navigation lost its signed
            # cookie, explain the loop instead of silently showing a blank form.
            session_error = (
                'ログイン後の認証情報がブラウザーに保存されていません。'
                'iPhoneのSafariでURLを直接開いて、Cookieを許可して再度お試しください。'
                if environ.get('QUERY_STRING', '') == 'session=check' else ''
            )
            return login_page(session_error)
        if method == 'POST' and path == '/login':
            # No paid data reads and no logs, storage, URL password parameters,
            # cross-site login, or Basic challenge on a failed form submission.
            # The browser-bound CSRF token authenticates a same-browser form
            # submission even when Render or iPhone Safari alters Origin.
            # Still reject explicit cross-site Fetch Metadata unconditionally.
            fetch_site = environ.get('HTTP_SEC_FETCH_SITE', '')
            fetch_ok = fetch_site != 'cross-site'
            type_ok = (environ.get('CONTENT_TYPE', '').split(';')[0].strip().lower()
                       == 'application/x-www-form-urlencoded')
            query_ok = not environ.get('QUERY_STRING', '')
            rejection_kind = 'request'
            rejection_code = ('R1' if not query_ok else
                              'R2' if not fetch_ok else
                              'R4' if not type_ok else 'R5')
            try:
                size = int(environ.get('CONTENT_LENGTH', '0'))
                if not query_ok or not fetch_ok or not type_ok or not 0 < size <= 4096:
                    raise ValueError()
                body = environ['wsgi.input'].read(size)
                if len(body) != size:
                    raise ValueError()
                rejection_code = 'R6'
                fields = parse_qs(body.decode('utf-8', errors='strict'),
                                  keep_blank_values=True, strict_parsing=True,
                                  max_num_fields=3, errors='strict')
                if set(fields) != {'username', 'password', 'login_csrf'} or any(len(v) != 1 for v in fields.values()):
                    raise ValueError()
                rejection_code = 'R3'
                if not login_form_csrf_valid(environ.get('HTTP_COOKIE', ''), fields['login_csrf'][0]):
                    raise ValueError()
                rejection_kind = 'credentials'
                if not owner_credentials_match(fields['username'][0], fields['password'][0],
                                               expected, username):
                    raise ValueError()
            except (ValueError, KeyError, TypeError, UnicodeError):
                detail = (
                    'ログインフォームの検証で止まりました（診断コード：' +
                    rejection_code + '）。このページを再読み込みして試してください。'
                    if rejection_kind == 'request' else
                    'ユーザー名とパスワードが一致しません。RenderのEnvironmentに保存された値を直接コピーしてください。'
                )
                return login_page('ログインできませんでした。' + detail,
                                  status='401 Unauthorized')
            return response('303 See Other', '', 'text/plain; charset=utf-8',
                            extra=[('Location', '/login?session=check'),
                                   ('Set-Cookie', session_cookie(expected))])
        if not valid:
            if method == 'GET' and path in ('/', '/preview-v2', '/my-tickets', '/owner-backup', '/my-scorecard', '/owner-races', '/owner-review', '/owner-auto-trial', '/research-batch-demo', '/research-validation-demo', '/day-pipeline', '/jrdb-mail-local'):
                return response('303 See Other', '', 'text/plain; charset=utf-8',
                                extra=[('Location', '/login')])
            # Do not summon an iPhone native Basic-password popup when an
            # anonymous stylesheet/script request misses a browser cookie.
            # Explicit Authorization headers are still accepted above.
            if method == 'GET' and path in (
                '/app.js', '/app.css', '/my-tickets.js',
                '/my-tickets.css', '/my-purchases.js', '/research-batch-demo.css',
                '/day-pipeline.css', '/day-pipeline.js',
                '/jrdb-mail-local.js', '/jrdb-mail-local.css', '/jrdb-manual-numbers.js', '/owner-backup.js', '/owner-backup.css', '/owner-scorecard.js', '/owner-scorecard.css', '/owner-race-workbench.js', '/owner-race-workbench.css', '/owner-review.js', '/owner-review.css', '/owner-auto-trial.js', '/owner-auto-trial.css', '/jra-official-pdf.js', '/jra-web-card.js', '/owner-update.js', '/ui-version'
            ):
                return response('401 Unauthorized', {'error': 'ログインが必要です。'})
            return response('401 Unauthorized', {'error': '本人認証が必要です。'},
                            extra=[('WWW-Authenticate',
                                    'Basic realm="KEIBA NINE private", charset="UTF-8"')])
        if path.startswith('/api/'):
            # Custom header stops cross-origin form submissions; no CORS is granted.
            if environ.get('HTTP_X_KEIBA_REQUEST') != 'private' or environ.get('HTTP_SEC_FETCH_SITE') == 'cross-site':
                return response('403 Forbidden', {'error': '本人用画面から操作してください。'})
        if method == 'GET' and path == '/owner-update.js':
            return response('200 OK', OWNER_UPDATE_JS, 'text/javascript; charset=utf-8')
        if method == 'GET' and path in ('/', '/preview-v2', '/app.js', '/app.css'):
            text, mime = {'/': (HTML, 'text/html; charset=utf-8'),
                          '/preview-v2': (HTML, 'text/html; charset=utf-8'),
                          '/app.js': (JS, 'text/javascript; charset=utf-8'),
                          '/app.css': (CSS, 'text/css; charset=utf-8')}[path]
            if path in ('/', '/preview-v2'):
                text = text.replace('__OWNER_RELEASE__', release_tag)
            return response('200 OK', text, mime)
        if method == 'GET' and path in ('/owner-auto-trial', '/owner-auto-trial.js', '/owner-auto-trial.css'):
            data, mime = {
                '/owner-auto-trial': (AUTO_HTML, 'text/html; charset=utf-8'),
                '/owner-auto-trial.js': (AUTO_JS, 'text/javascript; charset=utf-8'),
                '/owner-auto-trial.css': (AUTO_CSS, 'text/css; charset=utf-8'),
            }[path]
            return response('200 OK', data, mime)
        if method == 'GET' and path in ('/owner-review', '/owner-review.js', '/owner-review.css'):
            page, mime = {
                '/owner-review': (REVIEW_HTML, 'text/html; charset=utf-8'),
                '/owner-review.js': (REVIEW_JS, 'text/javascript; charset=utf-8'),
                '/owner-review.css': (REVIEW_CSS, 'text/css; charset=utf-8'),
            }[path]
            return response('200 OK', page, mime)
        if method == 'GET' and path in ('/owner-races', '/owner-race-workbench.js', '/owner-race-workbench.css'):
            code, mime = {
                '/owner-races': (WORKBENCH_HTML, 'text/html; charset=utf-8'),
                '/owner-race-workbench.js': (WORKBENCH_JS, 'text/javascript; charset=utf-8'),
                '/owner-race-workbench.css': (WORKBENCH_CSS, 'text/css; charset=utf-8'),
            }[path]
            return response('200 OK', code, mime)
        if method == 'GET' and path in ('/my-scorecard', '/owner-scorecard.js', '/owner-scorecard.css'):
            code, mime = {
                '/my-scorecard': (SCORE_HTML, 'text/html; charset=utf-8'),
                '/owner-scorecard.js': (SCORE_JS, 'text/javascript; charset=utf-8'),
                '/owner-scorecard.css': (SCORE_CSS, 'text/css; charset=utf-8'),
            }[path]
            return response('200 OK', code, mime)
        if method == 'GET' and path in ('/owner-backup', '/owner-backup.js', '/owner-backup.css'):
            code, mime = {
                '/owner-backup': (BACKUP_HTML, 'text/html; charset=utf-8'),
                '/owner-backup.js': (BACKUP_JS, 'text/javascript; charset=utf-8'),
                '/owner-backup.css': (BACKUP_CSS, 'text/css; charset=utf-8'),
            }[path]
            return response('200 OK', code, mime)
        if method == 'GET' and path in ('/my-tickets', '/my-tickets.js',
                                           '/my-tickets.css', '/my-purchases.js'):
            # Both JS bundles are static; all actual purchase entries remain in
            # localStorage on the owner's browser, never in this Render service.
            notebook = TICKET_HTML.replace('</main>', PURCHASE_HTML + '</main>')
            notebook = notebook.replace('__OWNER_RELEASE__', release_tag)
            notebook = notebook.replace(
                '<section id="formationPanel">',
                '<section><h2>調教・近走・適性・血統・展開を評価</h2><p class="muted">手入力した5項目から暫定のS/A/B/Cと総合評価順を計算し、3連単下書きへ渡せます。</p><a href="/my-scorecard">5項目の評価表を開く（自動AI予想ではありません）</a></section><section id="formationPanel">')
            notebook = notebook.replace(
                '<section id="savedPanel">',
                '<section><h2>本人用の一括バックアップ</h2><p class="muted">端末を変える前に、下書き・実購入記録・想定メール・馬番メモの5種類をまとめて保存できます。</p><a href="/owner-backup">5種類をまとめてバックアップ・復元</a></section><section id="savedPanel">')
            notebook = notebook.replace(
                '<script src="/my-tickets.js" defer></script>',
                '<script src="/my-tickets.js?v=drafts-v2" defer></script>'
                '<script src="/my-purchases.js?v=ledger-v2" defer></script><script src="/owner-update.js" defer></script>')
            content, mime = {
                '/my-tickets': (notebook, 'text/html; charset=utf-8'),
                '/my-tickets.js': (TICKET_JS + '\n' + TICKET_HANDOFF_JS, 'text/javascript; charset=utf-8'),
                '/my-tickets.css': (TICKET_CSS + PURCHASE_CSS, 'text/css; charset=utf-8'),
                '/my-purchases.js': (PURCHASE_JS, 'text/javascript; charset=utf-8'),
            }[path]
            return response('200 OK', content, mime)
        if method == 'GET' and path in ('/jrdb-mail-local', '/jrdb-mail-local.js',
                                        '/jrdb-mail-local.css', '/jrdb-manual-numbers.js', '/jra-official-pdf.js', '/jra-web-card.js'):
            # Static code only. Neither licensed mail nor manual JRA numbers
            # transit this service or repository. Separate browser storage.
            page = MAIL_HTML.replace(
                '<section><button id="clearAll"', WEB_CARD_HTML + JRA_PDF_HTML + NUMBERS_HTML + '<section><button id="clearAll"')
            page = page.replace(
                '</body>', '<script src="/jrdb-manual-numbers.js" defer></script><script src="/jra-official-pdf.js" defer></script><script src="/jra-web-card.js" defer></script></body>')
            source, mime = {
                '/jrdb-mail-local': (page, 'text/html; charset=utf-8'),
                '/jrdb-mail-local.js': (MAIL_JS, 'text/javascript; charset=utf-8'),
                '/jrdb-mail-local.css': (MAIL_CSS + NUMBERS_CSS + JRA_PDF_CSS + WEB_CARD_CSS, 'text/css; charset=utf-8'),
                '/jrdb-manual-numbers.js': (NUMBERS_JS, 'text/javascript; charset=utf-8'),
                '/jra-official-pdf.js': (JRA_PDF_JS, 'text/javascript; charset=utf-8'),
                '/jra-web-card.js': (WEB_CARD_JS, 'text/javascript; charset=utf-8'),
            }[path]
            return response('200 OK', source, mime)
        if method == 'GET' and path == '/research-validation-demo':
            # Synthetic-only chronological holdout: no real results,
            # provider requests, model training, persistence or bets.
            return response('200 OK', render_validation_html(build_validation_review()),
                            'text/html; charset=utf-8')
        if method == 'GET' and path == '/research-batch-demo':
            # The fixture never contacts a provider, persists records, or
            # generates a live recommendation; it runs after owner auth.
            return response('200 OK', render_batch_html(build_demo_batch()),
                            'text/html; charset=utf-8')
        if method == 'GET' and path == '/research-batch-demo.css':
            return response('200 OK', BATCH_DEMO_CSS, 'text/css; charset=utf-8')
        if method == 'GET' and path in ('/day-pipeline', '/day-pipeline.css',
                                        '/day-pipeline.js'):
            data, mime = {
                '/day-pipeline': (DAY_PIPELINE_HTML, 'text/html; charset=utf-8'),
                '/day-pipeline.css': (DAY_PIPELINE_CSS, 'text/css; charset=utf-8'),
                '/day-pipeline.js': (DAY_PIPELINE_JS, 'text/javascript; charset=utf-8'),
            }[path]
            return response('200 OK', data, mime)
        if method == 'GET' and path == '/api/deploy-status':
            # On demand only; no user, JRDB, ticket, or credential payload is sent.
            return response('200 OK', inspect_owner_revision(release_sha))
        if method == 'GET' and path == '/ui-version':
            # Authenticated, no-cache diagnostic. Never expose secret values.
            sha = release_sha
            research_first = HTML.index('id="researchPanel"') < HTML.index('<h2>JRDB接続</h2>')
            return response('200 OK', (
                'KEIBA NINE\n'
                'uiVersion=' + UI_VERSION + '\n'
                'researchFirst=' + ('yes' if research_first else 'no') + '\n'
                'renderCommit=' + sha + '\n'
                'note=認証済みの配信コードの識別情報。JRDBやレースの実データは取得しません。'
            ), 'text/plain; charset=utf-8')
        if method == 'GET' and path == '/api/status':
            ready = settings.get('JRDB_PRIVATE_ENABLED') == '1' and all(settings.get(k) for k in ('JRDB_API_KEY', 'JRDB_AUTH_KEY')) and settings.get('GITHUB_ACTIONS') != 'true'
            return response('200 OK', {'jrdbConfigured': ready,
                                       'historyConfigured': bool(ready and settings.get('KEIBA_HISTORY_ENABLED') == '1'),
                                       'manualComparisonConfigured': bool(ready and settings.get('KEIBA_MANUAL_REFERENCE_ENABLED') == '1'),
                                       'livePredictionEnabled': False})
        if method == 'GET' and path == '/api/setup':
            # Strictly coarse, owner-only flags. This endpoint never pings JRDB,
            # discloses credentials, claims entitlement, or authorizes predictions.
            configured = settings.get('JRDB_PRIVATE_ENABLED') == '1' and all(
                isinstance(settings.get(k), str) and bool(settings.get(k).strip())
                for k in ('JRDB_API_KEY', 'JRDB_AUTH_KEY')) and settings.get('GITHUB_ACTIONS') != 'true'
            return response('200 OK', {
                'transport': 'https' if secure else 'local-dev',
                'jrdbConfigured': configured,
                'prestartBodyEnabled': bool(configured and settings.get('KEIBA_PRESTART_BODY_ENABLED') == '1'),
                'historyConfigured': bool(configured and settings.get('KEIBA_HISTORY_ENABLED') == '1'),
                'liveConnectionVerified': False,
                'realPredictionEnabled': False,
                'nextStep': ('本人専用のHTTPS環境でJRDB実接続を検証する' if configured
                             else 'β版の専用API認証情報と本人専用HTTPS環境を準備する'),
            })
        if method == 'GET' and path == '/api/jra/official-pdf-links':
            # One on-demand visit to the fixed JRA HTML index. Only PDF links
            # are discovered: no PDF download, runner mapping or verification.
            query = parse_qs(environ.get('QUERY_STRING', ''), keep_blank_values=True)
            if set(query) != {'date'} or len(query['date']) != 1:
                return response('400 Bad Request', {'error': '開催日を1つ指定してください。'})
            try:
                result = discover_official_pdf_links(query['date'][0])
            except JRAIndexError as exc:
                if 'Date' in str(exc) or 'date' in str(exc):
                    return response('400 Bad Request', {'error': '開催日の形式・掲載期間を確認してください。'})
                return response('502 Bad Gateway', {'error': 'JRA公式PDF一覧へ接続・解析できませんでした。後ほどJRA公式ページで確認してください。'})
            return response('200 OK', result)
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
        if method == 'GET' and path == '/api/jrdb/race-day':
            if settings.get('JRDB_PRIVATE_ENABLED') != '1' or settings.get('GITHUB_ACTIONS') == 'true':
                return response('503 Service Unavailable', {'error': 'JRDB接続はまだ有効になっていません。'})
            query = parse_qs(environ.get('QUERY_STRING', ''), keep_blank_values=True)
            if set(query) != {'date'} or len(query['date']) != 1 or not _valid_date(query['date'][0]):
                return response('400 Bad Request', {'error': '正しい開催日を1つ指定してください。'})
            try:
                date = query['date'][0]
                programme = normalize_program_rows(fetch_race_program(date), date)
                entries = fetch_horse_entries(date)
                conditions = fetch_venue_conditions(date)
                report = audit_race_day_checks(programme, entries, conditions, date)
                report['prestartFreshness'] = audit_prestart_freshness(
                    programme, conditions, date, _now_in_jst()
                )
                # No authorized independent JRA source adapter is connected
                # yet. Never accept a browser-provided snapshot or claim an
                # official check based on provider data alone.
                report['independentComparison'] = compare_independent_race_snapshot(
                    programme, entries, conditions, date, None
                )
            except (JRDBError, ProgrammeFormatError, CoverageError, RaceContextError,
                    FreshnessError, ReferenceCompareError, ValueError):
                return response('502 Bad Gateway', {
                    'error': '出走取消・馬場の資料が安全に照合できませんでした。'})
            return response('200 OK', report)
        if method == 'POST' and path == '/api/operator/factor-note':
            # Own enumerated manual input only; no JRDB request, storage, or
            # evaluation. Keep the route behind the existing owner auth.
            if (environ.get('QUERY_STRING', '')
                    or environ.get('CONTENT_TYPE', '').split(';')[0].strip().lower() != 'application/json'):
                return response('400 Bad Request', {'error': '本人入力の形式が不正です。'})
            try:
                size = int(environ.get('CONTENT_LENGTH', '0'))
                if not 0 < size <= 350:
                    raise ValueError()
                raw = environ['wsgi.input'].read(size)
                if len(raw) != size:
                    raise ValueError()
                result = validate_operator_factor_note(json.loads(raw), _now_in_jst())
            except (ValueError, TypeError, KeyError, UnicodeError):
                return response('400 Bad Request', {
                    'error': '開催日・競馬場・レース・馬番・資料項目を確認してください。'})
            return response('200 OK', result)
        if method == 'POST' and path == '/api/jrdb/compare-manual':
            # One owner-entered race only, no storage and no claiming JRA
            # authenticity. Validate the entire input BEFORE any provider call.
            if (settings.get('JRDB_PRIVATE_ENABLED') != '1'
                    or settings.get('KEIBA_MANUAL_REFERENCE_ENABLED') != '1'
                    or settings.get('GITHUB_ACTIONS') == 'true'
                    or not all(settings.get(k) for k in ('JRDB_API_KEY', 'JRDB_AUTH_KEY'))):
                return response('503 Service Unavailable', {
                    'error': '本人用の手入力照合は有効になっていません。'})
            if (environ.get('QUERY_STRING', '')
                    or environ.get('CONTENT_TYPE', '').split(';')[0].strip().lower() != 'application/json'):
                return response('400 Bad Request', {'error': 'JSON形式が必要です。'})
            try:
                length = int(environ.get('CONTENT_LENGTH', '0'))
                if not 0 < length <= 1400:
                    raise ValueError()
                raw = environ['wsgi.input'].read(length)
                if len(raw) != length:
                    raise ValueError()
                manual = validate_single_manual_reference(json.loads(raw))
            except (ValueError, KeyError, TypeError, UnicodeError, ReferenceCompareError):
                return response('400 Bad Request', {
                    'error': '手入力した開催日・レース・取消・馬場・時刻の形式を確認してください。'})
            try:
                date = manual['date']
                programme = normalize_program_rows(fetch_race_program(date), date)
                entries = fetch_horse_entries(date)
                conditions = fetch_venue_conditions(date)
                report = compare_independent_race_snapshot(
                    programme, entries, conditions, date, manual
                )
            except (JRDBError, ProgrammeFormatError, CoverageError,
                    RaceContextError, ReferenceCompareError, ValueError):
                return response('502 Bad Gateway', {
                    'error': '本人用の独立資料との比較に失敗しました。接続とデータ形式を確認してください。'})
            # Only aggregate differences; never source horse identifiers.
            return response('200 OK', report)
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
        if method == 'GET' and path == '/api/jrdb/day-pipeline':
            # Owner-initiated full-day gate: one /tra, /tky, /tcy, /tze, /tka
            # call each. Never a scheduled paid fetch or live predictor.
            if (settings.get('JRDB_PRIVATE_ENABLED') != '1'
                    or settings.get('GITHUB_ACTIONS') == 'true'
                    or not all(isinstance(settings.get(k), str) and settings[k].strip()
                               for k in ('JRDB_API_KEY', 'JRDB_AUTH_KEY'))):
                return response('503 Service Unavailable', {
                    'error': 'JRDBのβ版認証情報が未発行・未設定のため一括資料取得は停止中です。'})
            query = parse_qs(environ.get('QUERY_STRING', ''), keep_blank_values=True)
            if (set(query) != {'date'} or len(query['date']) != 1
                    or not _valid_date(query['date'][0])):
                return response('400 Bad Request', {'error': '開催日をYYYYMMDDで1つ指定してください。'})
            try:
                date = query['date'][0]
                programme = normalize_program_rows(fetch_race_program(date), date)
                entries = fetch_horse_entries(date)
                training = fetch_training_analysis(date)
                recent = fetch_recent_runs(date)
                conditions = fetch_venue_conditions(date)
                report = inspect_day(programme, entries, training, recent,
                                     conditions, date)
                freshness = audit_prestart_freshness(
                    programme, conditions, date, _now_in_jst()
                )
                report['reviewQueue'] = build_day_review_queue(report, freshness)
                report['factorProgress'] = summarize_day_factor_progress(
                    programme, entries, training, recent, date, report
                )
                report['sourceMaterials'] = summarize_day_materials(
                    programme, entries, training, recent, date, report
                )
            except (JRDBError, ProgrammeFormatError, CoverageError,
                    RaceContextError, FreshnessError, ValueError, KeyError, TypeError):
                return response('502 Bad Gateway', {
                    'error': '全レースの資料を安全に一括照合できませんでした。'})
            return response('200 OK', report)
        if method == 'GET' and path == '/api/jrdb/prestart-body':
            # Separate explicit opt-in for up to three JRDB reads: /tra,/tky,/tpd.
            # Not part of the day pipeline, not auto-polled, never uses odds.
            if (settings.get('JRDB_PRIVATE_ENABLED') != '1'
                    or settings.get('KEIBA_PRESTART_BODY_ENABLED') != '1'
                    or settings.get('GITHUB_ACTIONS') == 'true'
                    or not all(isinstance(settings.get(k), str) and settings[k].strip()
                               for k in ('JRDB_API_KEY', 'JRDB_AUTH_KEY'))):
                return response('503 Service Unavailable', {
                    'error': '直前の馬体資料取得はまだ有効になっていません。'})
            query = parse_qs(environ.get('QUERY_STRING', ''), keep_blank_values=True)
            now = _now_in_jst()
            if (set(query) != {'date'} or len(query['date']) != 1
                    or not _valid_date(query['date'][0])
                    or query['date'][0] != now[:10].replace('-', '')):
                return response('400 Bad Request', {
                    'error': '直前情報は日本時間の当日のみ、開催日を1つ選んでください。'})
            try:
                date = query['date'][0]
                programme = normalize_program_rows(fetch_race_program(date), date)
                entries = fetch_horse_entries(date)
                prestart = fetch_prestart_body(date)
                report = audit_prestart_body(programme, entries, prestart, date)
            except (JRDBError, ProgrammeFormatError, CoverageError,
                    ValueError, KeyError, TypeError):
                return response('502 Bad Gateway', {
                    'error': '当日の馬体・パドック資料を安全に照合できませんでした。'})
            return response('200 OK', report)
        if method == 'GET' and path == '/api/jrdb/one-day-trial':
            # Explicit owner-click only. Five date-scoped source reads
            # ONCE for the entire day (including venue conditions /tka),
            # not one request per race. Do not claim official JRA verification.
            if (settings.get('JRDB_PRIVATE_ENABLED') != '1'
                    or settings.get('GITHUB_ACTIONS') == 'true'
                    or not all(settings.get(k) for k in ('JRDB_API_KEY', 'JRDB_AUTH_KEY'))):
                return response('503 Service Unavailable', {
                    'error': 'JRDB β版のAPI接続がまだ有効ではありません。'})
            query = parse_qs(environ.get('QUERY_STRING', ''), keep_blank_values=True)
            if (set(query) != {'date'} or len(query['date']) != 1
                    or not _valid_date(query['date'][0])):
                return response('400 Bad Request', {
                    'error': '開催日を1つ正しく選んでください。'})
            date = query['date'][0]
            try:
                programme = normalize_program_rows(fetch_race_program(date), date)
                trial = build_day_trial(
                    programme, fetch_horse_entries(date),
                    fetch_training_analysis(date), fetch_recent_runs(date), date,
                    fetch_venue_conditions(date)
                )
            except (JRDBError, ProgrammeFormatError, CoverageError,
                    RaceContextError, ValueError, KeyError, TypeError):
                return response('502 Bad Gateway', {
                    'error': '全Rの調教・近走データを安全に照合できませんでした。'
                             'API接続または対象日の元資料を確認してください。'})
            return response('200 OK', trial)
        if method == 'GET' and path == '/api/jrdb/one-race-trial':
            # Private, user-triggered pilot only: compare TWO provisional
            # source-derived factors. Do not publish, forecast a winner,
            # create a ticket, retain provider rows or claim JRA verification.
            if (settings.get('JRDB_PRIVATE_ENABLED') != '1'
                    or settings.get('GITHUB_ACTIONS') == 'true'
                    or not all(settings.get(k) for k in ('JRDB_API_KEY', 'JRDB_AUTH_KEY'))):
                return response('503 Service Unavailable', {
                    'error': 'JRDB β版の専用API接続がまだ有効ではありません。'})
            query = parse_qs(environ.get('QUERY_STRING', ''), keep_blank_values=True)
            if (set(query) != {'date', 'track', 'race'}
                    or any(len(values) != 1 for values in query.values())):
                return response('400 Bad Request', {
                    'error': '日付・競馬場・レースを1つ選んでください。'})
            date, track, number = (query['date'][0], query['track'][0], query['race'][0])
            if (not _valid_date(date)
                    or track not in {'札幌', '函館', '福島', '新潟', '東京',
                                     '中山', '中京', '京都', '阪神', '小倉'}
                    or number not in {str(i) for i in range(1, 13)}):
                return response('400 Bad Request', {'error': 'レース指定が不正です。'})
            try:
                programme = normalize_program_rows(fetch_race_program(date), date)
                trial = build_one_race_trial(
                    programme, fetch_horse_entries(date),
                    fetch_training_analysis(date), fetch_recent_runs(date),
                    date, track, int(number)
                )
            except (JRDBError, ProgrammeFormatError, CoverageError,
                    ValueError, KeyError, TypeError):
                return response('502 Bad Gateway', {
                    'error': '調教・近走の資料を安全に自動照合できませんでした。'
                             'API接続や元資料を確認してください。'})
            return response('200 OK', trial)
        if method == 'GET' and path == '/api/jrdb/selected-readiness':
            # Single owner-triggered request with one /tra /tky /tcy /tze /tka
            # read each; only a selected race's redacted counts leave the server.
            if (settings.get('JRDB_PRIVATE_ENABLED') != '1'
                    or settings.get('GITHUB_ACTIONS') == 'true'
                    or not all(settings.get(k) for k in ('JRDB_API_KEY', 'JRDB_AUTH_KEY'))):
                return response('503 Service Unavailable', {
                    'error': '実データの安全な本人用接続がまだ有効ではありません。'})
            query = parse_qs(environ.get('QUERY_STRING', ''), keep_blank_values=True)
            if (set(query) != {'date', 'track', 'race'}
                    or any(len(values) != 1 for values in query.values())):
                return response('400 Bad Request', {
                    'error': '開催日・競馬場・レースを1つずつ選んでください。'})
            date, track, number = (query['date'][0], query['track'][0], query['race'][0])
            valid_tracks = {
                '札幌', '函館', '福島', '新潟', '東京',
                '中山', '中京', '京都', '阪神', '小倉',
            }
            if (not _valid_date(date) or track not in valid_tracks
                    or number not in {str(i) for i in range(1, 13)}):
                return response('400 Bad Request', {'error': '指定された開催日・競馬場・Rが不正です。'})
            try:
                programme = normalize_program_rows(fetch_race_program(date), date)
                report = selected_race_readiness(
                    programme, fetch_horse_entries(date),
                    fetch_training_analysis(date), fetch_recent_runs(date),
                    fetch_venue_conditions(date), date, track, int(number),
                    _now_in_jst()
                )
            except (JRDBError, ProgrammeFormatError, CoverageError,
                    RaceContextError, FreshnessError, ValueError, KeyError, TypeError):
                return response('502 Bad Gateway', {
                    'error': '対象レースの資料を安全に照合できませんでした。'})
            return response('200 OK', report)
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
        if method == 'POST' and path == '/api/jrdb/history':
            # Separate opt-in: no page load, scheduler, or public feed invokes this.
            if (settings.get('JRDB_PRIVATE_ENABLED') != '1'
                    or settings.get('KEIBA_HISTORY_ENABLED') != '1'
                    or settings.get('GITHUB_ACTIONS') == 'true'
                    or not all(settings.get(k) for k in ('JRDB_API_KEY', 'JRDB_AUTH_KEY'))):
                return response('503 Service Unavailable', {
                    'error': '本人用の過去履歴照合はまだ有効になっていません。'})
            if environ.get('QUERY_STRING', '') or environ.get('CONTENT_TYPE', '').split(';')[0].strip().lower() != 'application/json':
                return response('400 Bad Request', {'error': 'JSONで開催日を指定してください。'})
            try:
                size = int(environ.get('CONTENT_LENGTH', '0'))
                if not 0 < size <= 128:
                    raise ValueError()
                raw = environ['wsgi.input'].read(size)
                if len(raw) != size:
                    raise ValueError()
                args = json.loads(raw)
                if not isinstance(args, dict) or set(args) - {'date', 'limit'}:
                    raise ValueError()
                date, limit = args.get('date'), args.get('limit', 8)
                if not _valid_date(date) or type(limit) is not int or not 1 <= limit <= 8:
                    raise ValueError()
            except (ValueError, TypeError, UnicodeError, KeyError):
                return response('400 Bad Request', {'error': '開催日または取得上限が不正です。'})
            try:
                programme = normalize_program_rows(fetch_race_program(date), date)
                entries = fetch_horse_entries(date)
                previous = fetch_recent_runs(date)
                training = fetch_training_analysis(date)
                current_conditions = fetch_venue_conditions(date)
                preview = run_bounded_history_audit(
                    programme, entries, previous, current_conditions, date,
                    fetch_dra=fetch_historical_race_program,
                    fetch_dka=fetch_historical_venue_conditions, limit=limit,
                    training=training)
            except (JRDBError, ProgrammeFormatError, CoverageError, HistoryFetchError, ValueError):
                return response('502 Bad Gateway', {
                    'error': '過去馬場の照合に失敗しました。履歴や実接続を確認してください。'})
            return response('200 OK', preview)
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
