"""
agent/orchestrate.py
--------------------
Thin client for FinPath AI's deployed watsonx Orchestrate agent.

Authentication uses the ADK's cached MCSP token from ~/.wxo/ — obtained by
running `orchestrate env activate finpath`.  No secrets are read from .env
in this module.  Call health_check() to verify connectivity before the UI
starts.

Public API
----------
    ask_agent(user_message, profile, thread_id=None)
        -> tuple[str, list[dict] | None, str | None]

    health_check() -> bool
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any

from ibm_watsonx_orchestrate.client.chat.run_client import RunClient
from ibm_watsonx_orchestrate.client.threads.threads_client import ThreadsClient
from ibm_watsonx_orchestrate.client.utils import instantiate_client
from ibm_watsonx_orchestrate.cli.commands.agents.agents_helper import get_agent_id_by_name

logger = logging.getLogger(__name__)

AGENT_NAME = "finpath_agent"
RUN_TIMEOUT_SECONDS = 120  # max seconds to wait for a run to complete


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _make_clients() -> tuple[RunClient, ThreadsClient]:
    """Return fresh ADK clients bound to the active Orchestrate environment."""
    return (
        instantiate_client(RunClient),
        instantiate_client(ThreadsClient),
    )


def _build_prompt(user_message: str, profile: dict | None) -> str:
    """Prepend the user's financial profile as structured context."""
    if not profile:
        return user_message

    lines = ["## User financial profile (use these values as inputs to tools)\n"]
    field_labels = {
        "monthly_income": "Monthly income",
        "monthly_expenses": "Monthly essential expenses",
        "monthly_savings_contribution": "Monthly savings contribution",
        "monthly_debt_payment": "Monthly debt payment",
        "cash_savings": "Current cash savings",
        "debt_balance": "Debt balance",
        "debt_rate": "Annual debt interest rate",
        "savings_goal": "Stated goal",
    }
    for key, label in field_labels.items():
        if key in profile:
            value = profile[key]
            if key == "debt_rate":
                value = f"{value * 100:.2f}%"
            lines.append(f"- {label}: {value}")

    lines.append(f"\n## User question\n{user_message}")
    return "\n".join(lines)


def _extract_text(content: Any) -> str:
    """Pull plain text out of an Orchestrate message content field."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, dict):
                if item.get("response_type") == "text":
                    parts.append(item.get("text", ""))
                elif "text" in item:
                    parts.append(item["text"])
        return "\n".join(p for p in parts if p)
    return str(content) if content else ""


def _extract_tool_calls(messages: list[dict]) -> list[str]:
    """Return tool names called during the last assistant turn."""
    tool_names: list[str] = []
    for msg in reversed(messages):
        if not isinstance(msg, dict):
            continue
        for step in msg.get("step_history", []):
            for detail in step.get("step_details", []):
                for tc in detail.get("tool_calls", []):
                    name = tc.get("name")
                    if name and name not in tool_names:
                        tool_names.append(name)
        if tool_names:
            break
    return tool_names


def _extract_scenarios(text: str) -> list[dict] | None:
    """Try to find a JSON scenario list embedded in the reply text."""
    patterns = [
        r"```(?:json)?\s*(\[.*?\])\s*```",  # fenced code block
        r"(\[\s*\{.*?\}\s*\])",              # bare JSON array
    ]
    for pat in patterns:
        for raw in re.findall(pat, text, re.DOTALL):
            try:
                data = json.loads(raw)
                if (
                    isinstance(data, list)
                    and data
                    and isinstance(data[0], dict)
                    and "cash_flow" in data[0]
                ):
                    return data
            except (json.JSONDecodeError, ValueError):
                pass
    return None


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def ask_agent(
    user_message: str,
    profile: dict | None = None,
    thread_id: str | None = None,
) -> tuple[str, list[dict] | None, str | None]:
    """Send a message to finpath_agent and return structured results.

    Args:
        user_message: The user's question in plain language.
        profile:      Optional dict of financial profile fields to inject as
                      context (monthly_income, monthly_expenses, etc.).
        thread_id:    Existing conversation thread to continue, or None to
                      start a fresh thread.

    Returns:
        reply_text:  The agent's plain-text response.
        scenarios:   List of scenario result dicts when compare_scenarios was
                     called, or None if no structured results were found.
        thread_id:   The thread ID to pass on the next call for continuity.

    Raises:
        RuntimeError: Wraps any ADK or network error with a user-friendly message.
        TimeoutError: If the run does not complete within RUN_TIMEOUT_SECONDS.
    """
    prompt = _build_prompt(user_message, profile)

    try:
        run_client, threads_client = _make_clients()
        agent_id = get_agent_id_by_name(AGENT_NAME)

        run_response = run_client.create_run(
            message=prompt,
            agent_id=agent_id,
            thread_id=thread_id,
        )
        new_thread_id: str = run_response["thread_id"]
        run_id: str = run_response["run_id"]

        max_retries = RUN_TIMEOUT_SECONDS // 2
        status = run_client.wait_for_run_completion(run_id, max_retries=max_retries)

        if status.get("status") == "failed":
            raise RuntimeError(status.get("error", "Agent run failed."))

        msgs_response = threads_client.get_thread_messages(new_thread_id)
        if isinstance(msgs_response, list):
            messages = msgs_response
        elif isinstance(msgs_response, dict) and "data" in msgs_response:
            messages = msgs_response["data"]
        else:
            messages = []

        reply_text = ""
        for msg in reversed(messages):
            if isinstance(msg, dict) and msg.get("role") == "assistant":
                reply_text = _extract_text(msg.get("content", ""))
                break

        if not reply_text:
            reply_text = "No response received from agent."

        scenarios = _extract_scenarios(reply_text)
        return reply_text, scenarios, new_thread_id

    except (RuntimeError, TimeoutError):
        raise
    except Exception as exc:
        logger.debug("ADK call failed", exc_info=True)
        raise RuntimeError(
            "Could not reach FinPath AI. "
            "Make sure your Orchestrate environment is active "
            "(run `orchestrate env activate finpath`). "
            f"Detail: {exc}"
        ) from exc


def health_check() -> bool:
    """Return True if the Orchestrate environment is reachable and the agent exists.

    Does not send any user data; only resolves the agent ID.
    Returns False (does not raise) on any failure, so callers can gate the UI.
    """
    try:
        run_client, _ = _make_clients()
        agent_id = get_agent_id_by_name(AGENT_NAME)
        return bool(agent_id)
    except Exception:
        logger.debug("health_check failed", exc_info=True)
        return False
