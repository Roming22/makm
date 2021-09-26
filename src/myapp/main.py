#!/usr/bin/env python3
"""Main module"""
from __future__ import annotations

import sys

from myapp.__version__ import __commit__, __version__

APP_NAME = __name__.split(".", maxsplit=1)[0]


def main(args: list[str]) -> None:
    """Main function"""
    echo(f"{APP_NAME} {__version__} ({__commit__})")
    echo(f"Args: {args}")


def echo(message: str) -> None:
    """This gives us something to mock"""
    print(message)


if __name__ == "__main__":
    main(sys.argv)
