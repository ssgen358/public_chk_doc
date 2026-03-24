@echo off
setlocal
chcp 65001 > /dev/null

rem ============================================================
rem  check_notation 実行バッチ
rem  以下の SET 行の値を用途に合わせて変更してください
rem ============================================================

rem チェック対象の CSV ファイルのパス
SET INPUT_CSV=C:\work\design.csv

rem 表記揺れルール定義 YAML のパス
SET RULES=%~dp0notation_rules_sample.yaml

rem チェック対象の列名（スペース区切り、複数指定可、省略時は全列）
SET COLS=

rem 出力 CSV のパス
SET OUTPUT=%~dp0..\csv\check_notation_result.csv

rem 出力 CSV の文字コード（省略時: cp932）
SET ENCODING=

rem 部分一致モードで検索する場合は --partial、しない場合は空
SET PARTIAL=--partial

rem 大文字/小文字を区別する場合は --case-sensitive、しない場合は空
SET CASE_SENSITIVE=

rem ============================================================

SET SCRIPT_DIR=%~dp0

SET CMD=python "%SCRIPT_DIR%check_notation.py" "%INPUT_CSV%" --rules "%RULES%"

IF NOT "%COLS%"==""           SET CMD=%CMD% --cols %COLS%
IF NOT "%OUTPUT%"==""         SET CMD=%CMD% --output "%OUTPUT%"
IF NOT "%ENCODING%"==""       SET CMD=%CMD% --encoding %ENCODING%
IF NOT "%PARTIAL%"==""        SET CMD=%CMD% %PARTIAL%
IF NOT "%CASE_SENSITIVE%"=="" SET CMD=%CMD% %CASE_SENSITIVE%

echo 実行コマンド: %CMD%
echo.
%CMD%

echo.
pause
endlocal
