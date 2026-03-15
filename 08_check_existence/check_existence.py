"""
check_existence.py - 設計書記載ファイルと実ファイルの突合チェックツール

【概要】
設計書から抽出したファイル名一覧（CSV）と、実フォルダ・SVN等から取得した
ファイル名一覧（CSV）を突合し、過不足をチェックしてCSVに出力する。

両方の入力CSVは file_list.py / file_list_batch.py の出力形式を想定している。

【チェック内容】
  - 設計書のみ : 設計書に記載があるが実ファイルが存在しない（未実装・誤記の可能性）
  - 実ファイルのみ: 実ファイルが存在するが設計書に記載がない（設計書未記載の可能性）
  - 一致       : 両方に存在する

【使い方】
  python check_existence.py <設計書CSVパス> <実ファイルCSVパス> [オプション]

【引数】
  doc_csv        設計書から抽出したファイル名一覧CSV
  actual_csv     実ファイルのファイル名一覧CSV（file_list.py 出力等）

【オプション】
  --doc-col      設計書CSV内のファイル名列名（省略時: ファイル名）
  --actual-col   実ファイルCSV内のファイル名列名（省略時: ファイル名）
  --output, -o   出力CSVのパス（省略時: check_existence_result.csv）
  --encoding     出力CSVの文字コード（省略時: cp932）
  --ignore-case  ファイル名の大文字/小文字を区別しない（省略時: 区別しない）

【出力CSVの列】
  ファイル名, 設計書, 実ファイル, 判定

  設計書・実ファイル列の値: ○（存在する） / -（存在しない）
  判定列の値             : 一致 / 設計書のみ / 実ファイルのみ

【入力CSVの準備】
  設計書側 : file_list.py で設計書ファイルを一覧化するか、
             設計書から手動で抽出したファイル名をCSV化する。
             「ファイル名」列にチェック対象のファイル名を記載すること。
  実ファイル側: file_list.py / file_list_batch.py でSVNチェックアウト済みフォルダ等を一覧化する。

【使用例】
  python check_existence.py doc_files.csv actual_files.csv
  python check_existence.py doc_files.csv actual_files.csv --output result.csv
  python check_existence.py doc_files.csv actual_files.csv --doc-col ファイル名 --actual-col ファイル名
"""

import argparse
import csv
import os
import sys


# -----------------------------------------------------------------------
# CSV 読み込み
# -----------------------------------------------------------------------

def load_csv(path: str, col_name: str) -> list[str]:
    """CSVファイルから指定列のファイル名一覧を読み込む。UTF-8 / CP932 の両方に対応。"""
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

    names = []
    for i, row in enumerate(rows, start=2):
        val = row.get(col_name, "").strip()
        if val:
            names.append(val)
        else:
            print(f"[WARN] {i}行目: '{col_name}' が空のためスキップします。")

    return names


# -----------------------------------------------------------------------
# 突合処理
# -----------------------------------------------------------------------

def compare(doc_names: list[str], actual_names: list[str], ignore_case: bool) -> list[dict]:
    """設計書ファイル名一覧と実ファイル名一覧を突合してレコードを返す。"""

    def normalize(name: str) -> str:
        return name.lower() if ignore_case else name

    doc_set = {normalize(n): n for n in doc_names}
    actual_set = {normalize(n): n for n in actual_names}

    all_keys = sorted(set(doc_set.keys()) | set(actual_set.keys()))

    results = []
    for key in all_keys:
        in_doc = key in doc_set
        in_actual = key in actual_set

        # 表示用ファイル名（設計書側を優先、なければ実ファイル側）
        display_name = doc_set.get(key) or actual_set.get(key)

        if in_doc and in_actual:
            judgment = "一致"
        elif in_doc and not in_actual:
            judgment = "設計書のみ"
        else:
            judgment = "実ファイルのみ"

        results.append({
            "ファイル名": display_name,
            "設計書": "○" if in_doc else "-",
            "実ファイル": "○" if in_actual else "-",
            "判定": judgment,
        })

    return results


# -----------------------------------------------------------------------
# CSV 出力
# -----------------------------------------------------------------------

def write_csv(results: list[dict], output_path: str, encoding: str) -> None:
    """突合結果をCSVに書き出す。"""
    fieldnames = ["ファイル名", "設計書", "実ファイル", "判定"]
    with open(output_path, "w", newline="", encoding=encoding) as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
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
            print(f"  [{r['判定']}] {r['ファイル名']}")


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
    parser.add_argument("--output", "-o", default="check_existence_result.csv", help="出力CSVのパス（デフォルト: check_existence_result.csv）")
    parser.add_argument("--encoding", default="cp932", help="出力CSVの文字コード（デフォルト: cp932）")
    parser.add_argument("--ignore-case", action="store_true", default=True, help="ファイル名の大文字/小文字を区別しない（デフォルト: 区別しない）")
    parser.add_argument("--case-sensitive", action="store_true", help="ファイル名の大文字/小文字を区別する")

    args = parser.parse_args()

    # --case-sensitive が指定された場合は ignore_case を無効化
    ignore_case = not args.case_sensitive

    # ファイル存在確認
    for path, label in [(args.doc_csv, "設計書CSV"), (args.actual_csv, "実ファイルCSV")]:
        if not os.path.isfile(path):
            print(f"[ERROR] {label}が見つかりません: {path}", file=sys.stderr)
            sys.exit(1)

    print(f"設計書CSV    : {args.doc_csv}（列: {args.doc_col}）")
    print(f"実ファイルCSV: {args.actual_csv}（列: {args.actual_col}）")
    print(f"大文字小文字 : {'区別しない' if ignore_case else '区別する'}")
    print()

    # データ読み込み
    doc_names = load_csv(args.doc_csv, args.doc_col)
    actual_names = load_csv(args.actual_csv, args.actual_col)

    print(f"設計書側ファイル数    : {len(doc_names)} 件")
    print(f"実ファイル側ファイル数 : {len(actual_names)} 件")
    print()

    # 突合
    results = compare(doc_names, actual_names, ignore_case)

    # 出力
    write_csv(results, args.output, args.encoding)
    print_summary(results)
    print()
    print(f"出力先: {os.path.abspath(args.output)}")


if __name__ == "__main__":
    main()
