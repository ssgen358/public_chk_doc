"""
check_naming.py - 命名規約違反の検出ツール

【概要】
CSVファイルの指定列の値が、YAMLで定義した命名規約（正規表現パターン・
最大文字数・禁止語）に準拠しているかチェックし、違反行をCSVに出力する。
列ごとに異なるルールを定義できるため、カラム名・テーブル名・画面IDなど
複数の命名規約を1ファイルで管理できる。

【使い方】
  python check_naming.py <CSVファイル> --rules <ルールYAML> [オプション]

【引数】
  CSVファイル          チェック対象のCSVファイルのパス
  --rules, -r          命名規約ルール定義YAMLファイルのパス（必須）
  --output, -o         出力CSVのパス（省略時: check_naming_result.csv）
  --encoding           出力CSVの文字コード（省略時: cp932）

【出力CSVの列】
  行番号, 列名, 値, 違反種別, 詳細

  違反種別の値:
    パターン不一致   : 許可パターン（正規表現）に一致しない
    文字数超過       : max_length を超えている
    禁止語あり       : forbidden_words に含まれる語が使用されている
    必須値なし       : allow_empty: false かつ値が空

【依存ライブラリ】
  pip install pyyaml

【使用例】
  python check_naming.py design.csv --rules naming_rules.yaml
  python check_naming.py design.csv --rules naming_rules.yaml --output result.csv
"""

import argparse
import csv
import os
import re
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
class NamingViolation:
    row_num: int          # CSVの行番号（ヘッダー除く1始まり）
    col_name: str         # 列名
    value: str            # セルの値
    violation_type: str   # 違反種別
    detail: str           # 詳細メッセージ


# -----------------------------------------------------------------------
# ルール読み込み
# -----------------------------------------------------------------------

def load_rules(rules_path: str) -> list[dict]:
    """YAMLルール定義ファイルを読み込み、rulesリストを返す。"""
    with open(rules_path, encoding="utf-8") as f:
        data = yaml.safe_load(f)

    if not isinstance(data, dict) or "rules" not in data:
        print("[ERROR] ルールYAMLに 'rules' キーが見つかりません。", file=sys.stderr)
        sys.exit(1)

    rules = data["rules"]
    if not isinstance(rules, list):
        print("[ERROR] 'rules' はリスト形式で定義してください。", file=sys.stderr)
        sys.exit(1)

    # 正規表現のコンパイル（起動時に一括チェック）
    for rule in rules:
        pattern_str = rule.get("pattern")
        if pattern_str:
            try:
                rule["_compiled_pattern"] = re.compile(pattern_str)
            except re.error as e:
                print(
                    f"[ERROR] 正規表現のコンパイルエラー "
                    f"(target={rule.get('target')}, pattern={pattern_str}): {e}",
                    file=sys.stderr,
                )
                sys.exit(1)
        else:
            rule["_compiled_pattern"] = None

    return rules


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
# 命名規約チェック処理
# -----------------------------------------------------------------------

def check_single_value(
    row_num: int,
    col_name: str,
    value: str,
    rule: dict,
) -> list[NamingViolation]:
    """1つのセル値に対してルールを適用し、違反リストを返す。"""
    violations: list[NamingViolation] = []
    stripped = value.strip()

    # 空値チェック
    allow_empty = rule.get("allow_empty", True)
    if not stripped:
        if not allow_empty:
            violations.append(NamingViolation(
                row_num=row_num,
                col_name=col_name,
                value=value,
                violation_type="必須値なし",
                detail=f"列「{col_name}」は空値を許可していません",
            ))
        return violations  # 空値の場合は以降のチェックをスキップ

    # パターンチェック
    compiled = rule.get("_compiled_pattern")
    if compiled is not None:
        if not compiled.match(stripped):
            pattern_str = rule.get("pattern", "")
            description = rule.get("description", "")
            detail = f"許可パターン「{pattern_str}」に一致しません"
            if description:
                detail += f"（{description}）"
            violations.append(NamingViolation(
                row_num=row_num,
                col_name=col_name,
                value=stripped,
                violation_type="パターン不一致",
                detail=detail,
            ))

    # 最大文字数チェック
    max_length = rule.get("max_length")
    if max_length is not None:
        actual_length = len(stripped)
        if actual_length > max_length:
            violations.append(NamingViolation(
                row_num=row_num,
                col_name=col_name,
                value=stripped,
                violation_type="文字数超過",
                detail=f"文字数 {actual_length} が最大文字数 {max_length} を超えています",
            ))

    # 禁止語チェック
    forbidden_words = rule.get("forbidden_words", [])
    for word in forbidden_words:
        if word.lower() in stripped.lower():
            violations.append(NamingViolation(
                row_num=row_num,
                col_name=col_name,
                value=stripped,
                violation_type="禁止語あり",
                detail=f"禁止語「{word}」が含まれています",
            ))

    return violations


