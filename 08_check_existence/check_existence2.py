"""
check_existence2.py - 軸ファイル方式の突合チェックツール

【概要】
軸ファイル（A）の全列をそのまま出力しつつ、比較ファイル（B）のキー列の値を
横に付加して突合する。軸ファイルの行順は保持される。
比較ファイルにのみ存在する行は末尾にまとめて追記される。

【使い方】
  python check_existence2.py --axis A.csv --compare B.csv [オプション]

【引数】
  --axis           軸ファイルのCSVパス（全列を出力）
  --compare        比較ファイルのCSVパス
  --axis-key       軸ファイルのキー列名（デフォルト: ファイル名）
  --compare-key    比較ファイルのキー列名（デフォルト: ファイル名）
  --compare-label  出力CSV上での比較列のヘッダ名（デフォルト: 比較）
  --output, -o     出力CSVのパス（デフォルト: check_existence2_result.csv）
  --encoding       出力CSVの文字コード（デフォルト: cp932）
  --case-sensitive キー列の大文字/小文字を区別する（省略時: 区別しない）

【出力CSVの構造】
  軸ファイルの全列 + 比較列（Bのキー値） + 判定列
  ・判定の値: 一致 / 軸のみ / 比較のみ
  ・軸ファイルの行順はそのまま維持される
  ・比較ファイルにのみ存在する行は末尾にまとめて追記される

【使用例】
  python check_existence2.py --axis 設計書.csv --compare 実ファイル.csv
  python check_existence2.py --axis 設計書.csv --compare 実ファイル.csv \\
      --axis-key ファイル名 --compare-key ファイル名 --compare-label 実ファイル
  python check_existence2.py --axis A.csv --compare B.csv -o result.csv
"""

import argparse
import csv
import os
import sys


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

    print(f"[ERROR] ファイルの文字コードが判別できません（UTF-8 または CP932 で保存してください）: {path}", file=sys.stderr)
    sys.exit(1)


def validate_key_col(fieldnames: list[str], key_col: str, label: str, path: str) -> None:
    """キー列が存在するか確認する。存在しない場合はエラー終了。"""
    if key_col not in fieldnames:
        print(f"[ERROR] {label}に '{key_col}' 列が見つかりません: {path}", file=sys.stderr)
        print(f"        利用可能な列名: {fieldnames}", file=sys.stderr)
        sys.exit(1)


# -----------------------------------------------------------------------
# 突合処理
# -----------------------------------------------------------------------

def compare(
    axis_rows: list[dict],
    axis_fieldnames: list[str],
    axis_key: str,
    compare_rows: list[dict],
    compare_key: str,
    compare_label: str,
    ignore_case: bool,
) -> list[dict]:
    """軸ファイルの行順を保持しながら突合し、結果レコードを返す。

    処理の流れ:
      1. 比較ファイルをキー→値のマップに変換する
      2. 軸ファイルの全行を走査し、比較ファイルに存在するか判定する
      3. 比較ファイルにのみ存在する行を末尾に追記する

    Returns:
        突合結果のリスト（軸ファイルの全列 + compare_label列 + 判定列）
    """
    def normalize(value: str) -> str:
        return value.lower() if ignore_case else value

    # 比較ファイルを正規化キー → 元の値（表示用）に変換
    # 重複キーは後勝ちで警告を出す
    compare_map: dict[str, str] = {}
    compare_order: list[str] = []  # B-only行の順序保持用

    for row in compare_rows:
        val = row.get(compare_key, "").strip()
        if not val:
            continue
        norm = normalize(val)
        if norm in compare_map:
            print(f"[WARN] 比較ファイルにキーの重複があります（後の値を使用）: '{val}'")
        else:
            compare_order.append(norm)
        compare_map[norm] = val

    results: list[dict] = []
    matched_keys: set[str] = set()

    # --- 軸ファイルの行を処理（行順を保持）---
    for i, row in enumerate(axis_rows, start=2):
        axis_val = row.get(axis_key, "").strip()
        if not axis_val:
            print(f"[WARN] 軸ファイル {i}行目: '{axis_key}' が空のためスキップします。")
            continue

        norm = normalize(axis_val)

        if norm in compare_map:
            compare_val = compare_map[norm]
            judgment = "一致"
            matched_keys.add(norm)
        else:
            compare_val = "-"
            judgment = "軸のみ"

        result = {col: row.get(col, "") for col in axis_fieldnames}
        result[compare_label] = compare_val
        result["判定"] = judgment
        results.append(result)

    # --- 比較ファイルにのみ存在する行を末尾に追記（比較ファイルの行順を保持）---
    for norm in compare_order:
        if norm not in matched_keys:
            orig_val = compare_map[norm]
            result = {col: "" for col in axis_fieldnames}
            result[compare_label] = orig_val
            result["判定"] = "比較のみ"
            results.append(result)

    return results


