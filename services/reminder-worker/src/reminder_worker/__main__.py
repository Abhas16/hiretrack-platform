"""Entry point: `python -m reminder_worker` (what the CronJob container runs)."""

import sys

from reminder_worker.jobs.run_reminders import run


def main() -> None:
    sys.exit(run())


if __name__ == "__main__":
    main()
