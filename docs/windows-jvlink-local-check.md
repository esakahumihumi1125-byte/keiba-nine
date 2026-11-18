# ARC RACE: Windows用 JRA-VAN JV-Link 接続の確認

2026-11-18。本人用PCでJRA-VAN Data Lab. (JV-Link 64bit) の最初の接続を簡単に確認するための小さな**読取専用診断**。以前の Data Lab.検証ツールのセットアップに戻る必要はありません。

## PCを再開したときだけ

1. GitHub Desktopで最新の変更を取得したあと、リポジトリの `scripts/windows_check_jvlink.cmd` をダブルクリックする。
2. 黒いウィンドウに `JVLINK_CHECK=INIT_OK` と出たら、64bit COM作成と `JVInit("UNKNOWN")` の呼出しが成功した状態。
3. `COM_UNAVAILABLE`、`WRONG_BITNESS`、`INIT_FAILED` または `INIT_EXCEPTION` の場合はその**状態名だけ**共有する。アカウントの利用キー、パスワード、ダイアログの秘密情報を送らない。

**「INIT_OK」でもJRA公式出馬表の取得・払戻・取消・馬場・発走時刻の取得や利用権限が検証されたわけではありません。** 競馬予想への接続も未実装。

## 安全性

- 64bitのWindows PowerShellでローカルCOM `JVDTLab.JVLink` と `JVInit` の呼出しだけを確認。JVOpen/JVRTOpen/JVRead/JVGetsは実行しない。
- レースデータのダウンロード、追加課金対象のデータ取得、ネットワーク転送、秘密トークンの表示・保存、GitHub/Renderへの送信、馬券購入は行わない。JV-Linkの内部初期化通信の有無までは確認しない。
- `.cmd` のPowerShell実行ポリシー変更は**その起動プロセス限り**。Windows全体の設定は変えない。
- テストはLinux上の**静的検査のみ**。Windows実機でのCOM動作は未確認。SDK Ver.5.0.0 の64bit登録が想定。
- 現段階で本番アプリへの統合や自動同期はなし。JRA-VAN Data Lab.の個人利用・転載・ソフトウェア登録条件は正式利用前に別途確認する。

