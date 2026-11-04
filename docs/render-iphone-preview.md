# iPhoneだけで本人用の架空データ画面を開く：Renderプレビュー

**ここは未設置の手順書です。** render.yamlを追加しても、外部のRenderサービスはまだ作られません。Render側の登録・作成は本人が行います。

## なぜプレビュー専用か

- Render FreeのWeb ServiceはHTTPSの**公開URL**を持ちます。Basic認証で画面を守りますが、インターネットから認証画面にはアクセス可能であり、Renderの内部限定Private Serviceとは異なります。
- **架空8頭の10項目評価・3連単テスト・設定診断のみ**を利用します。有料JRDBのAPIキー、JRDB生データ、本人の馬券記録は入れないでください。
- JRDB_PRIVATE_ENABLED=0、KEIBA_HISTORY_ENABLED=0、KEIBA_MANUAL_REFERENCE_ENABLED=0。起動設定が有効化やJRDBの秘密キーの存在を検出したら**起動を拒否**します。
- Freeは15分間アクセスしないと休止し、再起動に時間がかかることがあります。永続ファイル保存なし。無料枠の時間・帯域・ビルド時間等に制限があります。自動デプロイは **GitHubのCIチェック成功後に有効** となる設定です。ただし既存サービスがBlueprintと同期されていなければRender側の設定変更も必要です。

## Safariからの準備手順

