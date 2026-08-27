"""JEBAT Execute Code Tool — runs Python scripts that call tools programmatically.

This lets the agent batch process data through the tool system:
read_file -> process -> search_files -> patch -> terminal, all in one script.
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
import tempfile
import textwrap
from typing import Any

from jebat.tools import register_tool


# ── Injected Module (available as `from jebat_tools import ...`) ─────────────

_JEBAT_TOOLS_MODULE = textwrap.dedent('''\
    """JEBAT Tools — programmatic access to JEBAT tool system.

    Use this inside execute_code() scripts. Import with:
        from jebat_tools import read_file, write_file, search_files, patch, terminal, call_tool
    """

    import json
    import subprocess as _sp
    import sys as _sys
    import textwrap as _textwrap

    _JEBAT_PYTHON = _sys.executable


    def _jebat_cmd(method, **kwargs):
        """Call a JEBAT CLI tool via subprocess."""
        payload = json.dumps({"method": method, "params": kwargs})
        code = _textwrap.dedent("""\\
            import json, sys, asyncio
            from jebat.tools import call_tool, TOOL_REGISTRY
            from jebat.core.agent_loop import AgentLoop

            # Ensure tools are imported (lazy modules)
            try:
                tmp = AgentLoop.__new__(AgentLoop)
                tmp._tools_imported = False
                tmp._ensure_tools_imported()
            except Exception:
                pass

            payload = json.loads(sys.stdin.read())
            result = asyncio.run(call_tool(payload["method"], **payload["params"]))
            print(json.dumps(result))
        """)
        proc = _sp.run(
            [_JEBAT_PYTHON, "-c", code],
            input=payload,
            capture_output=True, text=True, timeout=120,
        )
        if proc.returncode != 0:
            raise RuntimeError("jebat tool call failed: " + proc.stderr[:500])
        return json.loads(proc.stdout)


    def read_file(path, offset=1, limit=500):
        return _jebat_cmd("file_read", path=path, offset=offset, limit=limit)

    def write_file(path, content):
        return _jebat_cmd("file_write", path=path, content=content)

    def search_files(pattern, target="content", path=".", file_glob=None, limit=50):
        params = dict(pattern=pattern, target=target, path=path, limit=limit)
        if file_glob:
            params["file_glob"] = file_glob
        return _jebat_cmd("file_search", **params)

    def patch(path, old_string, new_string, replace_all=False):
        return _jebat_cmd(
            "file_patch", path=path, old_string=old_string,
            new_string=new_string, replace_all=replace_all,
        )

    def terminal(command, timeout=None, workdir=None):
        params = dict(command=command)
        if timeout is not None:
            params["timeout"] = timeout
        if workdir is not None:
            params["workdir"] = workdir
        return _jebat_cmd("terminal", **params)

    def call_tool(name, **params):
        return _jebat_cmd(name, **params)

    # Utilities
    def json_parse(text):
        return json.loads(text, strict=False)

    def shell_quote(s):
        if not s:
            return "''"
        return "'" + s.replace("'", "'\\\\''") + "'"
''')


# ── Execute Code Tool ──────────────────────────────────────────────────────

@register_tool(
    "execute_code",
    schema={
        "type": "object",
        "properties": {
            "code": {
                "type": "string",
                "description": (
                    "Python code to execute. Import tools with: "
                    "from jebat_tools import read_file, write_file, search_files, patch, terminal, call_tool. "
                    "Print your final result to stdout."
                ),
            },
            "timeout": {
                "type": "integer",
                "default": 120,
                "minimum": 5,
                "maximum": 300,
                "description": "Maximum execution time in seconds.",
            },
        },
        "required": ["code"],
    },
    safety_tier="dangerous",
    timeout=300,
    max_output=200_000,
    description=(
        "Run a Python script that can call JEBAT tools programmatically. "
        "Import tools with `from jebat_tools import read_file, write_file, search_files, patch, terminal`. "
        "Use this for 3+ tool calls with processing logic, conditional branches, or loops."
    ),
)
async def execute_code(code: str, timeout: int = 120) -> dict[str, Any]:
    """Execute a Python script with access to jebat_tools module.

    The script runs in a subprocess. The `jebat_tools` module is injected
    into its sys.path so `from jebat_tools import ...` just works.

    Returns:
        dict with status, output, error, exit_code
    """
    with tempfile.TemporaryDirectory(prefix="jebat_exec_") as tmpdir:
        # Write the injected module
        tools_path = os.path.join(tmpdir, "jebat_tools.py")
        with open(tools_path, "w", encoding="utf-8") as f:
            f.write(_JEBAT_TOOLS_MODULE)

        # Write user script
        user_script_path = os.path.join(tmpdir, "user_script.py")
        with open(user_script_path, "w", encoding="utf-8") as f:
            f.write(code)

        # Wrapper that injects jebat_tools into sys.path and runs the script
        wrapper = textwrap.dedent(f"""\
import sys
sys.path.insert(0, {json.dumps(tmpdir)})
exec(open({json.dumps(user_script_path)}, encoding="utf-8").read())
""")

        python_exe = sys.executable
        proc = await asyncio.create_subprocess_exec(
            python_exe, "-c", wrapper,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=os.getcwd(),
        )

        try:
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(), timeout=timeout,
            )
        except asyncio.TimeoutError:
            proc.kill()
            await proc.wait()
            return {
                "status": "timeout",
                "output": "",
                "error": f"Script exceeded {timeout}s timeout",
                "exit_code": -1,
            }

        out_decoded = stdout.decode("utf-8", errors="replace")
        err_decoded = stderr.decode("utf-8", errors="replace")

        # Cap output size
        max_out = 200_000
        if len(out_decoded) > max_out:
            out_decoded = out_decoded[:max_out] + f"\n... (truncated, {len(out_decoded)} total chars)"

        if proc.returncode != 0:
            return {
                "status": "error",
                "output": out_decoded,
                "error": err_decoded[:5000] if err_decoded else f"Exit code: {proc.returncode}",
                "exit_code": proc.returncode,
            }

        return {
            "status": "ok",
            "output": out_decoded,
            "error": err_decoded[:2000] if err_decoded else "",
            "exit_code": proc.returncode,
        }