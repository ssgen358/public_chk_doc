@echo off
chcp 65001 > nul
setlocal

rem ============================================================
rem  check_existence2 実行バッチ（軸ファイル方式）
rem  ★ 以下の SET 行を環境に合わせて変更してください
rem ============================================================

rem 軸ファイルのCSVパス（全列を出力する主役）
SET AXIS_CSV=C:\work\axis.csv

rem 比較ファイルのCSVパス
SET COMPARE_CSV=C:\work\compare.csv

rem 軸ファイルのキー列名（省略時: ファイル名）
SET AXIS_KEY=

rem 比較ファイルのキー列名（省略時: ファイル名）
SET COMPARE_KEY=

rem 出力CSV上での比較列のヘッダ名（省略時: 比較）
SET COMPARE_LABEL=

rem 出力CSVのパス（省略時: このバッチと同じフォルダに check_existence2_result.csv を出力）
SET OUTPUT=

rem 出力CSVの文字コード（省略時: cp932）
SET ENCODING=

rem キー列の大文字/小文字を区別する場合は --case-sensitive、しない場合は空欄
SET CASE_SENSITIVE=

rem ============================================================

SET SCRIPT_DIR=%~dp0

SET CMD=python "%SCRIPT_DIR%check_existence2.py" --axis "%AXIS_CSV%" --compare "%COMPARE_CSV%"

IF NOT "%AXIS_KEY%"==""       SET CMD=%CMD% --axis-key "%AXIS_KEY%"
IF NOT "%COMPARE_KEY%"==""    SET CMD=%CMD% --compare-key "%COMPARE_KEY%"
IF NOT "%COMPARE_LABEL%"==""  SET CMD=%CMD% --compare-label "%COMPARE_LABEL%"
IF NOT "%OUTPUT%"==""         SET CMD=%CMD% --output "%OUTPUT%"
IF NOT "%ENCODING%"==""       SET CMD=%CMD% --encoding %ENCODING%
IF NOT "%CASE_SENSITIVE%"=""  SET CMD=%CMD% %CASE_SENSITIVE%

echo 実行コマンド: %CMD%
echo.
%CMD%

echo.
pause
endlocal
