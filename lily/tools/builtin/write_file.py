"""Write or append to a text file."""
from lily.self import access
from lily.tools import filetext, syntax_check
from lily.tools.base import BaseTool
from lily.utils.errors import ToolError
from lily.utils.paths import in_workplace, workplace


class Tool(BaseTool):
    name = "write_file"
    description = (
        "Write text to a file (creates folders as needed). Set append to add to the end instead. "
        "Files may only be staged: they are saved when the user applies them. "
        "A new Python, JSON or TOML text that does not parse is refused. Use edit_file for small changes."
    )
    parameters = {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "file path inside the workplace (a relative path starts there)"},
            "content": {"type": "string", "description": "the text to write"},
            "append": {"type": "boolean", "description": "add to the end instead of replacing"},
        },
        "required": ["path", "content"],
    }

    def run(self, path, content, append=False):
        file = in_workplace(path)
        if workplace() not in file.parents:
            raise ToolError(f"{file} is outside the workplace {workplace()}; Lily only writes there")
        staging = access.staging(self.lily)
        if not append:
            problem = syntax_check.breaks(file, filetext.current(file, staging), content)
            if problem:
                raise ToolError(f"{file.name} would not be valid ({problem}). Nothing was written; fix the text.")
        if staging is not None:
            return staging.stage_write(file, content, append)
        try:
            file.parent.mkdir(parents=True, exist_ok=True)
            with open(file, "a" if append else "w", encoding="utf-8") as handle:
                handle.write(content)
        except OSError as err:
            raise ToolError(f"cannot write {file}: {err}") from err
        verb = "appended to" if append else "wrote"
        return f"{verb} {file} ({len(content)} characters)"
