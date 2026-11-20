"""A copy of the workplace taken before a worker changes it with commands, so a failed attempt can be undone."""
import filecmp
import shutil
import tempfile
from pathlib import Path


def _files(root):
    return {path.relative_to(root) for path in Path(root).rglob("*") if path.is_file() and not path.is_symlink()}


class Snapshot:
    def __init__(self, root, max_files, max_bytes):
        self.root, self.copy, self.ok = Path(root), None, False
        try:
            files = _files(self.root)
            if len(files) > max_files or sum((self.root / rel).stat().st_size for rel in files) > max_bytes:
                return   # too big to copy on a phone: the attempt then cannot be undone
            self.copy = Path(tempfile.mkdtemp(prefix="lily-snapshot-"))
            for rel in files:
                (self.copy / rel).parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(self.root / rel, self.copy / rel)
        except OSError:
            self.discard()
            return
        self.ok = True

    def restore(self):
        """Put the workplace back as it was. Returns (files removed, files restored), or None if no copy."""
        if not self.ok:
            return None
        before, now = _files(self.copy), _files(self.root)
        for rel in now - before:
            (self.root / rel).unlink(missing_ok=True)
        restored = 0
        for rel in before:
            src, dest = self.copy / rel, self.root / rel
            if dest.is_file() and filecmp.cmp(src, dest, shallow=False):
                continue
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dest)
            restored += 1
        return len(now - before), restored

    def discard(self):
        if self.copy is not None:
            shutil.rmtree(self.copy, ignore_errors=True)
            self.copy = None