参照： [JRA-VAN公式SDK Ver.5.0.0](https://developer.jra-van.jp/t/topic/45)、
[公式Python開発ガイド](https://developer.jra-van.jp/t/topic/949)。

## JRA-VAN RA/SEの固定長出馬表候補を読む（2026-11-18、開発用）

`scripts/jvdata_ra_se_candidate.py` を追加。正式なJRA-VAN JV-Dataの「RA レース詳細（1272バイト）」と「SE 馬毎レース情報（555バイト）」の**出馬表データ区分2**を対象に、開催日・場・開催回・開催日目・レース番号・馬番とRAの予定発走時刻を、サーバーへ送らず**プライベートなメモリ内だけ**で検証します。独自のレコード順序や改行変換を推測せず、現行の固定長・末尾CRLFを要件とします。

JRDBの同日/場/Rの番組と馬番集合・頭数・予定時刻を比較する関数も用意しました。返すのは、馬番候補の一致などと**最終確認が未完了**という状態だけで、出走確定・取消なし・最新馬場・確定発走時刻を保証しません。馬名・血統登録番号・有料レコード本体は出力しません。過去成績データ区分3〜7を出馬表に混ぜません。

**現時点の境界**：`scripts/windows_check_jvlink.cmd` ではまだJVInitのみを試します。JVOpen、JVRead、RA/SE抽出は**未実装**で、PC上の実データ取得も試していません。これらのパーサーは合成レコードでのテストのみです。JV-Dataの利用権限も自動認証しません。取得時点とJV-Linkの元データが真正か、RA/SE以降の変更情報を取りこぼしていないかを別途検証するまでは正式10項目採点ゲートへ通しません。

技術資料： [JRA-VAN現行SDK](https://developer.jra-van.jp/t/topic/45)、[JV-Data仕様書](https://jra-van.jp/dlb/sdv/sdk/JV-Data4901.pdf)、[RAフィールドの読み方](https://ht-0328.github.io/jvdata-store/reference/RA/)、[SEフィールドの読み方](https://ht-0328.github.io/jvdata-store/reference/SE/)。

## 「今週データ」を本人PCで1回だけ取得する実行ファイル（2026-11-18）

- **まだ実機未検証。** 開発ブランチの `scripts/windows_jvlink_weekly_read.cmd` をダブルクリック。**Enterだけなら直近の土曜日**、日曜や祝日なら開催日を `YYYYMMDD` で1回入力する想定。PCのWindowsにJV-Link 64bitと、64bit Python（pywin32ライブラリ）がインストールされている必要がある。Pythonを自動インストールせず、権限のないAPIを自動連打しない。
- `windows_jvlink_weekly_read.py` は `JVInit("UNKNOWN")` → **1回だけ** `JVOpen("RACE","00000000000000",2,...)` → 最大5,000レコード（小さいWindows PCでのCOMバッファ消費を抑えるため）の `JVGets` → `JVClose`。公式JV-Data option 2（今週データ）のみで、過去データのsetup option 3/4、通常蓄積 option 1、リアルタイム監視は行わない。実行対象日はPC現地日付から7日以内の今日以降だけ。
- 取り出すのは対象開催日の**出馬表区分2のRA/SE**のみ。日付・競馬場・レース・馬番・登録頭数が完全一致した場合だけ、各場各Rの候補をまとめる。区分3以降の結果や馬名、血統ID、ファイル名、生レコードは保存しない。欠損や矛盾、取得上限超過、JVClose失敗なら全体を保留。
- 成功時には `%LOCALAPPDATA%\ARC-RACE-private\jvdata-candidate-YYYYMMDD.json` に**非公開の候補要約だけ**保存する。OneDriveとGitHubの作業フォルダを避けるため通常のDocumentsには保存しない。候補JSONを同じフォルダで完全に書いてから原子的に確定名へリンクし、途中書き込みで不完全な確定ファイルを残さない。同じ開催日のファイルが既に存在したら**上書きしない**。後の発走前記録と混同しないため、現在は追記や自動再取得を許可しない。JSONを公開リポジトリ、チャット、SNS、Google Driveに転送しない。
- 失敗時は `ARCRACE_WEEKLY_READ=...` の**固定ステータス名のみ**表示。完全なエラーログ、利用キーや実レース原票は送らない。 `PYWIN32_NOT_INSTALLED` なら同じ64bit Python環境にpywin32が未導入。 `JVOPEN_NOT_READY` はJV-Linkや利用状態、今週データの提供状態を公式設定で個別に確認する必要があるが、**自動で再試行しない**。
- 正常終了時に**取得できたレース数、観測できた競馬場数、その競馬場の各12Rがそろっているか**を表示。これはその日に開催される**すべての競馬場を観測できた証明ではない**。未確認の会場や提供開始前のレースがあり得るため、最新データ不足時は正式採点へ昇格しない。
- **重要**: これはJRA最終確定の証明ではなく、候補馬番・予定時刻だけ。AV(出走取消・除外)、WE(馬場)、TC(発走時刻変更)、WH(馬体重)の直前変更と元データの真正性・配信タイミング・出走馬最終確定はまだ未接続。本人用Renderへの取り込み、正式100点採点、全場全R3連単自動生成・公式結果照合は**未完成**。
- LinuxのGitHub Actionsでは合成COMを使ったテストのみ。実際のJRA-VANサーバーへの有料アクセス、Windows COM動作、利用キーの認証、配信の同時性、契約適合性は確認していない。

[公式Data Lab. SDK・JV-Linkドキュメント](https://developer.jra-van.jp/t/topic/45) を参照。


## 同日全RをJRDBと比較する内部処理（2026-11-18）

`scripts/owner_jvdata_jrdb_day_check.py` は**本人認証済みのサーバーか個人PC内の処理として利用する想定**。既存の `windows_jvlink_weekly_read.py` が作った候補結果と、JRDBですでに正規化した同日 `/tra` と `/tky`（当日場・R・頭数・馬番・予定発走時刻）をレース単位に照合し、候補一致・不足・不一致を診断する。新しいJRA-VAN取得や有料JRDB API通信は一切しない。馬名・有料原票・馬IDは結果に含めない。

- **候補が一致しても**出走取消・除外・馬場・当日発走時刻変更を最新速報で確認していないため、`finalJraStarterListVerified=false`、`formalTenFactorReady=false`、`bettingReady=false`。
- JRDB側にRがあるのにJRA-VAN候補がない場合は `missing_jvdata_candidate` とする。馬番集合・予定時刻・頭数が異なる場合は `hold_source_mismatch`。日付違い、異なる競馬場や別レースの混入・重複・不正な採点許可フラグは処理を拒否する。
- **現時点では関数と合成テストのみ**。Windowsでの実データ取得、Render本人用認証とのファイル連携、インターネット転送、公式最終確認との結合は行っていない。JRA-VANの契約・再利用/再配信条件に従う必要がある。
