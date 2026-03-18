"""
keyword_search.py - キーワード検索ツール

【概要】
指定したフォルダ配下のファイルを対象に、特定のキーワードを含む行・セルを検索し、
ファイル名と該当箇所の内容を一覧で出力する。
テキスト系ファイル（.txt/.csv/.md 等）、Excel（.xlsx/.xls）、Word（.docx）に対応。

【使い方】
  単一フォルダ指定:
    python keyword_search.py <フォルダパス> <キーワード> [オプション]

  複数フォルダ指定（テキストファイル）:
    python keyword_search.py <キーワード> --folders-file <テキストファイルパス> [オプション]

  ※ テキストファイルは1行1フォルダパスで記載（空行・#始まり行はスキップ）

【オプション】
  --folders-file テキストファイルから対象フォルダを複数読み込む（1行1フォルダ）
  --ext          対象拡張子をカンマ区切りで指定（省略時: .txt,.csv,.md,.xlsx,.xls,.docx）
                 例: --ext .xlsx,.csv
  --filename     ファイル名フィルタ（ワイルドカード対応、省略時: 全ファイル）
                 例: --filename "IF*.xlsx"
  --no-recursive サブフォルダを含めない（省略時: サブフォルダも含める）
  --ignore-case  大文字/小文字を区別しない（省略時: 区別する）
  --outdir       出力先フォルダのパス（省略時: このスクリプトと同じフォルダ）
  --encoding     CSVの文字コード（省略時: cp932＝Excelでそのまま開いて文字化けしない）

【出力列】
  ファイルパス, ファイル名, 場所, 内容

  「場所」の表記：
    テキスト/CSV系 → 行番号（例: L12）
    Excel          → シート名と行番号（例: Sheet1:R5）
    Word           → 段落番号（例: P3）

【出力ファイル名】
  keyword_search_YYYYMMDD_HHMMSS.csv（タイムスタンプ付き）

【使用例】
  # 単一フォルダ
  python keyword_search.py C:/work/設計書 "ユーザーID"
  python keyword_search.py C:/work/設計書 "ユーザーID" --ext .xlsx,.docx
  python keyword_search.py C:/work/設計書 "エラー" --ignore-case --outdir C:/work/output

  # 複数フォルダ（テキストファイル指定）
  python keyword_search.py "ユーザーID" --folders-file folders.txt
  python keyword_search.py "エラー" --folders-file folders.txt --ext .xlsx --ignore-case
"""

import argparse
import csv
import fnmatch
import os
import sys
from datetime import datetime


# ---------------------------------------------------------------------------
# 検索ロジック（ファイル種別ごと）
# ---------------------------------------------------------------------------

def search_text_file(filepath: str, keyword: str, ignore_case: bool) -> list[dict]:
    """テキスト系ファイル（.txt / .csv / .md 等）を行単位で検索する。"""
    results = []
    # 文字コードを順に試す（BOMあり UTF-8 → UTF-8 → cp932）
    for enc in ("utf-8-sig", "utf-8", "cp932"):
        try:
            with open(filepath, encoding=enc, errors="strict") as f:
                lines = f.readlines()
            break
        except (UnicodeDecodeError, LookupError):
            continue
    else:
        # すべてのエンコードで失敗した場合はスキップ
        return results

    needle = keyword.lower() if ignore_case else keyword
    for lineno, line in enumerate(lines, start=1):
        haystack = line.lower() if ignore_case else line
        if needle in haystack:
            results.append({
                "場所": f"L{lineno}",
                "内容": line.rstrip("\n"),
            })
    return results


def search_excel_file(filepath: str, keyword: str, ignore_case: bool) -> list[dict]:
    """Excel ファイル（.xlsx / .xls）をセル単位で検索する。"""
    try:
        import openpyxl  # noqa: PLC0415
    except ImportError:
        print("[WARN] openpyxl が未インストールのため Excel ファイルをスキップします。"
              "  pip install openpyxl", file=sys.stderr)
        return []

    results = []
    needle = keyword.lower() if ignore_case else keyword

    try:
        wb = openpyxl.load_workbook(filepath, read_only=True, data_only=True)
    except Exception as e:  # noqa: BLE001
        print(f"[WARN] Excel を開けませんでした ({os.path.basename(filepath)}): {e}",
              file=sys.stderr)
        return results

    for sheet_name in wb.sheetnames:
        ws = wb[sheet_name]
        for row in ws.iter_rows():
            for cell in row:
                if cell.value is None:
                    continue
                cell_str = str(cell.value)
                haystack = cell_str.lower() if ignore_case else cell_str
                if needle in haystack:
                    results.append({
                        "場所": f"{sheet_name}:R{cell.row}",
                        "内容": cell_str,
                    })
    wb.close()
    return results


