@echo off
SET log_file="startup.log"
echo Starting app.py... > %log_file%
python app.py >> %log_file% 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo Failed to start app.py, error level: %ERRORLEVEL% >> %log_file%
) ELSE (
    echo app.py started successfully. >> %log_file%
)
