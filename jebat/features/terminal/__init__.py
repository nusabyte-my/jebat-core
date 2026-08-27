"""JEBAT Terminal Execution — shell commands, background processes, PTY mode."""


async def execute(command: str, timeout: int = 180, workdir: str | None = None, background: bool = False, pty: bool = False) -> dict:
    ...


async def process_list() -> list[dict]:
    ...


async def process_log(session_id: str) -> str:
    ...


async def process_kill(session_id: str) -> bool:
    ...