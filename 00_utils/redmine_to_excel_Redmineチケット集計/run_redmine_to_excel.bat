@echo off
setlocal
chcp 65001 > nul
cd /d "%~dp0"

rem ============================================================
rem  Redmine CSV -> Excel 値貼り付け 実行バッチ
rem ============================================================
rem
rem  設定方法:
rem    1. 下の「設定ここから」以降を書き換えて実行してください。
rem    2. URL、Excelパス、APIキーは実環境の値を設定してください。
rem    3. このフォルダをGit管理しない前提なら、APIキーもここに直接設定できます。
rem
rem  URL設定時の注意:
rem    - set "REDMINE_URL=..." の形式は崩さず、値だけを書き換えてください。
rem    - URL内の & や ? はそのまま書けます。
rem    - URL内の % は bat では特殊文字です。%2F は %%2F のように % を2つにしてください。
rem      例: ...?query_id=123&f%%5B%%5D=status_id
rem    - % を含むURLをそのまま使いたい場合は、URLだけを書いたテキストファイルを作り、
rem      REDMINE_URL_FILE にそのファイルパスを設定してください。
rem
rem  主な設定項目:
rem    REDMINE_URL      RedmineのCSVエクスポートURL
rem    REDMINE_URL_FILE URLだけを書いたテキストファイル。設定時はREDMINE_URLより優先。
rem    REDMINE_API_KEY  Redmine APIキー。URLに key= がない場合だけ自動付与されます。
rem    EXCEL_PATH       貼り付け先Excelファイル
rem    SHEET_NAME       貼り付け先シート名
rem    CLEAR_RANGE      貼り付け前に値を消す範囲。不要なら空欄。
rem    PASTE_CELL       CSV値の貼り付け開始セル
rem    SKIP_HEADER      CSVの1行目を貼り付けない場合は --skip-header。貼る場合は空欄。
rem    TEMP_CSV         ダウンロードしたCSVの一時保存先
rem    FORMULA_*        数式列を最終行までFillDownする設定。不要なら3項目とも空欄。
rem
rem ============================================================
rem  設定ここから
rem ============================================================

set "REDMINE_URL=https://redmine.example.com/issues.csv?query_id=123"
set "REDMINE_URL_FILE="
set "REDMINE_API_KEY="

set "EXCEL_PATH=C:\work\redmine_summary.xlsx"
set "SHEET_NAME=チケット一覧"

set "CLEAR_RANGE=A4:Y10000"
set "PASTE_CELL=A4"
set "SKIP_HEADER=--skip-header"

set "TEMP_CSV=%TEMP%\redmine_download.csv"

set "FORMULA_SOURCE_ROW=5"
set "FORMULA_START_ROW=6"
set "FORMULA_COLS=Z,AA"

rem ============================================================
rem  設定ここまで
rem ============================================================

if not "%REDMINE_URL_FILE%"=="" (
    if not exist "%REDMINE_URL_FILE%" (
        echo URLファイルが見つかりません: %REDMINE_URL_FILE%
        goto error
    )
    set /p REDMINE_URL=<"%REDMINE_URL_FILE%"
)

if "%FORMULA_SOURCE_ROW%"=="" set "FORMULA_SOURCE_ROW=0"
if "%FORMULA_START_ROW%"=="" set "FORMULA_START_ROW=0"

echo 実行コマンド:
echo python "%~dp0redmine_to_excel.py" --url "[REDMINE_URL]" --excel "%EXCEL_PATH%" --sheet "%SHEET_NAME%"
echo.
python "%~dp0redmine_to_excel.py" ^
  --url "%REDMINE_URL%" ^
  --excel "%EXCEL_PATH%" ^
  --sheet "%SHEET_NAME%" ^
  --clear-range "%CLEAR_RANGE%" ^
  --paste-cell "%PASTE_CELL%" ^
  --temp-csv "%TEMP_CSV%" ^
  %SKIP_HEADER% ^
  --formula-source-row %FORMULA_SOURCE_ROW% ^
  --formula-start-row %FORMULA_START_ROW% ^
  --formula-cols "%FORMULA_COLS%"
IF ERRORLEVEL 1 goto error

echo.
echo 完了しました。
pause
exit /b 0

:error
echo.
echo エラーが発生しました。上のメッセージを確認してください。
pause
exit /b 1
