"""
md_merge.py - Markdownファイルを結合するツール

【概要】
指定フォルダ配下の Markdown ファイル（.md）を収集し、
ファイルごとに見出し（## ファイル名）を付けて1つの Markdown ファイルに結合する。
設計書群をまとめて参照・AI レビューに渡す用途を想定している。

【使い方】
  python md_merge.py <フォルダパス> [オプション]

【オプション】
  --output, -o   出力先フォルダのパス（省略時: このスクリプトと同じフォルダ）
  --level        ファイル名見出しのレベル（1〜3、省略時: 2）
                 1 → # ファイル名
                 2 → ## ファイル名（デフォルト）
                 3 → ### ファイル名
  --no-recursive サブフォルダを含めない（省略時: サブフォルダも含める）
  --no-separator ファイル間の区切り線を出力しない（省略時: --- を挿入する）
  --encoding-in  入力ファイルの文字コード（省略時: 自動判定）
  --encoding-out 出力ファイルの文字コード（省略時: utf-8）

【出力ファイル名】
  md_merge_YYYYMMDD_HHMMSS.md（タイムスタンプ付き）

【出力構造】
  ## 01_設計書A.md
  （ファイルAの内容）

  ---

  ## 02_設計書B.md
  （ファイルBの内容）

【使用例】
  python md_merge.py C:/work/docs
  python md_merge.py C:/work/docs --level 1
  python md_merge.py C:/work/docs --output C:/work/output
  python md_merge.py C:/work/docs --no-recursive --no-separator
"""

import argparse
import os
import sys
from datetime import datetime


def collect_md_files(root_dir: str, recursive: bool) -> list[str]:
    """対象フォルダから .md ファイルを収集する（ソート済み）。"""
    filepaths = []

    if recursive:
        for dirpath, _, filenames in os.walk(root_dir):
            for name in sorted(filenames):
                if name.lower().endswith(".md"):
                    filepaths.append(os.path.join(dirpath, name))
    else:
        for entry in sorted(os.scandir(root_dir), key=lambda e: e.name):
            if entry.is_file() and entry.name.lower().endswith(".md"):
                filepaths.append(entry.path)

    return filepaths


def read_file(filepath: str, encoding_in: str | None) -> str:
    """ファイルを読み込む。encoding_in が None の場合は自動判定。"""
    candidates = [encoding_in] if encoding_in else ["utf-8-sig", "utf-8", "cp932"]
    for enc in candidates:
        try:
            with open(filepath, encoding=enc, errors="strict") as f:
                return f.read()
        except (UnicodeDecodeError, LookupError):
            continue
    # 最終手段: エラーを無視して読む
    with open(filepath, encoding="utf-8", errors="replace") as f:
        print(f"  [WARN] 文字コードを特定できなかったため一部文字を置換しました: {os.path.basename(filepath)}",
              file=sys.stderr)
        return f.read()


def merge_files(
    filepaths: list[str],
    root_dir: str,
    heading_level: int,
    use_separator: bool,
    encoding_in: str | None,
) -> str:
    """複数の Markdown ファイルを結合した文字列を返す。"""
    prefix = "#" * heading_level
    blocks = []

    for filepath in filepaths:
        # ファイル名（root_dir からの相対パスで見出しに使う）
        rel_path = os.path.relpath(filepath, root_dir)
        heading = f"{prefix} {rel_path}"

        content = read_file(filepath, encoding_in)
        # 末尾の空白行を正規化
        content = content.rstrip("\n")

        blocks.append(f"{heading}\n\n{content}")

    separator = "\n\n---\n\n" if use_separator else "\n\n"
    return separator.join(blocks) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="フォルダ配下の Markdown ファイルを1つに結合する"
    )
    parser.add_argument("folder", help="対象フォルダのパス")
    parser.add_argument("--output", "-o", default="",
                        help="出力先フォルダのパス（省略時: このスクリプトと同じフォルダ）")
    parser.add_argument("--level", type=int, default=2, choices=[1, 2, 3],
                        help="ファイル名見出しのレベル（デフォルト: 2）")
    parser.add_argument("--no-recursive", action="store_true",
                        help="サブフォルダを含めない")
    parser.add_argument("--no-separator", action="store_true",
                        help="ファイル間の区切り線（---）を出力しない")
    parser.add_argument("--encoding-in", default="",
                        help="入力ファイルの文字コード（省略時: 自動判定）")
    parser.add_argument("--encoding-out", default="utf-8",
                        help="出力ファイルの文字コード（デフォルト: utf-8）")

    args = parser.parse_args()

    # フォルダの存在確認
    if not os.path.isdir(args.folder):
        print(f"[ERROR] フォルダが見つかりません: {args.folder}", file=sys.stderr)
        sys.exit(1)

    # 出力先フォルダの決定（省略時: スクリプトと同じフォルダ）
    outdir = args.output if args.output else os.path.dirname(os.path.abspath(__file__))
    if not os.path.isdir(outdir):
        print(f"[ERROR] 出力先フォルダが見つかりません: {outdir}", file=sys.stderr)
        sys.exit(1)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = os.path.join(outdir, f"md_merge_{timestamp}.md")

    recursive = not args.no_recursive
    use_separator = not args.no_separator
    encoding_in = args.encoding_in if args.encoding_in else None

    print(f"対象フォルダ   : {args.folder}")
    print(f"サブフォルダ   : {'含める' if recursive else '含めない'}")
    print(f"見出しレベル   : {'#' * args.level}")
    print(f"区切り線       : {'あり（---）' if use_separator else 'なし'}")
    print(f"出力先         : {output_path}")
    print()

    # ファイル収集
    filepaths = collect_md_files(args.folder, recursive)
    if not filepaths:
        print("Markdown ファイルが見つかりませんでした。")
        sys.exit(0)

    print(f"対象ファイル数 : {len(filepaths)} 件")
    for fp in filepaths:
        print(f"  {os.path.relpath(fp, args.folder)}")
    print()

    # 結合
    merged = merge_files(filepaths, args.folder, args.level, use_separator, encoding_in)

    # 出力
    with open(output_path, "w", encoding=args.encoding_out) as f:
        f.write(merged)

    print(f"完了: {len(filepaths)} ファイルを結合しました。")
    print(f"出力先: {output_path}")


if __name__ == "__main__":
    main()
