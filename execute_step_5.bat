@echo off
echo =========================================
echo STEP 5: Final Cross-Version Verification
echo =========================================

echo --- Verifying complete repository health post-migration ---
python scripts\quick_verify.py

echo.
echo =========================================
echo STEP 5 EXECUTED.
echo Please copy the console output above and paste it to Antigravity!
echo =========================================
pause
