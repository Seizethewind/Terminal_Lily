"""Unit tests (run: python -m unittest discover -s tests -t .)."""
import os
import tempfile

# Tests must never create the real workplace in the home folder.
os.environ["LILY_WORKPLACE_DIR"] = tempfile.mkdtemp()
