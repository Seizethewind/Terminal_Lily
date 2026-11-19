"""Entry point: build Lily and start the terminal."""
from config.settings import Settings
from lily.bootstrap import build
from lily.ui.terminal import Terminal
from lily.utils.errors import LilyError
from lily.utils.paths import workplace


def main():
    try:
        lily = build(Settings.load())
    except LilyError as err:
        raise SystemExit(f"Config problem: {err}")
    try:
        print(f"workplace: {workplace()}")
    except OSError as err:
        raise SystemExit(f"Cannot create the workplace: {err}")
    Terminal(lily).run()


if __name__ == "__main__":
    main()
