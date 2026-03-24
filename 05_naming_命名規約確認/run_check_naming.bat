@echo off
setlocal
chcp 65001 > /dev/null

rem ============================================================
rem  check_naming 実行バッチ
rem  以下の SET 行の値を用途に合わせて変更してください
rem ============================================================

rem チェック対象の CSV ファイルのパス
SET INPUT_CSV=C:\work\design.csv

rem 命名規約ルール定義 YAML のパス
SET RULES=%~dp0naming_rules_sample.yaml

rem 出力 CSV のパス
SET OUTPUT=%~dp0..\csv\check_naming_result.csv

rem 出力 CSV の文字コード（省略時: cp932）
SET ENCODING=

rem ============================================================

SET SCRIPT_DIR=%~dp0

SET CMD=python "%SCRIPT_DIR%check_naming.py" "%INPUT_CSV%" --rules "%RULES%"

IF NOT "%OUTPUT%"==""   SET CMD=%CMD% --output "%OUTPUT%"
IF NOT "%ENCODING%"=="" SET CMD=%CMD% --encoding %ENCODING%

echo 実行コマンド: %CMD%
echo.
%CMD%

echo.
pause
endlocal
