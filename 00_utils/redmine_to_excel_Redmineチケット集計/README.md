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
このバッチファイルは Windows の `cmd.exe` で実行する前提のため、Shift-JIS/CP932 で保存して使う想定です。

このフォルダをGit管理しない前提で使う場合は、`run_redmine_to_excel.bat` の設定欄に APIキーを直接設定できます。

```bat
set "REDMINE_API_KEY=<your_redmine_api_key>"
```

Redmine の CSV URL は、バッチ内に直接書くより、URLファイルに書いて `REDMINE_URL_FILE` から読み込む使い方を推奨します。
URLファイル置き場として `url/` を用意しています。
`url/redmine_url.example.txt` を参考に、ローカル用の `url/redmine_url.txt` を作成してください。
`url/redmine_url.txt` は実URLを含む可能性があるため、Git管理対象外にしています。

```bat
set "REDMINE_URL_FILE=%~dp0url\redmine_url.txt"
```

URLファイルには、URLだけを1行で書いてください。
コメント行や説明文は書かないでください。

```text
https://redmine.example.com/issues.csv?query_id=123
```

URLファイルを使う場合、URL内の `&`、`?`、`%` はそのまま書けます。
URLファイルは `utf-8-sig`、`cp932`、`shift_jis`、`utf-8` の順に読み込みを試すため、UTF-8 BOM付きやShift-JIS/CP932でも利用できます。
Windowsのメモ帳やbat運用に合わせるなら Shift-JIS/CP932 で保存しておくと扱いやすいです。

バッチ内の `REDMINE_URL` に直接URLを書く場合だけ、`%` がbatの特殊文字として解釈されます。
その場合は `%2F` を `%%2F` のように `%` を2つにしてください。

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
| `--url-file` | Redmine CSV エクスポート URL を記載したテキストファイル |
| `--api-key` | Redmine API キー。通常は使わず環境変数を推奨 |
| `--api-key-env` | APIキーを読む環境変数名。デフォルトは `REDMINE_API_KEY` |
| `--excel` | 貼り付け先 Excel ファイル |
| `--sheet` | 貼り付け先シート名 |
| `--paste-cell` | 貼り付け開始セル。デフォルトは `A1` |
| `--clear-range` | 貼り付け前に値を消す範囲 |
| `--skip-header` | CSV の1行目を貼り付けない |
| `--temp-csv` | ダウンロードCSVの保存先 |
| `--encoding` | CSV文字コード。デフォルトは `auto` |
| `--formula-source-row` | 数式コピー元の行 |
| `--formula-start-row` | 数式コピー開始行 |
| `--formula-cols` | 数式をコピーする列。例: `Z,AA` |
| `--visible` | Excelを表示して実行 |

## 注意

- Excel ファイルを開いたままだと保存に失敗する場合があります。
- CSV の値は文字列として読み込み、Excelへ値として貼り付けます。
- Excel 側の表示形式を使いたい列は、貼り付け先シート側で事前に書式設定してください。

## 文字コードエラーが出る場合

`utf-8 codec can't decode byte 0x83...` のようなエラーが出る場合、Redmine から取得したCSVが UTF-8 ではなく Shift-JIS/CP932 系で出力されている可能性があります。

通常は `--encoding auto` のままで、`utf-8-sig`、`cp932`、`shift_jis`、`utf-8` の順に自動判定します。
バッチでは以下の設定を使います。

```bat
set "ENCODING=auto"
```

自動判定でうまくいかない場合は、Windows向けの日本語CSVとして `cp932` を明示してください。

```bat
set "ENCODING=cp932"
```
