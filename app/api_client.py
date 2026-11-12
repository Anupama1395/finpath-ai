"""
app/api_client.py
-----------------
Thin wrapper around the ADK RunClient + ThreadsClient.

Authentication is handled entirely by the ADK's instantiate_client()
utility, which reads the active environment token from the ADK config
files (~/.wxo/).  No secrets are read, stored, or logged here.

Usage:
    from app.api_client import ask_agent
    reply, scenarios = ask_agent("Can I save $500/mo?", thread_id=None)
"""

from __future__ import annotations

import json
import logging
from typing import Any

from ibm_watsonx_orchestrate.client.chat.run_client import RunClient
from ibm_watsonx_orchestrate.client.threads.threads_client import ThreadsClient
from ibm_watsonx_orchestrate.client.utils import instantiate_client
from ibm_watsonx_orchestrate.cli.commands.agents.agents_helper import get_agent_id_by_name

logger = logging.getLogger(__name__)

AGENT_NAME = "finpath_agent"
# Maximum seconds to wait for a run to complete before raising TimeoutError
RUN_TIMEOUT_SECONDS = 120


def _make_clients() -> tuple[RunClient, ThreadsClient]:
    """Return fresh ADK clients bound to the active environment."""
    return (
        instantiate_client(RunClient),
        instantiate_client(ThreadsClient),
    )


def _extract_text(content: Any) -> str:
    """Pull plain text out of an Orchestrate message content field.

    Content can be a plain string or a list of response-type dicts.
    """
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


def _extract_scenarios(text: str) -> list[dict] | None:
    """Try to find a JSON list of scenario result dicts embedded in the reply.

    The agent is instructed to always call compare_scenarios; its tool
    output is sometimes echoed as a JSON code block in the reply text.
    Returns None if no parseable scenario list is found.
    """
    import re

    # Look for ```json ... ``` or bare [...] blocks
    patterns = [
        r"```(?:json)?\s*(\[.*?\])\s*```",  # fenced code block
        r"(\[\s*\{.*?\}\s*\])",              # bare JSON array
    ]
    for pat in patterns:
        matches = re.findall(pat, text, re.DOTALL)
        for raw in matches:
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


def ask_agent(
    message: str,
    thread_id: str | None = None,
) -> tuple[str, list[dict] | None, str | None]:
    """Send a message to finpath_agent and return (reply_text, scenarios, thread_id).

    Args:
        message: The user's question, already enriched with profile context.
        thread_id: Existing conversation thread to continue, or None to start fresh.

    Returns:
        reply_text:  The agent's plain-text response.
        scenarios:   List of scenario result dicts when compare_scenarios was called,
                     or None if no structured results were found in the reply.
        thread_id:   The thread ID to pass on the next call for conversation continuity.

    Raises:
        RuntimeError: Wraps any ADK or network error with a user-friendly message.
        TimeoutError: If the run does not complete within RUN_TIMEOUT_SECONDS.
    """
    try:
        run_client, threads_client = _make_clients()
        agent_id = get_agent_id_by_name(AGENT_NAME)

        # Create the run (POST /runs)
        run_response = run_client.create_run(
            message=message,
            agent_id=agent_id,
            thread_id=thread_id,
        )
        new_thread_id: str = run_response["thread_id"]
        run_id: str = run_response["run_id"]

        # Poll until completed / failed
        max_retries = RUN_TIMEOUT_SECONDS // 2  # poll every 2 s
        status = run_client.wait_for_run_completion(run_id, max_retries=max_retries)

        if status.get("status") == "failed":
            err = status.get("error", "Unknown error from agent")
            raise RuntimeError(err)

        # Fetch messages and find the latest assistant reply
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
            f"Could not reach FinPath AI. "
            f"Make sure your Orchestrate environment is active "
            f"(run `orchestrate env activate finpath`). Detail: {exc}"
        ) from exc
