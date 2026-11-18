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
