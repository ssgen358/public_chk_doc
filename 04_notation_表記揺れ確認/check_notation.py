"""
check_notation.py - 表記揺れ検出ツール

【概要】
CSVファイルの指定列（省略時は全列）を対象に、YAMLで定義した
表記揺れ対応表と照合し、非推奨の表記が使われていないかチェックする。
部分一致モードでは「ユーザー」を除いた残りテキストに「ユーザ」がないか
検索するため、正規表記と揺れ表記が混在するケースも正確に検出できる。

【使い方】
  python check_notation.py <CSVファイル> --rules <ルールYAML> [オプション]

【引数】
  CSVファイル          チェック対象のCSVファイルのパス
  --rules, -r          表記揺れルール定義YAMLファイルのパス（必須）
  --cols               チェック対象の列名（スペース区切り、省略時は全列）
  --output, -o         出力CSVのパス（省略時: check_notation_result.csv）
  --encoding           出力CSVの文字コード（省略時: cp932）
  --partial            部分一致モードで検索する（省略時: 完全一致）
  --case-sensitive     大文字/小文字を区別する（省略時: 区別しない）

【出力CSVの列】
  行番号, 列名, セル値, 正規表記, 検出語, 詳細

【依存ライブラリ】
  pip install pyyaml

【使用例】
  python check_notation.py design.csv --rules notation_rules.yaml
  python check_notation.py design.csv --rules notation_rules.yaml --partial
  python check_notation.py design.csv --rules notation_rules.yaml --cols カラム名 画面名
  python check_notation.py design.csv --rules notation_rules.yaml --partial --output result.csv
"""

import argparse
import csv
import os
import sys
from dataclasses import dataclass

try:
    import yaml
except ImportError:
    print("[ERROR] pyyaml がインストールされていません。: pip install pyyaml", file=sys.stderr)
    sys.exit(1)


# -----------------------------------------------------------------------
# データクラス
# -----------------------------------------------------------------------

@dataclass
class NotationViolation:
    row_num: int       # CSVの行番号（ヘッダー除く1始まり）
    col_name: str      # 列名
    cell_value: str    # セルの値
    correct: str       # 正規表記
    detected: str      # 検出された揺れ語
    detail: str        # 詳細メッセージ


# -----------------------------------------------------------------------
# ルール読み込み
# -----------------------------------------------------------------------

def load_rules(rules_path: str) -> list[dict]:
    """YAMLルール定義ファイルを読み込み、synonymsリストを返す。"""
    with open(rules_path, encoding="utf-8") as f:
        data = yaml.safe_load(f)

    if not isinstance(data, dict) or "synonyms" not in data:
        print("[ERROR] ルールYAMLに 'synonyms' キーが見つかりません。", file=sys.stderr)
        sys.exit(1)

    synonyms = data["synonyms"]
    if not isinstance(synonyms, list):
        print("[ERROR] 'synonyms' はリスト形式で定義してください。", file=sys.stderr)
        sys.exit(1)

    return synonyms


# -----------------------------------------------------------------------
# CSV 読み込み
# -----------------------------------------------------------------------

def load_csv(path: str) -> tuple[list[dict], list[str]]:
    """CSVファイルを読み込む。UTF-8 / CP932 の両方に対応。"""
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


# -----------------------------------------------------------------------
# 表記揺れチェック処理
# -----------------------------------------------------------------------

def find_variants_in_text(
    text: str,
    correct: str,
    variants: list[str],
    partial: bool,
    ignore_case: bool,
) -> list[str]:
    """テキスト中に揺れ語が含まれるか調べ、検出された揺れ語のリストを返す。

    部分一致モード（partial=True）では:
      テキストから正規表記をすべて除去した残りに揺れ語が含まれるか検索する。
      これにより「ユーザー管理とユーザ一覧」のような混在ケースも検出できる。

    完全一致モード（partial=False）では:
      テキスト全体が揺れ語に等しいか判定する。
    """
    def normalize(s: str) -> str:
        return s.lower() if ignore_case else s

    detected = []

    if partial:
        # 正規表記を除去した残りテキストで揺れ語を検索
        normalized_correct = normalize(correct)
        remaining = normalize(text).replace(normalized_correct, "")
        for variant in variants:
            if normalize(variant) in remaining:
                detected.append(variant)
    else:
        # 完全一致チェック
        normalized_text = normalize(text.strip())
        for variant in variants:
            if normalized_text == normalize(variant):
                detected.append(variant)

    return detected


