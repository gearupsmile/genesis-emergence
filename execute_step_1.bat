@echo off
echo =========================================
echo STEP 1: Merge Codebase and Verify
echo =========================================
echo.

echo --- Attempting to install Pytest securely ---
python -m pip install pytest numpy pandas matplotlib

echo --- Checking out v5-cleanup securely ---
git checkout v5-cleanup

echo --- Merging V4 assets from v3-secretion into v5-cleanup ---
git merge v3-secretion --no-edit
echo.

echo --- Running quick_verify.py ---
python scripts/quick_verify.py

echo.
echo =========================================
echo STEP 1 EXECUTED. 
echo Please copy the console output above and paste it to Antigravity!
echo =========================================
pause
