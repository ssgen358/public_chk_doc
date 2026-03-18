"""
check_existence.py - 設計書記載ファイルと実ファイルの突合チェックツール

【概要】
設計書から抽出したファイル名一覧（CSV）と、実フォルダ・SVN等から取得した
ファイル名一覧（CSV）を突合し、過不足をチェックしてCSVに出力する。

両方の入力CSVは file_list.py / file_list_batch.py の出力形式を想定している。
設計書側CSVが excel_extract.py の出力の場合、「抽出元ファイル名」列が自動的に
出力CSVの「出典（設計書）」列として付加される。

【チェック内容】
  - 設計書のみ : 設計書に記載があるが実ファイルが存在しない（未実装・誤記の可能性）
  - 実ファイルのみ: 実ファイルが存在するが設計書に記載がない（設計書未記載の可能性）
  - 一致       : 両方に存在する

【使い方】
  python check_existence.py <設計書CSVパス> <実ファイルCSVパス> [オプション]

【引数】
  doc_csv          設計書から抽出したファイル名一覧CSV
  actual_csv       実ファイルのファイル名一覧CSV（file_list.py 出力等）

【オプション】
  --doc-col        設計書CSV内のファイル名列名（省略時: ファイル名）
  --actual-col     実ファイルCSV内のファイル名列名（省略時: ファイル名）
  --doc-info-col   設計書CSVの出典列名（省略時: 抽出元ファイル名）
                   この列が設計書CSVに存在する場合、出力の「出典（設計書）」列に付加する。
                   存在しない場合は無視される。
  --output, -o     出力CSVのパス（省略時: check_existence_result.csv）
  --encoding       出力CSVの文字コード（省略時: cp932）
  --case-sensitive ファイル名の大文字/小文字を区別する（省略時: 区別しない）

【出力CSVの列】
  ファイル名, 出典（設計書）, 設計書, 実ファイル, 判定

  出典（設計書）列: どの設計書ファイルに記載されていたか（出典列がない場合は省略）
  設計書・実ファイル列の値: ○（存在する） / -（存在しない）
  判定列の値             : 一致 / 設計書のみ / 実ファイルのみ

【入力CSVの準備】
  設計書側 : excel_extract.py で設計書からファイル名を抽出すると、
             「抽出元ファイル名」列が自動で付加されるため出典が追跡可能。
             file_list.py の出力や手動CSVも使用可能（「ファイル名」列が必要）。
  実ファイル側: file_list.py / file_list_batch.py でSVNチェックアウト済みフォルダ等を一覧化する。

【使用例】
  python check_existence.py doc_files.csv actual_files.csv
  python check_existence.py doc_files.csv actual_files.csv --output result.csv
  python check_existence.py doc_files.csv actual_files.csv --doc-info-col 出典ファイル名
"""

import argparse
import csv
import os
import sys


# -----------------------------------------------------------------------
# CSV 読み込み
# -----------------------------------------------------------------------

def load_csv(path: str, col_name: str, info_col: str | None = None) -> list[dict]:
    """CSVファイルからファイル名と出典情報を読み込む。UTF-8 / CP932 の両方に対応。

    Returns:
        list of dict with keys:
          'name' : ファイル名（col_name 列の値）
          'info' : 出典情報（info_col 列の値、列がない場合は空文字）
    """
    rows = None
    fieldnames = None

    for encoding in ("utf-8-sig", "utf-8", "cp932"):
        try:
            with open(path, newline="", encoding=encoding) as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                fieldnames = reader.fieldnames
            break
        except UnicodeDecodeError:
            continue

    if rows is None:
        print(f"[ERROR] ファイルの文字コードが判別できません（UTF-8 または CP932 で保存してください）: {path}", file=sys.stderr)
        sys.exit(1)

    if fieldnames is None or col_name not in fieldnames:
        print(f"[ERROR] '{col_name}' 列が見つかりません: {path}", file=sys.stderr)
        print(f"        利用可能な列名: {list(fieldnames) if fieldnames else '(なし)'}", file=sys.stderr)
        sys.exit(1)

    # 出典列が存在するか確認（存在しない場合は無視）
    has_info_col = info_col and fieldnames and info_col in fieldnames

    records = []
    for i, row in enumerate(rows, start=2):
        val = row.get(col_name, "").strip()
        if val:
            records.append({
                "name": val,
                "info": row.get(info_col, "").strip() if has_info_col else "",
            })
        else:
            print(f"[WARN] {i}行目: '{col_name}' が空のためスキップします。")

    return records


# -----------------------------------------------------------------------
# 突合処理
# -----------------------------------------------------------------------

