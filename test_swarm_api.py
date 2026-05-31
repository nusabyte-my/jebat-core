#!/usr/bin/env python3
"""
Focused verification for the JEBAT swarm API contract.
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from jebat.core.agents import AgentOrchestrator, SwarmSearchBackend


async def main():
    try:
        from jebat.services.api import jebat_api
        from jebat.services.api.jebat_api import SwarmTaskRequest, plan_swarm_task, execute_swarm_task
    except ModuleNotFoundError as exc:
        if exc.name == "fastapi":
            print("skip - swarm api contract tests (fastapi not installed)")
            return
        raise

    orchestrator = AgentOrchestrator()
    orchestrator.register_builtin_agents()
    orchestrator.register_search_handler(
        SwarmSearchBackend(repo_root=Path(__file__).parent, remote_enabled=False).search
    )
    jebat_api.jebat_components["agent_orchestrator"] = orchestrator  # type: ignore

    try:
        # === Execute endpoint contract ===
        response = await execute_swarm_task(
            SwarmTaskRequest(
                description="Review the safest production database migration rollout with rollback guardrails",
                execution_mode="consensus",
                required_capabilities=["database", "operations", "review"],
                enable_search=True,
                max_agents=3,
                user_id="test-user",
            )
        )
        assert response.success is True
        assert response.execution_mode == "consensus"
        assert response.result is not None, "result missing on success"
        result = response.result
        assert isinstance(result, dict), "result must be dict on success"

        # Reducer payload structure
        assert response.result.get("reducer") is not None, "reducer missing"
        reducer = response.result["reducer"]
        assert "result" in reducer, "reducer.result missing"
        assert "decision" in reducer["result"], "reducer.result.decision missing"
        assert "confidence" in reducer["result"], "reducer.result.confidence missing"
        assert "recommended_next_actions" in reducer["result"], "reducer.result.recommended_next_actions missing"

        # Doctrine payload structure
        assert response.result.get("doctrine") is not None, "doctrine missing"
        doctrine = response.result["doctrine"]
        assert "result" in doctrine, "doctrine.result missing"
        assert "doctrine_checks" in doctrine["result"], "doctrine.result.doctrine_checks missing"
        assert isinstance(doctrine["result"]["doctrine_checks"], list), "doctrine_checks must be list"
        assert len(doctrine["result"]["doctrine_checks"]) >= 1, "doctrine_checks should not be empty"

        # Security layer structure (high-risk task)
        security_layer = response.result.get("security_layer")
        assert security_layer is not None, "security_layer missing from execution result"
        assert security_layer.get("risk_level") == "high"
        assert "migration" in security_layer.get("triggers", [])
        assert "review" in security_layer.get("required_roles", [])
        assert "security" in security_layer.get("required_roles", [])
        assert "defense" in security_layer.get("required_roles", [])
        assert security_layer.get("enforced") is True
        assert "active_roles" in security_layer
        assert "required_roles_present" in security_layer
        assert "coverage_ok" in security_layer
        assert "recommended_controls" in security_layer
        assert isinstance(security_layer.get("required_roles_present", []), list)
        assert isinstance(security_layer.get("recommended_controls", []), list)
        # Durable policy
        assert "policy_rules" in security_layer
        assert isinstance(security_layer.get("policy_rules"), list)
        # Exposure controls
        assert "exposure_controls" in security_layer
        assert "credential_redaction_enabled" in security_layer["exposure_controls"]
        assert "exposure_findings" in security_layer
        assert "unsafe_warnings" in security_layer

        # Swarm lead
        assert response.result.get("swarm_lead") is not None

        print("ok - execute endpoint contract validated")

        # === Plan endpoint contract ===
        plan_response = await plan_swarm_task(
            SwarmTaskRequest(
                description="Audit the safest database migration rollout",
                execution_mode="consensus",
                required_capabilities=["database", "review"],
                enable_search=True,
                max_agents=3,
                user_id="test-user",
            )
        )
        assert plan_response.task_id
        assert plan_response.execution_mode in {"consensus", "swarm", "single"}
        # Security layer in plan should have base classification fields only (no runtime fields)
        plan_sec = plan_response.security_layer
        assert plan_sec is not None
        assert "risk_level" in plan_sec
        assert "triggers" in plan_sec
        assert "required_roles" in plan_sec
        assert "enforced" in plan_sec
        # For this high-risk description, enforcement should be True
        assert plan_sec.get("enforced") is True
        assert "review" in plan_sec.get("required_roles", [])
        # Plan should NOT include runtime-only fields like active_roles, coverage_ok, exposure_controls
        assert "active_roles" not in plan_sec, "plan should not include runtime active_roles"
        assert "coverage_ok" not in plan_sec, "plan should not include coverage_ok"
        assert "exposure_controls" not in plan_sec, "plan should not include exposure_controls"
        print("ok - plan endpoint contract validated")

        # === Low-risk task contract ===
        low_plan = await plan_swarm_task(
            SwarmTaskRequest(
                description="What is the capital of France?",
                execution_mode="single",
                required_capabilities=["research"],
                enable_search=True,
                max_agents=1,
                user_id="test-user",
            )
        )
        low_sec = low_plan.security_layer
        assert low_sec.get("risk_level") == "low"
        assert low_sec.get("enforced") is False
        assert low_sec.get("required_roles") == []
        print("ok - low-risk task security_layer correct")

        # === Critical task plan shows risk but not blocked ===
        critical_plan = await plan_swarm_task(
            SwarmTaskRequest(
                description="Drop database production immediately",
                execution_mode="single",
                required_capabilities=[],
                enable_search=False,
                max_agents=1,
                user_id="test-user",
            )
        )
        crit_sec = critical_plan.security_layer
        assert crit_sec.get("risk_level") == "critical"
        assert "drop database" in crit_sec.get("triggers", [])
        # Plan endpoint does not enforce block; policy_action only appears after execution attempt
        assert "policy_action" not in crit_sec, "plan should not include policy_action"
        print("ok - critical task plan shows risk without block")

        # === Critical execution blocked without approval ===
        critical_exec = await execute_swarm_task(
            SwarmTaskRequest(
                description="Drop database production immediately",
                execution_mode="single",
                required_capabilities=[],
                enable_search=False,
                max_agents=1,
                user_id="test-user",
            )
        )
        assert critical_exec.success is False
        assert "approval" in (critical_exec.error or "").lower()
        exec_sec = critical_exec.security_layer
        assert exec_sec is not None, "security_layer missing for blocked critical task"
        assert exec_sec.get("risk_level") == "critical"
        assert exec_sec.get("policy_action") == "blocked"
        assert exec_sec.get("approval_required") is True
        print("ok - critical execution blocked without approval")

        print("ok - all API contract checks passed")
    finally:
        pass


if __name__ == "__main__":
    asyncio.run(main())
