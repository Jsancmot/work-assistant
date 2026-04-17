"""
Application entry point.
"""

import logging

from src.interfaces.telegram.bot import run_bot

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)


def main() -> None:
    run_bot()


if __name__ == "__main__":
    main()
