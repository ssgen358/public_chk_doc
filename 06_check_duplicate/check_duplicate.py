"""
check_duplicate.py - 重複定義・重複記述の検出ツール

【概要】
CSVファイルの指定列に重複する値がないかチェックする。
列は複数指定可能で、各列を独立してチェックする。
空値は重複扱いしない。

【使い方】
  python check_duplicate.py <CSVファイル> --cols <列名1> [列名2 ...] [オプション]

【引数】
  CSVファイル        チェック対象のCSVファイルのパス
  --cols             チェック対象の列名（スペース区切りで複数指定可）
  --output, -o       出力CSVのパス（デフォルト: check_duplicate_result.csv）
  --encoding         出力CSVの文字コード（デフォルト: cp932）
  --case-sensitive   値の大文字/小文字を区別する（省略時: 区別しない）

【出力CSVの構造】
  元のCSVの全列 + チェック列ごとに以下の2列を追加:
    {列名}_判定  : 重複あり / なし
    {列名}_グループ : 重複グループ番号（重複なしの場合は空）

【使用例】
  python check_duplicate.py 設計書.csv --cols ファイル名
  python check_duplicate.py 設計書.csv --cols 画面ID 画面名 -o result.csv
  python check_duplicate.py 設計書.csv --cols 項目ID --case-sensitive
"""

import argparse
import csv
import os
import sys
from collections import defaultdict


# -----------------------------------------------------------------------
# CSV 読み込み
# -----------------------------------------------------------------------

def load_csv(path: str) -> tuple[list[dict], list[str]]:
    """CSVファイルを全列読み込みする。UTF-8 / CP932 の両方に対応。

    Returns:
        (rows, fieldnames):
          rows       : 全行のデータ（list of dict）
          fieldnames : 列名リスト（元の順序を保持）
    """
    for encoding in ("utf-8-sig", "utf-8", "cp932"):
        try:
            with open(path, newline="", encoding=encoding) as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                fieldnames = list(reader.fieldnames) if reader.fieldnames else []
            return rows, fieldnames
        except UnicodeDecodeError:
            continue

    print(
        f"[ERROR] ファイルの文字コードが判別できません"
        f"（UTF-8 または CP932 で保存してください）: {path}",
        file=sys.stderr,
    )
    sys.exit(1)


def validate_cols(fieldnames: list[str], cols: list[str], path: str) -> None:
    """指定列が全て存在するか確認する。存在しない場合はエラー終了。"""
    missing = [c for c in cols if c not in fieldnames]
    if missing:
        print(f"[ERROR] 以下の列がCSVに見つかりません: {missing}", file=sys.stderr)
        print(f"        利用可能な列名: {fieldnames}", file=sys.stderr)
        sys.exit(1)


# -----------------------------------------------------------------------
# 重複チェック処理
# -----------------------------------------------------------------------

def check_duplicates(
    rows: list[dict],
    cols: list[str],
    ignore_case: bool,
) -> tuple[list[dict], dict[str, dict]]:
    """各列について独立して重複チェックを行い、判定・グループ番号を付加する。

    Returns:
        (result_rows, stats):
          result_rows : 全行データに判定列・グループ列を付加したリスト
          stats       : 列ごとの集計情報 {列名: {"total": int, "duplicated": int, "groups": int}}
    """
    def normalize(value: str) -> str:
        return value.lower() if ignore_case else value

    # 列ごとに: 正規化キー → 出現行インデックスリスト
    col_index: dict[str, dict[str, list[int]]] = {}
    for col in cols:
        index: dict[str, list[int]] = defaultdict(list)
        for i, row in enumerate(rows):
            val = row.get(col, "").strip()
            if not val:
                continue  # 空値はスキップ
            norm = normalize(val)
            index[norm].append(i)
        col_index[col] = index

    # 列ごとに: 行インデックス → (判定, グループ番号)
    col_judgments: dict[str, dict[int, tuple[str, str]]] = {}
    stats: dict[str, dict] = {}

    for col in cols:
        index = col_index[col]
        row_results: dict[int, tuple[str, str]] = {}
        group_num = 0
        duplicated_row_count = 0

        for norm, indices in index.items():
            if len(indices) >= 2:
                group_num += 1
                duplicated_row_count += len(indices)
                for idx in indices:
                    row_results[idx] = ("重複あり", str(group_num))
            else:
                row_results[indices[0]] = ("なし", "")

        col_judgments[col] = row_results
        stats[col] = {
            "total": sum(len(v) for v in index.values()),  # 非空値の行数
            "duplicated": duplicated_row_count,
            "groups": group_num,
        }

    # 全行に判定列・グループ列を付加
    result_rows: list[dict] = []
    for i, row in enumerate(rows):
        result = dict(row)
        for col in cols:
            judgment_map = col_judgments[col]
            if i in judgment_map:
                judgment, group = judgment_map[i]
            else:
                # 空値の行
                judgment, group = ("", "")
            result[f"{col}_判定"] = judgment
            result[f"{col}_グループ"] = group
        result_rows.append(result)

    return result_rows, stats


