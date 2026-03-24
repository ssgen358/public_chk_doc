"""
file_list_batch.py - リストファイルに記載した複数フォルダのファイルを一覧化するツール

【概要】
CSVリストファイルに記載したフォルダパスを読み込み、
各フォルダ配下のファイルを一覧化してCSVに出力する。
複数フォルダをまとめて処理したい場合に使用する。

【使い方】
  python file_list_batch.py <リストファイル(CSV)> [オプション]

【リストファイルの形式】
  CSVファイル（1行目はヘッダー）
  列構成: フォルダパス, 備考

  例:
    フォルダパス,備考
    C:/work/設計書/画面設計,画面設計書
    C:/work/設計書/IF設計,IF設計書
    C:/work/設計書/バッチ設計,バッチ設計書

【オプション】
  --output      出力CSVのパス（省略時: file_list_batch.csv）
  --ext         対象拡張子をカンマ区切りで指定（省略時: 全ファイル）
                例: --ext .xlsx,.docx
  --no-recursive  サブフォルダを含めない（省略時: サブフォルダも含める）
  --encoding    CSVの文字コード（省略時: cp932＝Excelでそのまま開いて文字化けしない）

【出力CSVの列】
  備考, フォルダパス, ファイル名, 拡張子, 更新日時, ファイルサイズ(bytes)

【使用例】
  python file_list_batch.py folder_list.csv
  python file_list_batch.py folder_list.csv --ext .xlsx,.docx --output result.csv
  python file_list_batch.py folder_list.csv --no-recursive
"""

import argparse
import csv
import os
import sys
from datetime import datetime


def load_folder_list(list_path: str) -> list[dict]:
    """リストCSVからフォルダパスと備考を読み込む。UTF-8 / CP932 の両方に対応。"""
    entries = []
    for encoding in ("utf-8-sig", "utf-8", "cp932"):
        try:
            with open(list_path, newline="", encoding=encoding) as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                fieldnames = reader.fieldnames
            break
        except UnicodeDecodeError:
            continue
    else:
        print("[ERROR] リストファイルの文字コードが判別できません（UTF-8 または CP932 で保存してください）。", file=sys.stderr)
        sys.exit(1)

    if fieldnames is None or "フォルダパス" not in fieldnames:
        print("[ERROR] リストファイルに 'フォルダパス' 列が見つかりません。", file=sys.stderr)
        sys.exit(1)

    for i, row in enumerate(rows, start=2):
        folder = row.get("フォルダパス", "").strip()
        note = row.get("備考", "").strip()

        if not folder:
            print(f"[WARN] {i}行目: フォルダパスが空のため、スキップします。")
            continue

        entries.append({"フォルダパス": folder, "備考": note})

    return entries


def collect_files(folder: str, note: str, extensions: list[str] | None, recursive: bool) -> list[dict]:
    """指定フォルダ配下のファイル情報を収集する。"""
    results = []

    if not os.path.isdir(folder):
        print(f"[WARN] フォルダが見つかりません（スキップ）: {folder}")
        return results

    if recursive:
        walker = os.walk(folder)
    else:
        top_entries = os.scandir(folder)
        walker = [(folder, [], [e.name for e in top_entries if e.is_file()])]

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
                "備考": note,
                "フォルダパス": dirpath,
                "ファイル名": filename,
                "拡張子": ext,
                "更新日時": mtime,
                "ファイルサイズ(bytes)": size,
            })

    results.sort(key=lambda x: (x["フォルダパス"], x["ファイル名"]))
    return results


def write_csv(records: list[dict], output_path: str, encoding: str = "cp932") -> None:
    """結果をCSVに書き出す。encoding は Excel でそのまま開く場合は cp932 を推奨。"""
    fieldnames = ["備考", "フォルダパス", "ファイル名", "拡張子", "更新日時", "ファイルサイズ(bytes)"]
    with open(output_path, "w", newline="", encoding=encoding) as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="リストCSVに記載した複数フォルダのファイルを一覧化してCSVに出力する"
    )
    parser.add_argument("list_file", help="フォルダパスを記載したリストCSVのパス")
    parser.add_argument("--output", default="file_list_batch.csv", help="出力CSVのパス（デフォルト: file_list_batch.csv）")
    parser.add_argument("--ext", default="", help="対象拡張子をカンマ区切りで指定（例: .xlsx,.docx）")
    parser.add_argument("--no-recursive", action="store_true", help="サブフォルダを含めない")
    parser.add_argument("--encoding", default="cp932", help="CSVの文字コード（デフォルト: cp932＝Excelで文字化けしない）")

    args = parser.parse_args()

    # リストファイルの存在確認
    if not os.path.isfile(args.list_file):
        print(f"[ERROR] リストファイルが見つかりません: {args.list_file}", file=sys.stderr)
        sys.exit(1)

    # 拡張子リストの整形
    extensions = None
    if args.ext:
        extensions = [e.strip().lower() for e in args.ext.split(",") if e.strip()]

    recursive = not args.no_recursive

    # リストCSV読み込み
    entries = load_folder_list(args.list_file)
    if not entries:
        print("[ERROR] リストファイルに有効なフォルダパスがありませんでした。", file=sys.stderr)
        sys.exit(1)

    print(f"リストファイル  : {args.list_file}")
    print(f"対象フォルダ数  : {len(entries)} 件")
    print(f"サブフォルダ    : {'含める' if recursive else '含めない'}")
    print(f"拡張子フィルタ  : {extensions if extensions else '全ファイル'}")
    print()

    # 全フォルダのファイルを収集
    all_records = []
    for entry in entries:
        folder = entry["フォルダパス"]
        note = entry["備考"]
        print(f"  処理中: {folder}（{note}）")
        records = collect_files(folder, note, extensions, recursive)
        print(f"          → {len(records)} 件検出")
        all_records.extend(records)

    print()

    if not all_records:
        print("対象ファイルが見つかりませんでした。")
        sys.exit(0)

    write_csv(all_records, args.output, encoding=args.encoding)

    print(f"合計 {len(all_records)} 件のファイルを検出しました。")
    print(f"出力先: {os.path.abspath(args.output)}")


if __name__ == "__main__":
    main()
