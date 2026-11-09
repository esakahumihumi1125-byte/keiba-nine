# 本人用JRDBアプリの自動更新：最初の1回だけ行う設定

更新日：2026-11-09

## 対象を間違えない

- **対象サービス**：`keiba-nine-owner-jrdb`
- **対象サービスID**：`srv-dbo1m515efls73cl39s0`
- **Renderダッシュボード**：https://dashboard.render.com/web/srv-dbo1m515efls73cl39s0
- **本人用アプリ**：https://keiba-nine-owner-jrdb.onrender.com
- **GitHubリポジトリ**：https://github.com/esakahumihumi1125-byte/keiba-nine
- **登録するGitHub Actions Secret名**：`RENDER_JRDB_DEPLOY_HOOK_URL`

`keiba-nine-owner-preview` および `keiba-nine-owner-preview-mvxz` は別サービス。そちらのDeploy HookやAPIキーを登録しない。

## iPhoneのSafariから行うこと

1. [JRDB本人用サービスのRender画面](https://dashboard.render.com/web/srv-dbo1m515efls73cl39s0) を開いて、**Settings → Deploy Hook** を探す。対象サービス名が `keiba-nine-owner-jrdb` であることを先に確認する。
2. Renderで**Deploy Hook URLだけ**をコピーする。このURLは秘密なので、スクリーンショット、チャット、メール、GitHubのソースコードに貼らない。
3. [GitHub Actions Secrets設定](https://github.com/esakahumihumi1125-byte/keiba-nine/settings/secrets/actions) を開き、**New repository secret** を押す。
4. **Name** に `RENDER_JRDB_DEPLOY_HOOK_URL` と入力。**Secret** にさっきコピーした本人用サービスのDeploy Hook URLを貼り、**Add secret** で保存する。値を画面に共有しない。

## 自動更新の初回実地検証

秘密URLの登録後、リポジトリの `main` に安全な更新を入れ、
`Private service checks` → `Owner Render deploy after private checks / deploy-jrdb` →
Render `keiba-nine-owner-jrdb` の順で確認する。

検証は **Render APIからの手動デプロイを使わない**。
GitHub Actionsで `DEPLOY REQUEST SENT` となり、Render上で同じSHAが
`Live` になった場合だけ自動更新成功と判断する。
`SKIPPED` / `BLOCKED` / `failure` は未成功。
Secretの値・Deploy Hook URLを診断ログやチャットに転載しない。

## 登録後の確認方法

Secretを追加しただけでは、過去に完了したGitHub Actionsは自動で再実行しない。**次のmainへのコード更新**をきっかけに動く。

1. GitHub Actionsの **Private service checks** の合格を確認する。
2. 続く **Owner Render deploy after private checks → deploy-jrdb** を確認する。設定がなければ `SKIPPED`。Secretがプレビュー用サービスのものなら、**不一致としてBLOCKED** する。
3. `DEPLOY REQUEST SENT` はまだ配信成功ではない。[RenderのDeploys](https://dashboard.render.com/web/srv-dbo1m515efls73cl39s0) で**LiveとなったコミットSHA**がGitHub `main` と一致して初めて最新版と判定する。
4. 本人用アプリのログイン後、配信中の版を照合する。接続しているJRDBの実データ・10項目予想が完成している意味ではない。

## なぜこの設定が必要か

2026-11-09に、Renderのサービス設定は `autoDeploy=yes` / `autoDeployTrigger=commit` なのに、GitHubの新規コミットでは本人用JRDBのデプロイが開始されない現象を確認。前回はRender APIからの手動再デプロイで最新版を反映した。根本原因はまだ未確定で、公開GitリポジトリのURLだけで作成したサービスや、GitHub Appの接続権限の問題も候補になる。

安全な代替経路として `.github/workflows/owner-render-after-checks.yml` に、Previewとは**独立した**JRDB専用のデプロイ処理を追加した。Secretが未登録なら一切リクエストを送らない。**必ずテスト合格済み・最新mainだけを対象とし、予想データ・有料JRDBキー・ログインパスワードを扱わない。**

ネイティブ自動デプロイが復旧した場合は、2経路で二重デプロイしないようRenderとGitHub Actionsのどちらか片方に統一する。RenderのGitHub接続状態は **Settings → Git Credentials**、GitHub連携自体は https://render.com/docs/git-provider を参照。

参考：Render公式 https://render.com/docs/deploy-hooks 、GitHub Actions SecretsとDeploy Hooksの連携を説明。