# -----------------------------------------------------------------------
# CSV 出力
# -----------------------------------------------------------------------

def write_csv(
    results: list[dict],
    fieldnames: list[str],
    output_path: str,
    encoding: str,
) -> None:
    """チェック結果をCSVに書き出す。"""
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    with open(output_path, "w", newline="", encoding=encoding) as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(results)


# -----------------------------------------------------------------------
# サマリー表示
# -----------------------------------------------------------------------

def print_summary(
    result_rows: list[dict],
    cols: list[str],
    stats: dict[str, dict],
) -> None:
    """チェック結果のサマリーをコンソール出力する。"""
    total_rows = len(result_rows)

    print("-" * 50)
    print("重複チェック結果サマリー")
    print(f"  総行数: {total_rows} 件")
    print()

    for col in cols:
        s = stats[col]
        print(f"  【{col}】")
        print(f"    チェック対象（非空値）: {s['total']} 件")
        print(f"    重複あり              : {s['duplicated']} 件")
        print(f"    重複グループ数        : {s['groups']} グループ")

        if s["duplicated"] > 0:
            print(f"    重複一覧:")
            # グループ番号ごとにまとめて表示
            from collections import defaultdict as dd
            groups: dict[str, list[str]] = dd(list)
            for row in result_rows:
                if row.get(f"{col}_判定") == "重複あり":
                    grp = row.get(f"{col}_グループ", "")
                    val = row.get(col, "")
                    if val not in groups[grp]:
                        groups[grp].append(val)
            for grp in sorted(groups.keys(), key=lambda x: int(x)):
                vals = groups[grp]
                print(f"      グループ{grp}: {', '.join(vals)}")
        print()

    print("-" * 50)


# -----------------------------------------------------------------------
# メイン
# -----------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="CSVの指定列に重複する値がないかチェックするツール"
    )
    parser.add_argument("csv_file",
                        help="チェック対象のCSVファイルのパス")
    parser.add_argument("--cols", nargs="+", required=True,
                        help="チェック対象の列名（スペース区切りで複数指定可）")
    parser.add_argument("--output", "-o", default="check_duplicate_result.csv",
                        help="出力CSVのパス（デフォルト: check_duplicate_result.csv）")
    parser.add_argument("--encoding", default="cp932",
                        help="出力CSVの文字コード（デフォルト: cp932）")
    parser.add_argument("--case-sensitive", action="store_true",
                        help="値の大文字/小文字を区別する（省略時: 区別しない）")

    args = parser.parse_args()
    ignore_case = not args.case_sensitive

    # ファイル存在確認
    if not os.path.isfile(args.csv_file):
        print(f"[ERROR] CSVファイルが見つかりません: {args.csv_file}", file=sys.stderr)
        sys.exit(1)

    print(f"対象CSVファイル : {args.csv_file}")
    print(f"チェック列      : {args.cols}")
    print(f"大文字小文字    : {'区別しない' if ignore_case else '区別する'}")
    print()

    # データ読み込み
    rows, fieldnames = load_csv(args.csv_file)

    # 列の存在確認
    validate_cols(fieldnames, args.cols, args.csv_file)

    print(f"読み込み行数: {len(rows)} 件")
    print()

    # 重複チェック
    result_rows, stats = check_duplicates(rows, args.cols, ignore_case)

    # 出力列: 元の全列 + チェック列ごとに _判定 / _グループ 列
    output_fieldnames = list(fieldnames)
    for col in args.cols:
        output_fieldnames.append(f"{col}_判定")
        output_fieldnames.append(f"{col}_グループ")

    write_csv(result_rows, output_fieldnames, args.output, args.encoding)
    print_summary(result_rows, args.cols, stats)
    print(f"出力先: {os.path.abspath(args.output)}")


if __name__ == "__main__":
    main()
