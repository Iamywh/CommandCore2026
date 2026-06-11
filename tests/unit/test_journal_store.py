from datetime import datetime
from pathlib import Path
from uuid import uuid4

from app.schemas import (
    AgentName,
    ConversationContext,
    FinalResponse,
    Message,
    ToolCall,
    ToolName,
    UserRequest,
)
from memory.journal_store import JournalStore


def test_journal_directory_created_on_init(tmp_path: Path) -> None:
    journal_store = JournalStore(tmp_path)

    assert tmp_path.exists()
    assert tmp_path.is_dir()
    assert journal_store.journal_path == tmp_path


def test_get_daily_path_returns_yyyy_mm_dd_md(tmp_path: Path) -> None:
    journal_store = JournalStore(tmp_path)
    date = datetime(2025, 1, 2, 12, 0, 0)

    daily_path = journal_store._get_daily_path(date)

    assert daily_path == tmp_path / "2025-01-02.md"
    assert daily_path.suffix == ".md"
    assert daily_path.name == "2025-01-02.md"


def test_get_daily_journal_returns_empty_string_when_no_journal_exists(tmp_path: Path) -> None:
    journal_store = JournalStore(tmp_path)
    date = datetime(2025, 1, 3, 8, 0, 0)

    assert journal_store.get_daily_journal(date) == ""


def test_log_decision_creates_daily_file_and_includes_expected_sections(tmp_path: Path) -> None:
    journal_store = JournalStore(tmp_path)
    date = datetime(2025, 2, 3, 9, 15, 0)

    journal_store.log_decision(
        decision_type="approval",
        description="Approve the budget.",
        reasoning="The numbers are within risk tolerance.",
        date=date,
    )

    content = journal_store.get_daily_journal(date)

    assert "# 2025-02-03" in content
    assert "Decision:" in content
    assert "Reasoning:" in content
    assert "Approve the budget." in content
    assert "The numbers are within risk tolerance." in content


def test_log_error_includes_error_and_context(tmp_path: Path) -> None:
    journal_store = JournalStore(tmp_path)
    date = datetime(2025, 2, 4, 10, 0, 0)

    journal_store.log_error(
        error_message="Failed to fetch data.",
        context="API timeout",
        date=date,
    )

    content = journal_store.get_daily_journal(date)

    assert "Error:" in content
    assert "Context:" in content
    assert "Failed to fetch data." in content
    assert "API timeout" in content


def test_log_summary_includes_section_title_and_summary_text(tmp_path: Path) -> None:
    journal_store = JournalStore(tmp_path)
    date = datetime(2025, 2, 5, 11, 0, 0)

    journal_store.log_summary(
        summary="The team completed the sprint review.",
        section="Daily Summary",
        date=date,
    )

    content = journal_store.get_daily_journal(date)

    assert "## Daily Summary" in content
    assert "The team completed the sprint review." in content


def test_list_journals_returns_markdown_files_sorted_newest_first(tmp_path: Path) -> None:
    journal_store = JournalStore(tmp_path)
    older_date = datetime(2025, 2, 1, 8, 0, 0)
    newer_date = datetime(2025, 2, 2, 8, 0, 0)

    journal_store.log_summary(summary="First entry.", section="Summary", date=older_date)
    journal_store.log_summary(summary="Second entry.", section="Summary", date=newer_date)

    journals = journal_store.list_journals()
    journal_names = [journal.name for journal in journals]

    assert journal_names == ["2025-02-02.md", "2025-02-01.md"]


def test_get_stats_returns_expected_counts_and_journal_names(tmp_path: Path) -> None:
    journal_store = JournalStore(tmp_path)
    first_date = datetime(2025, 3, 1, 8, 0, 0)
    second_date = datetime(2025, 3, 2, 9, 0, 0)

    journal_store.log_decision(
        decision_type="routing",
        description="Route to dev agent.",
        reasoning="The request is implementation-heavy.",
        date=first_date,
    )
    journal_store.log_summary(
        summary="Dev agent will handle the work.",
        section="Routing Summary",
        date=second_date,
    )

    stats = journal_store.get_stats()

    assert stats["total_journals"] == 2
    assert stats["total_entries"] == 2
    assert stats["total_size_bytes"] > 0
    assert stats["newest_journal"] == "2025-03-02.md"
    assert stats["oldest_journal"] == "2025-03-01.md"


def test_log_conversation_includes_expected_markdown_sections(tmp_path: Path) -> None:
    journal_store = JournalStore(tmp_path)
    date = datetime(2025, 4, 1, 14, 30, 0)

    context = ConversationContext(
        user_request=UserRequest(text="What is the status?"),
        messages=[
            Message(
                sender=AgentName.DIRECTOR,
                content="Checking status now.",
            )
        ],
        final_response=FinalResponse(
            request_id=uuid4(),
            response_text="Everything is on track.",
        ),
        tool_calls=[
            ToolCall(
                tool=ToolName.GITHUB,
                parameters={"repo": "my-repo"},
            )
        ],
        created_at=date,
    )

    journal_store.log_conversation(context)
    content = journal_store.get_daily_journal(date)

    assert "User Request" in content
    assert "Input:" in content
    assert "Agent Messages" in content
    assert "Final Response" in content
    assert "Tools Used" in content
    assert "What is the status?" in content
    assert "Checking status now." in content
    assert "Everything is on track." in content
    assert "github" in content.lower()
