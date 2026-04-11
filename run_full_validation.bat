@echo off
echo ===================================================
echo Starting Genesis V5 vs V4 Full Validation Suite
echo ===================================================
echo.

echo [1/3] Running V5 Seeded Validation (10k Gens, Seeds [42, 123, 456])...
python v5/experiments/run_validation_v5_seeds.py
if %errorlevel% neq 0 exit /b %errorlevel%
echo V5 runs completed.
echo.

echo [2/3] Running V4 Baseline Seeded Validation (10k Gens, Seeds [42, 123, 456])...
python v4/experiments/run_baseline_comparison.py
if %errorlevel% neq 0 exit /b %errorlevel%
echo V4 runs completed.
echo.

echo [3/3] Running Statistical Analysis and Plotting...
python v5/experiments/analyze_v5_vs_v4.py
if %errorlevel% neq 0 exit /b %errorlevel%
echo.

echo ===================================================
echo Suite Finished! Check docs/v5_v4_comparison.png
echo ===================================================
pause
