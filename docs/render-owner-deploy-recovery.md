# 本人用Renderサービス：GitHub最新との差分を解消する手順

## 2026-11-05に観測した事実

- **利用するホーム画面のサービスは `keiba-nine-owner-preview`**。似た名前の `keiba-nine-owner-preview-mvxz` とは別。
- 本人用サービスは `main`、Auto-Deploy = `yes`、Auto-Deploy Trigger = `checksPass` と表示された。
- Render Deploysでは `4c7f36010fee`（09:16 UTC）の配信が `live`。この時点のGitHub `main` はすでにさらに進んでおり、**CIが通っただけではRenderの新コードは配信されていなかった**。
- この観測のみでは原因を断定できない。GitHubの連携権限、サービスが「Public Git Repository URL」として作られたかどうか、Renderの自動デプロイ設定、すべてのGitHub Checksの状態を確認する。

## 一度だけ確認する接続と配信

1. Render Dashboardで **`keiba-nine-owner-preview`** を開く（別名の `-mvxz` は操作しない）。
2. **Settings → Git Credentials** で、接続元がGitHubアカウントの認証済みリポジトリ `esakahumihumi1125-byte/keiba-nine` か確認。公開リポジトリのURLだけを入力して作成したサービスには、Render公式上「自動デプロイ」は適用されない。必要なら Account Settings → Account Security → Git Deployment Credentials から GitHub を接続し、サービスに権限を割り当てる。
3. **Settings → Auto-Deploy** はGitHub連携が有効になってから **After CI Checks Pass** を使用。GitHubの最新コミットの Private service checks と Pages 等に `failure`・`cancelled` があれば、そのコミットのCI完了判定に注意。問題が残る場合は原因を特定してから On Commit を選ぶか判断する（CIゲートを外すことになる）。
4. **Deploys → Manual Deploy → Deploy latest commit** で、GitHub `main` の最新版を1回配信する。これは現在の自動デプロイ停止を補う一時措置。歴史的な特定SHAでのデプロイではない。部署者が実行し、新しい `live` のコミットSHAを確認する。
5. 本人用トップの **「配信中の版を照合」** は、ログイン後かつ本人がボタンを押した時だけ、Render配信中SHAとGitHub `main` の公開SHAを比較する。返り値は `current` / `behind` / `unknown`。ネットワーク不通・GitHub制限・Render SHA未報告では `unknown` と表示し、「最新」とは主張しない。
6. iPhoneホーム画面の本人用アプリを閉じて開き直し、変更が反映されているか確認する。iPhoneのSafari/ホーム画面版は端末内保存領域が別の場合があるので、JSONバックアップを先に残す。

## セキュリティと実戦利用の境界

- GitHubの公開コミット情報だけを照合。JRDBの会員・メール・API認証、馬番、買い目、購入記録は送信しない。
- 版チェック自体にはデプロイ権限がなく、勝手にサービスをデプロイしない。
- Render配信一致は、実レースのJRA照合、JRDBのAPI有効化、AI予想の精度・完成を意味しない。

参考：
- https://render.com/docs/deploys
- https://render.com/docs/git-provider