def check_notation(
    rows: list[dict],
    cols: list[str],
    synonyms: list[dict],
    partial: bool,
    ignore_case: bool,
) -> list[NotationViolation]:
    """CSV全行の指定列に対して表記揺れチェックを実施する。"""
    violations: list[NotationViolation] = []

    for row_idx, row in enumerate(rows):
        row_num = row_idx + 1  # 1始まり

        for col in cols:
            cell_value = row.get(col, "")
            if cell_value is None:
                cell_value = ""
            cell_value = str(cell_value).strip()

            if not cell_value:
                continue  # 空セルはスキップ

            for synonym in synonyms:
                correct = synonym.get("correct", "")
                variants = synonym.get("variants", [])

                if not correct or not variants:
                    continue

                detected_list = find_variants_in_text(
                    cell_value, correct, variants, partial, ignore_case
                )

                for detected in detected_list:
                    mode_str = "部分一致" if partial else "完全一致"
                    violations.append(NotationViolation(
                        row_num=row_num,
                        col_name=col,
                        cell_value=cell_value,
                        correct=correct,
                        detected=detected,
                        detail=f"{mode_str}で「{detected}」を検出。正規表記は「{correct}」",
                    ))

    return violations


# -----------------------------------------------------------------------
# CSV 出力
# -----------------------------------------------------------------------

def write_csv(
    violations: list[NotationViolation],
    output_path: str,
    encoding: str,
) -> None:
    """チェック結果をCSVに書き出す。"""
    fieldnames = ["行番号", "列名", "セル値", "正規表記", "検出語", "詳細"]
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    with open(output_path, "w", newline="", encoding=encoding) as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for v in violations:
            writer.writerow({
                "行番号": v.row_num,
                "列名": v.col_name,
                "セル値": v.cell_value,
                "正規表記": v.correct,
                "検出語": v.detected,
                "詳細": v.detail,
            })


# -----------------------------------------------------------------------
# サマリー表示
# -----------------------------------------------------------------------

def print_summary(
    violations: list[NotationViolation],
    rows: list[dict],
    cols: list[str],
    partial: bool,
) -> None:
    """チェック結果のサマリーをコンソール出力する。"""
    mode_str = "部分一致" if partial else "完全一致"
    print("-" * 50)
    print("表記揺れチェック結果サマリー")
    print(f"  チェックモード: {mode_str}")
    print(f"  チェック対象行数: {len(rows)} 行")
    print(f"  チェック対象列: {cols}")
    print(f"  検出件数: {len(violations)} 件")
    print("-" * 50)

    if violations:
        print("【検出一覧】")
        for v in violations:
            print(f"  行{v.row_num} / {v.col_name}: 「{v.detected}」→ 正規:「{v.correct}」 (値: {v.cell_value})")
    else:
        print("  表記揺れは検出されませんでした。")


# -----------------------------------------------------------------------
# メイン
# -----------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="CSVの指定列に表記揺れがないかチェックするツール"
    )
    parser.add_argument("csv_file", help="チェック対象のCSVファイルのパス")
    parser.add_argument("--rules", "-r", required=True, help="表記揺れルール定義YAMLファイルのパス")
    parser.add_argument("--cols", nargs="+", help="チェック対象の列名（省略時は全列）")
    parser.add_argument("--output", "-o", default="check_notation_result.csv",
                        help="出力CSVのパス（デフォルト: check_notation_result.csv）")
    parser.add_argument("--encoding", default="cp932",
                        help="出力CSVの文字コード（デフォルト: cp932）")
    parser.add_argument("--partial", action="store_true",
                        help="部分一致モードで検索する（省略時: 完全一致）")
    parser.add_argument("--case-sensitive", action="store_true",
                        help="大文字/小文字を区別する（省略時: 区別しない）")

    args = parser.parse_args()
    ignore_case = not args.case_sensitive

    # ファイル存在確認
    if not os.path.isfile(args.csv_file):
        print(f"[ERROR] CSVファイルが見つかりません: {args.csv_file}", file=sys.stderr)
        sys.exit(1)
    if not os.path.isfile(args.rules):
        print(f"[ERROR] ルールYAMLファイルが見つかりません: {args.rules}", file=sys.stderr)
        sys.exit(1)

    # ルール読み込み
    synonyms = load_rules(args.rules)

    # CSV読み込み
    rows, fieldnames = load_csv(args.csv_file)

    # チェック対象列の決定
    if args.cols:
        missing = [c for c in args.cols if c not in fieldnames]
        if missing:
            print(f"[ERROR] 以下の列がCSVに見つかりません: {missing}", file=sys.stderr)
            print(f"        利用可能な列名: {fieldnames}", file=sys.stderr)
            sys.exit(1)
        cols = args.cols
    else:
        cols = fieldnames  # 全列チェック

    mode_str = "部分一致" if args.partial else "完全一致"
    print(f"対象CSVファイル : {args.csv_file}")
    print(f"ルールファイル  : {args.rules}")
    print(f"チェック対象列  : {cols}")
    print(f"チェックモード  : {mode_str}")
    print(f"大文字小文字    : {'区別しない' if ignore_case else '区別する'}")
    print(f"揺れルール数    : {len(synonyms)} 件")
    print()

    # チェック実施
    violations = check_notation(rows, cols, synonyms, args.partial, ignore_case)

    # 結果出力
    write_csv(violations, args.output, args.encoding)
    print_summary(violations, rows, cols, args.partial)
    print()
    print(f"出力先: {os.path.abspath(args.output)}")


if __name__ == "__main__":
    main()
