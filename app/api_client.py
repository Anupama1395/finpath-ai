"""
app/api_client.py
-----------------
Thin wrapper around the ADK RunClient + ThreadsClient.

Authentication is handled entirely by the ADK's instantiate_client()
utility, which reads the active environment token from the ADK config
files (~/.wxo/).  No secrets are read, stored, or logged here.

Public API
----------
    ask_agent(message, profile, thread_id=None) -> dict
        message:   plain question text (profile context is prepended here)
        profile:   dict of financial fields from session state
        thread_id: pass the returned thread_id on follow-ups to continue
                   the same conversation thread

    Returns a dict with keys:
        reply      str   — agent's plain-text response
        tools      list  — tool names called during this turn
        thread_id  str   — thread ID to pass on the next call
"""

from __future__ import annotations

import logging
from typing import Any

from ibm_watsonx_orchestrate.client.chat.run_client import RunClient
from ibm_watsonx_orchestrate.client.threads.threads_client import ThreadsClient
from ibm_watsonx_orchestrate.client.utils import instantiate_client
from ibm_watsonx_orchestrate.cli.commands.agents.agents_helper import get_agent_id_by_name

logger = logging.getLogger(__name__)

AGENT_NAME          = "finpath_agent"
RUN_TIMEOUT_SECONDS = 120


# ─────────────────────────────────────────────────────────────────────────────
# Internal helpers
# ─────────────────────────────────────────────────────────────────────────────

def _make_clients() -> tuple[RunClient, ThreadsClient]:
    """Return fresh ADK clients bound to the active environment."""
    return instantiate_client(RunClient), instantiate_client(ThreadsClient)


def _build_message(message: str, profile: dict) -> str:
    """Prepend the full profile block to every message sent to the agent.

    The debt rate is supplied in both percentage and decimal so the agent
    can pass the correct decimal value to tools without conversion.
    Tools expect the decimal form (e.g. 0.07 for 7%).
    """
    rate_pct     = profile.get("annual_debt_rate_pct", 0.0)   # e.g. 7.0
    rate_decimal = rate_pct / 100                              # e.g. 0.07

    block = (
        f"User profile: "
        f"monthly_income=${profile.get('monthly_income', 0):,}; "
        f"monthly_expenses=${profile.get('monthly_expenses', 0):,}; "
        f"monthly_savings_contribution=${profile.get('monthly_savings_contribution', 0):,}; "
        f"current_savings=${profile.get('current_savings', 0):,}; "
        f"debt_balance=${profile.get('debt_balance', 0):,}; "
        f"annual_debt_rate={rate_pct:.2f}% ({rate_decimal:.4f}) — "
        f"pass {rate_decimal:.4f} to tools that take a decimal rate; "
        f"monthly_debt_payment=${profile.get('monthly_debt_payment', 0):,}; "
        f"goal={profile.get('goal', 'not specified')}.\n"
        f"Question: {message}"
    )

    # Print full message to terminal for verification — never prints tokens or keys.
    print("\n" + "="*60)
    print("[FinPath → agent message]")
    print(block)
    print("="*60 + "\n")

    return block


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


def _extract_tools_and_outputs(messages: list[dict]) -> tuple[list[str], list[str]]:
    """Return (tool_names, tool_output_texts) for the latest assistant turn."""
    for msg in reversed(messages):
        if not isinstance(msg, dict) or msg.get("role") != "assistant":
            continue
        names: list[str] = []
        outputs: list[str] = []
        for step in msg.get("step_history", []):
            for detail in step.get("step_details", []):
                if detail.get("type") == "tool_calls":
                    for tc in detail.get("tool_calls", []):
                        name = tc.get("name") or tc.get("function", {}).get("name", "")
                        if name and name not in names:
                            names.append(name)
                        # Collect tool output text for verification
                        output = tc.get("output") or tc.get("result") or ""
                        if isinstance(output, dict):
                            output = str(output)
                        if output:
                            outputs.append(str(output))
        if names:
            return names, outputs
    return [], []


