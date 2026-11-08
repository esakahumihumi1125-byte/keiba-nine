# 競馬ナイン：Gmail直前連携の初回設定（本人用）

これは直前メールを自動確認し、本人ログイン済み画面に短いメモを表示する機能です。メール本文・JRDB独自指数・オッズ・認証情報・馬券記録は外部に送信しません。予想と3連単は自動変更しません。

## iPhone Safariで最初に一度だけすること

1. [Google Apps Scriptで新規プロジェクト](https://script.google.com/home/projects/create) を開き、[Code.gs](./Code.gs) のコード全文をコードエディタに貼り付け、保存する。
2. 関数「createKeibaBridgeToken」を一度実行する。プロジェクト設定（歯車）→スクリプトプロパティに KEIBA_BRIDGE_TOKEN という秘密トークンが作られる。コピーして安全に保存し、チャットやGitHubに貼らない。
3. 関数「installKeibaMailTrigger」を一度実行し、本人のGoogleアカウントでGmailへのアクセスを許可する。これで1分間隔の自動確認トリガーが作成される。トリガー実行には遅延が生じるため、必ず発走前に完了する保証はない。
4. Apps Scriptで「デプロイ」→「新しいデプロイ」→「ウェブアプリ」。実行ユーザーは「自分」、アクセスは「全員（Anyone）」。発行された https://script.google.com/macros/s/.../exec のURLを控える。ウェブアプリには到達可能な状態になるが、秘密トークンのないリクエストへはデータを返さない。
5. [Renderの本人用サービス](https://dashboard.render.com/web/srv-dbl61lijnfac73emrshg) → Environmentに、KEIBA_MAIL_BRIDGE_URL（手順4のURL）とKEIBA_MAIL_BRIDGE_TOKEN（手順2の秘密トークン）を追加・保存する。既存の環境変数は変更しない。保存すると再デプロイされる。
6. [本人用予想画面](https://keiba-nine-owner-preview.onrender.com/owner-preday-forecast) を開き、Gmail自動連携の表示を確認する。メールが来ていなければ直前メモなしのままで正常。開いている画面では約60秒ごとに読み直す。

## 安全条件

- 対象送信元：jrdb-minig2@mailman.jrdb.com と jrdb-hotg3@mailman.jrdb.com、東京・京都・福島のメール。
- 発走2分前より遅い受信・取り込みは採用しない。Render側も当日の既存のレース日付・時刻に一致する内容だけを認める。
- メール本文、写真、JRDB独自評価指数、元のオッズや有料ランキングはクラウドの別サービスに転載しない。本人用の簡単な場・R・時刻・馬場・注目馬番のみ送る。
- Google側の処理が失敗しても既存の本人用予想、実購入記録、過去の成績を変更しない。
- Apps Scriptの1分間隔トリガーは公式に対応。ただし時刻は厳密ではなく、Googleの割当制限の影響もある。稼働時間は日本時間9:00～17:00。Apps Scriptのトリガー・実行履歴で稼働を確認する。
- 直前情報は発走前の検討材料。買い目や予想の「最終確定」は、JRA公式で取消・馬場・発走時刻を確認して別途判断する。
- Webアプリを「全員」に公開する方式が気になる場合は連携を有効にせず、手動メモ方式を維持する。

JRDBの資料は本人の利用範囲と提供元の契約条件に従って扱い、公開サービスに再配布しない。
