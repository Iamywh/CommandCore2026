"""
Markdown journal store for human-readable JARVIS2026 memories.

Stores summaries and decisions in markdown format for easy reading.
"""

from datetime import datetime
from pathlib import Path

from app.schemas import ConversationContext


class JournalStore:
    """Markdown-based journal for human-readable records."""

    def __init__(self, journal_path: Path, daily_file: str = "daily_journal.md"):
        self.journal_path = journal_path
        self.daily_file = daily_file
        self.journal_path.mkdir(parents=True, exist_ok=True)

    def _get_daily_path(self, date: datetime | None = None) -> Path:
        """Get path to the daily journal file."""
        if date is None:
            date = datetime.utcnow()

        filename = date.strftime("%Y-%m-%d.md")
        return self.journal_path / filename

    def _ensure_daily_header(self, path: Path) -> None:
        """Ensure daily journal has a date header."""
        if not path.exists():
            date_str = path.stem
            header = f"# {date_str}\n\nDaily journal for JARVIS2026\n\n"
            path.write_text(header)

    def log_conversation(self, context: ConversationContext) -> None:
        """Log a conversation to the journal.

        Args:
            context: Conversation context to log
        """
        daily_path = self._get_daily_path(context.created_at)
        self._ensure_daily_header(daily_path)

        # Format the conversation entry
        timestamp = context.created_at.strftime("%H:%M:%S")
        entry = f"\n## {timestamp} - User Request\n\n"
        entry += f"**Input:** {context.user_request.text}\n\n"

        if context.messages:
            entry += "### Agent Messages\n\n"
            for msg in context.messages:
                entry += f"- **{msg.sender.value}**: {msg.content[:100]}...\n"
            entry += "\n"

        if context.final_response:
            entry += "### Final Response\n\n"
            entry += f"{context.final_response.response_text}\n\n"

        if context.tool_calls:
            entry += "### Tools Used\n\n"
            for tool_call in context.tool_calls:
                entry += f"- {tool_call.tool.value}\n"
            entry += "\n"

        # Append to daily journal
        with open(daily_path, "a", encoding="utf-8") as f:
            f.write(entry)

    def log_decision(
        self,
        decision_type: str,
        description: str,
        reasoning: str,
        date: datetime | None = None,
    ) -> None:
        """Log a decision to the journal.

        Args:
            decision_type: Type of decision (routing, approval, etc)
            description: What was decided
            reasoning: Why it was decided
            date: Optional date (defaults to today)
        """
        daily_path = self._get_daily_path(date)
        self._ensure_daily_header(daily_path)

        timestamp = (date or datetime.utcnow()).strftime("%H:%M:%S")
        entry = f"\n## {timestamp} - {decision_type.title()}\n\n"
        entry += f"**Decision:** {description}\n\n"
        entry += f"**Reasoning:** {reasoning}\n\n"

        with open(daily_path, "a", encoding="utf-8") as f:
            f.write(entry)

    def log_error(
        self,
        error_message: str,
        context: str | None = None,
        date: datetime | None = None,
    ) -> None:
        """Log an error to the journal.

        Args:
            error_message: Error description
            context: Optional context about the error
            date: Optional date (defaults to today)
        """
        daily_path = self._get_daily_path(date)
        self._ensure_daily_header(daily_path)

        timestamp = (date or datetime.utcnow()).strftime("%H:%M:%S")
        entry = f"\n### ❌ {timestamp} - Error\n\n"
        entry += f"**Error:** {error_message}\n"
        if context:
            entry += f"**Context:** {context}\n"
        entry += "\n"

        with open(daily_path, "a", encoding="utf-8") as f:
            f.write(entry)

    def log_summary(
        self,
        summary: str,
        section: str = "Summary",
        date: datetime | None = None,
    ) -> None:
        """Log a summary section to the journal.

        Args:
            summary: Summary text
            section: Section name (defaults to "Summary")
            date: Optional date (defaults to today)
        """
        daily_path = self._get_daily_path(date)
        self._ensure_daily_header(daily_path)

        entry = f"\n## {section}\n\n{summary}\n\n"

        with open(daily_path, "a", encoding="utf-8") as f:
            f.write(entry)

    def get_daily_journal(self, date: datetime | None = None) -> str:
        """Get the contents of the daily journal.

        Args:
            date: Optional date (defaults to today)

        Returns:
            Contents of the daily journal file
        """
        daily_path = self._get_daily_path(date)
        if not daily_path.exists():
            return ""
        return daily_path.read_text(encoding="utf-8")

    def list_journals(self) -> list[Path]:
        """List all journal files.

        Returns:
            List of journal file paths sorted by date (newest first)
        """
        journals = sorted(self.journal_path.glob("*.md"), reverse=True)
        return journals

    def get_stats(self) -> dict:
        """Get journal statistics.

        Returns:
            Dict with stats about the journal
        """
        journals = self.list_journals()
        total_entries = 0
        total_size = 0

        for journal in journals:
            content = journal.read_text(encoding="utf-8")
            total_entries += content.count("##")
            total_size += len(content)

        return {
            "total_journals": len(journals),
            "total_entries": total_entries,
            "total_size_bytes": total_size,
            "newest_journal": journals[0].name if journals else None,
            "oldest_journal": journals[-1].name if journals else None,
        }
