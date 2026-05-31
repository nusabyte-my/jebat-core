#!/usr/bin/env python3
"""
Focused verification for the canonical JEBAT swarm orchestrator.
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from jebat.core.agents import (
    AgentOrchestrator,
    AgentTask,
    ExecutionMode,
    SwarmSearchBackend,
    classify_prompt_with_hang_nadim,
    format_swarm_result_text,
    infer_swarm_task,
    should_route_prompt_to_swarm,
)


async def test_builtin_agent_bootstrap():
    orchestrator = AgentOrchestrator()
    count = orchestrator.register_builtin_agents()

    assert count >= 15
    registry = orchestrator.get_agent_registry()
    assert "panglima-001" in registry
    assert "tukang-001" in registry
    assert "hang-tuah-001" in registry
    assert "hang-lekiu-001" in registry
    assert "hang-lekir-001" in registry
    assert "hang-kasturi-001" in registry
    assert "hang-nadim-001" in registry
    assert registry["panglima-001"]["automation_enabled"] is True
    assert registry["hang-nadim-001"]["automation_enabled"] is True

    print("ok - built-in agents bootstrap")


async def test_swarm_consensus_and_search():
    orchestrator = AgentOrchestrator()
    orchestrator.register_builtin_agents()

    async def search_handler(task, agent_info, queries):
        return {
            "queries": queries,
            "results": [
                {
                    "title": f"{agent_info['role']} source",
                    "snippet": f"Search context for {task.description}",
                }
            ],
        }

    async def research_handler(task, agent_info, context):
        assert context["search_queries"]
        return {
            "decision": "run migration dry-run before apply",
            "recommended_next_actions": [
                "Collect production schema diff",
                "Run migration dry-run in staging",
            ],
            "role": agent_info["role"],
        }

    async def database_handler(task, agent_info, context):
        assert context["search_results"]["results"]
        return {
            "decision": "run migration dry-run before apply",
            "recommended_next_actions": [
                "Benchmark affected queries",
                "Run migration dry-run in staging",
            ],
            "role": agent_info["role"],
        }

    async def review_handler(task, agent_info, context):
        return {
            "decision": "review rollback plan before apply",
            "recommended_next_actions": [
                "Validate rollback path",
            ],
            "role": agent_info["role"],
        }

    orchestrator.register_search_handler(search_handler)
    orchestrator.register_handler("research", research_handler)
    orchestrator.register_handler("database", database_handler)
    orchestrator.register_handler("review", review_handler)

    task = AgentTask(
        description="Research and judge the safest database migration rollout",
        execution_mode=ExecutionMode.CONSENSUS,
        enable_search=True,
        max_agents=3,
        require_consensus=True,
        required_capabilities=["research", "database", "review"],
    )

    result = await orchestrator.run_task(task)

    assert result.success is True
    assert result.result["execution_mode"] == "consensus"
    assert result.result["consensus"]["decision"] == "run migration dry-run before apply"
    assert result.result["reducer"] is not None
    assert result.result["reducer"]["result"]["synthesized_decision"] == "run migration dry-run before apply"
    assert result.result["reducer"]["result"]["confidence"] >= 0.25
    assert "supporting_roles" in result.result["reducer"]["result"]
    assert len(result.result["agent_results"]) >= 3
    roles = {agent_result["role"] for agent_result in result.result["agent_results"]}
    assert {"research", "database", "review"} <= roles
    assert any(agent_result["search_queries"] for agent_result in result.result["agent_results"])

    print("ok - swarm consensus and search")


async def test_capability_based_selection():
    orchestrator = AgentOrchestrator()
    orchestrator.register_agent(
        "analyst-001",
        {"name": "Analyst", "role": "analysis", "capabilities": ["analysis", "research"]},
    )
    orchestrator.register_agent(
        "builder-001",
        {"name": "Builder", "role": "development", "capabilities": ["coding", "testing"]},
    )

    task = AgentTask(description="Analyze failure patterns in the deployment logs")
    selected = orchestrator._select_agent(task)

    assert selected == "analyst-001"
    print("ok - capability based selection")


async def test_search_backend_local_repo_results():
    backend = SwarmSearchBackend(repo_root=Path(__file__).parent, remote_enabled=False)
    payload = await backend.search(
        task=AgentTask(description="Inspect orchestrator search behavior"),
        agent_info={"role": "research"},
        queries=["AgentOrchestrator"],
    )

    assert payload["backend"].startswith("local")
    assert payload["local_results"]
    assert any("orchestrator.py" in item["path"] for item in payload["local_results"])
    print("ok - local search backend")


async def test_builtin_role_handler_output():
    orchestrator = AgentOrchestrator()
    orchestrator.register_builtin_agents()

    result = await orchestrator.execute_task(
        AgentTask(
            description="Review the safest way to roll out a schema change",
            execution_mode=ExecutionMode.CONSENSUS,
            required_capabilities=["database", "review", "operations"],
            max_agents=3,
            require_consensus=True,
            enable_search=False,
        )
    )

    assert result.success is True
    agent_results = result.result["agent_results"]
    assert len(agent_results) >= 3
    roles = {agent_result["role"] for agent_result in agent_results}
    assert {"database", "operations", "review"} <= roles
    assert all(agent_result["result"]["recommended_next_actions"] for agent_result in agent_results)
    assert all(agent_result["result"]["actions_executed"] for agent_result in agent_results)
    assert all(agent_result["result"]["scope"]["focus"] for agent_result in agent_results)
    assert any(
        agent_result["result"]["execution_adapter"] == "database"
        for agent_result in agent_results
    )
    database_scope = next(
        agent_result["result"]["scope"]["focus"]
        for agent_result in agent_results
        if agent_result["role"] == "database"
    )
    review_scope = next(
        agent_result["result"]["scope"]["focus"]
        for agent_result in agent_results
        if agent_result["role"] == "review"
    )
    assert database_scope != review_scope
    print("ok - built-in role handler output")


async def test_execution_adapters_return_real_findings():
    orchestrator = AgentOrchestrator()
    orchestrator.register_builtin_agents()

    result = await orchestrator.execute_task(
        AgentTask(
            description="Inspect database schema and deployment workflow for rollout planning",
            execution_mode=ExecutionMode.CONSENSUS,
            required_capabilities=["database", "operations", "review"],
            max_agents=3,
            require_consensus=True,
            enable_search=False,
        )
    )

    database_result = next(
        agent_result["result"]
        for agent_result in result.result["agent_results"]
        if agent_result["role"] == "database"
    )
    operations_result = next(
        agent_result["result"]
        for agent_result in result.result["agent_results"]
        if agent_result["role"] == "operations"
    )

    assert database_result["tool_findings"]["findings"]
    assert operations_result["tool_findings"]["findings"]
    print("ok - execution adapters return real findings")


async def test_chat_router_helpers():
    orchestrator = AgentOrchestrator()
    orchestrator.register_builtin_agents()

    prompt = "Research and decide the best database rollout strategy"
    assert should_route_prompt_to_swarm(prompt) is True
    task = infer_swarm_task(prompt, user_id="tester", orchestrator=orchestrator)
    assert task.enable_search is True
    assert task.require_consensus is True
    assert "database" in task.required_capabilities

    formatted = format_swarm_result_text(
        {
            "consensus": {"decision": "Use a staged rollout", "agreement": 0.5},
            "recommended_next_actions": ["Run staging dry-run", "Prepare rollback plan"],
            "reducer": {
                "result": {
                    "synthesized_decision": "Use Taming Sari final output",
                    "confidence": 0.75,
                    "recommended_next_actions": ["Run staging dry-run", "Prepare rollback plan"],
                    "conflicts": [{"decision": "Delay rollout", "votes": 1}],
                }
            },
            "doctrine": {
                "result": {
                    "doctrine_checks": ["Keep the swarm aligned under one governing decision"]
                }
            },
        }
    )
    assert "Use Taming Sari final output" in formatted
    assert "Confidence: 0.75" in formatted
    assert "Run staging dry-run" in formatted
    assert "Doctrine checks:" in formatted
    assert "Conflicts observed:" in formatted
    print("ok - chat router helpers")


async def test_hang_nadim_classifier_routes_legendary_prompts():
    decision = classify_prompt_with_hang_nadim(
        "Research and decide the safest rollout strategy with routing intelligence"
    )

    assert decision.route == "legendary_swarm"
    assert decision.execution_mode == ExecutionMode.CONSENSUS
    assert decision.enable_search is True
    assert "strategy" in decision.required_capabilities
    assert "defense" in decision.required_capabilities
    assert "intelligence" in decision.required_capabilities
    print("ok - hang nadim classifier")


async def test_legendary_inference_preserves_required_capabilities():
    orchestrator = AgentOrchestrator()
    orchestrator.register_builtin_agents()

    task = infer_swarm_task(
        "Research and decide the safest rollout strategy with routing intelligence",
        user_id="tester",
        requested_model="jebat-legend",
        orchestrator=orchestrator,
    )

    assert task.execution_mode == ExecutionMode.CONSENSUS
    assert task.enable_search is True
    assert "strategy" in task.required_capabilities
    assert "reconnaissance" in task.required_capabilities
    assert "defense" in task.required_capabilities
    assert "intelligence" in task.required_capabilities
    assert task.max_agents >= 4
    print("ok - legendary inference preserves capabilities")


async def test_legendary_strategy_prompt_prefers_hang_tuah_as_lead():
    orchestrator = AgentOrchestrator()
    orchestrator.register_builtin_agents()

    task = infer_swarm_task(
        "Research and decide the safest rollout strategy with routing intelligence",
        user_id="tester",
        requested_model="jebat-legend",
        orchestrator=orchestrator,
    )
    selected = orchestrator._select_swarm_agents(task)
    lead = orchestrator._choose_swarm_lead(task, selected)

    assert selected[0][0] == "hang-tuah-001"
    assert lead["agent_id"] == "hang-tuah-001"
    assert lead["role"] == "strategy"
    print("ok - strategy prompt prefers hang tuah lead")


async def test_legendary_recon_prompt_prefers_hang_lekiu_as_lead():
    orchestrator = AgentOrchestrator()
    orchestrator.register_builtin_agents()

    task = infer_swarm_task(
        "Research and discover every migration and map the terrain before deciding",
        user_id="tester",
        requested_model="jebat-legend",
        orchestrator=orchestrator,
    )
    selected = orchestrator._select_swarm_agents(task)
    lead = orchestrator._choose_swarm_lead(task, selected)

    assert selected[0][0] == "hang-lekiu-001"
    assert lead["agent_id"] == "hang-lekiu-001"
    assert lead["role"] == "reconnaissance"
    print("ok - recon prompt prefers hang lekiu lead")


async def test_plan_task_exposes_rankings_and_lead():
    orchestrator = AgentOrchestrator()
    orchestrator.register_builtin_agents()

    task = infer_swarm_task(
        "Research and decide the safest rollout strategy with routing intelligence",
        user_id="tester",
        requested_model="jebat-legend",
        orchestrator=orchestrator,
    )
    plan = orchestrator.plan_task(task)

    assert plan["execution_mode"] == "consensus"
    assert plan["swarm_lead"]["agent_id"] == "hang-tuah-001"
    assert plan["preferred_roles"][0] == "strategy"
    assert plan["selected_agents"][0]["agent_id"] == "hang-tuah-001"
    assert "score_breakdown" in plan["ranked_agents"][0]
    print("ok - plan task exposes rankings and lead")


async def test_plan_task_resolves_auto_mode():
    orchestrator = AgentOrchestrator()
    orchestrator.register_builtin_agents()

    plan = orchestrator.plan_task(
        AgentTask(
            description="Research and compare rollout options",
            execution_mode=ExecutionMode.AUTO,
            enable_search=True,
        )
    )

    assert plan["execution_mode"] == "consensus"
    assert plan["search_enabled"] is True
    assert plan["full_orchestration"] is True
    assert plan["selected_agents"]
    print("ok - plan task resolves auto mode")


async def test_security_layer_injects_roles_for_high_risk_tasks():
    orchestrator = AgentOrchestrator()
    orchestrator.register_builtin_agents()

    plan = orchestrator.plan_task(
        AgentTask(
            description="Review the safest production database migration rollout with rollback guardrails",
            execution_mode=ExecutionMode.AUTO,
        )
    )

    selected_roles = {agent["role"] for agent in plan["selected_agents"]}
    assert plan["security_layer"]["risk_level"] == "high"
    assert "migration" in plan["security_layer"]["triggers"]
    assert "review" in plan["security_layer"]["required_roles"]
    assert "security" in plan["security_layer"]["required_roles"]
    assert "defense" in plan["security_layer"]["required_roles"]
    assert {"review", "security", "defense"} <= selected_roles
    print("ok - security layer injects roles")


async def test_full_orchestration_keeps_pinned_agent_inside_swarm():
    orchestrator = AgentOrchestrator()
    orchestrator.register_builtin_agents()

    plan = orchestrator.plan_task(
        AgentTask(
            description="Implement and review the safest authentication rollout",
            agent_id="tukang-001",
            execution_mode=ExecutionMode.AUTO,
        )
    )

    selected_ids = {agent["agent_id"] for agent in plan["selected_agents"]}
    selected_roles = {agent["role"] for agent in plan["selected_agents"]}
    assert plan["execution_mode"] == "consensus"
    assert "tukang-001" in selected_ids
    assert plan["swarm_lead"]["agent_id"] == "tukang-001"
    assert "orchestration" in selected_roles
    assert "review" in selected_roles
    assert "reduction" in selected_roles
    print("ok - full orchestration keeps pinned agent inside swarm")


async def test_swarm_execution_exposes_security_layer():
    orchestrator = AgentOrchestrator()
    orchestrator.register_builtin_agents()

    result = await orchestrator.execute_task(
        AgentTask(
            description="Research and review the safest production database migration rollout with rollback guardrails",
            execution_mode=ExecutionMode.CONSENSUS,
        )
    )

    security_layer = result.result["security_layer"]
    assert security_layer["risk_level"] == "high"
    assert security_layer["enforced"] is True
    assert {"review", "security", "defense"} <= set(security_layer["required_roles"])
    assert "security" in security_layer["active_roles"]
    assert "defense" in security_layer["active_roles"]
    assert "review" in security_layer["active_roles"]
    assert security_layer["recommended_controls"]
    print("ok - swarm execution exposes security layer")


async def test_legendary_agents_can_route_and_execute():
    orchestrator = AgentOrchestrator()
    orchestrator.register_builtin_agents()

    result = await orchestrator.execute_task(
        AgentTask(
            description="Research and decide the best protected rollout strategy with routing intelligence",
            execution_mode=ExecutionMode.CONSENSUS,
            required_capabilities=["strategy", "reconnaissance", "defense"],
            max_agents=3,
            require_consensus=True,
            enable_search=False,
        )
    )

    roles = {agent_result["role"] for agent_result in result.result["agent_results"]}
    assert "strategy" in roles
    assert "reconnaissance" in roles
    assert "defense" in roles
    assert result.result["swarm_lead"]["role"] == "strategy"
    assert result.result["reducer"] is not None
    assert result.result["reducer"]["result"]["synthesized_decision"]
    assert result.result["doctrine"] is not None
    assert result.result["doctrine"]["result"]["doctrine_checks"]
    assert any(
        agent_result["result"]["execution_adapter"] == "strategy"
        for agent_result in result.result["agent_results"]
    )
    print("ok - legendary agents route and execute")


async def test_critical_task_requires_explicit_approval():
    """Critical tasks must be explicitly approved or they are blocked."""
    orchestrator = AgentOrchestrator()
    orchestrator.register_builtin_agents()

    result = await orchestrator.execute_task(
        AgentTask(
            description="Drop database production immediately",
            execution_mode=ExecutionMode.AUTO,
        )
    )
    # Should be blocked by policy
    assert result.success is False
    assert "approval" in (result.error or "").lower()
    assert result.metadata.get("security_layer", {}).get("risk_level") == "critical"
    sec = result.metadata.get("security_layer", {})
    assert sec.get("policy_action") == "blocked"
    assert sec.get("approval_required") is True
    print("ok - critical task blocked without approval")


async def test_critical_task_approved_executes():
    """Critical tasks with approve_critical=True proceed."""
    orchestrator = AgentOrchestrator()
    orchestrator.register_builtin_agents()

    result = await orchestrator.execute_task(
        AgentTask(
            description="Drop database production immediately",
            execution_mode=ExecutionMode.AUTO,
            parameters={"approve_critical": True},
        )
    )
    # Should execute (though may fail due to lack of real handlers, but not blocked by policy)
    assert result.success is not False or "policy" not in (result.error or "").lower()
    sec = (result.result or {}).get("security_layer") or result.metadata.get("security_layer", {})
    assert sec.get("risk_level") == "critical"
    # Should not be blocked; policy_action should be explicit_override or absent
    assert sec.get("policy_action") != "blocked"
    print("ok - critical task proceeds with approval")


async def test_role_specific_output_budgets():
    """Security, defense, and review roles produce compact outputs."""
    orchestrator = AgentOrchestrator()
    orchestrator.register_builtin_agents()

    # Build a task that will involve security and review roles
    plan = orchestrator.plan_task(
        AgentTask(
            description="Review the safest production database migration rollout with rollback guardrails",
            execution_mode=ExecutionMode.AUTO,
        )
    )
    # Verify required roles include compact ones
    required = plan["security_layer"]["required_roles"]
    assert "review" in required
    assert "security" in required or "defense" in required

    # Execute and check outputs are bounded in those agents
    result = await orchestrator.execute_task(
        AgentTask(
            description="Review the safest production database migration rollout with rollback guardrails",
            execution_mode=ExecutionMode.CONSENSUS,
        )
    )
    # Find agent results for compact roles
    for agent_res in result.result.get("agent_results", []):
        role = agent_res.get("role", "")
        payload = agent_res.get("result", {})
        if role in {"security", "defense", "review"}:
            actions = payload.get("recommended_next_actions", [])
            assert len(actions) <= 3, f"{role} output exceeded 3 actions: {len(actions)}"
            summary = payload.get("summary", "")
            assert len(summary) <= 200, f"{role} summary too long: {len(summary)}"
    print("ok - role-specific output budgets apply")


async def test_exposure_redaction_in_agent_outputs():
    """Credentials and secrets in agent outputs are redacted."""
    orchestrator = AgentOrchestrator()
    orchestrator.register_builtin_agents()

    # Create a leaking handler to simulate an agent that outputs credentials
    def leaking_handler(task, agent_info, context):
        return {
            "decision": "use password=SuperSecret123 for the API",
            "summary": "Configure endpoint with api_key=sk-abcdef123456 and token=bearer xyz",
            "recommended_next_actions": ["set password=admin", "deploy"],
        }

    orchestrator.register_agent("leak-test-001", {
        "name": "LeakTest",
        "role": "development",
        "handler": leaking_handler,
        "status": "idle",
        "automation_enabled": True,
        "search_enabled": False,
    })

    result = await orchestrator.execute_task(
        AgentTask(
            description="Implement API authentication",
            agent_id="leak-test-001",
            execution_mode=ExecutionMode.AUTO,  # will become swarm under full_orchestration
            parameters={"full_orchestration": False},  # force single-agent for isolation
        )
    )
    # In single-agent mode, result.result is the agent payload itself
    payload = result.result if isinstance(result.result, dict) else {}
    # Check exposures were detected and redacted in the agent result
    findings = payload.get("_exposure_findings", [])
    assert len(findings) >= 3, f"Expected at least 3 exposure findings, got {len(findings)}"
    # Verify redaction occurred in returned fields
    decision = str(payload.get("decision", ""))
    summary = str(payload.get("summary", ""))
    assert "SuperSecret123" not in decision, "Credential not redacted in decision"
    assert "sk-abcdef123456" not in summary, "API key not redacted in summary"
    assert "REDACTED" in decision or "[REDACTED]" in decision or "***" in decision, "Redaction marker missing"
    print("ok - exposure redaction in agent outputs")


async def test_unsafe_output_paths_flagged():
    """Agent outputs suggesting unsafe public deployment are flagged."""
    orchestrator = AgentOrchestrator()
    orchestrator.register_builtin_agents()

    def reckless_handler(task, agent_info, context):
        return {
            "decision": "Publish this to the public npm registry without auth",
            "summary": "Make it open to internet with no auth required",
            "recommended_next_actions": ["push to production now"],
        }

    orchestrator.register_agent("reckless-001", {
        "name": "Reckless",
        "role": "operations",
        "handler": reckless_handler,
        "status": "idle",
        "automation_enabled": True,
        "search_enabled": False,
    })

    result = await orchestrator.execute_task(
        AgentTask(
            description="Deploy the service",
            agent_id="reckless-001",
            execution_mode=ExecutionMode.AUTO,
            parameters={"full_orchestration": False},
        )
    )
    payload = result.result if isinstance(result.result, dict) else {}
    warnings = payload.get("_unsafe_warnings", [])
    assert len(warnings) >= 2, f"Expected unsafe warnings, got {warnings}"
    assert any("public npm" in w for w in warnings), "npm exposure not flagged"
    assert any("internet" in w for w in warnings), "open internet not flagged"
    print("ok - unsafe output paths flagged")


async def test_exposure_findings_propagate_to_security_layer():
    """Aggregated exposure findings appear in swarm security_layer."""
    orchestrator = AgentOrchestrator()
    orchestrator.register_builtin_agents()

    result = await orchestrator.execute_task(
        AgentTask(
            description="Implement user login endpoint",
            agent_id="development-001",
            execution_mode=ExecutionMode.SINGLE,
            parameters={"full_orchestration": False},
        )
    )
    sec = (result.result or {}).get("security_layer") or result.metadata.get("security_layer", {})
    assert "exposure_controls" in sec, "exposure_controls missing from security_layer"
    controls = sec.get("exposure_controls", [])
    assert any("redaction" in c.lower() for c in controls), "credential redaction not indicated in controls"
    print("ok - exposure findings propagate to security_layer")


async def test_security_layer_contract_low_vs_high_risk():
    """security_layer schema varies correctly with risk level."""
    orch = AgentOrchestrator()
    orch.register_builtin_agents()

    # Low-risk plan — minimal fields, no runtime enforcement
    low_plan = orch.plan_task(AgentTask(description="What is Python?"))
    low_sec = low_plan["security_layer"]
    assert low_sec["risk_level"] == "low"
    assert low_sec["enforced"] is False
    assert low_sec["required_roles"] == []
    # Plan-level security_layer excludes runtime fields like active_roles, policy_rules, exposure_controls
    assert "active_roles" not in low_sec
    assert "policy_rules" not in low_sec

    # High-risk plan — elevated fields, still no runtime specifics
    high_plan = orch.plan_task(AgentTask(description="Database migration rollout"))
    high_sec = high_plan["security_layer"]
    assert high_sec["risk_level"] == "high"
    assert high_sec["enforced"] is True
    assert "review" in high_sec["required_roles"]
    assert "security" in high_sec["required_roles"]
    assert "defense" in high_sec["required_roles"]
    assert "active_roles" not in high_sec  # runtime-only
    assert "policy_rules" not in high_sec   # runtime-only for now
    print("ok - security_layer plan contract differs by risk")

    # High-risk execution — includes runtime fields
    exec_result = await orch.execute_task(
        AgentTask(description="Database migration rollout", execution_mode=ExecutionMode.CONSENSUS)
    )
    exec_sec = (exec_result.result or {}).get("security_layer") or exec_result.metadata.get("security_layer", {})
    assert "active_roles" in exec_sec
    assert "policy_rules" in exec_sec
    assert "exposure_controls" in exec_sec
    print("ok - execution security_layer includes runtime fields")


async def test_doctrine_uses_durable_policy():
    """doctrine.result.doctrine_checks comes from durable_doctrine, not task description."""
    orch = AgentOrchestrator()
    orch.register_builtin_agents()
    orch.durable_doctrine = ["Custom rule 1", "Custom rule 2"]

    result = await orch.execute_task(
        AgentTask(description="some task", execution_mode=ExecutionMode.CONSENSUS)
    )
    # doctrine appears in final swarm result
    doctrine = result.result.get("doctrine") if isinstance(result.result, dict) else None
    assert doctrine is not None, "doctrine missing from swarm result"
    checks = doctrine["result"]["doctrine_checks"]
    assert "Custom rule 1" in checks
    assert "Custom rule 2" in checks
    print("ok - doctrine uses durable policy")


async def test_reducer_has_required_fields():
    """Reducer payload always includes decision, confidence, synthesized_decision, votes, conflicts."""
    orch = AgentOrchestrator()
    orch.register_builtin_agents()

    result = await orch.execute_task(
        AgentTask(description="compare database options", execution_mode=ExecutionMode.CONSENSUS)
    )
    assert isinstance(result.result, dict), "expected dict result"
    reducer = result.result.get("reducer")
    assert reducer is not None, "reducer missing"
    r = reducer["result"]
    assert "decision" in r and isinstance(r["decision"], str)
    assert "confidence" in r and isinstance(r["confidence"], (int, float))
    assert "synthesized_decision" in r
    assert "votes" in r and isinstance(r["votes"], dict)
    assert "conflicts" in r and isinstance(r["conflicts"], list)
    print("ok - reducer has required fields")


async def main():
    await test_builtin_agent_bootstrap()
    await test_swarm_consensus_and_search()
    await test_capability_based_selection()
    await test_search_backend_local_repo_results()
    await test_builtin_role_handler_output()
    await test_execution_adapters_return_real_findings()
    await test_chat_router_helpers()
    await test_hang_nadim_classifier_routes_legendary_prompts()
    await test_legendary_inference_preserves_required_capabilities()
    await test_legendary_strategy_prompt_prefers_hang_tuah_as_lead()
    await test_legendary_recon_prompt_prefers_hang_lekiu_as_lead()
    await test_plan_task_exposes_rankings_and_lead()
    await test_plan_task_resolves_auto_mode()
    await test_security_layer_injects_roles_for_high_risk_tasks()
    await test_full_orchestration_keeps_pinned_agent_inside_swarm()
    await test_swarm_execution_exposes_security_layer()
    await test_legendary_agents_can_route_and_execute()
    await test_critical_task_requires_explicit_approval()
    await test_critical_task_approved_executes()
    await test_role_specific_output_budgets()
    await test_exposure_redaction_in_agent_outputs()
    await test_unsafe_output_paths_flagged()
    await test_exposure_findings_propagate_to_security_layer()
    await test_security_layer_contract_low_vs_high_risk()
    await test_doctrine_uses_durable_policy()
    await test_reducer_has_required_fields()
    print("all swarm orchestrator tests passed")


if __name__ == "__main__":
    asyncio.run(main())
