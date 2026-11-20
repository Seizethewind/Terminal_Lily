"""Everything one worker attempt changed, so a failed attempt can be undone."""
from lily.self import access
from lily.self.snapshot import Snapshot
from lily.utils.paths import workplace


class Rollback:
    def __init__(self, lily, limits):
        self.lily = lily
        self.max_files = limits.get("snapshot_max_files", 2000)
        self.max_bytes = limits.get("snapshot_max_mb", 20) * 1_000_000
        self.staged = {}   # file -> its staged text before this attempt (None: it was not staged)
        self.snapshot = None

    def before_write(self, file):
        staging = access.staging(self.lily)
        if staging is None:   # writes land at once, so copy the workplace first
            self.before_command()
        elif file not in self.staged:
            self.staged[file] = staging.read(file)

    def before_command(self):
        if self.snapshot is None:
            self.snapshot = Snapshot(workplace(), self.max_files, self.max_bytes)

    def undo(self):
        """Undo this attempt. Returns a short sentence about what was undone ('' when nothing changed)."""
        notes = []
        staging = access.staging(self.lily)
        if staging is not None and self.staged:
            for file, previous in self.staged.items():
                staging.restore(file, previous)
            notes.append(f"un-staged {len(self.staged)} file(s)")
        if self.snapshot is not None:
            notes.append("workplace restored" if self.snapshot.restore() else "workplace too big to restore")
        self.discard()
        return ", ".join(notes)

    def discard(self):
        if self.snapshot is not None:
            self.snapshot.discard()
            self.snapshot = None
        self.staged = {}
