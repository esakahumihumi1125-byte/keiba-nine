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

## 2026-11-05 追加：GitHub CI → Render Deploy Hookの安全な予備経路

Render上で `Auto-Deploy: On Commit` と表示されていても、GitHubの複数のpush・CI成功後に新しいRenderのDeployが自動で開始されないことを観測。原因はまだ断定できない。**毎回手動デプロイする代わりの予備経路**として、`.github/workflows/owner-render-after-checks.yml` を用意した。

### 1回だけ必要な本人の操作（Render秘密URLは絶対にチャットで共有しない）

1. 先にRenderの本人用サービス `keiba-nine-owner-preview` の **Settings → Deploy Hook** にあるURLを自分の端末でコピーする。ユーザー・パスワード・メール・会員情報と同様に秘密扱い。公開リポジトリへ貼らない。
2. [GitHubのリポジトリ設定](https://github.com/esakahumihumi1125-byte/keiba-nine/settings/secrets/actions) の **New repository secret** を開く。名前を正確に `RENDER_DEPLOY_HOOK_URL` とし、値にRenderのDeploy Hook URLを貼る。画面のスクショやチャットへURLの中身を送らない。
3. GitHub `main` で後続の新しいコミットが発生すると、`Private service checks` が成功した場合だけ、この予備ワークフローが起動する。最新HEADとテスト合格のコミットSHAが一致した場合のみ、秘密URLにPOSTでデプロイを依頼する。Renderで `live` になったことは別途確認する。
4. **予備ルートが実際に稼働したことを確認した後**、Render元来のAuto-Deployが復旧すると同じコミットで二重ビルドになる可能性がある。二重デプロイを避けるには、使用する自動化ルートを1本に揃える。GitHub Actionsフックを主とするなら、Render SettingsのAuto-DeployはOffにする。逆にRender標準連携が直ったら、GitHub ActionsのSecretを削除するかワークフローを停止する。
5. GitHub Actions `Owner Render deploy after private checks` が `RENDER_DEPLOY_HOOK_URL is not configured: deploy safely skipped.` と表示したら、設定前なので **まだ自動配信されていない**。一切の秘密はログに表示されない設計。

- **Secretがない現状ではデプロイしない（自動配信は未完成）**。
- PR・他ブランチ・失敗したCIからの配信は禁止。最新のmain以外の古いテスト合格コミットはスキップする。
- GitHubのワークフローはコードの配信手順だけを管理し、JRDB・馬番・馬券・購入記録・本人のログイン情報は読み取らない。
- Deploy Hookは本人が知る人だけが持つ秘密。万一漏れたらRenderでRegenerate Hookし、GitHubのSecretを新しい値へ更新する。

参考：[Render Deploy Hooks](https://render.com/docs/deploy-hooks)。

## Deploy Hook 登録後の動作検証（2026-11-06）

本人が GitHub リポジトリ Secret の追加完了画面を確認後、次回の `main` コミットで `Private service checks` と `Owner Render deploy after private checks` を実行し、最新SHAがRenderで `live` になったことを確認する。**GitHub上の秘密設定の登録成功だけでは、正常な自動デプロイは保証しない。**

- `Private service checks` の成功 → 後段ワークフローの **実行ログ** に `Render deploy hook accepted the request` が実行結果として表示される（ソースコード表示やechoコマンド表示ではなく実行結果を確認）。
- 次に Render の最新デプロイ `status=live` とGitHub HEADのコミットSHAが一致するかを確認する。ビルド失敗・キャンセル時は成功と報告しない。
- 不要な二重デプロイを避けるため、Renderネイティブの自動更新が後で復旧した場合は標準のGitHub連携かGitHub Actions Deploy Hookのどちらか一方に統一する。
- Deploy HookのURL、JRDBなどの会員情報、サービスのログイン情報はリポジトリ・CI出力・チャットに表示しない。
