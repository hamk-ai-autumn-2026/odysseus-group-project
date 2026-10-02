"""
Cross-platform verification script for DocuMind.
Runs seamlessly on Windows (cmd/PowerShell), Linux, and macOS.
"""

import sys
import subprocess


def run_step(step_num: int, description: str, command: list[str]) -> None:
    print(f"[{step_num}/3] {description}...")
    try:
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Step {step_num} failed with exit code {e.returncode}")
        sys.exit(e.returncode)


def main() -> None:
    print("==========================================")
    print("🧪 Running DocuMind Automated Sanity Checks (Cross-Platform)")
    print("==========================================")

    run_step(1, "Checking UV environment", ["uv", "--version"])
    run_step(2, "Running pytest suite", ["uv", "run", "pytest", "-v"])
    run_step(
        3,
        "Verifying Streamlit module dry-run",
        [
            "uv",
            "run",
            "python",
            "-c",
            "import app; print('✅ app.py syntax and imports verified!')",
        ],
    )

    print("==========================================")
    print("🎉 ALL SANITY CHECKS PASSED SUCCESSFULLY!")
    print("==========================================")


if __name__ == "__main__":
    main()
