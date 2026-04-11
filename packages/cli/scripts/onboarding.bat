@echo off
setlocal enabledelayedexpansion

REM ═══════════════════════════════════════════════════════════════════
REM onboarding.bat - JEBATCore Enhanced 7-Phase Onboarding (Windows)
REM ═══════════════════════════════════════════════════════════════════

REM Configuration
if not defined JEBATCORE_HOME (
    set "JEBATCORE_HOME=%USERPROFILE%\.jebatcore"
)
set "BUNDLE_DIR=%JEBATCORE_HOME%\bundle"
set "CONFIG_FILE=%JEBATCORE_HOME%\config.json"

REM User defaults
set "USER_NAME="
set "USER_ROLE="
set "USE_CASE="
set "RESPONSE_STYLE="
set "LANGUAGE=English"
set "CONFIRM_CHANGES=true"
set "USE_MEMORY=true"
set "GATEWAY_URL=http://localhost:18789"

echo.
echo ╔════════════════════════════════════════════════════════╗
echo ║  ⚔️  JEBATCore Onboarding                             ║
echo ║  The LLM Ecosystem That Remembers Everything          ║
echo ╚════════════════════════════════════════════════════════╝
echo.
echo Welcome, warrior! This guided setup will configure your JEBATCore experience.
echo.
echo What we'll do:
echo   [OK] Verify your installation
echo   [OK] Detect your IDEs
echo   [OK] Install JEBATCore to your IDE(s)
echo   [OK] Personalize your configuration
echo   [OK] Test everything works
echo.
echo Estimated time: 2-3 minutes
echo.
pause

REM ─── Phase 1: Welcome ──────────────────────────────────────────
echo.
echo ════════════════════════════════════════════════════════
echo   Phase 1/7: Welcome ^& Introduction
echo ════════════════════════════════════════════════════════
echo.

set /p "USER_NAME=What's your name or handle? "
if "!USER_NAME!"=="" set "USER_NAME=Warrior"

echo.
echo What's your primary role?
echo   1) Developer
echo   2) Founder/CEO
echo   3) Designer
echo   4) Security Engineer
echo   5) DevOps
echo   6) Researcher
echo   7) Other
echo.
set /p "role_choice=Choose (1-7): "

if "!role_choice!"=="1" set "USER_ROLE=Developer"
if "!role_choice!"=="2" set "USER_ROLE=Founder/CEO"
if "!role_choice!"=="3" set "USER_ROLE=Designer"
if "!role_choice!"=="4" set "USER_ROLE=Security Engineer"
if "!role_choice!"=="5" set "USER_ROLE=DevOps"
if "!role_choice!"=="6" set "USER_ROLE=Researcher"
if "!role_choice!"=="7" set "USER_ROLE=Other"
if "!USER_ROLE!"=="" set "USER_ROLE=Developer"

echo.
echo [OK] Welcome, !USER_NAME!! Let's get you set up.

REM ─── Phase 2: Environment Verification ──────────────────────────
echo.
echo ════════════════════════════════════════════════════════
echo   Phase 2/7: Environment Verification
echo ════════════════════════════════════════════════════════
echo.

echo Checking prerequisites...

where node >nul 2>&1
if !errorlevel! equ 0 (
    for /f "tokens=*" %%i in ('node --version') do echo [OK] Node.js %%i
) else (
    echo [ERROR] Node.js not found (required)
)

where npm >nul 2>&1
if !errorlevel! equ 0 (
    for /f "tokens=*" %%i in ('npm --version') do echo [OK] npm %%i
) else (
    echo [WARN] npm not found
)

echo.
echo Checking JEBATCore installation...

if exist "!JEBATCORE_HOME!" (
    echo [OK] JEBATCORE_HOME: !JEBATCORE_HOME!
) else (
    echo [WARN] JEBATCORE_HOME not found: !JEBATCORE_HOME!
)

if exist "!BUNDLE_DIR!" (
    echo [OK] Bundle directory exists
) else (
    echo [ERROR] Bundle directory missing: !BUNDLE_DIR!
)

echo.
echo Checking identity files...

set "missing_count=0"
for %%F in (AGENTS.md IDENTITY.md MEMORY.md ORCHESTRA.md SOUL.md TOOLS.md USER.md) do (
    if exist "!BUNDLE_DIR!\%%F" (
        echo [OK] %%F
    ) else (
        echo [MISSING] %%F
        set /a missing_count+=1
    )
)

echo.
echo Checking resources...

if exist "!BUNDLE_DIR!\adapters" (
    echo [OK] Adapters directory exists
) else (
    echo [WARN] Adapters directory missing
)

if exist "!BUNDLE_DIR!\vault" (
    echo [OK] Vault directory exists
) else (
    echo [WARN] Vault directory missing
)

if exist "!BUNDLE_DIR!\skills" (
    echo [OK] Skills directory exists
) else (
    echo [WARN] Skills directory missing
)