def compare(doc_records: list[dict], actual_records: list[dict], ignore_case: bool) -> tuple[list[dict], bool]:
    """設計書ファイル名一覧と実ファイル名一覧を突合してレコードを返す。

    Returns:
        (results, has_info):
          results  : 突合結果のリスト
          has_info : 出典情報列が存在するかどうか
    """

    def normalize(name: str) -> str:
        return name.lower() if ignore_case else name

    # key: 正規化ファイル名 → {name: 表示用名, info: 出典情報}
    doc_map = {normalize(r["name"]): r for r in doc_records}
    actual_map = {normalize(r["name"]): r for r in actual_records}

    has_info = any(r["info"] for r in doc_records)
    all_keys = sorted(set(doc_map.keys()) | set(actual_map.keys()))

    results = []
    for key in all_keys:
        in_doc = key in doc_map
        in_actual = key in actual_map

        display_name = doc_map[key]["name"] if in_doc else actual_map[key]["name"]
        info = doc_map[key]["info"] if in_doc else ""

        if in_doc and in_actual:
            judgment = "一致"
        elif in_doc and not in_actual:
            judgment = "設計書のみ"
        else:
            judgment = "実ファイルのみ"

        results.append({
            "ファイル名": display_name,
            "出典（設計書）": info,
            "設計書": "○" if in_doc else "-",
            "実ファイル": "○" if in_actual else "-",
            "判定": judgment,
        })

    return results, has_info


# -----------------------------------------------------------------------
# CSV 出力
# -----------------------------------------------------------------------

def write_csv(results: list[dict], output_path: str, encoding: str, has_info: bool) -> None:
    """突合結果をCSVに書き出す。出典情報がある場合は列を追加する。"""
    if has_info:
        fieldnames = ["ファイル名", "出典（設計書）", "設計書", "実ファイル", "判定"]
    else:
        fieldnames = ["ファイル名", "設計書", "実ファイル", "判定"]
    with open(output_path, "w", newline="", encoding=encoding) as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(results)


# -----------------------------------------------------------------------
# サマリー表示
# -----------------------------------------------------------------------

def print_summary(results: list[dict]) -> None:
    """突合結果のサマリーをコンソール出力する。"""
    total = len(results)
    matched = sum(1 for r in results if r["判定"] == "一致")
    doc_only = sum(1 for r in results if r["判定"] == "設計書のみ")
    actual_only = sum(1 for r in results if r["判定"] == "実ファイルのみ")

    print("-" * 50)
    print("突合結果サマリー")
    print(f"  対象ファイル数合計 : {total} 件")
    print(f"  一致               : {matched} 件")
    print(f"  設計書のみ（要確認）: {doc_only} 件")
    print(f"  実ファイルのみ（要確認）: {actual_only} 件")
    print("-" * 50)

    issues = [r for r in results if r["判定"] != "一致"]
    if issues:
        print("【要確認ファイル一覧】")
        for r in issues:
            info_str = f"  ← {r['出典（設計書）']}" if r.get("出典（設計書）") else ""
            print(f"  [{r['判定']}] {r['ファイル名']}{info_str}")


# -----------------------------------------------------------------------
# メイン
# -----------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="設計書記載ファイルと実ファイルの突合チェックツール"
    )
    parser.add_argument("doc_csv", help="設計書から抽出したファイル名一覧CSVのパス")
    parser.add_argument("actual_csv", help="実ファイルのファイル名一覧CSVのパス（file_list.py 出力等）")
    parser.add_argument("--doc-col", default="ファイル名", help="設計書CSV内のファイル名列名（デフォルト: ファイル名）")
    parser.add_argument("--actual-col", default="ファイル名", help="実ファイルCSV内のファイル名列名（デフォルト: ファイル名）")
    parser.add_argument("--doc-info-col", default="抽出元ファイル名", help="設計書CSVの出典列名（デフォルト: 抽出元ファイル名）。列が存在する場合のみ出力に付加する。")
    parser.add_argument("--output", "-o", default="check_existence_result.csv", help="出力CSVのパス（デフォルト: check_existence_result.csv）")
    parser.add_argument("--encoding", default="cp932", help="出力CSVの文字コード（デフォルト: cp932）")
    parser.add_argument("--case-sensitive", action="store_true", help="ファイル名の大文字/小文字を区別する（省略時: 区別しない）")

    args = parser.parse_args()

    ignore_case = not args.case_sensitive

    # ファイル存在確認
    for path, label in [(args.doc_csv, "設計書CSV"), (args.actual_csv, "実ファイルCSV")]:
        if not os.path.isfile(path):
            print(f"[ERROR] {label}が見つかりません: {path}", file=sys.stderr)
            sys.exit(1)

    print(f"設計書CSV    : {args.doc_csv}（列: {args.doc_col}）")
    print(f"実ファイルCSV: {args.actual_csv}（列: {args.actual_col}）")
    print(f"出典列       : {args.doc_info_col}（設計書CSVに列が存在する場合のみ付加）")
    print(f"大文字小文字 : {'区別しない' if ignore_case else '区別する'}")
    print()

    # データ読み込み
    doc_records = load_csv(args.doc_csv, args.doc_col, args.doc_info_col)
    actual_records = load_csv(args.actual_csv, args.actual_col)

    print(f"設計書側ファイル数    : {len(doc_records)} 件")
    print(f"実ファイル側ファイル数 : {len(actual_records)} 件")
    print()

    # 突合
    results, has_info = compare(doc_records, actual_records, ignore_case)

    # 出力
    write_csv(results, args.output, args.encoding, has_info)
    print_summary(results)
    print()
    if has_info:
        print("※ 出典（設計書）列：どの設計書ファイルに記載されていたかを示します。")
        print()
    print(f"出力先: {os.path.abspath(args.output)}")


if __name__ == "__main__":
    main()
