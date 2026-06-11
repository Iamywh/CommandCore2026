from pathlib import Path

from app.main import (
    EXIT_KEYWORDS,
    HELP_COMMAND,
    JOURNAL_COMMAND,
    STATS_COMMAND,
    _log_routing_decision,
    _print_banner,
    _print_decision,
    _print_help,
    _print_journal_stats,
    _print_today_journal,
)
from app.schemas import AgentName, RoutingDecision
from memory.journal_store import JournalStore


def test_exit_keywords_contains_expected_values() -> None:
    assert {"exit", "quit", "q"} == EXIT_KEYWORDS


def test_print_banner(capsys) -> None:
    _print_banner()

    captured = capsys.readouterr()
    assert captured.out == "JARVIS2026 CLI\nType a request, or 'exit' to quit.\n"


def test_print_decision(capsys) -> None:
    decision = RoutingDecision(
        request_id="00000000-0000-0000-0000-000000000000",
        primary_agent=AgentName.DEV,
        secondary_agents=[],
        confidence=0.85,
        reasoning="Test routing decision",
        matched_keywords=["test", "debug"],
    )

    _print_decision(decision)
    captured = capsys.readouterr()

    assert "Primary agent: dev\n" in captured.out
    assert "Confidence: 0.85\n" in captured.out
    assert "Matched keywords: test, debug\n" in captured.out
    assert "Reasoning: Test routing decision\n" in captured.out


def test_journal_command_constant() -> None:
    assert JOURNAL_COMMAND == "/journal"


def test_help_command_constant() -> None:
    assert HELP_COMMAND == "/help"


def test_print_help(capsys) -> None:
    _print_help()

    captured = capsys.readouterr()
    assert "JARVIS2026 Commands\n" in captured.out
    assert "/help     Show available commands.\n" in captured.out
    assert "/journal  Show today's journal.\n" in captured.out
    assert "/stats    Show journal statistics.\n" in captured.out
    assert "exit      Quit the CLI.\n" in captured.out
    assert "quit      Quit the CLI.\n" in captured.out
    assert "q         Quit the CLI.\n" in captured.out


def test_stats_command_constant() -> None:
    assert STATS_COMMAND == "/stats"


def test_print_journal_stats_no_entries(capsys, tmp_path: Path) -> None:
    journal_store = JournalStore(tmp_path)

    _print_journal_stats(journal_store)

    captured = capsys.readouterr()
    assert "--- Journal Stats ---\n" in captured.out
    assert "Total journals: 0\n" in captured.out
    assert "Total entries: 0\n" in captured.out
    assert "Total size bytes: 0\n" in captured.out
    assert "Newest journal: None\n" in captured.out
    assert "Oldest journal: None\n" in captured.out
    assert "---------------------\n" in captured.out


def test_print_journal_stats_with_content(capsys, tmp_path: Path) -> None:
    journal_store = JournalStore(tmp_path)
    journal_store.log_summary(
        summary="Journal stats test.",
        section="Summary",
        date=None,
    )

    _print_journal_stats(journal_store)

    captured = capsys.readouterr()
    assert "--- Journal Stats ---\n" in captured.out
    assert "Total journals: 1\n" in captured.out
    assert "Total entries: 1\n" in captured.out
    assert "Total size bytes: " in captured.out
    assert "Newest journal: " in captured.out
    assert "Oldest journal: " in captured.out
    assert "---------------------\n" in captured.out


def test_print_today_journal_no_entries(capsys, tmp_path: Path) -> None:
    journal_store = JournalStore(tmp_path)

    _print_today_journal(journal_store)

    captured = capsys.readouterr()
    assert captured.out == "No journal entries found for today.\n"


def test_print_today_journal_with_content(capsys, tmp_path: Path) -> None:
    journal_store = JournalStore(tmp_path)
    journal_store.log_summary(
        summary="Today we made progress.",
        section="Summary",
        date=None,
    )

    _print_today_journal(journal_store)

    captured = capsys.readouterr()
    assert "--- Today's Journal ---\n" in captured.out
    assert "Today we made progress." in captured.out
    assert "-----------------------\n" in captured.out


def test_log_routing_decision_writes_expected_entry(tmp_path: Path) -> None:
    journal_store = JournalStore(tmp_path)
    decision = RoutingDecision(
        request_id="00000000-0000-0000-0000-000000000000",
        primary_agent=AgentName.DEV,
        secondary_agents=[],
        confidence=0.85,
        reasoning="Test routing decision",
        matched_keywords=["test", "debug"],
    )

    _log_routing_decision(journal_store, decision)

    journals = journal_store.list_journals()
    assert len(journals) == 1

    content = journal_store.get_daily_journal()
    assert "**Decision:** Routed request to dev" in content
    assert "**Reasoning:** Test routing decision" in content


def test_log_routing_decision_failure_prints_warning(capsys) -> None:
    class BrokenStore:
        def log_decision(self, *_, **__):
            raise RuntimeError("disk full")

    decision = RoutingDecision(
        request_id="00000000-0000-0000-0000-000000000000",
        primary_agent=AgentName.DEV,
        secondary_agents=[],
        confidence=0.85,
        reasoning="Test routing decision",
        matched_keywords=["test", "debug"],
    )

    _log_routing_decision(BrokenStore(), decision)

    captured = capsys.readouterr()
    assert "Warning: failed to write journal entry: disk full" in captured.out
