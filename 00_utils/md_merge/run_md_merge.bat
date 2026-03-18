@echo off
chcp 65001 > nul
setlocal

rem ============================================================
rem  md_merge 実行バッチ
rem  ★ 以下の SET 行を環境に合わせて変更してください
rem ============================================================

rem 対象フォルダ（結合する .md ファイルがあるフォルダのパス）
SET TARGET_FOLDER=C:\work\docs

rem 出力先フォルダ（省略するとこのバッチと同じフォルダに出力）
SET OUTDIR=

rem 見出しレベル（1=# / 2=## / 3=###）
SET LEVEL=2

rem サブフォルダを含めない場合は --no-recursive、含める場合は空欄
SET NO_RECURSIVE=

rem ファイル間の区切り線（---）を省略する場合は --no-separator、付ける場合は空欄
SET NO_SEPARATOR=

rem ============================================================

SET SCRIPT_DIR=%~dp0

SET CMD=python "%SCRIPT_DIR%md_merge.py" "%TARGET_FOLDER%"

SET CMD=%CMD% --level %LEVEL%
IF NOT "%OUTDIR%"==""       SET CMD=%CMD% --output "%OUTDIR%"
IF NOT "%NO_RECURSIVE%"=="" SET CMD=%CMD% %NO_RECURSIVE%
IF NOT "%NO_SEPARATOR%"=""  SET CMD=%CMD% %NO_SEPARATOR%

echo 実行コマンド: %CMD%
echo.
%CMD%

echo.
pause
endlocal
