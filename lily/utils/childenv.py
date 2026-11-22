"""The environment a shell command gets: Lily's own keys never go into it."""
import os

HIDDEN = {"LILY_API_KEY"}   # config.settings.load_env adds every name it reads from .env


def clean():
    return {name: value for name, value in os.environ.items() if name not in HIDDEN}
