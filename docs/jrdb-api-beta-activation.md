# JRDB-API β版：本人専用の安全な接続手順（2026-11-08）

JRDBからの2026-11-08の通知でβ版テストユーザー登録完了。
ログイン済みのダッシュボードで「有料会員」、APIキー、本人専用認証キーを確認できた。
**実際のJRDB APIへの通信・本番予想完成は未確認。**

## 重要：既存Renderプレビューとは別サービス

既存の `keiba-nine-owner-preview` はプレビュー専用。ここにJRDBの
`JRDB_API_KEY` または `JRDB_AUTH_KEY` を絶対に設定しないこと。
`deploy/render-gunicorn.py` は有料API認証情報があれば起動を拒否する。

本番接続のために **別の本人用HTTPS Render Web Service** を作る。
既存のプレビュー、GitHub Pages、記録、Googleシート、Gmailブリッジは
そのまま保持する。無料枠でもWebサービスURL自体はインターネットへ公開されるため、
本人認証を必須にする。無認証のデータAPIアクセスは禁止。

## 2026-11-08 15:47 JST 現在の作業状況

無料の別サービス `keiba-nine-owner-jrdb` を作成済み：
https://dashboard.render.com/web/srv-dbo1m515efls73cl39s0

ビルド成功を確認。起動は `KEIBA_OWNER_PASSWORD` 未設定で意図どおり停止。
現時点ではJRDB-API認証情報は一切設定していない。
既存プレビューは別サービスとして継続稼働中。

**本人が次に設定するものは**新サービスの
`KEIBA_OWNER_PASSWORD`（強力なランダム値）、
`JRDB_API_KEY`、`JRDB_AUTH_KEY` の3つ。
それぞれRenderのEnvironmentの非公開入力欄だけに入れる。
その後 `JRDB_PRIVATE_ENABLED` を `1` にする。
これらの値はチャット・GitHub・スクリーンショットに出さない。

## 新しいRenderサービスの作成

Render Dashboard → New → Web Service → このGitHubレポジトリの `main`。

- サービス名例：`keiba-nine-owner-jrdb`（既存のプレビューとは異なる名前）
- Runtime: Python、Plan: Free（課金プランへの変更は本人が判断）
- Build Command: `pip install -r deploy/render-requirements.txt`
- Start Command: `gunicorn --config deploy/render-owner-private.py`
- Auto Deploy: On（既存のプレビューとは別に構成）
- 既定のルートディレクトリを使う。RenderがHTTPSを終端する想定。

初回のRender Environmentは次のとおり。表示してよい値のみ記載する。

| 環境変数 | 設定値 |
| --- | --- |
| `KEIBA_RENDER_PRIVATE_ONLY` | `1` |
| `KEIBA_RENDER_PREVIEW_ONLY` | `0` |
| `JRDB_PRIVATE_ENABLED` | `0`（最初は必ず無効） |
| `JRDB_API_BASE_URL` | `https://api.bigtime.world/v1` |
| `KEIBA_ALLOW_LOCAL_HTTP` | `0` |
| `KEIBA_HISTORY_ENABLED` | `0` |
| `KEIBA_MANUAL_REFERENCE_ENABLED` | `0` |
| `KEIBA_OWNER_USERNAME` | `owner` |
| `KEIBA_OWNER_PASSWORD` | Renderの非公開欄で強いランダムな32文字以上を設定 |

**パスワードをこのチャットやGitHubに貼らない。**
新しいサービスのパスワードは既存プレビューと別でもよい。
パスワードなし・弱いパスワード・プレビュー設定のままでは起動拒否。
デプロイしたら、本人ログインと `/api/setup` の「未設定」をまず確認する。

## API認証情報を設定する（上記ログイン確認後）

新しい**JRDB本人専用サービスだけ**のRender Environmentに、
JRDBダッシュボードに表示された値を貼る。

| 環境変数 | 入れる値 |
| --- | --- |
| `JRDB_API_KEY` | 「APIキー」（URLの `?api_key=` 用） |
| `JRDB_AUTH_KEY` | 「認証キー」（HTTP `x-user-key` 用、本人専用） |
| `JRDB_PRIVATE_ENABLED` | 上記2つを非公開欄に保存した後、`1` に切り替える |

ダッシュボードのAPIキー・認証キーはブラウザーのアプリ画面、
スクリーンショット、GitHub、Googleシート、ChatGPTの本文に貼らない。
サービスに登録した値をチャットで確認しない。

その後、本人認証済み画面で開催日を選び、`JRDB β版の接続を1回だけ確認`
を本人が押す。これは **/traの番組データ1回だけ**を読み取り、
接続の成功有無と件数だけを表示する。取得した元データは公開しない。
接続が失敗した場合は、401（キー不一致）／403（会員権限や期限）／429
（頻度制限）の区別だけを確認し、秘密情報やレスポンス本文をログに出さない。

**注意：**接続成功は総合S/A/B/C、全36R最終予想、3連単、回収率集計の
実装完了を意味しない。公式JRA出走・取消・馬場を独立照合してから
実戦モデルへ接続する。

## 利用条件と期限

2026-11-08のJRDB案内では、β版は正式提供開始前まで無料（会員条件内）。
12日で認証キーが期限切れになる。期限切れ時は
JRDBダッシュボードで認証キーを再発行し、Render側のみ差し替える。

データの再配布や第三者提供は禁止、β期間中の有料予想販売は禁止。
外部公開・サブスク提供は契約と利用許諾を別途確認する。
実データ保存・履歴大量取得・公衆公開機能は、この接続確認の段階では無効。

JRDBから案内された参考：
- https://jrdb.com/member/auth/index.php?to=api
- https://api.jrdb.com/terms/tester
- https://jrdb-api.keiba.bigtime.world/docs/authentication
