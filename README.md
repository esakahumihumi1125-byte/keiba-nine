# keiba-nine
競馬ナイン公式Webアプリ
競馬ナイン Webアプリ公開テスト

## 個人利用に向けた研究機能

- [評価基準・1着候補の再点検](docs/evaluation-policy.md)
- [1着候補・総合順位の取りこぼし検証（架空データ）](docs/winner-review-validation.md)
- [買い目の構成・時系列検証](docs/research-pipeline.md)
- [JRDBの非公開接続準備](docs/jrdb-private.md)
- [JRDB-API β版承認後の本人専用接続手順（2026-11-08）](docs/jrdb-api-beta-activation.md)
- [本人用10項目の資料確認・直前馬体重の件数チェック（2026-11-09）](docs/owner-ten-factor-source-inventory.md)
- [JRDB本人用の自動更新：iPhoneで最初の1回だけ行う設定](docs/jrdb-owner-automatic-deploy-once.md)
- [本人用予想のサーバー永続保存：安全な有効化・保存済み記録の読み取り](docs/owner-postgres-archive-activation.md)
- [本人認証付き接続サービスの実装と設定](docs/private-service.md)
- [本人用サーバーの設置準備](docs/private-deployment.md)
- [iPhoneだけで作る本人用・架空データ画面（Render Free・任意）](docs/render-iphone-preview.md)

合成テストと本人専用JRDB研究用の処理を実装しています。公開予想への自動連携・正式なJRA独立照合・10項目の本採点は未完成です。
`python -m unittest discover -s tests -p 'test_*.py'` で動作確認できます。

## iPhoneからの本人用プレビュー（任意）

Render用の設定を追加しています。既存プレビューとJRDB本人専用サービスは**別々に管理**してください。
プレビューには有料JRDBの認証情報を絶対に入れません。本人専用JRDBの設定・稼働・最新コミット反映はRenderで別途確認が必要です。
[Safariからの設定手順](docs/render-iphone-preview.md)を参照してください。
