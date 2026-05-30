# redmine_to_excel_Redmineチケット集計

Redmine のチケット一覧を CSV で取得し、指定した Excel ブックの指定シートへ値だけ貼り付けるツールです。

Excel 側の集計表、書式、列幅、フィルター、数式列は事前に整えておき、このツールでは CSV の値貼り付けだけを行います。

## 前提

- Windows
- Microsoft Excel がインストール済み
- Python
- Redmine の CSV エクスポート URL
- 必要に応じて Redmine API キー

依存ライブラリ:

```bat
pip install -r requirements.txt
```

## 基本の使い方

```bat
python redmine_to_excel.py ^
  --url "https://redmine.example.com/issues.csv?query_id=123" ^
  --excel "C:\work\redmine_summary.xlsx" ^
  --sheet "チケット一覧" ^
  --clear-range "A4:Y10000" ^
  --paste-cell "A4" ^
  --skip-header
```

## APIキー

APIキーは公開リポジトリに書かないでください。
通常は環境変数 `REDMINE_API_KEY` に設定します。

```bat
set REDMINE_API_KEY=<your_redmine_api_key>
```

URLに `key=` が含まれていない場合だけ、ツールが自動で `key=` を追加します。

## 数式列の FillDown

貼り付け後、指定列の数式を最終データ行までコピーできます。

```bat
python redmine_to_excel.py ^
  --url "https://redmine.example.com/issues.csv?query_id=123" ^
  --excel "C:\work\redmine_summary.xlsx" ^
  --sheet "チケット一覧" ^
  --clear-range "A4:Y10000" ^
  --paste-cell "A4" ^
  --skip-header ^
  --formula-source-row 5 ^
  --formula-start-row 6 ^
  --formula-cols "Z,AA"
```

## バッチで使う

`run_redmine_to_excel.bat` をコピーまたは編集して使います。

このフォルダをGit管理しない前提で使う場合は、`run_redmine_to_excel.bat` の設定欄に APIキーを直接設定できます。

```bat
set "REDMINE_API_KEY=<your_redmine_api_key>"
```

Redmine の CSV URL に `&` や `?` が含まれる場合でも、バッチ内では `set "REDMINE_URL=..."` の形式を崩さず値だけ書き換えてください。
URL に `%` が含まれる場合は bat の特殊文字として解釈されるため、`%2F` は `%%2F` のように `%` を2つにしてください。

`%` を含むURLをそのまま貼り付けたい場合は、URLだけを書いたテキストファイルを作り、バッチの `REDMINE_URL_FILE` にそのファイルパスを設定してください。この場合、テキストファイル内の `%` は `%%` にしなくてかまいません。

## Redmine URL の指定

`REDMINE_URL` には、Redmine の画面表示用URLではなく、CSVを直接ダウンロードできるURLを指定してください。
通常は `issues` ではなく `issues.csv` のURLを使います。

```bat
set "REDMINE_URL=https://redmine.example.com/issues.csv?query_id=123"
```

Redmine のチケット一覧画面で条件を整えたあと、CSVエクスポート用のURLを指定するのが基本です。
運用を安定させる場合は、Redmine側でカスタムクエリを保存して `query_id=123` のようなURLにすると扱いやすくなります。

```text
OK: https://redmine.example.com/issues.csv?query_id=123
NG: https://redmine.example.com/issues?query_id=123
```

`issues` だけのURLではHTML画面が返る場合があり、このツールではCSVとして正しく読み込めません。

## オプション

| オプション | 説明 |
| --- | --- |
| `--url` | Redmine CSV エクスポート URL |
| `--api-key` | Redmine API キー。通常は使わず環境変数を推奨 |
| `--api-key-env` | APIキーを読む環境変数名。デフォルトは `REDMINE_API_KEY` |
| `--excel` | 貼り付け先 Excel ファイル |
| `--sheet` | 貼り付け先シート名 |
| `--paste-cell` | 貼り付け開始セル。デフォルトは `A1` |
| `--clear-range` | 貼り付け前に値を消す範囲 |
| `--skip-header` | CSV の1行目を貼り付けない |
| `--temp-csv` | ダウンロードCSVの保存先 |
| `--encoding` | CSV文字コード。デフォルトは `utf-8-sig` |
| `--formula-source-row` | 数式コピー元の行 |
| `--formula-start-row` | 数式コピー開始行 |
| `--formula-cols` | 数式をコピーする列。例: `Z,AA` |
| `--visible` | Excelを表示して実行 |

## 注意

- Excel ファイルを開いたままだと保存に失敗する場合があります。
- CSV の値は文字列として読み込み、Excelへ値として貼り付けます。
- Excel 側の表示形式を使いたい列は、貼り付け先シート側で事前に書式設定してください。
