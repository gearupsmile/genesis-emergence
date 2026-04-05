@echo off
echo =========================================
echo STEP 0: Branch Cleanup and Verification
echo =========================================
echo.

echo --- Current Branches ---
git branch -a
echo.

echo --- Checking unique commits on v3-secretion vs main ---
git log main..v3-secretion --oneline > temp_unique_commits.txt

for %%I in (temp_unique_commits.txt) do set FILE_SIZE=%%~zI
if %FILE_SIZE% EQU 0 (
    echo No unique commits found in v3-secretion.
) else (
    echo Unique commits found! Creating backup branch...
    git branch backup-v3-secretion v3-secretion
    echo Backup branch 'backup-v3-secretion' created successfully.
)
del temp_unique_commits.txt
echo.

echo --- Checking out 'main' branch ---
git checkout main
echo.

echo --- Creating working branch 'v5-cleanup' ---
git checkout -b v5-cleanup
echo.

echo --- Verifying existing tests (v3 codebase) ---
echo Note: Full global tests will be executed properly after Step 2 migration.
echo Running localized v3 tests...
pytest genesis_engine_v3/tests/

echo.
echo =========================================
echo STEP 0 EXECUTED. 
echo Please copy the console output above and paste it to Antigravity!
echo =========================================
pause