def check_naming(
    rows: list[dict],
    fieldnames: list[str],
    rules: list[dict],
) -> tuple[list[NamingViolation], list[str]]:
    """全行・全ルールに対して命名規約チェックを実施する。

    Returns:
        (violations, skipped_targets):
          violations       : 違反リスト
          skipped_targets  : CSVに存在しなかったルールのtarget列名リスト
    """
    violations: list[NamingViolation] = []
    skipped_targets: list[str] = []

    for rule in rules:
        target_col = rule.get("target", "")
        if not target_col:
            continue

        # CSVに対象列が存在するか確認
        if target_col not in fieldnames:
            skipped_targets.append(target_col)
            continue

        for row_idx, row in enumerate(rows):
            row_num = row_idx + 1
            value = row.get(target_col, "")
            if value is None:
                value = ""

            row_violations = check_single_value(row_num, target_col, str(value), rule)
            violations.extend(row_violations)

    return violations, skipped_targets


# -----------------------------------------------------------------------
# CSV 出力
# -----------------------------------------------------------------------

def write_csv(
    violations: list[NamingViolation],
    output_path: str,
    encoding: str,
) -> None:
    """チェック結果をCSVに書き出す。"""
    fieldnames = ["行番号", "列名", "値", "違反種別", "詳細"]
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    with open(output_path, "w", newline="", encoding=encoding) as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for v in violations:
            writer.writerow({
                "行番号": v.row_num,
                "列名": v.col_name,
                "値": v.value,
                "違反種別": v.violation_type,
                "詳細": v.detail,
            })


# -----------------------------------------------------------------------
# サマリー表示
# -----------------------------------------------------------------------

def print_summary(
    violations: list[NamingViolation],
    rows: list[dict],
    rules: list[dict],
    skipped_targets: list[str],
) -> None:
    """チェック結果のサマリーをコンソール出力する。"""
    # 列ごとの件数集計
    col_counts: dict[str, int] = {}
    for v in violations:
        col_counts[v.col_name] = col_counts.get(v.col_name, 0) + 1

    print("-" * 50)
    print("命名規約チェック結果サマリー")
    print(f"  チェック対象行数    : {len(rows)} 行")
    print(f"  チェック対象ルール数: {len(rules)} 件")
    print(f"  違反合計            : {len(violations)} 件")

    if skipped_targets:
        print(f"  ※ CSV に存在しないためスキップした列: {skipped_targets}")

    print("-" * 50)

    if violations:
        print("【違反種別の内訳】")
        type_counts: dict[str, int] = {}
        for v in violations:
            type_counts[v.violation_type] = type_counts.get(v.violation_type, 0) + 1
        for vtype, count in sorted(type_counts.items()):
            print(f"  {vtype}: {count} 件")
        print()

        print("【違反一覧】")
        for v in violations:
            print(f"  行{v.row_num} / {v.col_name}: 「{v.value}」 [{v.violation_type}] {v.detail}")
    else:
        print("  命名規約違反は検出されませんでした。")


# -----------------------------------------------------------------------
# メイン
# -----------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="CSVの指定列が命名規約に準拠しているかチェックするツール"
    )
    parser.add_argument("csv_file", help="チェック対象のCSVファイルのパス")
    parser.add_argument("--rules", "-r", required=True, help="命名規約ルール定義YAMLファイルのパス")
    parser.add_argument("--output", "-o", default="check_naming_result.csv",
                        help="出力CSVのパス（デフォルト: check_naming_result.csv）")
    parser.add_argument("--encoding", default="cp932",
                        help="出力CSVの文字コード（デフォルト: cp932）")

    args = parser.parse_args()

    # ファイル存在確認
    if not os.path.isfile(args.csv_file):
        print(f"[ERROR] CSVファイルが見つかりません: {args.csv_file}", file=sys.stderr)
        sys.exit(1)
    if not os.path.isfile(args.rules):
        print(f"[ERROR] ルールYAMLファイルが見つかりません: {args.rules}", file=sys.stderr)
        sys.exit(1)

    # ルール読み込み
    rules = load_rules(args.rules)

    # CSV読み込み
    rows, fieldnames = load_csv(args.csv_file)

    print(f"対象CSVファイル : {args.csv_file}")
    print(f"ルールファイル  : {args.rules}")
    print(f"ルール数        : {len(rules)} 件")
    print(f"対象列          : {[r.get('target') for r in rules]}")
    print()

    # チェック実施
    violations, skipped_targets = check_naming(rows, fieldnames, rules)

    # 結果出力
    write_csv(violations, args.output, args.encoding)
    print_summary(violations, rows, rules, skipped_targets)
    print()
    print(f"出力先: {os.path.abspath(args.output)}")


if __name__ == "__main__":
    main()
