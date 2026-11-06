# JRDB personal integration — preparation only

Status: disabled by default. No live request or credential configuration has been performed.

The current GitHub repository and Pages site are public. Neither JRDB source data
nor predictions derived from it may be placed in public feeds, commits, logs,
Actions artifacts, backups shared with others, or public web responses.
A “personal” label or an unlisted URL does not restrict access.

## Prepared client

`scripts/jrdb_private.py` contains private-only POST readers for `/v1/tra`
(programme), `/v1/tky` (horse entries), `/v1/tcy` (training), and `/v1/tze`
(previous runs). These endpoints are enabled only in an owner-authenticated private
backend. The client returns rows in memory, writes no feed files, blocks redirects,
limits response size, rejects invalid dates, and omits credentials and returned
data from error messages. Tests use synthetic responses; they are not live tests.
Provider beta endpoint paths and schemas must be reconfirmed against the issued beta
account documentation before any real request.

Official sources checked 2026-10-26:
- https://jrdb-api.keiba.bigtime.world/
- https://jrdb-api.keiba.bigtime.world/docs/authentication

## Before activation

1. Obtain the separate JRDB API beta test account and verify its current entitlement. The provider advised that the beta could be tested with a Basic subscription; the eventual production API was planned for the AI tier. These are not interchangeable with a Basic member login. Confirm the provider's latest instructions before activation.
2. Provision an owner-only backend and private storage; verify unauthenticated
   and other-user requests are denied, including direct data URLs.
3. Configure `JRDB_API_KEY` and `JRDB_AUTH_KEY` using the backend's secret manager.
   Never put their values into chat, browser HTML, GitHub commits, or public logs.
4. Only in that private backend, set `JRDB_PRIVATE_ENABLED=1`. This flag itself
   does not implement access control. GitHub Actions execution remains blocked.
5. Perform a live connection test there, then implement schema mapping and
   private prediction storage. Preserve the existing public/test ledger separately.

Public distribution of derived predictions needs separate permission/contract;
member authentication, commercial licensing and referrals must not be treated
as already available. This preparation does not enable any of them.

## Current integration boundary (2026-11-03)

- The Basic membership application and beta-account request have been submitted to the provider, but dedicated beta API credentials have not been confirmed as issued.
- Never repurpose the Basic member password as `JRDB_API_KEY` or `JRDB_AUTH_KEY`.
- No credentials are added to the public repository or GitHub Actions; there is no public race-data or derived-prediction pipeline.
- `scripts/private_service.py` exposes owner-only connectivity/coverage diagnostics, **not** operational real-data forecasting.
- Historical failed PR check notifications do not indicate current main is failing: check the current GitHub Actions result rather than relying on the old email.

## 2026-11-06: β版接続までの最短手順（本人用のみ）

2026年11月6日現在、ベーシック会員の支払いとβ版専用アカウント申請は完了しているが、**専用APIキーの発行通知は未確認**。会員ログイン用ID・パスワードはAPIのキーではない。発行までは `JRDB_PRIVATE_ENABLED=0` のままにし、プライベート接続先でも実データ試算・自動更新を実行しない。

JRDB公式認証ガイド（2026-11-06再確認）：
https://jrdb-api.keiba.bigtime.world/docs/authentication
仕様：https://jrdb-api.keiba.bigtime.world/docs/request-response

### アカウント発行後に本人が設定するもの

本人専用HTTPSのRenderサービスの **Environment／Secret** だけに設定する（値はGitHub、チャット、Safariの入力欄、公開Pages、ログ、GitHub Actionsに入れない）。

| キー名 | 設定内容 |
| --- | --- |
| `JRDB_API_KEY` | JRDB API側のアプリ共通APIキー（通常の会員IDとは異なる） |
| `JRDB_AUTH_KEY` | JRDB API側の本人専用 `x-user-key`（会員ログインパスワードと混同しない） |
| `JRDB_API_BASE_URL` | **発行時に指定された**JRDBのHTTPS接続先。従来のβ版は `https://dev.api.bigtime.world/v1`、公開ドキュメントは `https://api.bigtime.world/v1` を記載。どちらを使うかは提供元の案内に合わせる。上記2候補のみコードで許可 |
| `JRDB_PRIVATE_ENABLED` | 権限・ログイン・HTTPS・契約条件を確認してから `1` にする |

1. 配信したコード版と認証付きのサービスを照合する。β版APIの契約範囲、保存先、本人だけのアクセス制限を確認する。
2. 本人用ホームで開催日を選び、**「安全な設定診断を実行」**を押す。この段階ではAPIへ通信しない。未設定・未接続で「設定あり」と表示させない。
3. 接続設定が揃った場合だけ有効になる **「JRDB β版の接続を1回だけ確認」** を押す。新しい `GET /api/jrdb/connection-test?date=YYYYMMDD` は本人認証と私有リクエストヘッダーを必須とし、発行済みAPI資格で **`/tra` を1回だけ**読み出す。
4. 通信に成功した場合も、画面へ返すのは日付・番組R件数・「接続確認成功」と、`predictionReady=false` だけ。馬名・指数・有料生データ・キーは表示・保存・配信しない。通信エラーはHTTP 401／403／429を判別できる安全な説明だけを返す。
5. 次に既存 `/owner-auto-trial` の1R／全R研究用確認を行い、JRA公式出走表・取消・当日の馬場・予想モデル全項目を検証する。**この手順は自動予想の完成ではなく、接続確認**。実戦用3連単や予想の一般公開を自動解放しない。

`JRDB_PRIVATE_ENABLED` と認証キーが揃っただけでもAPIの権限や利用成功を意味せず、`/api/setup` は引き続き `liveConnectionVerified=false` を返す。追加された接続確認はユーザーの明示クリック時だけで、ページ表示、CI、公開アプリ、無料のRenderプレビュー、無人スケジューラからは有料APIを呼び出さない設計。

### 未完の本番機能

現時点で自動化されて**いない**もの：JRA公式の独立した出馬・取消・馬場照合、検証済み調教／近走／血統／適性／展開の全項目AI評価、全Rの本番S/A/B/C・最終3連単30〜40点・日付別自動更新と継続保存。β版接続確認とこれらの完了を混同しない。一般公開・サブスク提供はJRDBとの別途契約が前提。

**プレビュー保護（2026-11-06追加）：** `KEIBA_RENDER_PREVIEW_ONLY=1` のRenderプレビューに `JRDB_PRIVATE_ENABLED=1` を設定すると、Webアプリは意図的に起動を拒否する。これは有料・個人契約データをプレビューに投入しないための保護。β版認証後は、別途、本人だけがアクセスできるHTTPSの本番専用サービスと非公開ストレージ、キー管理、権限確認を整えてから接続を有効にする。プレビューを単純に本番として扱ったり、保護を迂回したりしない。
