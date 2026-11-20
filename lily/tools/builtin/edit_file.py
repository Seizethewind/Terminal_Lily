"""Change part of a text file: replace exact old text with new text."""
from lily.self import access
from lily.tools import edit_engine, filetext, syntax_check
from lily.tools.base import BaseTool
from lily.utils.errors import ToolError
from lily.utils.paths import in_workplace, workplace


class Tool(BaseTool):
    name = "edit_file"
    description = (
        "Change part of a file: replace the old text with the new text. Copy the old text exactly from the "
        "file; it must appear once (extra surrounding lines make it unique). Wrong indentation is forgiven. "
        "An edit that breaks a Python, JSON or TOML file is refused. Use write_file for new files."
    )
    parameters = {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "file path inside the workplace"},
            "old": {"type": "string", "description": "the exact text to replace"},
            "new": {"type": "string", "description": "the text to put in its place (empty deletes)"},
        },
        "required": ["path", "old", "new"],
    }

    def run(self, path, old, new):
        file = in_workplace(path)
        if workplace() not in file.parents:
            raise ToolError(f"{file} is outside the workplace {workplace()}; Lily only writes there")
        staging = access.staging(self.lily)
        text = filetext.current(file, staging)
        if text is None:
            raise ToolError(f"{file} does not exist; use write_file to create it")
        fresh, how = edit_engine.apply_edit(text, str(old), str(new))
        problem = syntax_check.breaks(file, text, fresh)
        if problem:
            raise ToolError(f"the edit would break the file ({problem}). Nothing was changed; fix the new text.")
        if staging is not None:
            return f"{staging.stage_write(file, fresh)} (edit matched: {how})"
        try:
            file.write_text(fresh, encoding="utf-8")
        except OSError as err:
            raise ToolError(f"cannot write {file}: {err}") from err
        return f"edited {file} (matched: {how})"
