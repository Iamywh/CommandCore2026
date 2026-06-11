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
from app.settings import get_settings
from memory.journal_store import JournalStore

EXIT_KEYWORDS: set[str] = {"exit", "quit", "q"}
JOURNAL_COMMAND = "/journal"
HELP_COMMAND = "/help"
STATS_COMMAND = "/stats"
HISTORY_COMMAND = "/history"
CLEAR_COMMAND = "/clear"


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


def _log_routing_decision(journal_store: JournalStore, decision) -> None:
    try:
        journal_store.log_decision(
            decision_type="routing",
            description=f"Routed request to {decision.primary_agent.value}",
            reasoning=decision.reasoning,
        )
    except Exception as exc:
        print(f"Warning: failed to write journal entry: {exc}")


def _print_help() -> None:
    print("JARVIS2026 Commands")
    print("/help     Show available commands.")
    print("/journal  Show today's journal.")
    print("/stats    Show journal statistics.")
    print("/history  Show available journal files.")
    print("/clear    Clear the CLI screen.")
    print("exit      Quit the CLI.")
    print("quit      Quit the CLI.")
    print("q         Quit the CLI.")


def _print_journal_stats(journal_store: JournalStore) -> None:
    stats = journal_store.get_stats()
    print("--- Journal Stats ---")
    print(f"Total journals: {stats['total_journals']}")
    print(f"Total entries: {stats['total_entries']}")
    print(f"Total size bytes: {stats['total_size_bytes']}")
    print(f"Newest journal: {stats['newest_journal']}")
    print(f"Oldest journal: {stats['oldest_journal']}")
    print("---------------------")


def _print_today_journal(journal_store: JournalStore) -> None:
    content = journal_store.get_daily_journal()
    if not content:
        print("No journal entries found for today.")
        return

    print("--- Today's Journal ---")
    print(content.rstrip())
    print("-----------------------")


def _print_journal_history(journal_store: JournalStore) -> None:
    journals = journal_store.list_journals()
    if not journals:
        print("No journal history found.")
        return

    print("--- Journal History ---")
    for journal in journals:
        print(f"- {journal.name}")
    print("-----------------------")


def _clear_screen() -> None:
    print("\033c", end="")


def _process_cli_command(text: str, journal_store: JournalStore) -> bool:
    normalized = text.lower()
    if normalized == JOURNAL_COMMAND:
        _print_today_journal(journal_store)
        return True
    if normalized == HELP_COMMAND:
        _print_help()
        return True
    if normalized == STATS_COMMAND:
        _print_journal_stats(journal_store)
        return True
    if normalized == HISTORY_COMMAND:
        _print_journal_history(journal_store)
        return True
    if normalized == CLEAR_COMMAND:
        _clear_screen()
        return True
    return False


async def run_cli() -> None:
    orchestrator = Orchestrator()
    settings = get_settings()
    settings.initialize()
    journal_store = JournalStore(settings.paths.journal_path, settings.paths.journal_file)

    _print_banner()

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

        if _process_cli_command(text, journal_store):
            continue

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
        _log_routing_decision(journal_store, decision)


def main() -> int:
    try:
        asyncio.run(run_cli())
    except KeyboardInterrupt:
        print("\nExiting.")
        return 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
