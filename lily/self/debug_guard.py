"""Counts failed commands inside one worker attempt and stops the attempt after too many."""
import re

EXIT = re.compile(r"^exit code (-?\d+)")


class DebugLimit(Exception):
    """Too many failed commands in a row.

    Not a LilyError on purpose: it has to end the attempt, not be handed back to the model.
    """


class DebugGuard:
    def __init__(self, tries, note=None):
        self.tries, self.failed = max(1, int(tries)), 0
        self.note = note or (lambda line: None)   # told about every failure (the hive mind trail)

    def after(self, output):
        """Look at a shell result. A success resets the count; a failure adds a hint for the model."""
        match = EXIT.match(output)
        if match is None or match.group(1) == "0":
            self.failed = 0
            return output
        return output + self._failure(output.split("\n", 1)[-1])

    def error(self, text):
        """The same for a command that could not run at all (a timeout, say). Returns the hint."""
        return self._failure(text)

    def _failure(self, detail):
        self.failed += 1
        line = (detail.strip().splitlines() or ["no output"])[-1][:120]
        self.note(line)
        if self.failed >= self.tries:
            raise DebugLimit(f"{self.failed} failed commands in a row, last: {line}")
        return (f"\n[Command failed, try {self.failed} of {self.tries}. Read the error, fix the cause and run "
                f"it again. After {self.tries} failed commands in a row this attempt is stopped and undone.]")
