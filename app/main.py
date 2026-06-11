"""Minimal text CLI entrypoint for JARVIS2026.

Usage:
    python -m app.main

This CLI creates a `UserRequest` from user input and asks the `Orchestrator`
to route it. It prints the primary agent, confidence, matched keywords and
reasoning for each request. It is intentionally minimal and does not call any
LLM or UI providers.
"""
from __future__ import annotations

import asyncio

from app.orchestrator import Orchestrator
from app.schemas import UserRequest

EXIT_KEYWORDS: set[str] = {"exit", "quit", "q"}


def _print_banner() -> None:
    print("JARVIS2026 CLI")
    print("Type a request, or 'exit' to quit.")


def _print_decision(decision) -> None:
    # decision is a RoutingDecision model
    print("--- Routing Result ---")
    print(f"Primary agent: {decision.primary_agent.value}")
    print(f"Confidence: {decision.confidence:.2f}")
    print(f"Matched keywords: {', '.join(decision.matched_keywords) if decision.matched_keywords else '(none)'}")
    print(f"Reasoning: {decision.reasoning}")
    print("----------------------")


async def run_cli() -> None:
    orchestrator = Orchestrator()

    _print_banner()

    # Use built-in input loop; input_fn is unused but present for easier testing extension
    while True:
        try:
            user_input = input("> ")
        except (KeyboardInterrupt, EOFError):
            print("\nExiting.")
            return

        if not user_input:
            continue

        text = user_input.strip()
        if not text:
            continue

        if text.lower() in EXIT_KEYWORDS:
            print("Goodbye.")
            return

        # Build request and route it
        try:
            request = UserRequest(text=text)
        except Exception as exc:  # Keep validation errors local and continue loop
            print(f"Invalid request: {exc}")
            continue

        try:
            decision = await orchestrator.route_request(request)
        except KeyboardInterrupt:
            print("\nInterrupted. Exiting.")
            return
        except Exception as exc:
            print(f"Error routing request: {exc}")
            continue

        _print_decision(decision)


def main() -> int:
    try:
        asyncio.run(run_cli())
    except KeyboardInterrupt:
        print("\nExiting.")
        return 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
