@echo off
setlocal

rem ============================================================
rem  file_list_batch 実行バッチ
rem  ★ 以下の SET 行を環境に合わせて変更してください
rem ============================================================

rem フォルダ一覧CSVのパス
rem （CSVの列構成: フォルダパス,備考）
SET LIST_CSV=C:\work\folder_list.csv

rem 対象拡張子（カンマ区切り。全ファイルは空欄のまま）
SET EXT=.bat

rem サブフォルダを含めない場合は --no-recursive、含める場合は空欄
SET NO_RECURSIVE=

rem 出力CSVのパス（省略するとこのバッチと同じフォルダに file_list_batch.csv を出力）
SET OUTPUT=

rem ============================================================

SET SCRIPT_DIR=%~dp0

SET CMD=python "%SCRIPT_DIR%file_list_batch.py" "%LIST_CSV%"

IF NOT "%EXT%"==""          SET CMD=%CMD% --ext "%EXT%"
IF NOT "%NO_RECURSIVE%"==""  SET CMD=%CMD% %NO_RECURSIVE%
IF NOT "%OUTPUT%"==""       SET CMD=%CMD% --output "%OUTPUT%"

echo 実行コマンド: %CMD%
echo.
%CMD%

echo.
pause
endlocal
