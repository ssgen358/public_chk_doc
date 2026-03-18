@echo off
chcp 65001 > nul
setlocal

rem ============================================================
rem  keyword_search 実行バッチ
rem  ★ 以下の SET 行を環境に合わせて変更してください
rem ============================================================

rem 対象フォルダ（検索するフォルダのパス）
SET TARGET_FOLDER=C:\work\設計書

rem 検索キーワード
SET KEYWORD=ユーザーID

rem 対象拡張子（カンマ区切り。全ファイルは空欄のまま）
SET EXT=.xlsx,.docx

rem ファイル名フィルタ（ワイルドカード可。不要なら空欄）
SET FILENAME_FILTER=

rem 大文字小文字を区別しない場合は --ignore-case、区別する場合は空欄
SET IGNORE_CASE=--ignore-case

rem 出力先フォルダ（省略するとこのバッチと同じフォルダに出力）
SET OUTDIR=

rem ============================================================

SET SCRIPT_DIR=%~dp0

SET CMD=python "%SCRIPT_DIR%keyword_search.py" "%TARGET_FOLDER%" "%KEYWORD%"

IF NOT "%EXT%"==""              SET CMD=%CMD% --ext %EXT%
IF NOT "%FILENAME_FILTER%"==""  SET CMD=%CMD% --filename "%FILENAME_FILTER%"
IF NOT "%IGNORE_CASE%"==""      SET CMD=%CMD% %IGNORE_CASE%
IF NOT "%OUTDIR%"==""           SET CMD=%CMD% --outdir "%OUTDIR%"

echo 実行コマンド: %CMD%
echo.
%CMD%

echo.
pause
endlocal
