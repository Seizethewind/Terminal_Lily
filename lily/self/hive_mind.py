"""The live board Lily and every worker share: who does what, what they did, and approval requests."""
import threading

KEEP = 20   # notes kept per task


class HiveMind:
    def __init__(self, on_request=None):
        self.lock = threading.Lock()
        self.on_request = on_request   # told when a worker starts waiting for the user (a notification)
        self.workers = {}     # task id -> {"role", "state", "note"}
        self.notes = {}       # task id -> short lines about what was done (Lily reads them on a takeover)
        self.approvals = {}   # approval key -> {"task", "text", "answer", "event"}
        self._next = 0

    def join(self, task_id, role):
        with self.lock:
            self.workers[task_id] = {"role": role, "state": "running", "note": "starting"}
            self.notes[task_id] = []

    def note(self, task_id, line):
        with self.lock:
            self.notes.setdefault(task_id, []).append(line[:200])
            del self.notes[task_id][:-KEEP]
            if task_id in self.workers:
                self.workers[task_id]["note"] = line[:80]

    def set_state(self, task_id, state):
        with self.lock:
            if task_id in self.workers:
                self.workers[task_id]["state"] = state

    def trail(self, task_id):
        with self.lock:
            return list(self.notes.get(task_id, []))

    def leave(self, task_id):
        with self.lock:
            self.workers.pop(task_id, None)
            self.notes.pop(task_id, None)

    def request(self, task_id, text, wait):
        """A worker asks to do something. Blocks until the user answers; no answer in time means no."""
        event = threading.Event()
        with self.lock:
            self._next += 1
            key = self._next
            self.approvals[key] = {"task": task_id, "text": text, "answer": None, "event": event}
        self.note(task_id, f"waiting for approval: {text}")
        if self.on_request:
            try:
                self.on_request(task_id, text)
            except Exception:   # noqa: BLE001 - a failed notification must never block an approval
                pass
        event.wait(wait)
        with self.lock:
            item = self.approvals.pop(key)
        return item["answer"] is True

    def pending(self):
        with self.lock:
            return [(key, a["task"], a["text"]) for key, a in self.approvals.items() if a["answer"] is None]

    def answer(self, key, yes):
        """The user's answer. False if that request is gone (answered already or timed out)."""
        with self.lock:
            item = self.approvals.get(key)
            if item is None or item["answer"] is not None:
                return False
            item["answer"] = bool(yes)
        item["event"].set()
        return True

    def snapshot(self):
        """Lines for Lily: the workers right now and what waits for the user."""
        with self.lock:
            busy = [f"#{tid} {w['role']} ({w['state']}): {w['note']}" for tid, w in self.workers.items()]
        lines = ["Workers right now:"] + busy if busy else []
        waiting = self.pending()
        if waiting:
            lines.append("Waiting for the user's approval (ask them, then call approve_task):")
            lines += [f"approval {key} for task #{task}: {text}" for key, task, text in waiting]
        return lines
