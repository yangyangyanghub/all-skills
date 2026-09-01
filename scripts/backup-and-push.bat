@echo off
REM Bi-monthly skill backup script
REM Syncs skill directories and commits to git

cd /d E:\code\all-skills

REM Run sync script
powershell -ExecutionPolicy Bypass -File scripts\sync-skills.ps1

REM Git operations
git add -A
git diff --cached --quiet
if errorlevel 1 (
    git commit -m "chore: bi-monthly skill backup %date:~0,10%"
    git push
    echo [OK] Backup committed and pushed
) else (
    echo [OK] No changes to commit
)
