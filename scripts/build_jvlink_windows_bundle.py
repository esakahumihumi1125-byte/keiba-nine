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
    "scripts/windows_check_jvlink.cmd",
    "scripts/windows_check_jvlink.ps1",
    "scripts/windows_jvlink_weekly_read.cmd",
    "scripts/windows_jvlink_weekly_read.py",
    "scripts/windows_jvlink_horse_data_probe.cmd",
    "scripts/windows_jvlink_horse_data_probe.py",
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
   Enterだけなら次の土曜日。日曜日は YYYYMMDD を入力。
5. 成功時はPC内の %LOCALAPPDATA%\\ARC-RACE-private に
   JSON・ブラウザー用HTMLの候補要約を保存します。
   どちらもGitHubやRenderへ自動送信しません。

6. 過去走補てんデータRCVNが利用できるかを確認したい場合だけ
   scripts/windows_jvlink_horse_data_probe.cmd を開きます。
   画面に YES と入力した場合だけ、1回限定でRCVNへ問い合わせます。
   取得した馬のデータは一切保存・転送しません。
   NO_NEW_DATA や空応答だけで契約の不備を断定しないでください。

画面に出る CHECK=... / ARCRACE_WEEKLY_READ=... /
ARC_RACE_RCVN_CHECK=... の状態名だけ
教えてください。利用キーやパスワードは見せたり送ったりしないでください。

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
