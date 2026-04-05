@echo off
echo =========================================
echo STEP 6: Final Commit and Merge to Main
echo =========================================

echo --- Committing Reorganized Structure ---
git add .
git commit -m "chore: finalize repository reorganization, migrate to structured v1-v3 format, and generate review docs"

echo --- Merging to Main ---
git checkout main
git merge v5-cleanup

echo.
echo =========================================
echo STEP 6 EXECUTED.
echo ✅ Repository successfully reorganized!
echo Please copy the console output above and paste it to Antigravity!
echo =========================================
pause
