# KEIBA NINE — iPhoneから安全に開く、本人専用の開発画面

GitHub Codespacesの「本人のみ閲覧できる開発用ポート」を使って、
現在のPythonサービスを**架空データ専用**で起動する準備です。

これは公開アプリの切替ではなく、JRDB実データの取得でもありません。
GitHub PagesのBETA 5.1・Googleバックアップ・実戦記録は変更されません。

## iPhone Safariでの初回テスト（GitHubアカウントでログイン）

1. `https://github.com/esakahumihumi1125-byte/keiba-nine` を開きます。
2. **Code → Codespaces → Create codespace on main** を選びます。
   iPhoneの小さい画面で操作しづらい場合はSafariの「デスクトップ用Webサイトを表示」を利用します。
3. 開いたCodespacesのターミナルで、以下の**1行だけ**を実行します。

   `python scripts/codespace_preview.py`

4. ターミナルに本人用の一時ログインユーザー名とパスワードが表示されます。
   外部へ共有しないでください。サーバーが停止すると無効になります。
5. **PORTS**タブで番号 `8765` が**Private**であることを必ず確認します。
   PublicまたはOrganizationならURLを開かず、Privateに戻してください。
6. `8765` の転送URLを開き、画面のログインでターミナルに表示された
   一時パスワードを使ってください。表示内容は「JRDB未接続」が正解です。
7. テスト後はターミナルで `Ctrl+C` を押してサーバーを止め、
   GitHub Codespacesも停止してください。Codespacesの利用には
   アカウントごとの無料枠・課金上限があります。

### セキュリティ上の制限

- **本機能は架空テスト専用。** 起動時にJRDB APIキーを空にして、
  `JRDB_PRIVATE_ENABLED=0`を強制します。
- 本人用一時パスワードは、明示的に起動した**自分のCodespacesターミナルにだけ表示**します。
  GitHubの公開リポジトリやActionsログへ記録しません。
- HTTPS転送を使い、**PrivateポートでGitHub本人認証が必要**というCodespacesの
  機能を前提にしています。アプリ側の本人認証も必須です。
  `KEIBA_ALLOW_LOCAL_HTTP=1`はループバックの開発用例外としてだけ使用します。
- 「Public」ポートへの変更は禁止です。JRDBの有料データを追加したり、
  API認証情報をリポジトリ・チャット・公開HTMLへ入れてはいけません。
- Codespacesは一時的な開発環境です。24時間稼働、自動更新、発走前の
  正確な配信時刻は保証しません。実データ用の長期運用は別の安全な本人専用サーバーが必要です。

## 参考（GitHub公式）

- https://docs.github.com/en/codespaces/reference/security-in-github-codespaces
- https://docs.github.com/en/codespaces/developing-in-a-codespace/forwarding-ports-in-your-codespace
- https://docs.github.com/en/codespaces/billing-and-payments/about-billing-for-github-codespaces

JRDBのベーシックコース会員パスワードと、API β版で配布される専用キーは別物です。
現在、JRDBのテスト用アカウントの返答を待っているため、**実データ取得はまだ不可**です。