def _verify_figures(reply: str, tool_outputs: list[str]) -> bool | None:
    """Cross-check every dollar amount and percentage in the reply against tool outputs.

    Returns True if all figures found in tool outputs (within rounding),
    False if at least one figure cannot be matched, None if no figures in reply.
    """
    import re
    if not tool_outputs:
        return None

    # Extract all dollar amounts and percentages from the reply
    dollar_pattern = re.compile(r'\$\s*([\d,]+(?:\.\d{1,2})?)')
    pct_pattern    = re.compile(r'([\d]+(?:\.\d{1,2})?)\s*%')

    all_outputs_text = " ".join(tool_outputs)

    dollar_figures = [float(m.replace(",", "")) for m in dollar_pattern.findall(reply)]
    pct_figures    = [float(m) for m in pct_pattern.findall(reply)]
    all_figures    = dollar_figures + pct_figures

    if not all_figures:
        return None

    unverified = []
    for fig in all_figures:
        # Look for the figure (±0.51 rounding tolerance) in tool output text
        pattern = re.compile(r'[\d,]+(?:\.\d{1,2})?')
        output_numbers = [float(m.replace(",","")) for m in pattern.findall(all_outputs_text)]
        if not any(abs(fig - n) < 0.51 for n in output_numbers):
            unverified.append(fig)

    return len(unverified) == 0


# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────

def ask_agent(
    message: str,
    profile: dict,
    thread_id: str | None = None,
) -> dict:
    """Send a message to finpath_agent and return a result dict.

    Args:
        message:   The user's question in plain text.
        profile:   Dict with keys: monthly_income, monthly_expenses,
                   monthly_savings_contribution, current_savings, debt_balance,
                   annual_debt_rate_pct (percentage, e.g. 7.0),
                   monthly_debt_payment, goal.
        thread_id: Pass the thread_id from a previous call to continue the
                   same conversation thread. None starts a fresh thread.

    Returns:
        {
            "reply":     str   — agent's plain-text response,
            "tools":     list  — tool names called this turn (may be empty),
            "thread_id": str   — thread ID; pass on the next call,
        }

    Raises:
        RuntimeError: wraps any ADK / network error with a user-friendly message.
        TimeoutError: if the run doesn't complete within RUN_TIMEOUT_SECONDS.
    """
    full_message = _build_message(message, profile)

    try:
        run_client, threads_client = _make_clients()
        agent_id = get_agent_id_by_name(AGENT_NAME)

        run_response = run_client.create_run(
            message=full_message,
            agent_id=agent_id,
            thread_id=thread_id,        # None → new thread; existing → reuse
        )
        new_thread_id: str = run_response["thread_id"]
        run_id: str        = run_response["run_id"]

        print(f"[FinPath] thread_id={new_thread_id}  run_id={run_id}")

        max_retries = RUN_TIMEOUT_SECONDS // 2
        status = run_client.wait_for_run_completion(run_id, max_retries=max_retries)

        if status.get("status") == "failed":
            raise RuntimeError(status.get("error", "Agent run failed."))

        msgs_response = threads_client.get_thread_messages(new_thread_id)
        if isinstance(msgs_response, list):
            all_msgs = msgs_response
        elif isinstance(msgs_response, dict) and "data" in msgs_response:
            all_msgs = msgs_response["data"]
        else:
            all_msgs = []

        reply_text = ""
        for msg in reversed(all_msgs):
            if isinstance(msg, dict) and msg.get("role") == "assistant":
                reply_text = _extract_text(msg.get("content", ""))
                break

        tools, tool_outputs = _extract_tools_and_outputs(all_msgs)
        verified = _verify_figures(reply_text, tool_outputs)

        print(f"[FinPath] tools called: {tools or '(none)'}")
        print(f"[FinPath] verified: {verified}")

        return {
            "reply":     reply_text or "No response received from agent.",
            "tools":     tools,
            "thread_id": new_thread_id,
            "verified":  verified,
        }

    except (RuntimeError, TimeoutError):
        raise
    except Exception as exc:
        logger.debug("ADK call failed", exc_info=True)
        raise RuntimeError(
            "Could not reach FinPath AI. "
            "Make sure your Orchestrate environment is active "
            f"(`orchestrate env activate finpath`). Detail: {exc}"
        ) from exc
