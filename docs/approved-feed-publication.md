# KEIBA NINE｜承認済み予想の自動掲載（準備）

## 現状
- BETA 5.1 の公開画面は `keiba-nine-auto-feed.json` の読み込みに対応済み（画面表示中は約5分間隔で再確認）。
- GitHub Actions による更新用ワークフローと、検証用 Python プログラムを追加。
- **実データの自動取得元／分析サーバーは未接続。現状では新しい予想は自動生成されない。**
- 未設定の間は実行しても公開JSONを変更しない。既存アプリ・Googleバックアップ・購入/成績データを変更しない。

## 安全の原則
1. 公開できる権利を確認した **自分の独立した予想** のみを扱う。データ元の利用規約、再配布禁止・商用利用禁止は別途確認する。
2. JRDBの契約者向けデータ・推論から作った契約上非公開のデータや、APIキー、顧客情報をGitHub Pagesへ置かない。GitHubリポジトリもPagesも公開環境。
3. 外部ソースに `publicReleaseApproved: true` および `originalForecast: true` があっても、それ自体は**権利の証明にならない**。管理者が契約内容を確認して初めて設定する。
4. 未検証レースは `draft`（買い目なし）か `skip`。発走済みの新規予想・予想書き換えは禁止。
5. `final` は、照合済み全頭出走表、出典、取消状態、正しい買い目点数と発走前時刻がある場合だけ。正しいデータの内容を人間が確認したことまではプログラムで証明できない。
6. WIN5は別管理。確定したWIN5の買い目を締切後に変更しない。

## 接続のために必要なもの
- 公開利用許可がある予想JSONを返す **管理者が確認したHTTPS URL**。
- 配信側で開催日・出走取消・発走時刻・公式出馬表を検証する仕組み。こちらの受け口はデータそのものを取得・分析しない。
- JSONはルートオブジェクトの `schema: 1`、`date: YYYY-MM-DD`、`generatedAt`（タイムゾーン付き）、`source`、`forecasts` を含む。配列要素はアプリ既存の `keiba-nine-auto-feed.json` スキーマに従う。
- `source` に `name`、`rightsNote`、`publicReleaseApproved: true`、`originalForecast: true` を含める。
- 予想 `recordType: live`。確定予想には `raceCard`（`complete: true`、`date`、`track`、`race`、`source`、`checkedAt`、`runners`［馬番・馬名・active/scratched/excluded］）と `evidence.references` が必要。
- GitHub のリポジトリ **Settings → Secrets and variables → Actions → New repository secret** で、名前 `KEIBA_NINE_PUBLIC_FEED_URL` に上記URLを設定。APIキーやJRDBの認証情報はここへ流用しない。
- 設定が完了すると、GitHub Actionsの `KEIBA NINE - Approved Forecast Publication` が日本時間の朝〜夕方に約30分間隔でチェックする。GitHub側の都合で遅れるため、発走10分前の正確な更新は保証できない。

## 検証方法
```bash
python -m unittest discover -s tests -p 'test_approved_feed_publisher.py' -v
```

本番接続前に、許諾、全頭照合、取消馬、後出し防止、時刻、点数、継続配信、同一データ再配信、アプリ表示をテストする。事前にテスト用サーバーを用意し、実機iPhoneのSafariで確認する。

> ChatGPTの定期通知が自動的にこのJSONへ書き込まれるわけではない。別途、承認済み公開ソースを生成するサービスが必要。