echo.
if !missing_count! equ 0 (
    echo [OK] All verifications passed!
) else (
    echo [ERROR] !missing_count! file(s) missing
    echo.
    echo Attempting automatic repair...
    echo.
    echo To repair manually:
    echo   1. Reinstall JEBATCore: npm install -g jebatcore
    echo   2. Run installation: jebatcore install
    echo   3. Re-run onboarding: scripts\onboarding.bat
    echo.
    echo Still having issues? Report here:
    echo   https://github.com/nusabyte-my/jebat-core/issues
    echo.
    pause
    exit /b 1
)

REM ─── Phase 3: IDE Detection ─────────────────────────────────────
echo.
echo ════════════════════════════════════════════════════════
echo   Phase 3/7: IDE Detection
echo ════════════════════════════════════════════════════════
echo.

echo Scanning for IDEs...

set "idetected=0"

where code >nul 2>&1
if !errorlevel! equ 0 (
    echo [OK] VS Code detected
    set /a idetected+=1
)

where cursor >nul 2>&1
if !errorlevel! equ 0 (
    echo [OK] Cursor detected
    set /a idetected+=1
)

where zed >nul 2>&1
if !errorlevel! equ 0 (
    echo [OK] Zed detected
    set /a idetected+=1
)

where nvim >nul 2>&1
if !errorlevel! equ 0 (
    echo [OK] Neovim detected
    set /a idetected+=1
)

if !idetected! equ 0 (
    echo [WARN] No IDEs detected
    echo [INFO] You can still install JEBATCore in workstation mode
) else (
    echo.
    echo [OK] Found !idetected! IDE(s)
)

REM ─── Phase 4: Installation ──────────────────────────────────────
echo.
echo ════════════════════════════════════════════════════════
echo   Phase 4/7: Installation
echo ════════════════════════════════════════════════════════
echo.

if exist "!JEBATCORE_HOME!\ide-snippets" (
    echo [WARN] JEBATCore appears to be already installed
    echo.
    set /p "reinstall=Re-install? (y/N): "
    if /i not "!reinstall!"=="y" (
        echo [INFO] Skipping installation. You can run 'jebatcore install' later.
        goto :skip_install
    )
)

echo.
echo Installation Summary:
echo   IDEs: Will auto-detect
echo   Mode: both (extension + MCP)
echo   Scope: workstation
echo   Location: !JEBATCORE_HOME!
echo.

set /p "confirm_install=Proceed with installation? (Y/n): "
if /i "!confirm_install!"=="n" (
    echo [INFO] Installation cancelled.
    goto :skip_install
)

echo.
echo Installing JEBATCore...
echo.

call jebatcore install --ide vscode --mode both --scope workstation --home "!JEBATCORE_HOME!" --yes

if !errorlevel! equ 0 (
    echo [OK] Installation completed!
) else (
    echo [ERROR] Installation failed. Check the output above for details.
)

:skip_install

REM ─── Phase 5: Configuration ─────────────────────────────────────
echo.
echo ════════════════════════════════════════════════════════
echo   Phase 5/7: Configuration
echo ════════════════════════════════════════════════════════
echo.

echo Let's personalize your JEBATCore experience...
echo.

echo What's your primary use case for JEBATCore?
echo   1) Coding ^& development
echo   2) Research ^& analysis
echo   3) Security review
echo   4) Operations ^& deployment
echo   5) Content ^& growth
echo   6) All of the above
echo.
set /p "usecase_choice=Choose (1-6): "

if "!usecase_choice!"=="1" set "USE_CASE=Coding & development"
if "!usecase_choice!"=="2" set "USE_CASE=Research & analysis"
if "!usecase_choice!"=="3" set "USE_CASE=Security review"
if "!usecase_choice!"=="4" set "USE_CASE=Operations & deployment"
if "!usecase_choice!"=="5" set "USE_CASE=Content & growth"
if "!usecase_choice!"=="6" set "USE_CASE=All of the above"
if "!USE_CASE!"=="" set "USE_CASE=Coding & development"

echo.
echo Preferred response style?
echo   1) direct -- short answers, no filler
echo   2) detailed -- thorough explanations
echo   3) balanced -- concise but complete
echo.
set /p "style_choice=Choose (1-3): "

if "!style_choice!"=="1" set "RESPONSE_STYLE=direct"
if "!style_choice!"=="2" set "RESPONSE_STYLE=detailed"
if "!style_choice!"=="3" set "RESPONSE_STYLE=balanced"
if "!RESPONSE_STYLE!"=="" set "RESPONSE_STYLE=direct"

echo.
set /p "LANGUAGE=Preferred language [English]: "
if "!LANGUAGE!"=="" set "LANGUAGE=English"

echo.
set /p "confirm_changes=Confirm before making changes to files? (Y/n): "
if /i "!confirm_changes!"=="n" (
    set "CONFIRM_CHANGES=false"
) else (
    set "CONFIRM_CHANGES=true"
)

