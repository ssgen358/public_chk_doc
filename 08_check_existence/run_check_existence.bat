@echo off
chcp 65001 > nul
setlocal

rem ============================================================
rem  check_existence 実行バッチ
rem  ★ 以下の SET 行を環境に合わせて変更してください
rem ============================================================

rem 設計書から抽出したファイル名一覧CSV（excel_extract.py 等の出力）
SET DOC_CSV=C:\work\doc_files.csv

rem 実ファイルのファイル名一覧CSV（file_list.py 等の出力）
SET ACTUAL_CSV=C:\work\actual_files.csv

rem 設計書CSV内のファイル名列名（省略時: ファイル名）
SET DOC_COL=

rem 実ファイルCSV内のファイル名列名（省略時: ファイル名）
SET ACTUAL_COL=

rem 設計書CSVの出典列名（省略時: 抽出元ファイル名）
SET DOC_INFO_COL=

rem 出力CSVのパス（省略時: このバッチと同じフォルダに check_existence_result.csv を出力）
SET OUTPUT=

rem 出力CSVの文字コード（省略時: cp932）
SET ENCODING=

rem ファイル名の大文字/小文字を区別する場合は --case-sensitive、しない場合は空欄
SET CASE_SENSITIVE=

rem ============================================================

SET SCRIPT_DIR=%~dp0

SET CMD=python "%SCRIPT_DIR%check_existence.py" "%DOC_CSV%" "%ACTUAL_CSV%"

IF NOT "%DOC_COL%"==""       SET CMD=%CMD% --doc-col "%DOC_COL%"
IF NOT "%ACTUAL_COL%"==""    SET CMD=%CMD% --actual-col "%ACTUAL_COL%"
IF NOT "%DOC_INFO_COL%"==""  SET CMD=%CMD% --doc-info-col "%DOC_INFO_COL%"
IF NOT "%OUTPUT%"==""        SET CMD=%CMD% --output "%OUTPUT%"
IF NOT "%ENCODING%"==""      SET CMD=%CMD% --encoding %ENCODING%
IF NOT "%CASE_SENSITIVE%"="" SET CMD=%CMD% %CASE_SENSITIVE%

echo 実行コマンド: %CMD%
echo.
%CMD%

echo.
pause
endlocal