# -----------------------------------------------------------------------
# CSV 出力
# -----------------------------------------------------------------------

def write_csv(
    results: list[dict],
    fieldnames: list[str],
    output_path: str,
    encoding: str,
) -> None:
    """突合結果をCSVに書き出す。"""
    with open(output_path, "w", newline="", encoding=encoding) as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(results)


# -----------------------------------------------------------------------
# サマリー表示
# -----------------------------------------------------------------------

def print_summary(results: list[dict], axis_key: str, compare_label: str) -> None:
    """突合結果のサマリーをコンソール出力する。"""
    total = len(results)
    matched = sum(1 for r in results if r["判定"] == "一致")
    axis_only = sum(1 for r in results if r["判定"] == "軸のみ")
    compare_only = sum(1 for r in results if r["判定"] == "比較のみ")

    print("-" * 50)
    print("突合結果サマリー")
    print(f"  合計     : {total} 件")
    print(f"  一致     : {matched} 件")
    print(f"  軸のみ   : {axis_only} 件（要確認）")
    print(f"  比較のみ : {compare_only} 件（要確認）")
    print("-" * 50)

    issues = [r for r in results if r["判定"] != "一致"]
    if issues:
        print("【要確認一覧】")
        for r in issues:
            # 軸のみ → 軸キー列の値、比較のみ → 比較列の値を表示
            if r["判定"] == "軸のみ":
                key_display = r.get(axis_key, "")
            else:
                key_display = r.get(compare_label, "")
            print(f"  [{r['判定']}] {key_display}")


# -----------------------------------------------------------------------
# メイン
# -----------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="軸ファイル方式の突合チェックツール"
    )
    parser.add_argument("--axis", required=True,
                        help="軸ファイルのCSVパス（全列を出力）")
    parser.add_argument("--compare", required=True,
                        help="比較ファイルのCSVパス")
    parser.add_argument("--axis-key", default="ファイル名",
                        help="軸ファイルのキー列名（デフォルト: ファイル名）")
    parser.add_argument("--compare-key", default="ファイル名",
                        help="比較ファイルのキー列名（デフォルト: ファイル名）")
    parser.add_argument("--compare-label", default="比較",
                        help="出力CSV上での比較列のヘッダ名（デフォルト: 比較）")
    parser.add_argument("--output", "-o", default="check_existence2_result.csv",
                        help="出力CSVのパス（デフォルト: check_existence2_result.csv）")
    parser.add_argument("--encoding", default="cp932",
                        help="出力CSVの文字コード（デフォルト: cp932）")
    parser.add_argument("--case-sensitive", action="store_true",
                        help="キー列の大文字/小文字を区別する（省略時: 区別しない）")

    args = parser.parse_args()
    ignore_case = not args.case_sensitive

    # ファイル存在確認
    for path, label in [(args.axis, "軸ファイル"), (args.compare, "比較ファイル")]:
        if not os.path.isfile(path):
            print(f"[ERROR] {label}が見つかりません: {path}", file=sys.stderr)
            sys.exit(1)

    print(f"軸ファイル   : {args.axis}（キー列: {args.axis_key}）")
    print(f"比較ファイル : {args.compare}（キー列: {args.compare_key}）")
    print(f"比較列ラベル : {args.compare_label}")
    print(f"大文字小文字 : {'区別しない' if ignore_case else '区別する'}")
    print()

    # データ読み込み
    axis_rows, axis_fieldnames = load_csv(args.axis)
    compare_rows, compare_fieldnames = load_csv(args.compare)

    # キー列の存在確認
    validate_key_col(axis_fieldnames, args.axis_key, "軸ファイル", args.axis)
    validate_key_col(compare_fieldnames, args.compare_key, "比較ファイル", args.compare)

    print(f"軸ファイル行数   : {len(axis_rows)} 件")
    print(f"比較ファイル行数 : {len(compare_rows)} 件")
    print()

    # 突合
    results = compare(
        axis_rows, axis_fieldnames, args.axis_key,
        compare_rows, args.compare_key,
        args.compare_label,
        ignore_case,
    )

    # 出力列: 軸の全列 + 比較列 + 判定列
    output_fieldnames = axis_fieldnames + [args.compare_label, "判定"]

    write_csv(results, output_fieldnames, args.output, args.encoding)
    print_summary(results, args.axis_key, args.compare_label)
    print()
    print(f"出力先: {os.path.abspath(args.output)}")


if __name__ == "__main__":
    main()
