@echo off
setlocal

rem ============================================================
rem  check_existence2 ���s�o�b�`�i���t�@�C�������j
rem  �� �ȉ��� SET �s�����ɍ��킹�ĕύX���Ă�������
rem ============================================================

rem ���t�@�C����CSV�p�X�i�S����o�͂������j
SET AXIS_CSV=C:\work\axis.csv

rem ��r�t�@�C����CSV�p�X
SET COMPARE_CSV=C:\work\compare.csv

rem ���t�@�C���̃L�[�񖼁i�ȗ���: �t�@�C�����j
SET AXIS_KEY=

rem ��r�t�@�C���̃L�[�񖼁i�ȗ���: �t�@�C�����j
SET COMPARE_KEY=

rem �o��CSV��ł̔�r��̃w�b�_���i�ȗ���: ��r�j
SET COMPARE_LABEL=

rem �o��CSV�̃p�X�i�f�t�H���g: csv �t�H���_�� check_existence2_result.csv ���o�́j
SET OUTPUT=%~dp0..\csv\check_existence_result.csv

rem �o��CSV�̕����R�[�h�i�ȗ���: cp932�j
SET ENCODING=

rem �L�[��̑啶��/����������ʂ���ꍇ�� --case-sensitive�A���Ȃ��ꍇ�͋�
SET CASE_SENSITIVE=

rem ============================================================

SET SCRIPT_DIR=%~dp0

SET CMD=python "%SCRIPT_DIR%check_existence.py" --axis "%AXIS_CSV%" --compare "%COMPARE_CSV%"

IF NOT "%AXIS_KEY%"==""       SET CMD=%CMD% --axis-key "%AXIS_KEY%"
IF NOT "%COMPARE_KEY%"==""    SET CMD=%CMD% --compare-key "%COMPARE_KEY%"
IF NOT "%COMPARE_LABEL%"==""  SET CMD=%CMD% --compare-label "%COMPARE_LABEL%"
IF NOT "%OUTPUT%"==""         SET CMD=%CMD% --output "%OUTPUT%"
IF NOT "%ENCODING%"==""       SET CMD=%CMD% --encoding %ENCODING%
IF NOT "%CASE_SENSITIVE%"==""  SET CMD=%CMD% %CASE_SENSITIVE%

echo ���s�R�}���h: %CMD%
echo.
%CMD%

echo.
pause
endlocal
