"""
check_format.py - Excelファイルのフォーマット準拠チェックツール

【概要】
YAMLで定義したテンプレートに対して、対象Excelファイルのフォーマットが
準拠しているかチェックし、結果をCSVに出力する。

【チェック内容】
  - シート名の一致     : テンプレートで定義したシートが存在するか
  - 列名・ヘッダーの一致: 指定行に期待する列名が存在するか
  - 必須セルの存在     : 指定セルに値が入力されているか

【使い方】
  python check_format.py <対象ファイルまたはフォルダ> --template <テンプレートYAML> [オプション]

【引数】
  target           チェック対象のExcelファイル、またはフォルダのパス
  --template, -t   テンプレート定義YAMLファイルのパス（必須）
  --output, -o     出力CSVのパス（省略時: check_format_result.csv）
  --no-recursive   フォルダ指定時にサブフォルダを含めない

【出力CSVの列】
  ファイル名, シート名, チェック項目, 結果, 詳細

  結果の値:
    OK   : チェック通過
    NG   : チェック失敗（required: true の項目）
    WARN : チェック失敗（required: false の項目）

【依存ライブラリ】
  pip install openpyxl pyyaml

【使用例】
  python check_format.py C:/work/設計書 --template template.yaml
  python check_format.py C:/work/設計書/画面設計書.xlsx --template template.yaml --output result.csv
  python check_format.py C:/work/設計書 --template template.yaml --no-recursive
"""

import argparse
import csv
import os
import sys
from dataclasses import dataclass

try:
    import openpyxl
except ImportError:
    print("[ERROR] openpyxl がインストールされていません。: pip install openpyxl", file=sys.stderr)
    sys.exit(1)

try:
    import yaml
except ImportError:
    print("[ERROR] pyyaml がインストールされていません。: pip install pyyaml", file=sys.stderr)
    sys.exit(1)


# -----------------------------------------------------------------------
# データクラス
# -----------------------------------------------------------------------

@dataclass
class CheckResult:
    file_name: str
    sheet_name: str
    check_item: str
    result: str   # "OK" / "NG" / "WARN"
    detail: str


# -----------------------------------------------------------------------
# テンプレート読み込み
# -----------------------------------------------------------------------

def load_template(template_path: str) -> dict:
    """YAMLテンプレート定義ファイルを読み込む。"""
    with open(template_path, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict) or "sheets" not in data:
        print("[ERROR] テンプレートYAMLに 'sheets' キーが見つかりません。", file=sys.stderr)
        sys.exit(1)
    return data


# -----------------------------------------------------------------------
# チェック処理
# -----------------------------------------------------------------------

def check_excel(file_path: str, template: dict) -> list[CheckResult]:
    """1つのExcelファイルに対してフォーマットチェックを実施する。"""
    results = []
    file_name = os.path.basename(file_path)

    # ファイル読み込み
    try:
        wb = openpyxl.load_workbook(file_path, data_only=True)
    except Exception as e:
        results.append(CheckResult(
            file_name=file_name,
            sheet_name="-",
            check_item="ファイル読み込み",
            result="NG",
            detail=f"読み込みエラー: {e}",
        ))
        return results

    actual_sheet_names = wb.sheetnames

    for sheet_def in template.get("sheets", []):
        expected_sheet = sheet_def.get("name", "")
        required = sheet_def.get("required", True)

        # ── シート名チェック ──────────────────────────────────────────
        if expected_sheet not in actual_sheet_names:
            results.append(CheckResult(
                file_name=file_name,
                sheet_name=expected_sheet,
                check_item="シート名の一致",
                result="NG" if required else "WARN",
                detail=f"シート '{expected_sheet}' が存在しない",
            ))
            continue  # シートがないので以降のチェックはスキップ

        results.append(CheckResult(
            file_name=file_name,
            sheet_name=expected_sheet,
            check_item="シート名の一致",
            result="OK",
            detail=f"シート '{expected_sheet}' が存在する",
        ))

        ws = wb[expected_sheet]

        # ── 列名・ヘッダーチェック ────────────────────────────────────
        headers_def = sheet_def.get("headers")
        if headers_def:
            header_row_num = headers_def.get("row", 1)
            expected_columns = headers_def.get("columns", [])

            # 指定行のセル値を取得（空白除去・文字列化）
            actual_headers = []
            for cell in ws[header_row_num]:
                if cell.value is not None:
                    actual_headers.append(str(cell.value).strip())

            for col_name in expected_columns:
                if col_name in actual_headers:
                    results.append(CheckResult(
                        file_name=file_name,
                        sheet_name=expected_sheet,
                        check_item="列名の一致",
                        result="OK",
                        detail=f"{header_row_num}行目に列 '{col_name}' が存在する",
                    ))
                else:
                    results.append(CheckResult(
                        file_name=file_name,
                        sheet_name=expected_sheet,
                        check_item="列名の一致",
                        result="NG",
                        detail=f"{header_row_num}行目に列 '{col_name}' が存在しない",
                    ))

        # ── 必須セルチェック ──────────────────────────────────────────
        for cell_def in sheet_def.get("cells", []):
            address = cell_def.get("address", "")
            label = cell_def.get("label", address)
            cell_required = cell_def.get("required", True)

            try:
                cell_value = ws[address].value
                has_value = cell_value is not None and str(cell_value).strip() != ""
            except Exception:
                has_value = False

            if has_value:
                result_str = "OK"
                detail = f"セル {address}（{label}）: 値あり"
            else:
                result_str = "NG" if cell_required else "WARN"
                detail = f"セル {address}（{label}）: 空欄"

            results.append(CheckResult(
                file_name=file_name,
                sheet_name=expected_sheet,
                check_item=f"必須セルの存在（{label}）",
                result=result_str,
                detail=detail,
            ))

    wb.close()
    return results


