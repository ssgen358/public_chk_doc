@echo off
setlocal

rem ============================================================
rem  csv_merge 実行バッチ
rem  下の SET 行を必要に応じて変更してください
rem ============================================================

rem 対象フォルダ。Downloads を使う場合は USE_DOWNLOADS=1 にします。
SET TARGET_FOLDER=C:\work\downloads
SET USE_DOWNLOADS=1

rem 出力先CSV。ダウンロードフォルダに作る場合は以下のままでOK
SET OUTPUT=%USERPROFILE%\Downloads\merged.csv

rem 指定CSVへ貼り付ける場合に指定。使わない場合は空欄
SET PASTE_TO=
SET PASTE_START_ROW=

rem 指定Excelへ値だけ貼り付ける場合に指定。使わない場合は空欄
SET PASTE_TO_EXCEL=
SET EXCEL_SHEET=
SET PASTE_START_COL=A

rem replace: 指定行から上書き / insert: 指定行の前に挿入
SET PASTE_MODE=replace

rem 貼り付け時にバックアップを作らない場合は --no-backup、通常は空欄
SET NO_BACKUP=

rem ファイル名順: name / 更新日時順: mtime
SET SORT=mtime

rem 対象ファイル名パターン
SET PATTERN=*.csv

rem 直近N分以内に更新されたCSVだけ結合する場合に指定。例: 3 / 5
rem 全CSVを対象にする場合は空欄
SET SINCE_MINUTES=5

rem 文字コード。Excelで保存したCSVなら cp932、UTF-8なら utf-8-sig
SET ENCODING=utf-8-sig

rem どのファイル由来かを先頭列に出す場合は --add-source-column、不要なら空欄
SET ADD_SOURCE=

rem 2ファイル目以降のヘッダーも残す場合は --keep-all-headers、通常は空欄
SET KEEP_ALL_HEADERS=

rem 出力ファイルに1行目（ヘッダー）を入れない場合は --no-header-output、通常は空欄
SET NO_HEADER_OUTPUT=

rem ============================================================

SET SCRIPT_DIR=%~dp0

SET PYTHON_CMD=
where python >nul 2>nul
IF "%ERRORLEVEL%"=="0" SET PYTHON_CMD=python

IF "%PYTHON_CMD%"=="" (
    where py >nul 2>nul
    IF "%ERRORLEVEL%"=="0" SET PYTHON_CMD=py -3
)

IF "%PYTHON_CMD%"=="" (
    echo [ERROR] Python が見つかりません。Python をインストールするか、PATH を設定してください。
    echo.
    pause
    exit /b 1
)

IF "%USE_DOWNLOADS%"=="1" (
    SET CMD=%PYTHON_CMD% "%SCRIPT_DIR%csv_merge.py" --downloads
) ELSE (
    SET CMD=%PYTHON_CMD% "%SCRIPT_DIR%csv_merge.py" "%TARGET_FOLDER%"
)

SET CMD=%CMD% --output "%OUTPUT%"
SET CMD=%CMD% --sort %SORT%
SET CMD=%CMD% --pattern "%PATTERN%"
SET CMD=%CMD% --encoding %ENCODING%
IF NOT "%SINCE_MINUTES%"==""    SET CMD=%CMD% --since-minutes %SINCE_MINUTES%
IF NOT "%PASTE_TO%"==""         SET CMD=%CMD% --paste-to "%PASTE_TO%"
IF NOT "%PASTE_TO_EXCEL%"==""   SET CMD=%CMD% --paste-to-excel "%PASTE_TO_EXCEL%"
IF NOT "%EXCEL_SHEET%"==""      SET CMD=%CMD% --excel-sheet "%EXCEL_SHEET%"
IF NOT "%PASTE_START_ROW%"==""  SET CMD=%CMD% --paste-start-row %PASTE_START_ROW%
IF NOT "%PASTE_START_COL%"==""  SET CMD=%CMD% --paste-start-col %PASTE_START_COL%
IF NOT "%PASTE_TO%"==""         SET CMD=%CMD% --paste-mode %PASTE_MODE%
IF NOT "%PASTE_TO_EXCEL%"==""   SET CMD=%CMD% --paste-mode %PASTE_MODE%
IF NOT "%NO_BACKUP%"==""        SET CMD=%CMD% %NO_BACKUP%
IF NOT "%ADD_SOURCE%"==""       SET CMD=%CMD% %ADD_SOURCE%
IF NOT "%KEEP_ALL_HEADERS%"=="" SET CMD=%CMD% %KEEP_ALL_HEADERS%
IF NOT "%NO_HEADER_OUTPUT%"=="" SET CMD=%CMD% %NO_HEADER_OUTPUT%

echo 実行コマンド: %CMD%
echo.
%CMD%

echo.
pause
endlocal
