"""Build a small, reviewable Windows JV-Link ZIP from exact source files.

No paid source data, environment variables, generated cache, credentials,
private API endpoints or binary executables can enter this package. The ZIP
is for an *owner-initiated LOCAL diagnostic only*. Nothing in it installs
software or sends data to Render, GitHub or any web service.
"""
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / "dist" / "ARC-RACE-JV-Link-PC-check.zip"
FILES = (
    "scripts/windows_arc_race_preflight.cmd",
    "scripts/windows_jvlink_2026_history_store.cmd",
    "scripts/windows_jvlink_2026_history_store.py",
    "scripts/windows_jvlink_history_workflow.py",
    "scripts/windows_jvlink_history_workflow.cmd",
    "scripts/windows_jvlink_workout_store.py",
    "scripts/owner_jvdata_workout_features.py",
    "scripts/windows_jvlink_workout_pair_study.py",
    "scripts/windows_jvlink_workout_pair_study.cmd",
    "scripts/windows_jvlink_workout_store.cmd",
    "scripts/windows_jvlink_history_walkforward.py",
    "scripts/windows_jvlink_history_walkforward.cmd",
    "scripts/windows_arc_race_validate_history.py",
    "scripts/windows_arc_race_validate_history.cmd",
    "scripts/windows_check_jvlink.cmd",
    "scripts/windows_check_jvlink.ps1",
    "scripts/windows_jvlink_weekly_read.cmd",
    "scripts/windows_jvlink_weekly_read.py",
    "scripts/windows_jvlink_horse_data_probe.cmd",
    "scripts/windows_jvlink_horse_data_probe.py",
    "scripts/windows_jvlink_day_history_preview.cmd",
    "scripts/windows_jvlink_all_flat_history_preview.cmd",
    "scripts/windows_jvlink_day_history_preview.py",
    "scripts/windows_arc_race_saved_history_review.cmd",
    "scripts/windows_arc_race_saved_history_review.py",
    "scripts/windows_arc_race_saved_trifecta_trial.cmd",
    "scripts/windows_arc_race_saved_all_flat_trifecta_trial.cmd",
    "scripts/windows_arc_race_saved_all_flat_trifecta_trial.py",
    "scripts/windows_arc_race_saved_trifecta_trial.py",
    "scripts/owner_jvdata_offline_trifecta_trial.py",
    "scripts/owner_jvdata_offline_evidence.py",
    "scripts/evaluation_policy.py",
    "scripts/owner_jvdata_day_history_bridge.py",
    "scripts/owner_jvdata_horse_history_coverage.py",
    "scripts/owner_jvdata_horse_history_preview.py",
    "scripts/jvdata_ra_se_candidate.py",
    "scripts/owner_jvdata_local_report.py",
    "scripts/owner_jvdata_jrdb_day_check.py",
    "scripts/jrdb_coverage.py",
    "scripts/jrdb_evidence_readiness.py",
    "scripts/jrdb_program_preview.py",
    "docs/windows-jvlink-local-check.md",
)
README = """ARC RACE - JRA-VAN JV-Link PC確認用（研究・未完成版）

このZIPは自分のWindows PCだけで使う読み取り用ツールです。
JRA-VAN契約、JV-Link、64bit Python、pywin32 が別途必要です。

1. ZIPを「すべて展開」してから開きます（ZIP内から直接実行しない）。
2. scripts/windows_arc_race_preflight.cmd をダブルクリック。
   PYTHON64_CHECK / PYWIN32_CHECK / JVLINK_CHECK の結果を確認。
3. ARC_RACE_PC_READY=YES なら初期化環境の確認はOK。
   まだ実際のJRA出馬表データの取得成功ではありません。
4. JRA-VANの本人利用権限と提供開始を確認できた場合だけ、
   scripts/windows_jvlink_weekly_read.cmd をダブルクリック。
   Enterだけなら土日は今日（日本時間）、平日は次の土曜日。祝日は YYYYMMDD を指定。
5. 成功時はPC内の %LOCALAPPDATA%\\ARC-RACE-private に
   JSON・ブラウザー用HTMLの候補要約を保存します。
   どちらもGitHubやRenderへ自動送信しません。

6. 過去走補てんデータRCVNが利用できるかを確認したい場合だけ
   scripts/windows_jvlink_horse_data_probe.cmd を開きます。
   画面に YES と入力した場合だけ、1回限定でRCVNへ問い合わせます。
   取得した馬のデータは一切保存・転送しません。
   NO_NEW_DATA や空応答だけで契約の不備を断定しないでください。

7. RACEとRCVNを使って実際の1レースだけを検証する場合、
   scripts/windows_jvlink_day_history_preview.cmd を開きます。
   YES を明示入力した時だけRACEを1回読む。対象日（YYYYMMDD）を指定し、
   出走馬が全頭そろった発走前の1レースを選べた場合だけRCVNを1回読む。
   番組・馬番が不完全ならRCVNは照会せず保留。
   発走前の平地芝・ダートだけを対象に、距離と走路コードが
   確認できる全レースの馬IDを一時照合し、RCVNを1回だけ読む。
   障害・走路不明は飛ばし、過去走が一致した発走前レースのうち
   発走予定が最も早い1レースを選ぶ。一致がなければ見送り。
   平地候補がなければRCVNは呼ばず安全に停止する。
   （公式JRA最終出走確認ではありません。）
   RCVNは利用環境によってJVOpen時のダウンロードが長くなる場合があります。
   木曜夜の実機確認でRA7が5,000件より多かったため、統合版では
   RACEは最大5,000件、RCVNは最大80,000件・取得開始後60秒まで読取。
   RCVNは当日の馬に一致するSE7（最大5,000件）と過去RA7の候補
   （最大10,000件のリング）を実行中のメモリにだけ保持します。
   同じ過去レースに一致したRA7のみ距離・芝ダート・当時馬場を表示。
   古いRA7がリングから外れた場合は「不明」とし、補完しません。
   元のRA7、SE7、登録ID、提供元ファイルは保存・送信しません。
   未完了なら表示・保存しません。
   取得できた場合でも馬番と直近5走だけの研究用情報です。
   PC内の ARC-RACE-private に場・R番号ごとのJSONとHTMLを
   新規保存します。同じレースの前回記録は上書きせず、外部送信しません。
   過去走が0件でも「新馬」「全履歴なし」とは断定しません。
   直前の取消や最終出走確定、配信時刻の真正性は検証していません。

7a. 全開催場・発走前の平地レースを1回のRACE+RCVN読み込みで\n    PC内にまとめたい場合は（必要時のみ）、\n    scripts/windows_jvlink_all_flat_history_preview.cmd を開きます。\n    YESの明示入力でのみRACEを1回、RCVNを1回読み、\n    完全な馬番候補・発走前の芝ダートだけを最大36Rまでまとめます。\n    過去走が見つからない馬は未観測のままで、架空評価しません。\n    jvdata-all-flat-races-YYYYMMDD.json/.html に新規保存し、\n    既存の個別1Rファイルは上書きしません。すでに同名の\n    全Rファイルがある日は再保存せず、料金の再照会を促しません。\n    この研究用ファイルはJRA最終出走・取消・馬場・配信時刻を\n    独立検証せず、正式10項目採点・3連単購入には使えません。\n    GitHub・Render・インターネットへは送信しません。\n\n8. 一度取得済みの1レースを追加のJRA-VAN接続なしで確認するには
   scripts/windows_arc_race_saved_history_review.cmd をダブルクリック。
   当日（日本時間）の保存済みJSONから最新1レースを探して、
   「近走」「展開・脚質」の観測状況と、正式10項目の未採点状態を
   PC内の新規HTMLに表示します。再ダウンロード・画像送付は不要。
   HTMLとJSONは %LOCALAPPDATA%\ARC-RACE-private に新規作成し、
   生データ・馬登録ID・秘密キーを保存、転送しません。
   「資料あり」と「S/A/B判定」は別物で、3連単は生成しません。

9. 保存済みの1RデータからJRA-VANの過去走だけで
   「3連単の研究用フォーメーション」を試すには
   scripts/windows_arc_race_saved_trifecta_trial.cmd を開きます。
   追加のJRA-VAN・JRDB照会は0回。PC上の既存JSONだけを使います。
   今回の芝/ダート・距離の候補が分かり、全馬について
   過去の同じ芝ダート・距離差200m以内のRA7/SE7実績と
   最終コーナー位置が観測でき、発走予定前で、
   枠の境界に順位同点がない場合のみ研究用3連単を最大40点
   （上限48点、1点100円相当の机上計算）で表示。
   足りない資料があれば見送り（0点）で、人気・オッズは使いません。
   今回の取消・馬場・変更時刻・正確な配信時点、調教など
   正式10項目100点採点は未確認。予測精度の検証も未実施です。
   実際の馬券購入には使わず、既存の購入記録を変更しません。
   出力先はPC内の "-trifecta-study.html/.json" だけ。
   アプリやGitHub・Renderへは自動送信しません。

10. すでに1回保存した全平地レースの研究用JSONから、\n    追加の有料アクセス0回で全Rの3連単研究をまとめて作るには\n    scripts/windows_arc_race_saved_all_flat_trifecta_trial.cmd を使用。\n    発走済み・芝ダ距離±200mの過去記録が全頭で揃わないRは\n    必ず見送り0点。推測で埋めず、研究できるRだけ最大48点。\n    新規JSON/HTMLをPC内に保存し、再実行で上書きしません。\n    追加のJRA-VAN/ JRDB通信、GitHub/Renderアップロード、\n    実購入、収支記録、正式10項目採点は一切ありません。\n\n画面に出る CHECK=... / ARCRACE_WEEKLY_READ=... /
ARC_RACE_RCVN_CHECK=... / ARC_RACE_DAY_HISTORY=... /
ARC_RACE_OFFLINE_EVIDENCE=... /\nARC_RACE_LOCAL_TRIFECTA=... の状態名だけ
教えてください。利用キーやパスワードは見せたり送ったりしないでください。

11. 2026年の過去レースデータ蓄積（個人PC専用・実機未検証）
    scripts/windows_jvlink_2026_history_store.cmd をダブルクリック。
    契約・無料体験が有効で、個人利用の権限を確認した場合のみYES。
    通常RACEを20260101000000から1回取得し、中央競馬の2026年RA/SE
    のみをLOCALAPPDATAのARC-RACE-private/licensed-historyにSQLite保存。
    同一レコードは重複排除、異なる更新版は区別し、完了時のみ確定。
    SSD空き3GiB未満なら中断。読取には上限があり、JVOpenの配信容量・
    時間は制御できません。追加の自動取得や再試行はありません。
    完了表示は全レース網羅や正式採点・学習成功を意味しません。
    原データは有料情報です。外部共有・クラウド送信・GitHub登録禁止。
    契約終了時は保存元データ、キャッシュ、コピー、学習用データを削除。
    元データ復元不能の個人利用モデルだけ保持可能か別途確認してください。
    調教・血統・払戻等の蓄積、学習処理、差分更新は今回の対象外です。

12. 取得済みの2026年RA/SEデータからコース研究をする場合は、
    scripts/windows_jvlink_history_walkforward.cmd をダブルクリック。
    個人利用契約が有効な間のみYES。追加JV-Link通信0回。
    完全なRA7/SE7の全着順が揃うレースだけを使い、対象日より
    過去かつ作成日も前日の履歴だけで同場・同走路・200m帯の
    3着以内の実績を比較する。均等確率とのBrier誤差を集計。
    事後確定の出走馬・コースを使うため正式発走前検証ではない。
    元データ・学習済みモデル・買い目の外部出力はしない。
    実データ・正式10項目の評価は未検証。

13. 2026年の坂路・ウッド調教資料を本人PC内に蓄積するには、
    scripts/windows_jvlink_workout_store.cmd を開く。
    SLOP（坂路）またはWOOD（ウッド）を選択し、有効契約と
    個人利用権限を確認してYES。選択した通常データを1回取得。
    SQLiteは坂路・ウッド別に新規保存し、訂正・削除通知も保持。
    同じファイルを上書きしない。空き3GiB未満で停止。
    無料体験を含む契約終了時は原データ等の削除が必要。
    全期間網羅・発走前配信時点・正式調教30点の検証は未完成。
    外部送信・モデル学習・買い目生成は行わない。

14. 調教時計と過去の着順を比較する場合は、
    scripts/windows_jvlink_workout_pair_study.cmd を起動。
    保存済みの2026年レースDBと坂路/ウッドDBを読取専用で使用。
    同日・同調教場・同走路等の比較可能な馬同士について、
    終い1Fと加速の良否が着順と一致する割合を集計する。
    対象日前の14日間・作成日も対象日前の資料だけ使用する。
    事後確定出走馬を使う研究であり、発走前予想の精度ではない。
    追加照会・原データ外部転送・採点変更・モデル保存なし。

15. 2026年過去成績・坂路・ウッドをまとめて準備する場合は、
    scripts/windows_jvlink_history_workflow.cmd を起動。
    保存済みDBの種類・完了状態・件数を確認し、未取得分のみ表示。
    契約と利用権限を確認してYESと入力した時だけ、RACE・SLOP・WOOD
    の不足分を順番に各1回取得する。途中失敗時は後続照会を中止。
    再度本人が起動した場合、既存完了DBは読み直さない。
    3種類が揃っても取得期間網羅、正式採点、AI学習完了を意味しない。
    契約終了時の原データ等の削除条件は従来通り。

16. 保存済み3種類のDBをまとめて検証する場合は
    scripts/windows_arc_race_validate_history.cmd をダブルクリック。
    有効な個人利用権限を確認してYESを1回だけ入力。
    コース適性・調教複合比較・馬別調教指数の期間別検証を一括実行。
    追加のJV-Link照会0回。DBは読取専用、結果は集計値だけ画面に表示。
    ARC_RACE_VALIDATION=RETROSPECTIVE_ONLY は事後検証であり、
    正式採点・発走前予想の精度を証明するものではありません。
    キーや元データは共有せず、集計行だけ確認してください。

重要：
- Windows実機での成功は未検証。
- RA/SEは最終出走馬・取消・馬場・発走時刻変更を証明しません。
- ARC RACE正式10項目採点、3連単自動予想、公式払戻照合は未完成。
- 馬券を自動購入しません。追加ソフトの自動導入もしません。
- Microsoft Defender/SmartScreen等の警告を無条件に回避しないでください。
- このZIPにはパスワード、契約キー、有料レース原票は入っていません。
- ソースコードを確認するなら対応PR #189を参照してください。
"""


def build(destination=DEST):
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.resolve() == ROOT.resolve():
        raise ValueError("Destination must not be the repository")
    with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("ARC-RACE-JV-Link/README.txt", README.encode("utf-8-sig"))
        for rel in FILES:
            path = ROOT / rel
            if not path.is_file():
                raise FileNotFoundError(rel)
            zf.write(path, arcname="ARC-RACE-JV-Link/" + rel)
    return destination


if __name__ == "__main__":
    path = build()
    print("LOCAL_BUNDLE_READY=" + path.name)
