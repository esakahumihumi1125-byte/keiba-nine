"""Owner-only, iPhone-friendly setup page for an OPTIONAL Gmail digest bridge.

UI never reads, renders, or stores credential values. Its code-copy endpoint
serves public Apps Script source; the owner must authorize Gmail and add Render
environment secrets in the providers' own UIs.
"""
HTML = r'''<!doctype html><html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="theme-color" content="#09172b"><title>競馬ナイン｜直前メールの自動連携</title><link rel="stylesheet" href="/owner-gmail-setup.css"></head><body><main><a href="/owner-preday-forecast">← 今日の予想へ戻る</a><h1>Gmail直前メール連携</h1><p class="intro">ChatGPTでは既にGmailを確認できます。ただし本人用アプリへの自動配信は別の許可が必要です。iPhoneでも初回設定ができます。</p><section><h2>接続状況</h2><p id="setupStatus" role="status">接続を確認しています。</p><button type="button" id="setupCheck">接続状況を再確認</button></section><section><h2>① Gmailから読み込むコードをコピー</h2><p>次のボタンでGoogle Apps Script用のコードをコピーできます。まだGmailの権限は使いません。</p><button type="button" id="setupCopy">Apps Scriptコードをコピー</button><p id="copyStatus" role="status"></p><textarea id="setupCodeFallback" rows="6" readonly hidden aria-label="コピー用コード"></textarea><p><a href="https://script.google.com/home/projects/create" target="_blank" rel="noopener noreferrer">Google Apps Scriptを開く</a> → 新規プロジェクトのコード欄に貼り付けて保存。</p></section><section><h2>② Google側の許可（初回だけ）</h2><p>Apps Scriptで関数 <code>createKeibaBridgeToken</code> を実行し、続けて <code>installKeibaMailTrigger</code> を実行。自分のGmailを読む許可を与えます。</p><p>プロジェクト設定の「スクリプト プロパティ」で <code>KEIBA_BRIDGE_TOKEN</code> を確認してコピー。<strong>秘密トークンをこのチャットへ貼り付けないでな。</strong></p></section><section><h2>③ 配信URLを作る</h2><p>Apps Scriptの「デプロイ」→「新しいデプロイ」→「ウェブアプリ」。実行ユーザーは「自分」、アクセスできるユーザーは「全員」にする。発行された <code>/exec</code> で終わるURLを控える。</p><p class="warning">URL自体は外部からアクセスできますが、秘密トークンが一致しない限り情報は返しません。公開URLを使いたくなければ設定を中止して手動メモ運用のままにできます。</p></section><section><h2>④ Renderに2項目だけ登録</h2><p><a href="https://dashboard.render.com/web/srv-dbl61lijnfac73emrshg" target="_blank" rel="noopener noreferrer">本人用Renderの設定を開く</a> →「Environment」で次の2つを追加し、保存します。</p><p><code>KEIBA_MAIL_BRIDGE_URL</code> = ③のURL</p><p><code>KEIBA_MAIL_BRIDGE_TOKEN</code> = ②の秘密トークン</p><p class="warning">既存の環境変数は削除・上書きしないでな。秘密トークンはRenderに直接入力し、GitHubやチャットに送らないでください。</p></section><section><h2>連携が動くとどうなる？</h2><p>メールを約1分間隔でチェックし、馬場・パドック注目馬番・受信時刻だけを本人用予想画面へ表示します。発走2分前を過ぎて新規取り込みは行わず、予想や購入記録を自動変更しません。</p><p class="muted">Googleのトリガー実行時刻にずれや制限があるため、必ず発走前に更新できる保証はありません。JRDBの利用条件にも従ってください。</p><p><a href="/owner-preday-forecast">今日の予想を見る</a></p></section></main><script src="/owner-gmail-setup.js" defer></script></body></html>'''
CSS = r'''*{box-sizing:border-box}html{color-scheme:dark}body{margin:0;background:#09172b;color:#eef4fb;font:15px/1.7 system-ui,sans-serif}main{max-width:670px;margin:0 auto;padding:20px 15px 50px}h1{font-size:24px;color:#f3d189}h2{font-size:18px;color:#ffdd95}a{color:#f2d181}section{margin:15px 0;background:#152e48;border:1px solid #5a7994;border-radius:13px;padding:15px}code{color:#f4db9d;overflow-wrap:anywhere;font-size:13px}button{padding:12px 16px;background:#f0ce7f;border:0;border-radius:10px;color:#18233b;font-weight:bold;font-size:16px}textarea{width:100%;background:#10263d;color:#ebf2fa;font:12px monospace;white-space:pre;overflow:auto}p{overflow-wrap:anywhere}.muted{color:#bfcfe1;font-size:13px}.warning{background:#2e2a24;border:1px solid #a48445;border-radius:9px;padding:10px;color:#ffe3ab}.intro{font-size:14px;color:#cddbec}'''
JS = r'''(()=>{'use strict';
const $=id=>document.getElementById(id);
async function check(){
 $('setupStatus').textContent='接続を確認しています…';
 try{
  const res=await fetch('/api/owner-live-notes',{
   credentials:'same-origin',cache:'no-store',
   headers:{'X-Keiba-Request':'private','Accept':'application/json'}});
  if(!res.ok)throw Error('status');
  const data=await res.json(),sync=data?.sync;
  if(sync?.configured&&sync.status==='接続済み')
   $('setupStatus').textContent='Gmail自動連携：接続済み。前日予想への自動上書きはしません。';
  else if(sync?.configured){
   const reason={
    calendar:'本日の予想データが見つからないか、開催日が一致していません。',
    rejected:'Google側でリクエストが拒否されました。新しいトークンと公開設定を確認してください。',
    http:'GoogleへのアクセスがHTTPエラーになりました。WebアプリURLと公開設定を確認してください。',
    http_401:'HTTP 401：Google側で未認証として拒否されました。「アクセスできるユーザー」が「全員」か確認してください。',
    http_403:'HTTP 403：Google側でアクセス拒否です。「アクセスできるユーザー」が「全員」か確認してください。',
    http_404:'HTTP 404：URLのデプロイが見つからないか、Google側で一時的に応答を取得できません。URLとデプロイ状態を確認してください。',
    http_405:'HTTP 405：GoogleでPOSTリクエストが受け付けられていません。デプロイとdoPost関数を確認してください。',
    http_429:'HTTP 429：Google側の要求回数制限です。追加操作せず時間をおいて確認してください。',
    http_5xx:'HTTP 5xx：Google側の処理に問題があります。設定を変えず、あとで再確認してください。',
    non_json:'Googleから予期しない応答が返りました。Webアプリの公開設定やURLを確認してください。',
    network:'Googleへの通信が失敗またはタイムアウトしました。再確認してください。',
    format:'Googleから受け取った情報が検証条件に合っていません。'
   };
   $('setupStatus').textContent='連携設定あり。'+(reason[sync.issue]||'データ取得に問題があり、再確認が必要です。');
  }
  else $('setupStatus').textContent='まだGmail自動連携は未設定です。ChatGPTのGmail接続とは別に初回設定が必要です。';
 }catch(_){$('setupStatus').textContent='接続状況を確認できません。本人用アプリにログインして再試行してください。';}
}
async function copy(){
 const b=$('setupCopy');b.disabled=true;
 $('copyStatus').textContent='コピー用コードを確認中…';
 try{
  const r=await fetch('/api/owner-gmail-script-code',{
   credentials:'same-origin',cache:'no-store',
   headers:{'X-Keiba-Request':'private','Accept':'text/plain'}});
  if(!r.ok)throw Error('read');
  const code=await r.text();
  if(code.length<1000||code.length>25000||!code.includes('installKeibaMailTrigger'))
   throw Error('source');
  try{
   if(!navigator?.clipboard?.writeText)throw Error('unsupported');
   await navigator.clipboard.writeText(code);
   $('copyStatus').textContent='コピーできたで！ Google Apps Scriptのコード欄へ貼り付けてな。';
  }catch(_){
   const box=$('setupCodeFallback');box.hidden=false;box.value=code;box.focus();box.select();
   $('copyStatus').textContent='自動コピーできなかったので、下のコード欄を長押しして「コピー」を選んでな。';
  }
 }catch(_){$('copyStatus').textContent='コピー用コードを取得できません。GitHubのCode.gsからコピーしてください。';}
 finally{b.disabled=false;}
}
$('setupCopy').onclick=copy;$('setupCheck').onclick=check;check();
})();'''
