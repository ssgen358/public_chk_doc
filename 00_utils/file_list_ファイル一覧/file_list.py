"""
file_list.py - フォルダ配下のファイルを一覧化するツール

【概要】
指定したフォルダ配下のファイルを再帰的に検索し、
ファイルパス・ファイル名・拡張子・更新日時をCSVに出力する。

【使い方】
  python file_list.py <フォルダパス> [オプション]

【オプション】
  --output   出力CSVのパス（省略時: file_list.csv）
  --ext      対象拡張子をカンマ区切りで指定（省略時: 全ファイル）
             例: --ext .xlsx,.docx
  --no-recursive  サブフォルダを含めない（省略時: サブフォルダも含める）
  --encoding CSVの文字コード（省略時: cp932＝Excelでそのまま開いて文字化けしない）

【出力CSVの列】
  フォルダパス, ファイル名, 拡張子, 更新日時, ファイルサイズ(bytes)

【使用例】
  python file_list.py C:/work/設計書
  python file_list.py C:/work/設計書 --ext .xlsx,.docx --output result.csv
  python file_list.py C:/work/設計書 --no-recursive
"""

import argparse
import csv
import os
import sys
from datetime import datetime


def collect_files(root_dir: str, extensions: list[str] | None, recursive: bool) -> list[dict]:
    """指定フォルダ配下のファイル情報を収集する。"""
    results = []

    if recursive:
        walker = os.walk(root_dir)
    else:
        # サブフォルダを含めない場合はトップレベルのみ
        top_entries = os.scandir(root_dir)
        walker = [(root_dir, [], [e.name for e in top_entries if e.is_file()])]

    for dirpath, _, filenames in walker:
        for filename in filenames:
            ext = os.path.splitext(filename)[1].lower()

            # 拡張子フィルタ
            if extensions and ext not in extensions:
                continue

            full_path = os.path.join(dirpath, filename)
            try:
                stat = os.stat(full_path)
                mtime = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
                size = stat.st_size
            except OSError:
                mtime = ""
                size = ""

            results.append({
                "フォルダパス": dirpath,
                "ファイル名": filename,
                "拡張子": ext,
                "更新日時": mtime,
                "ファイルサイズ(bytes)": size,
            })

    # フォルダパス→ファイル名の順でソート
    results.sort(key=lambda x: (x["フォルダパス"], x["ファイル名"]))
    return results


def write_csv(records: list[dict], output_path: str, encoding: str = "cp932") -> None:
    """結果をCSVに書き出す。encoding は Excel でそのまま開く場合は cp932 を推奨。"""
    fieldnames = ["フォルダパス", "ファイル名", "拡張子", "更新日時", "ファイルサイズ(bytes)"]
    with open(output_path, "w", newline="", encoding=encoding) as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="フォルダ配下のファイルを一覧化してCSVに出力する"
    )
    parser.add_argument("folder", help="対象フォルダのパス")
    parser.add_argument("--output", default="file_list.csv", help="出力CSVのパス（デフォルト: file_list.csv）")
    parser.add_argument("--ext", default="", help="対象拡張子をカンマ区切りで指定（例: .xlsx,.docx）")
    parser.add_argument("--no-recursive", action="store_true", help="サブフォルダを含めない")
    parser.add_argument("--encoding", default="cp932", help="CSVの文字コード（デフォルト: cp932＝Excelで文字化けしない）")

    args = parser.parse_args()

    # フォルダの存在確認
    if not os.path.isdir(args.folder):
        print(f"[ERROR] フォルダが見つかりません: {args.folder}", file=sys.stderr)
        sys.exit(1)

    # 拡張子リストの整形
    extensions = None
    if args.ext:
        extensions = [e.strip().lower() for e in args.ext.split(",") if e.strip()]

    recursive = not args.no_recursive

    print(f"対象フォルダ : {args.folder}")
    print(f"サブフォルダ : {'含める' if recursive else '含めない'}")
    print(f"拡張子フィルタ: {extensions if extensions else '全ファイル'}")
    print()

    records = collect_files(args.folder, extensions, recursive)

    if not records:
        print("対象ファイルが見つかりませんでした。")
        sys.exit(0)

    write_csv(records, args.output, encoding=args.encoding)

    print(f"{len(records)} 件のファイルを検出しました。")
    print(f"出力先: {os.path.abspath(args.output)}")


if __name__ == "__main__":
    main()
