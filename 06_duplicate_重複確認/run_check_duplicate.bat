@echo off
setlocal

rem ============================================================
rem  check_duplicate 実行バッチ
rem  ★ 以下の SET 行の値を用途に合わせて変更してください
rem ============================================================

rem チェック対象のCsvファイルのパス
SET INPUT_CSV=C:\work\design.csv

rem チェック対象の列名（スペース区切りで複数指定可）
SET COLS=ファイル名

rem 出力CSVのパス（デフォルト: csv フォルダに check_duplicate_result.csv を出力）
SET OUTPUT=%~dp0..\csv\check_duplicate_result.csv

rem 出力CSVの文字コード（省略時: cp932）
SET ENCODING=

rem 値の大文字/小文字を区別する場合は --case-sensitive、しない場合は空
SET CASE_SENSITIVE=

rem ============================================================

SET SCRIPT_DIR=%~dp0

SET CMD=python "%SCRIPT_DIR%check_duplicate.py" "%INPUT_CSV%" --cols %COLS%

IF NOT "%OUTPUT%"==""         SET CMD=%CMD% --output "%OUTPUT%"
IF NOT "%ENCODING%"==""       SET CMD=%CMD% --encoding %ENCODING%
IF NOT "%CASE_SENSITIVE%"=="" SET CMD=%CMD% %CASE_SENSITIVE%

echo 実行コマンド: %CMD%
echo.
%CMD%

echo.
pause
endlocal
