"""Entry point: `python -m job_scout` (what the CronJob container runs)."""

import sys

from job_scout.jobs.run_scout import run


def main() -> None:
    sys.exit(run())


if __name__ == "__main__":
    main()
