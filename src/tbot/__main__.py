from __future__ import annotations

import logging

from .telegram.app import run_polling


logging.basicConfig(level=logging.INFO)


def main() -> None:
    run_polling()


if __name__ == "__main__":
    main()
