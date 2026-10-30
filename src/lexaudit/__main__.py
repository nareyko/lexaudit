"""Allow `python -m lexaudit`."""

from lexaudit.cli.main import main

if __name__ == "__main__":
    raise SystemExit(main())
