from __future__ import annotations

import subprocess
import sys


CHECKS = [
    ["python3", "-m", "unittest"],
    ["python3", "-m", "grocery_pricing.pipeline"],
]


def main() -> int:
    for command in CHECKS:
        print("+ " + " ".join(command), flush=True)
        completed = subprocess.run(command, check=False)
        if completed.returncode != 0:
            return completed.returncode
    return 0


if __name__ == "__main__":
    sys.exit(main())
