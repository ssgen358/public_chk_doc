# csv_merge_CSV結合

指定フォルダ内の CSV ファイルを、1つの CSV ファイルに単純結合するツールです。

## できること

- `a.csv`, `b.csv`, `c.csv` のような複数 CSV を1ファイルに結合
- デフォルトでは1つ目のヘッダーだけ残し、2つ目以降のヘッダーはスキップ
- オプションでヘッダーを出力しない設定にできる
- ファイル名順、または更新日時順で結合
- ダウンロードフォルダを直接対象にできる
- 直近N分以内に更新されたCSVだけ結合できる
- 必要なら元ファイル名列を追加できる
- 結合結果を指定CSVの指定行から貼り付けできる
- 結合結果を指定Excelの指定行から値だけ貼り付けできる

## よく使う実行例

```bat
python csv_merge.py C:\work\downloads --output merged.csv
```

ダウンロードフォルダを直接対象にする場合:

```bat
python csv_merge.py --downloads --sort mtime --output ..\..\csv\merged.csv
```

元ファイル名を先頭列に追加する場合:

```bat
python csv_merge.py --downloads --add-source-column --output ..\..\csv\merged.csv
```

1行目（ヘッダー）を出力しない場合:

```bat
python csv_merge.py --downloads --no-header-output --output ..\..\csv\merged.csv
```

直近5分以内にダウンロードされたCSVだけ結合する場合:

```bat
python csv_merge.py --downloads --since-minutes 5 --sort mtime --output ..\..\csv\merged.csv
```

直近3分以内だけにする場合:

```bat
python csv_merge.py --downloads --since-minutes 3 --sort mtime --output ..\..\csv\merged.csv
```

結合結果を指定CSVの10行目から貼り付ける場合:

```bat
python csv_merge.py --downloads --since-minutes 5 --sort mtime --no-header-output --paste-to C:\work\target.csv --paste-start-row 10
```

指定行の前に差し込みたい場合:

```bat
python csv_merge.py --downloads --since-minutes 5 --sort mtime --no-header-output --paste-to C:\work\target.csv --paste-start-row 10 --paste-mode insert
```

貼り付け時は、デフォルトで `target.csv.bak` というバックアップを作ります。
バックアップ不要の場合は `--no-backup` を付けます。

結合結果をExcelの指定シート10行目から値だけ貼り付ける場合:

```bat
python csv_merge.py --downloads --since-minutes 5 --sort mtime --no-header-output --output %USERPROFILE%\Downloads\merged.csv --paste-to-excel C:\work\target.xlsx --excel-sheet Sheet1 --paste-start-row 10
```

開始列を変える場合:

```bat
python csv_merge.py --downloads --since-minutes 5 --sort mtime --no-header-output --output %USERPROFILE%\Downloads\merged.csv --paste-to-excel C:\work\target.xlsx --excel-sheet Sheet1 --paste-start-row 10 --paste-start-col B
```

ExcelファイルがExcelアプリで開かれていると保存できない場合があります。
その場合は対象Excelを閉じてから実行してください。

Excel で保存した CSV が文字化けする場合:

```bat
python csv_merge.py C:\work\downloads --encoding cp932 --output merged.csv
```

## バッチで使う

`run_csv_merge.bat` を開き、必要に応じて上部の `SET` 行を変更してから実行します。

ダウンロードフォルダを使う場合は、初期設定のまま `USE_DOWNLOADS=1` で使えます。
初期設定では `SINCE_MINUTES=5` のため、直近5分以内に更新されたCSVだけを結合します。
