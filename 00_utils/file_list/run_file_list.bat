@echo off
setlocal

rem ============================================================
rem  file_list 実行バッチ
rem  ★ 以下の SET 行を環境に合わせて変更してください
rem ============================================================

rem 対象フォルダ（ファイルを一覧化するフォルダのパス）
SET TARGET_FOLDER=C:\work\設計書

rem 対象拡張子（カンマ区切り。全ファイルは空欄のまま）
SET EXT=.xlsx,.docx

rem サブフォルダを含めない場合は --no-recursive、含める場合は空欄
SET NO_RECURSIVE=

rem 出力CSVのパス（省略するとこのバッチと同じフォルダに file_list.csv を出力）
SET OUTPUT=

rem ============================================================

SET SCRIPT_DIR=%~dp0

SET CMD=python "%SCRIPT_DIR%file_list.py" "%TARGET_FOLDER%"

IF NOT "%EXT%"==""          SET CMD=%CMD% --ext %EXT%
IF NOT "%NO_RECURSIVE%"==""  SET CMD=%CMD% %NO_RECURSIVE%
IF NOT "%OUTPUT%"==""       SET CMD=%CMD% --output "%OUTPUT%"

echo 実行コマンド: %CMD%
echo.
%CMD%

echo.
pause
endlocal
