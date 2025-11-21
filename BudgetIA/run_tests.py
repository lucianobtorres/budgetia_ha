import subprocess

try:
    result = subprocess.run(
        [
            "poetry",
            "run",
            "pytest",
            "tests/initialization/onboarding/test_orchestrator.py",
            "-v",
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    print(result.stdout)
    print(result.stderr)
except Exception as e:
    print(e)
