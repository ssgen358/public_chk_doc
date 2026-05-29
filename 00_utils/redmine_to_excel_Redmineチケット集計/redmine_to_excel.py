"""
redmine_to_excel.py - Download Redmine issue CSV and paste values into Excel.

This tool is intended for Windows environments where Microsoft Excel is
installed. It keeps the target workbook formatting intact and writes only cell
values into the configured range.
"""

from __future__ import annotations

import argparse
import csv
import os
import sys
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit


def build_url(url: str, api_key: str) -> str:
    if not api_key:
        return url

    parts = urlsplit(url)
    query = parse_qsl(parts.query, keep_blank_values=True)
    if any(key.lower() == "key" for key, _ in query):
        return url

    query.append(("key", api_key))
    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query), parts.fragment))


def fetch_csv(url: str, api_key: str, output_path: Path, timeout: int) -> None:
    try:
        import requests
    except ImportError as exc:
        raise RuntimeError("requests is required. Install it with: pip install -r requirements.txt") from exc

    full_url = build_url(url, api_key)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    response = requests.get(full_url, timeout=timeout)
    response.raise_for_status()
    output_path.write_bytes(response.content)


def read_csv_rows(csv_path: Path, encoding: str, skip_header: bool) -> list[list[str]]:
    with csv_path.open("r", newline="", encoding=encoding) as f:
        sample = f.read(4096)
        f.seek(0)
        try:
            dialect = csv.Sniffer().sniff(sample)
        except csv.Error:
            dialect = csv.excel

        rows = list(csv.reader(f, dialect))

    if skip_header and rows:
        rows = rows[1:]
    return rows


def normalize_for_excel(rows: list[list[str]]) -> tuple[tuple[str, ...], ...]:
    if not rows:
        return tuple()

    max_cols = max(len(row) for row in rows)
    return tuple(tuple(row + [""] * (max_cols - len(row))) for row in rows)


def paste_values_to_excel(
    excel_path: Path,
    sheet_name: str,
    paste_cell: str,
    rows: list[list[str]],
    clear_range: str,
    formula_source_row: int,
    formula_start_row: int,
    formula_cols: str,
    visible: bool,
) -> int:
    try:
        import win32com.client as win32
    except ImportError as exc:
        raise RuntimeError("pywin32 is required. Install it with: pip install -r requirements.txt") from exc

    excel = win32.Dispatch("Excel.Application")
    excel.Visible = visible
    excel.DisplayAlerts = False

    workbook = None
    try:
        workbook = excel.Workbooks.Open(str(excel_path.resolve()))
        worksheet = workbook.Worksheets(sheet_name)

        if clear_range:
            worksheet.Range(clear_range).ClearContents()

        excel_values = normalize_for_excel(rows)
        row_count = len(excel_values)
        col_count = len(excel_values[0]) if excel_values else 0

        if row_count and col_count:
            start = worksheet.Range(paste_cell)
            end = start.Offset(row_count - 1, col_count - 1)
            worksheet.Range(start, end).Value = excel_values

        if formula_cols and row_count > 0:
            paste_start_row = worksheet.Range(paste_cell).Row
            last_data_row = paste_start_row + row_count - 1
            if last_data_row >= formula_start_row:
                for col in [c.strip() for c in formula_cols.split(",") if c.strip()]:
                    worksheet.Range(f"{col}{formula_source_row}:{col}{last_data_row}").FillDown()

        workbook.Save()
        workbook.Close(SaveChanges=True)
        workbook = None
        return row_count
    finally:
        if workbook is not None:
            workbook.Close(SaveChanges=False)
        excel.Quit()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Download Redmine issue CSV and paste values into an Excel workbook.",
    )
    parser.add_argument("--url", required=True, help="Redmine CSV export URL.")
    parser.add_argument("--api-key", default="", help="Redmine API key. Prefer REDMINE_API_KEY for normal use.")
    parser.add_argument("--api-key-env", default="REDMINE_API_KEY", help="Environment variable name for API key.")
    parser.add_argument("--excel", required=True, help="Target Excel .xlsx path.")
    parser.add_argument("--sheet", required=True, help="Target sheet name.")
    parser.add_argument("--paste-cell", default="A1", help="Start cell for value paste. Default: A1")
    parser.add_argument("--clear-range", default="", help="Optional range to clear before paste, such as A4:Y10000.")
    parser.add_argument("--skip-header", action="store_true", help="Skip the first row of the downloaded CSV.")
    parser.add_argument("--temp-csv", default="", help="Temporary CSV output path. Default: ./redmine_download.csv")
    parser.add_argument("--encoding", default="utf-8-sig", help="Downloaded CSV encoding. Default: utf-8-sig")
    parser.add_argument("--timeout", type=int, default=30, help="HTTP timeout seconds. Default: 30")
    parser.add_argument("--formula-source-row", type=int, default=0, help="Row containing formulas to fill down.")
    parser.add_argument("--formula-start-row", type=int, default=0, help="First row where formulas should be filled.")
    parser.add_argument("--formula-cols", default="", help="Comma-separated formula columns, such as Z,AA.")
    parser.add_argument("--visible", action="store_true", help="Show Excel while processing.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    api_key = args.api_key or os.environ.get(args.api_key_env, "")
    excel_path = Path(args.excel)
    temp_csv = Path(args.temp_csv) if args.temp_csv else Path(__file__).with_name("redmine_download.csv")

    if not excel_path.is_file():
        print(f"[ERROR] Excel file not found: {excel_path}", file=sys.stderr)
        sys.exit(1)

    try:
        fetch_csv(args.url, api_key, temp_csv, args.timeout)
        rows = read_csv_rows(temp_csv, args.encoding, args.skip_header)
        pasted_rows = paste_values_to_excel(
            excel_path=excel_path,
            sheet_name=args.sheet,
            paste_cell=args.paste_cell,
            rows=rows,
            clear_range=args.clear_range,
            formula_source_row=args.formula_source_row,
            formula_start_row=args.formula_start_row,
            formula_cols=args.formula_cols,
            visible=args.visible,
        )
    except Exception as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        sys.exit(1)

    print(f"Downloaded CSV : {temp_csv}")
    print(f"Excel file     : {excel_path}")
    print(f"Sheet          : {args.sheet}")
    print(f"Pasted rows    : {pasted_rows}")


if __name__ == "__main__":
    main()
