@echo off
setlocal

rem ============================================================
rem  keyword_search 実行バッチ
rem  ★ 以下の SET 行を必要に合わせて変更してください
rem ============================================================

rem --- フォルダ指定方法（どちらか一方を使用）---
rem
rem 【方法1】単一フォルダを直接指定
rem   TARGET_FOLDER にパスを設定し、FOLDERS_FILE は空欄にする
rem
rem 【方法2】複数フォルダをテキストファイルで指定（推奨）
rem   FOLDERS_FILE にテキストファイルのパスを設定し、TARGET_FOLDER は空欄にする
rem   テキストファイルは1行1フォルダで記載。空行・#始まり行はスキップされる。
rem
rem ★ FOLDERS_FILE が設定されている場合は TARGET_FOLDER より優先される

rem 単一フォルダ指定（方法1）
SET TARGET_FOLDER=

rem 複数フォルダリストファイル指定（方法2）
SET FOLDERS_FILE=%~dp0folders.txt

rem ============================================================

rem 検索キーワード
SET KEYWORD=ユーザーID

rem 対象拡張子（カンマ区切り。全ファイルは空欄のまま）
SET EXT=.xlsx,.docx

rem ファイル名フィルタ（ワイルドカード。不要なら空欄）
SET FILENAME_FILTER=

rem Excelシート名フィルタ（ワイルドカード。不要なら空欄）
rem   例: SET SHEET_FILTER=一覧*
SET SHEET_FILTER=

rem サブフォルダを含めない場合は --no-recursive、含める場合は空欄
SET NO_RECURSIVE=

rem 大文字小文字を区別しない場合は --ignore-case、区別する場合は空欄
SET IGNORE_CASE=--ignore-case

rem 出力先フォルダ（デフォルト: csv フォルダ）
SET OUTDIR=%~dp0..\..\csv

rem ============================================================

SET SCRIPT_DIR=%~dp0

rem キーワードと基本オプションを組み合わせる
IF NOT "%FOLDERS_FILE%"=="" (
    rem 方法2: フォルダリストファイル指定
    SET CMD=python "%SCRIPT_DIR%keyword_search.py" "%KEYWORD%" --folders-file "%FOLDERS_FILE%"
) ELSE (
    rem 方法1: 単一フォルダ直接指定
    SET CMD=python "%SCRIPT_DIR%keyword_search.py" "%TARGET_FOLDER%" "%KEYWORD%"
)

IF NOT "%EXT%"==""             SET CMD=%CMD% --ext "%EXT%"
IF NOT "%FILENAME_FILTER%"=="" SET CMD=%CMD% --filename "%FILENAME_FILTER%"
IF NOT "%SHEET_FILTER%"==""    SET CMD=%CMD% --sheet "%SHEET_FILTER%"
IF NOT "%NO_RECURSIVE%"==""    SET CMD=%CMD% %NO_RECURSIVE%
IF NOT "%IGNORE_CASE%"==""     SET CMD=%CMD% %IGNORE_CASE%
IF NOT "%OUTDIR%"==""          SET CMD=%CMD% --outdir "%OUTDIR%"

echo 実行コマンド: %CMD%
echo.
%CMD%

echo.
pause
endlocal
