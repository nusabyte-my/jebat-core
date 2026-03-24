from pathlib import Path

from jebat.cli.jebat_cli import JEBATCLI
from jebat.llm.auth import list_provider_auth_status
from jebat.llm.history import ChatHistoryStore
from jebat.llm.project_context import build_project_context
from jebat.llm.config import load_llm_config
from jebat.llm.providers import LocalEchoProvider, generate_with_failover, list_supported_providers
from jebat.llm.skills import build_skill_prompt, build_skill_registry, default_skills_path, select_relevant_skills


def test_load_llm_config_reads_yaml_defaults() -> None:
    config = load_llm_config(Path("jebat/config/config.yaml"))
    assert config.provider == "openai"
    assert config.model == "gpt-5.4"


def test_local_echo_provider_returns_prompt() -> None:
    import asyncio

    provider = LocalEchoProvider()
    response = asyncio.run(provider.generate("hello", system_prompt="system"))
    assert "hello" in response
    assert "system" in response


def test_supported_providers_include_openai_and_ollama() -> None:
    providers = {item["name"] for item in list_supported_providers()}
    assert "openai" in providers
    assert "ollama" in providers
    assert "google" in providers
    assert "openrouter" in providers


def test_project_context_collects_files(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("# Demo\n", encoding="utf-8")
    (tmp_path / "main.py").write_text("print('ok')\n", encoding="utf-8")
    context = build_project_context(tmp_path)
    assert "README.md" in context.summary
    assert "main.py" in context.summary


def test_chat_history_store_appends_and_loads(tmp_path: Path) -> None:
    history = ChatHistoryStore(tmp_path / "history.jsonl")
    history.append("abc123", "user", "hello")
    history.append("abc123", "assistant", "hi")
    turns = history.load("abc123")
    assert len(turns) == 2
    assert turns[0].content == "hello"


def test_generate_with_failover_uses_local_when_primary_fails(monkeypatch) -> None:
    import asyncio
    from jebat.llm.config import JebatLLMConfig

    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    config = JebatLLMConfig(provider="openai", fallback_providers=("local",))
    response, provider = asyncio.run(
        generate_with_failover(config, prompt="hello", system_prompt="system")
    )
    assert provider == "local"
    assert "hello" in response


def test_provider_auth_status_lists_major_providers() -> None:
    providers = {item.provider for item in list_provider_auth_status()}
    assert {"openai", "google", "anthropic", "openrouter", "ollama", "local"} <= providers


def test_skill_registry_loads_tokguru_repo_skills() -> None:
    registry = build_skill_registry(default_skills_path())
    skills = {skill.name for skill in registry.get_all_skills()}
    assert "python-patterns" in skills
    assert "cortex-reasoning" in skills
    assert "hermes-agent" in skills


def test_select_relevant_skills_matches_python_prompt() -> None:
    registry = build_skill_registry(default_skills_path())
    selected = select_relevant_skills(
        "Refactor this Python module using better patterns and cleaner design",
        registry=registry,
    )
    names = {skill.name for skill in selected}
    assert "python-patterns" in names


def test_build_skill_prompt_includes_requested_skill_content() -> None:
    registry = build_skill_registry(default_skills_path())
    prompt, selected = build_skill_prompt(
        "Help me reason through a system design problem",
        registry=registry,
        requested_skills=["cortex-reasoning"],
    )
    assert "Skill: cortex-reasoning" in prompt
    assert selected


def test_build_skill_prompt_can_pin_hermes_agent() -> None:
    registry = build_skill_registry(default_skills_path())
    prompt, selected = build_skill_prompt(
        "Be my daily coding copilot for this repo",
        registry=registry,
        requested_skills=["hermes-agent"],
        auto_discover=False,
    )
    names = [skill.name for skill in selected]
    assert names == ["hermes-agent"]
    assert "Skill: hermes-agent" in prompt


def test_doctor_reports_configured_provider(monkeypatch) -> None:
    import asyncio
    from jebat.llm.config import JebatLLMConfig

    cli = JEBATCLI()
    lines: list[str] = []
    cli.print = lambda message, style="": lines.append(str(message))

    monkeypatch.setattr(
        "jebat.cli.jebat_cli.load_llm_config",
        lambda: JebatLLMConfig(provider="local", model="echo", fallback_providers=("local",)),
    )

    asyncio.run(cli.cmd_doctor())

    output = "\n".join(lines)
    assert "Configured Provider: local" in output
    assert "Best Available Provider: local" in output