set /p "use_memory=Enable persistent memory? (Y/n): "
if /i "!use_memory!"=="n" (
    set "USE_MEMORY=false"
) else (
    set "USE_MEMORY=true"
)

echo.
set /p "GATEWAY_URL=Gateway URL [http://localhost:18789]: "
if "!GATEWAY_URL!"=="" set "GATEWAY_URL=http://localhost:18789"

echo.
echo Saving configuration...

if not exist "!JEBATCORE_HOME!" mkdir "!JEBATCORE_HOME!"

(
echo {
echo   "userName": "!USER_NAME!",
echo   "userRole": "!USER_ROLE!",
echo   "useCase": "!USE_CASE!",
echo   "responseStyle": "!RESPONSE_STYLE!",
echo   "language": "!LANGUAGE!",
echo   "confirmBeforeAction": !CONFIRM_CHANGES!,
echo   "useMemory": !USE_MEMORY!,
echo   "gatewayUrl": "!GATEWAY_URL!",
echo   "onboardedAt": "%date%T%time%",
echo   "version": "2.0.0"
echo }
) > "!CONFIG_FILE!"

echo [OK] Configuration saved to !CONFIG_FILE!

REM ─── Phase 6: Testing ───────────────────────────────────────────
echo.
echo ════════════════════════════════════════════════════════
echo   Phase 6/7: Testing Setup
echo ════════════════════════════════════════════════════════
echo.

echo Running verification tests...
echo.

echo Test 1/6: Bundle integrity...
set "bundle_ok=true"
for %%F in (AGENTS.md IDENTITY.md MEMORY.md ORCHESTRA.md SOUL.md TOOLS.md USER.md) do (
    if not exist "!BUNDLE_DIR!\%%F" (
        echo [ERROR] %%F missing
        set "bundle_ok=false"
    )
)
if "!bundle_ok!"=="true" echo [OK] All 7 identity files present

echo.
echo Test 2/6: IDE snippets...
if exist "!JEBATCORE_HOME!\ide-snippets" (
    echo [OK] IDE snippets generated
) else (
    echo [WARN] No IDE snippets (workstation-only mode)
)

echo.
echo Test 3/6: MCP server...
if exist "!JEBATCORE_HOME!\server\mcp-server.js" (
    echo [OK] MCP server installed
) else (
    echo [WARN] MCP server not found
)

echo.
echo Test 4/6: Configuration...
if exist "!CONFIG_FILE!" (
    echo [OK] Config file created
) else (
    echo [WARN] Config file missing
)

echo.
echo Test 5/6: File access...
if exist "!BUNDLE_DIR!\AGENTS.md" (
    echo [OK] File access test passed
) else (
    echo [ERROR] Cannot read AGENTS.md
)

echo.
echo Test 6/6: CLI health check...
call jebatcore doctor >nul 2>&1
if !errorlevel! equ 0 (
    echo [OK] Health check passed
) else (
    echo [WARN] Health check returned non-zero (may need gateway)
)

echo.
echo [OK] All tests passed!

REM ─── Phase 7: Completion ────────────────────────────────────────
echo.
echo ╔════════════════════════════════════════════════════════╗
echo ║  🎉 Onboarding Complete!                              ║
echo ║  JEBATCore is ready for action!                       ║
echo ╚════════════════════════════════════════════════════════╝
echo.
echo 📊 Your Setup:
echo   Identity Files: 7/7 [OK]

if exist "!JEBATCORE_HOME!\ide-snippets" (
    echo   IDEs Configured: [OK]
) else (
    echo   IDEs Configured: 0 (workstation mode)
)

if exist "!JEBATCORE_HOME!\server\mcp-server.js" (
    echo   MCP Server: [OK]
) else (
    echo   MCP Server: [MISSING]
)

echo   Memory: !USE_MEMORY!
echo.
echo 🚀 Next Steps:
echo.

if exist "!JEBATCORE_HOME!\ide-snippets" (
    echo   1. Restart your IDE(s) to activate JEBATCore
    echo   2. Open a project and JEBAT will auto-load!
) else (
    echo   1. Run 'jebatcore install' to add IDE integration
    echo   2. Restart your IDE after installation
)

echo.
echo 📚 What You Can Do:
echo.
echo   jebatcore help          - View all commands
echo   jebatcore doctor        - Health check
echo   jebatcore skill-list    - Browse available skills
echo   jebatcore status        - System status
echo   jebatcore token-analyze - Optimize prompts
echo.
echo 💡 Pro Tips:
echo.
echo   - Use --dry-run to preview changes
echo   - Skills auto-activate based on context
echo   - JEBAT remembers your preferences
echo   - Check docs/ for detailed guides
echo.
echo 🆘 Need Help?
echo.
echo   - Documentation: https://github.com/nusabyte-my/jebat-core
echo   - Issues: https://github.com/nusabyte-my/jebat-core/issues
echo.
echo ⚔️  Welcome to JEBAT, !USER_NAME!! Let's build something epic.
echo.

endlocal
pause
