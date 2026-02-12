"""
Comprehensive AI Prompts Test Runner

Runs both general and VTuber tests across all models and temperatures.
Saves results to timestamped files for comparison.
"""

import subprocess
import sys
from datetime import datetime
from pathlib import Path


def run_test(script_name, model, temperature, output_dir):
    """Run a single test and save output"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = output_dir / f"{script_name.stem}_{model.replace(':', '_')}_t{temperature}_{timestamp}.txt"

    print(f"\n{'='*80}")
    print(f"Running: {script_name.name}")
    print(f"Model: {model}")
    print(f"Temperature: {temperature}")
    print(f"Output: {output_file.name}")
    print('='*80)

    cmd = [
        sys.executable,
        str(script_name),
        '--model', model,
        '--temperature', str(temperature)
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent
        )

        # Save to file
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(result.stdout)
            if result.stderr:
                f.write("\n\n--- STDERR ---\n")
                f.write(result.stderr)

        # Also print to console
        print(result.stdout)

        return output_file, result.returncode == 0

    except Exception as e:
        print(f"ERROR: {e}")
        return None, False


def main():
    # Configuration
    MODELS = [
        'gemma3:12b',
        'qwen3:14b',
        'qwen2.5:7b'
    ]

    TEMPERATURES = [0.5]  # Can add more: [0.3, 0.5, 0.7]

    TESTS = [
        'test_prompts_v2.py',      # General test
        'test_vtuber_prompts.py'   # VTuber test
    ]

    # Create output directory
    output_dir = Path('test_results')
    output_dir.mkdir(exist_ok=True)

    print("\n" + "="*80)
    print("  COMPREHENSIVE AI PROMPTS TEST SUITE")
    print("="*80)
    print(f"\nModels to test: {', '.join(MODELS)}")
    print(f"Temperatures: {', '.join(map(str, TEMPERATURES))}")
    print(f"Test scripts: {', '.join(TESTS)}")
    print(f"Output directory: {output_dir}")
    print(f"\nTotal tests to run: {len(MODELS) * len(TEMPERATURES) * len(TESTS)}")

    input("\nPress Enter to start testing...")

    # Track results
    results = []

    # Run all combinations
    for test_script in TESTS:
        script_path = Path(__file__).parent / test_script

        if not script_path.exists():
            print(f"\n⚠️  WARNING: Test script not found: {test_script}")
            continue

        for model in MODELS:
            for temp in TEMPERATURES:
                output_file, success = run_test(script_path, model, temp, output_dir)

                results.append({
                    'test': test_script,
                    'model': model,
                    'temperature': temp,
                    'output': output_file,
                    'success': success
                })

    # Summary
    print("\n" + "="*80)
    print("  TEST SUMMARY")
    print("="*80)

    for result in results:
        status = "✓" if result['success'] else "✗"
        print(f"{status} {result['test']} - {result['model']} (T={result['temperature']})")
        if result['output']:
            print(f"   → {result['output']}")

    print(f"\n✓ All results saved to: {output_dir.absolute()}")
    print("\nNext steps:")
    print("1. Review output files for detailed results")
    print("2. Compare artist accuracy across models")
    print("3. Compare confidence calibration")
    print("4. Choose best model for your use case")


if __name__ == "__main__":
    main()
