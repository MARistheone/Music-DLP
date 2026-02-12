@echo off
REM Quick VTuber test comparison across all models

echo ================================================================================
echo VTuber Music Test - Model Comparison
echo ================================================================================
echo.
echo Testing all 3 models with temperature 0.5
echo Results will be saved to test_results\
echo.

REM Create output directory
if not exist test_results mkdir test_results

echo.
echo [1/3] Testing gemma3:12b...
echo ================================================================================
python test_vtuber_prompts.py --model gemma3:12b --temperature 0.5 > test_results\vtuber_gemma3_12b.txt
type test_results\vtuber_gemma3_12b.txt

echo.
echo.
echo [2/3] Testing qwen3:14b...
echo ================================================================================
python test_vtuber_prompts.py --model qwen3:14b --temperature 0.5 > test_results\vtuber_qwen3_14b.txt
type test_results\vtuber_qwen3_14b.txt

echo.
echo.
echo [3/3] Testing qwen2.5:7b...
echo ================================================================================
python test_vtuber_prompts.py --model qwen2.5:7b --temperature 0.5 > test_results\vtuber_qwen2_5_7b.txt
type test_results\vtuber_qwen2_5_7b.txt

echo.
echo ================================================================================
echo All tests complete!
echo ================================================================================
echo.
echo Results saved to:
echo   - test_results\vtuber_gemma3_12b.txt
echo   - test_results\vtuber_qwen3_14b.txt
echo   - test_results\vtuber_qwen2_5_7b.txt
echo.
echo Open these files to compare:
echo   - Artist accuracy
echo   - Confidence calibration
echo   - Average confidence
echo.
pause