# -----------------------------------------------------------------------
# ファイル収集
# -----------------------------------------------------------------------

def collect_excel_files(target: str, recursive: bool) -> list[str]:
    """対象パスからチェック対象のExcelファイルを収集する。"""
    if os.path.isfile(target):
        if target.lower().endswith(".xlsx"):
            return [target]
        else:
            print(f"[ERROR] 対象ファイルが .xlsx ではありません: {target}", file=sys.stderr)
            sys.exit(1)

    if not os.path.isdir(target):
        print(f"[ERROR] 対象パスが見つかりません: {target}", file=sys.stderr)
        sys.exit(1)

    files = []
    if recursive:
        for dirpath, _, filenames in os.walk(target):
            for name in filenames:
                if name.lower().endswith(".xlsx") and not name.startswith("~$"):
                    files.append(os.path.join(dirpath, name))
    else:
        for entry in os.scandir(target):
            if entry.is_file() and entry.name.lower().endswith(".xlsx") and not entry.name.startswith("~$"):
                files.append(entry.path)

    return sorted(files)


# -----------------------------------------------------------------------
# CSV出力
# -----------------------------------------------------------------------

def write_csv(results: list[CheckResult], output_path: str) -> None:
    """チェック結果をCSVに書き出す。"""
    fieldnames = ["ファイル名", "シート名", "チェック項目", "結果", "詳細"]
    with open(output_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in results:
            writer.writerow({
                "ファイル名": r.file_name,
                "シート名": r.sheet_name,
                "チェック項目": r.check_item,
                "結果": r.result,
                "詳細": r.detail,
            })


# -----------------------------------------------------------------------
# サマリー表示
# -----------------------------------------------------------------------

def print_summary(results: list[CheckResult]) -> None:
    """チェック結果のサマリーをコンソール出力する。"""
    total = len(results)
    ok_count = sum(1 for r in results if r.result == "OK")
    ng_count = sum(1 for r in results if r.result == "NG")
    warn_count = sum(1 for r in results if r.result == "WARN")

    print("-" * 50)
    print(f"チェック結果サマリー")
    print(f"  合計  : {total} 件")
    print(f"  OK    : {ok_count} 件")
    print(f"  NG    : {ng_count} 件")
    print(f"  WARN  : {warn_count} 件")
    print("-" * 50)

    # NGのみ詳細表示
    ng_results = [r for r in results if r.result in ("NG", "WARN")]
    if ng_results:
        print("【NG / WARN 一覧】")
        for r in ng_results:
            print(f"  [{r.result}] {r.file_name} / {r.sheet_name} - {r.detail}")


# -----------------------------------------------------------------------
# メイン
# -----------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Excelファイルのフォーマット準拠チェックツール"
    )
    parser.add_argument("target", help="チェック対象のExcelファイル、またはフォルダのパス")
    parser.add_argument("--template", "-t", required=True, help="テンプレート定義YAMLファイルのパス")
    parser.add_argument("--output", "-o", default="check_format_result.csv", help="出力CSVのパス（デフォルト: check_format_result.csv）")
    parser.add_argument("--no-recursive", action="store_true", help="サブフォルダを含めない")

    args = parser.parse_args()

    # テンプレート読み込み
    if not os.path.isfile(args.template):
        print(f"[ERROR] テンプレートファイルが見つかりません: {args.template}", file=sys.stderr)
        sys.exit(1)

    template = load_template(args.template)

    # 対象ファイル収集
    recursive = not args.no_recursive
    excel_files = collect_excel_files(args.target, recursive)

    if not excel_files:
        print("対象のExcelファイルが見つかりませんでした。")
        sys.exit(0)

    print(f"対象ファイル数: {len(excel_files)} 件")
    print(f"テンプレート  : {args.template}")
    print()

    # チェック実施
    all_results: list[CheckResult] = []
    for file_path in excel_files:
        print(f"  チェック中: {os.path.basename(file_path)}")
        results = check_excel(file_path, template)
        all_results.extend(results)

    print()

    # 結果出力
    write_csv(all_results, args.output)
    print_summary(all_results)
    print()
    print(f"出力先: {args.output}")


if __name__ == "__main__":
    main()
