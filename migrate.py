from pathlib import Path

from alembic import command
from alembic.config import Config

from database import DATABASE_URL

_cfg = Config(str(Path(__file__).with_name("alembic.ini")))
_cfg.set_main_option("sqlalchemy.url", DATABASE_URL)


def upgrade(rev: str = "head") -> None:
    command.upgrade(_cfg, rev)


def downgrade(rev: str) -> None:
    command.downgrade(_cfg, rev)


def revision(msg: str) -> None:
    command.revision(_cfg, message=msg, autogenerate=True)


if __name__ == "__main__":
    import argparse

    p = argparse.ArgumentParser()
    p.add_argument("cmd", choices=["upgrade", "downgrade", "revision"])
    p.add_argument("arg", nargs="?")
    args = p.parse_args()

    match args.cmd:
        case "upgrade":
            upgrade(args.arg or "head")
        case "downgrade":
            downgrade(args.arg)
        case "revision":
            if not args.arg:
                raise SystemExit("revision message required")
            revision(args.arg)
