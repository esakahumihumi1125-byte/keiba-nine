# iPhoneだけで本人用の架空データ画面を開く：Renderプレビュー

**ここは未設置の手順書です。** render.yamlを追加しても、外部のRenderサービスはまだ作られません。Render側の登録・作成は本人が行います。

## なぜプレビュー専用か

- Render FreeのWeb ServiceはHTTPSの**公開URL**を持ちます。Basic認証で画面を守りますが、インターネットから認証画面にはアクセス可能であり、Renderの内部限定Private Serviceとは異なります。
- **架空8頭の10項目評価・3連単テスト・設定診断のみ**を利用します。有料JRDBのAPIキー、JRDB生データ、本人の馬券記録は入れないでください。
- JRDB_PRIVATE_ENABLED=0、KEIBA_HISTORY_ENABLED=0、KEIBA_MANUAL_REFERENCE_ENABLED=0。起動設定が有効化やJRDBの秘密キーの存在を検出したら**起動を拒否**します。
- Freeは15分間アクセスしないと休止し、再起動に時間がかかることがあります。永続ファイル保存なし。無料枠の時間・帯域・ビルド時間等に制限があります。自動デプロイも無効です。

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
- Renderは自動デプロイを無効にしています。GitHubの更新を確認せずにRenderへ反映しません。
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

この手順書が存在するだけでは、デプロイやiPhone実機接続を確認したことにはなりません。
