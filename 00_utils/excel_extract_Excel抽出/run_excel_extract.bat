@echo off
setlocal

rem ============================================================
rem  excel_extract 実行バッチ
rem  ★ 以下の SET 行を環境に合わせて変更してください
rem ============================================================

rem 対象フォルダ（Excelファイルがあるフォルダのパス）
SET TARGET_FOLDER=C:\work\設計書

rem 読み込むシート名（ワイルドカード使用可: 例 ファイル* , *一覧）
SET SHEET=ファイル一覧

rem 空判定列名（この列が連続して空になったら読み込みを終了する）
SET STOP_COL=ファイル名

rem ヘッダー行番号（省略時: 1）
SET HEADER_ROW=1

rem データ開始行番号（省略時: ヘッダー行 + 1）
SET START_ROW=

rem 連続空行の閾値（省略時: 10）
SET MAX_EMPTY=

rem 出力CSVのパス（デフォルト: csv フォルダに excel_extract_result.csv を出力）
SET OUTPUT=%~dp0..\..\csv\excel_extract_result.csv

rem サブフォルダを含めない場合は --no-recursive、含める場合は空欄
SET NO_RECURSIVE=

rem ============================================================

SET SCRIPT_DIR=%~dp0

SET CMD=python "%SCRIPT_DIR%excel_extract.py" "%TARGET_FOLDER%"
SET CMD=%CMD% --sheet "%SHEET%"
SET CMD=%CMD% --stop-col "%STOP_COL%"
SET CMD=%CMD% --header-row %HEADER_ROW%

IF NOT "%START_ROW%"==""    SET CMD=%CMD% --start-row %START_ROW%
IF NOT "%MAX_EMPTY%"==""    SET CMD=%CMD% --max-empty %MAX_EMPTY%
IF NOT "%OUTPUT%"==""       SET CMD=%CMD% --output "%OUTPUT%"
IF NOT "%NO_RECURSIVE%"==""  SET CMD=%CMD% %NO_RECURSIVE%

echo 実行コマンド: %CMD%
echo.
%CMD%

echo.
pause
endlocal