def search_word_file(filepath: str, keyword: str, ignore_case: bool) -> list[dict]:
    """Word ファイル（.docx）を段落単位で検索する。"""
    try:
        from docx import Document  # noqa: PLC0415
    except ImportError:
        print("[WARN] python-docx が未インストールのため Word ファイルをスキップします。"
              "  pip install python-docx", file=sys.stderr)
        return []

    results = []
    needle = keyword.lower() if ignore_case else keyword

    try:
        doc = Document(filepath)
    except Exception as e:  # noqa: BLE001
        print(f"[WARN] Word を開けませんでした ({os.path.basename(filepath)}): {e}",
              file=sys.stderr)
        return results

    for para_no, para in enumerate(doc.paragraphs, start=1):
        text = para.text
        if not text.strip():
            continue
        haystack = text.lower() if ignore_case else text
        if needle in haystack:
            results.append({
                "場所": f"P{para_no}",
                "内容": text,
            })
    return results


# ---------------------------------------------------------------------------
# ファイル収集
# ---------------------------------------------------------------------------

DEFAULT_EXTENSIONS = {".txt", ".csv", ".md", ".xlsx", ".xls", ".docx"}


def collect_files(root_dir: str, extensions: set[str], filename_pattern: str | None,
                  recursive: bool) -> list[str]:
    """対象ファイルのパス一覧を返す。"""
    filepaths = []

    if recursive:
        walker = os.walk(root_dir)
    else:
        entries = os.scandir(root_dir)
        walker = [(root_dir, [], [e.name for e in entries if e.is_file()])]

    for dirpath, _, filenames in walker:
        for filename in sorted(filenames):
            ext = os.path.splitext(filename)[1].lower()
            if ext not in extensions:
                continue
            if filename_pattern and not fnmatch.fnmatch(filename, filename_pattern):
                continue
            filepaths.append(os.path.join(dirpath, filename))

    return filepaths


# ---------------------------------------------------------------------------
# 検索ディスパッチ
# ---------------------------------------------------------------------------

TEXT_EXTENSIONS = {".txt", ".csv", ".md", ".log", ".ini", ".yaml", ".yml", ".json"}
EXCEL_EXTENSIONS = {".xlsx", ".xls"}
WORD_EXTENSIONS = {".docx"}


def search_file(filepath: str, keyword: str, ignore_case: bool) -> list[dict]:
    """拡張子に応じて適切な検索関数を呼び出す。"""
    ext = os.path.splitext(filepath)[1].lower()
    if ext in EXCEL_EXTENSIONS:
        return search_excel_file(filepath, keyword, ignore_case)
    if ext in WORD_EXTENSIONS:
        return search_word_file(filepath, keyword, ignore_case)
    return search_text_file(filepath, keyword, ignore_case)


# ---------------------------------------------------------------------------
# 出力
# ---------------------------------------------------------------------------

def print_results(records: list[dict]) -> None:
    """コンソールに結果を出力する。"""
    if not records:
        return
    # 列幅を揃えるため最大幅を計算
    max_file = max(len(r["ファイル名"]) for r in records)
    max_loc  = max(len(r["場所"])     for r in records)
    header = f"{'ファイル名':<{max_file}}  {'場所':<{max_loc}}  内容"
    print(header)
    print("-" * min(len(header) + 20, 120))
    for r in records:
        print(f"{r['ファイル名']:<{max_file}}  {r['場所']:<{max_loc}}  {r['内容']}")


def write_csv(records: list[dict], output_path: str, encoding: str = "cp932") -> None:
    """結果をCSVに書き出す。"""
    fieldnames = ["ファイルパス", "ファイル名", "場所", "内容"]
    with open(output_path, "w", newline="", encoding=encoding) as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)


# ---------------------------------------------------------------------------
# メイン
# ---------------------------------------------------------------------------

def load_folders_file(filepath: str) -> list[str]:
    """フォルダリストファイルを読み込む。空行・#始まり行はスキップ。"""
    folders = []
    for enc in ("utf-8-sig", "utf-8", "cp932"):
        try:
            with open(filepath, encoding=enc, errors="strict") as f:
                lines = f.readlines()
            break
        except (UnicodeDecodeError, LookupError):
            continue
    else:
        print(f"[ERROR] フォルダリストファイルを読み込めませんでした: {filepath}", file=sys.stderr)
        sys.exit(1)

    for line in lines:
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        folders.append(line)
    return folders


