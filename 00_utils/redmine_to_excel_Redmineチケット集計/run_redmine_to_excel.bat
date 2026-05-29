@echo off
setlocal
chcp 65001 > nul
cd /d "%~dp0"

rem ============================================================
rem  Redmine CSV -> Excel 値貼り付け 実行バッチ
rem  実URL、実Excelパス、APIキーは公開リポジトリにコミットしないでください。
rem ============================================================

rem APIキーは環境変数で渡すことを推奨します。
rem 例: set REDMINE_API_KEY=<your_redmine_api_key>

SET REDMINE_URL=https://redmine.example.com/issues.csv?query_id=123
SET EXCEL_PATH=C:\work\redmine_summary.xlsx
SET SHEET_NAME=チケット一覧

SET CLEAR_RANGE=A4:Y10000
SET PASTE_CELL=A4
SET SKIP_HEADER=--skip-header

rem ダウンロードCSVの一時保存先
SET TEMP_CSV=%TEMP%\redmine_download.csv

rem 数式列のFillDownが不要な場合は、以下3行を空欄にしてください。
SET FORMULA_SOURCE_ROW=5
SET FORMULA_START_ROW=6
SET FORMULA_COLS=Z,AA

SET CMD=python "%~dp0redmine_to_excel.py"
SET CMD=%CMD% --url "%REDMINE_URL%"
SET CMD=%CMD% --excel "%EXCEL_PATH%"
SET CMD=%CMD% --sheet "%SHEET_NAME%"
SET CMD=%CMD% --clear-range "%CLEAR_RANGE%"
SET CMD=%CMD% --paste-cell "%PASTE_CELL%"
SET CMD=%CMD% --temp-csv "%TEMP_CSV%"
IF NOT "%SKIP_HEADER%"==""        SET CMD=%CMD% %SKIP_HEADER%
IF NOT "%FORMULA_SOURCE_ROW%"=="" SET CMD=%CMD% --formula-source-row %FORMULA_SOURCE_ROW%
IF NOT "%FORMULA_START_ROW%"==""  SET CMD=%CMD% --formula-start-row %FORMULA_START_ROW%
IF NOT "%FORMULA_COLS%"==""       SET CMD=%CMD% --formula-cols "%FORMULA_COLS%"

echo 実行コマンド:
echo %CMD%
echo.
%CMD%
IF %ERRORLEVEL% NEQ 0 goto error

echo.
echo 完了しました。
pause
exit /b 0

:error
echo.
echo エラーが発生しました。上のメッセージを確認してください。
pause
exit /b 1
