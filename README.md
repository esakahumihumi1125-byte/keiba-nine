# keiba-nine
競馬ナイン公式Webアプリ
競馬ナイン Webアプリ公開テスト

## 個人利用に向けた研究機能

- [評価基準・1着候補の再点検](docs/evaluation-policy.md)
- [買い目の構成・時系列検証](docs/research-pipeline.md)
- [JRDBの非公開接続準備](docs/jrdb-private.md)
- [本人認証付きの接続確認サービス（未設置）](docs/private-service.md)
- [本人用サーバーの設置準備](docs/private-deployment.md)
- [iPhoneだけで作る本人用・架空データ画面（Render Free・任意）](docs/render-iphone-preview.md)

研究機能は架空データ限定で、公開予想には未接続です。
`python -m unittest discover -s tests -p 'test_*.py'` で動作確認できます。

## iPhoneからの本人用プレビュー（任意）

Render用のBlueprintを追加しています。**Renderのアカウント操作と作成はまだ行っていません**。
サービスはBasic認証で保護する公開URLの架空データ研究画面であり、有料JRDBの実データ取得と本番のJRA予想は起動時に無効化します。
[Safariからの設定手順](docs/render-iphone-preview.md)を参照してください。