def main() -> None:
    parser = argparse.ArgumentParser(
        description="フォルダ配下のファイルからキーワードを検索し、該当行・セルを一覧表示する"
    )
    parser.add_argument("folder", nargs="?", default="",
                        help="対象フォルダのパス（--folders-file 指定時は省略可）")
    parser.add_argument("keyword", help="検索するキーワード")
    parser.add_argument("--folders-file", default="",
                        help="対象フォルダを列挙したテキストファイルのパス（1行1フォルダ）")
    parser.add_argument("--ext", default="",
                        help="対象拡張子をカンマ区切りで指定（例: .xlsx,.csv）。省略時はデフォルト拡張子を使用")
    parser.add_argument("--filename", default="",
                        help="ファイル名フィルタ（ワイルドカード対応、例: IF*.xlsx）")
    parser.add_argument("--no-recursive", action="store_true",
                        help="サブフォルダを含めない")
    parser.add_argument("--ignore-case", action="store_true",
                        help="大文字/小文字を区別しない")
    parser.add_argument("--outdir", default="",
                        help="出力先フォルダのパス（省略時: このスクリプトと同じフォルダ）")
    parser.add_argument("--encoding", default="cp932",
                        help="CSVの文字コード（デフォルト: cp932）")

    args = parser.parse_args()

    # 対象フォルダリストの決定
    if args.folders_file:
        # テキストファイルから複数フォルダを読み込む
        if not os.path.isfile(args.folders_file):
            print(f"[ERROR] フォルダリストファイルが見つかりません: {args.folders_file}", file=sys.stderr)
            sys.exit(1)
        target_folders = load_folders_file(args.folders_file)
        if not target_folders:
            print(f"[ERROR] フォルダリストファイルに有効なフォルダが1件もありません: {args.folders_file}",
                  file=sys.stderr)
            sys.exit(1)
    elif args.folder:
        # 単一フォルダ指定（従来通り）
        target_folders = [args.folder]
    else:
        print("[ERROR] 対象フォルダを指定してください（引数 or --folders-file）", file=sys.stderr)
        parser.print_help()
        sys.exit(1)

    # フォルダの存在確認
    invalid = [f for f in target_folders if not os.path.isdir(f)]
    if invalid:
        for f in invalid:
            print(f"[ERROR] フォルダが見つかりません: {f}", file=sys.stderr)
        sys.exit(1)

    # 拡張子セットの構築
    if args.ext:
        extensions = {e.strip().lower() for e in args.ext.split(",") if e.strip()}
    else:
        extensions = DEFAULT_EXTENSIONS

    recursive = not args.no_recursive
    filename_pattern = args.filename if args.filename else None

    # 出力先フォルダの決定（省略時: スクリプトと同じフォルダ）
    outdir = args.outdir if args.outdir else os.path.dirname(os.path.abspath(__file__))
    if not os.path.isdir(outdir):
        print(f"[ERROR] 出力先フォルダが見つかりません: {outdir}", file=sys.stderr)
        sys.exit(1)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = os.path.join(outdir, f"keyword_search_{timestamp}.csv")

    print(f"対象フォルダ   : {len(target_folders)} 件")
    for f in target_folders:
        print(f"  {f}")
    print(f"キーワード     : {args.keyword}")
    print(f"拡張子フィルタ : {sorted(extensions)}")
    print(f"ファイル名     : {filename_pattern if filename_pattern else '（指定なし）'}")
    print(f"サブフォルダ   : {'含めない' if not recursive else '含める'}")
    print(f"大文字小文字   : {'区別しない' if args.ignore_case else '区別する'}")
    print(f"出力先         : {output_path}")
    print()

    # ファイル収集（全フォルダ分）
    all_filepaths: list[str] = []
    for folder in target_folders:
        all_filepaths.extend(collect_files(folder, extensions, filename_pattern, recursive))

    if not all_filepaths:
        print("対象ファイルが見つかりませんでした。")
        sys.exit(0)

    # 検索
    all_records: list[dict] = []
    for filepath in all_filepaths:
        hits = search_file(filepath, args.keyword, args.ignore_case)
        dirpath = os.path.dirname(filepath)
        filename = os.path.basename(filepath)
        for hit in hits:
            all_records.append({
                "ファイルパス": dirpath,
                "ファイル名": filename,
                "場所": hit["場所"],
                "内容": hit["内容"],
            })

    # 結果出力
    print(f"検索ファイル数 : {len(all_filepaths)}")
    print(f"ヒット件数     : {len(all_records)}")
    print()

    if all_records:
        print_results(all_records)
    else:
        print(f"「{args.keyword}」に該当する箇所は見つかりませんでした。")

    # CSV出力（常に実行）
    write_csv(all_records, output_path, encoding=args.encoding)
    print()
    print(f"出力先: {output_path}")


if __name__ == "__main__":
    main()
