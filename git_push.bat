@echo off
REM JEBAT - Git Setup and Push Script for Windows
REM This script prepares and pushes JEBAT to GitHub

echo.
echo ====================================
echo  JEBAT - Git Setup ^& Push Script
echo ====================================
echo.

REM Check if git is installed
where git >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Git is not installed. Please install git first.
    echo Download from: https://git-scm.com/
    pause
    exit /b 1
)
echo [OK] Git is installed
echo.

REM Check if we're in a git repository
if not exist .git (
    echo [INFO] Initializing git repository...
    git init
    echo [OK] Git repository initialized
    echo.
)

REM Configure git if not already configured
git config user.name >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo [INFO] Configuring git...
    set /p GITHUB_USERNAME=Enter your GitHub username:
    set /p GITHUB_EMAIL=Enter your email:

    git config user.name "%GITHUB_USERNAME%"
    git config user.email "%GITHUB_EMAIL%"
    echo [OK] Git configured
    echo.
)

REM Check for remote
git remote | findstr "origin" >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo [INFO] Add your GitHub repository as remote:
    echo Example: https://github.com/YOUR_USERNAME/jebat-core.git
    set /p REMOTE_URL=Enter remote URL (or press Enter to skip):
    if not "%REMOTE_URL%"=="" (
        git remote add origin "%REMOTE_URL%"
        echo [OK] Remote added
    )
    echo.
)

REM Show current status
echo [INFO] Current git status:
git status --short
echo.

set /p COMMIT_MESSAGE=Enter commit message (or press Enter for default):
if "%COMMIT_MESSAGE%"=="" set COMMIT_MESSAGE=chore: Initial JEBAT commit with complete implementation

REM Add all files
echo [INFO] Staging all files...
git add .
echo [OK] Files staged

REM Commit
echo [INFO] Committing changes...
git commit -m "%COMMIT_MESSAGE%"
echo [OK] Changes committed

REM Check branch
for /f "tokens=*" %%i in ('git branch --show-current') do set CURRENT_BRANCH=%%i
echo [INFO] Current branch: %CURRENT_BRANCH%
echo.

REM Push
echo [INFO] Ready to push to GitHub
echo This will push all changes to the remote repository
set /p CONFIRM=Continue? (y/n):
if /i "%CONFIRM%"=="y" (
    echo [INFO] Pushing to GitHub...

    git push -u origin %CURRENT_BRANCH%
    if %ERRORLEVEL% equ 0 (
        echo.
        echo [OK] Successfully pushed to GitHub!
        echo.
        echo Next steps:
        echo 1. Go to your repository on GitHub
        echo 2. Review the files
        echo 3. Enable GitHub Actions for CI/CD
        echo 4. Share with the community!
    ) else (
        echo.
        echo [ERROR] Push failed. Check your credentials and try again.
        echo.
        echo Troubleshooting:
        echo - Make sure you have write access to the repository
        echo - Check if you need to set up SSH keys
        echo - Verify the remote URL is correct
    )
) else (
    echo [INFO] Push cancelled. You can push manually with: git push -u origin %CURRENT_BRANCH%
)

echo.
echo JEBAT - Because warriors remember everything that matters!
echo.
pause