1. Safariで[競馬ナインをRenderへ任意デプロイ](https://render.com/deploy?repo=https://github.com/esakahumihumi1125-byte/keiba-nine)を開きます。
2. Renderに登録・ログインし、GitHubの esakahumihumi1125-byte/keiba-nine のBlueprintを確認します。サービスは keiba-nine-owner-preview の**Free**プラン1つだけ。有料プランが表示された場合、選ばずに内容を再確認します。
3. RenderダッシュボードのEnvironmentで KEIBA_OWNER_PASSWORD の値を確認します。Renderがランダム生成した値で、GitHubに保存されません。必要ならRender内で秘密の長いパスワードに変更します。**ChatGPTやGitHub Issueへ貼らないでください。**
4. Renderで割り当てられたHTTPS URL（末尾 .onrender.com）をSafariで開きます。Basic認証のユーザー名は owner、パスワードは手順3の値です。
5. 画面の「安全な設定診断を実行」または「架空8頭で動作確認」を押します。「JRDBは未設定」が正常です。**実レース予想やJRDB照合はまだ動きません。**

「Deploy」を押すと外部サービスのリソースが実際に作られます。料金条件・枠・課金設定はRender側で必ず確認してください。停止・削除もRenderの画面で行います。

## セキュリティの注意

- Basic認証はSafariに資格情報が残る場合があり、独立したログアウト・多要素認証はありません。Renderアカウントには二段階認証を使い、パスワードを使い回さないでください。
- URLを知る第三者も認証画面には到達できます。秘密が漏れた場合、RenderのEnvironmentで直ちにパスワードを更新してください。
- このGunicorn設定は、RenderのTLSエッジが届く場合に限り転送プロトコルを信用します。**直接ポートへ外部から接続できるVPSには流用しないでください。**
- RenderはGitHubの自動テスト成功後に自動デプロイする設定です。既存サービスではRender側の設定と整合しているか確認してください。
- WSGIアクセスログを無効にしていますが、Render側で保持されるプラットフォームログや試行制限の詳細までは保証しません。
- paid APIを使いたい場合は、利用条件・秘密情報管理・出走データの取り扱いを別の非公開環境で見直します。このプレビューへ課金APIの認証情報を登録しないでください。

## 困ったら

| 状態 | 確認事項 |
| --- | --- |
| 認証画面 | ユーザー名 owner。パスワードはRenderのEnvironmentで確認 |
| 401 Unauthorized | パスワードやユーザー名の誤入力 |
| 426 Upgrade Required | https:// のURLを使っているか、RenderのTLS設定に問題がないか確認 |
| 最初の表示が遅い | 無料サービスがスリープしている可能性 |
| JRDBボタンが無効 | **正常**。実データは接続しない設計 |
| デプロイ失敗 | RenderのDeploy/Logsを確認し、秘密情報は第三者に転送しない |

参考資料：[Blueprint仕様](https://render.com/docs/blueprint-spec)、
[Web Service](https://render.com/docs/web-services)、
[無料プラン](https://render.com/docs/free)、
[デプロイリンク](https://render.com/docs/deploy-to-render)、
[環境変数](https://render.com/docs/configure-environment-variables)、
[Gunicornプロキシ設定](https://gunicorn.org/reference/settings/)。

## 2026-11-04：本人用プレビューの実機確認と画面改良

本人のiPhoneからRenderのサービスがLiveであること、`owner`認証で本人用画面を開けたこと、架空8頭の計算で36点／3,600円が表示されたことを確認しています。
これは**実レース予想や有料JRDB接続の成功ではありません**。

架空データの研究画面は、日常のiPhone操作向けに次を改善しました。

- 総合評価順を一頭ずつ読みやすいカード形式で表示。**Aランクは赤**、S/B/Cも区別。
- 1着・2着・3着の候補、3連単の点数・100円ずつの金額を先に表示。
- 各着順に表示した馬のすべての掛け合わせが実際の買い目とは限りません。**本当に生成した買い目だけを折りたたみ詳細で確認**。
- 長いJSON入力欄・ファイル選択は「開発者向け」詳細内に格納。架空テスト表示は常に明記。
- 計算・実レース、公開予想、馬券購入、記録・Googleバックアップは分離したまま。

**Render側の更新について：** 以下は自動デプロイ有効化前の手順です。
GitHubの改良が本体`main`に反映されたあと、Renderの
[keiba-nine-owner-preview-mvxz](https://keiba-nine-owner-preview.onrender.com)
を管理画面から開き、**Manual Deploy → Deploy latest commit** を1回実行してください。
最新のデプロイがLiveになったらSafariでページをリロードします。
「Restart service」では最新コードになりません。
パスワードやRenderの環境変数を再入力する必要はありません。
勝手に有料プランへ変更したり、実データのキーを設定したりしないでください。

[Render公式：手動デプロイ](https://render.com/docs/deploys#manual-deploys)

この手順書が存在するだけでは、デプロイやiPhone実機接続を確認したことにはなりません。

## 古い画面のままの場合：実際の配信版を確認

再デプロイが成功しても「JRDB接続」が先頭のままなら、これ以上むやみにキャッシュ消去・パスワード変更・再デプロイを繰り返さないでください。

本人ログイン済みの状態で [配信版の確認](https://keiba-nine-owner-preview.onrender.com/ui-version) を開きます。最新版なら `uiVersion=iphone-mobile-navigation-20261104-v4`、`researchFirst=yes` が表示されます。Renderの提供するコミット番号があれば先頭12桁だけ確認できます。秘密キーは表示されません。

続けて [別パスの新しい画面](https://keiba-nine-owner-preview.onrender.com/preview-v2) を開きます。通常のトップページと同じ画面を、以前のURLとは別のパスから取得します。URLのクエリだけの変更とは異なります。

`/ui-version` が404の場合、アクセス先で新しいコードが動いていない可能性があります。その場合はRenderダッシュボードの対象Webサービスとデプロイ履歴のSOURCEコミット番号を先に確認し、実際の提供URLとの食い違いを調べます。ログインが必要な本人専用機能であり、JRAやJRDBのデータ通信を増やしません。


## 2026-11-04：iPhone用の最上部ナビゲーション

本人用画面の先頭に **予想デモ／レース選択／資料チェック／接続・設定**
の４つのジャンプ項目を追加し、実戦データ未接続の状態を常時明示します。
画面の下方にある複数の開発用ツールへ何度も長くスクロールせず移れます。
Sランクのゴールド・Aランクの赤、架空８頭テスト、手入力資料チェック、
JRDBボタンの安全な無効化、Basic認証は変更していません。

この修正をGitHubの `main` に反映しても、**Render側の既存設定がOFFなら**
実機の画面はまだ変わりません。Renderダッシュボードの対象サービス
`keiba-nine-owner-preview` を開き、**Manual Deploy → Deploy latest commit**
を選択すると、同じ環境変数とパスワードのままコードを更新できます。
更新後に配信版確認 `/ui-version` で
`uiVersion=iphone-mobile-navigation-20261104-v4` を確認してください。


## 2026-11-04：自動デプロイを有効化

ユーザーの希望により、`render.yaml` の `autoDeployTrigger` を
`checksPass` に変更しました。GitHubの `main` が更新され、
GitHub Actions等の CI チェックがすべて成功した場合に限り
Renderが自動デプロイを開始する設定です。設定は `commit` より安全で、
テスト失敗時の自動反映を防ぎます。

**既存のRenderサービスでの適用は別途確認が必要です。**
このGitHub変更だけで、すでに存在するRenderサービスの Settings が
切り替わったとは限りません。Render Dashboard のサービス
`keiba-nine-owner-preview` → **Settings → Auto-Deploy → After CI Checks Pass**
を選んで保存してください。Blueprint管理のサービスならBlueprint syncで
設定を同期できます。Render側の実設定はGitHubから読み取れません。

**認証について**：自動デプロイはBasic認証を省略する機能ではありません。
`KEIBA_OWNER_PASSWORD` はRenderのEnvironmentに保存する設定で、
`render.yaml` の `generateValue: true` は変更していません。
認証の問題が解消するとは限らず、パスワードをGitHubやChatGPTへ
貼り付けないでください。月額課金データの接続や本番予想も無効のままです。


## 2026-11-04：本人用ログイン画面と正しいサービスURL

2026年11月4日に本人が共有した Render の Web Service 管理画面には
`keiba-nine-owner-preview` のURLとして
`https://keiba-nine-owner-preview.onrender.com` と表示されています。
以前の `-mvxz` 付きリンクは別サービスURLの可能性があるため、
本人が確認したリンクに統一しました。**URLの食い違いは認証失敗の可能性が
ありますが、原因を断定できるものではありません。**

本人用プレビューは新しい `/login` ページから
`KEIBA_OWNER_USERNAME`（既定 `owner`）と
**既存の** `KEIBA_OWNER_PASSWORD` を入力できるようになりました。
パスワードそのものは変更していません。
RenderのログインパスワードやGitHubログインとは別です。

ログイン成功後は、HttpOnly / Secure / SameSite=Strict の
署名付きCookieで最長7日間セッションを保持します。別のiPhone、
プライベートブラウズ終了、Cookie削除、7日経過では再ログインが必要です。
Render側でパスワードを更新すると古いCookieは無効になります。
旧Basic認証はAPIや既存の互換クライアント向けに残します。

- 入力したパスワードはGitHub、公開Pages、Cookie、URLやレースデータへ記録しません。
- 401が続く場合は **正しいサービスのRender Environmentで**
  `KEIBA_OWNER_PASSWORD` の設定状態を確認します。値をスクショ・チャットへ
  送らないでください。自動デプロイ設定を変えてもパスワードは変わりません。
- Cookieは個人端末のSafariにのみ保持されます。共有端末では使用しないでください。
- 公開URLの認証画面が表示されても、実戦予想・JRDB有料APIは有効になりません。

**反映確認**： GitHubのPR統合とCI成功だけでは、Renderへの最新版配信は
確認できません。Renderサービスで最新コミットのLiveを確認してください。
