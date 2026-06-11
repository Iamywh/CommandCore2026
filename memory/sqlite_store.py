"""
SQLite-based memory store for JARVIS2026.

Provides persistent storage for conversations, decisions, and metadata.
"""

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import UUID

from app.schemas import ConversationContext


class SqliteStore:
    """SQLite-backed persistence layer."""

    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self) -> None:
        """Initialize database schema."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Conversations table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS conversations (
                    id TEXT PRIMARY KEY,
                    user_request TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    final_response TEXT,
                    metadata TEXT
                )
                """
            )

            # Messages table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS messages (
                    id TEXT PRIMARY KEY,
                    conversation_id TEXT NOT NULL,
                    sender TEXT NOT NULL,
                    recipient TEXT,
                    content TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    FOREIGN KEY (conversation_id) REFERENCES conversations(id)
                )
                """
            )

            # Tool calls table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS tool_calls (
                    id TEXT PRIMARY KEY,
                    conversation_id TEXT NOT NULL,
                    tool TEXT NOT NULL,
                    parameters TEXT NOT NULL,
                    status TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    FOREIGN KEY (conversation_id) REFERENCES conversations(id)
                )
                """
            )

            # Tool results table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS tool_results (
                    id TEXT PRIMARY KEY,
                    tool_call_id TEXT NOT NULL,
                    tool TEXT NOT NULL,
                    success BOOLEAN NOT NULL,
                    output TEXT,
                    error TEXT,
                    execution_time_ms REAL NOT NULL,
                    timestamp TEXT NOT NULL,
                    FOREIGN KEY (tool_call_id) REFERENCES tool_calls(id)
                )
                """
            )

            # Decisions table for routing/approvals
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS decisions (
                    id TEXT PRIMARY KEY,
                    conversation_id TEXT NOT NULL,
                    decision_type TEXT NOT NULL,
                    decision_data TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    FOREIGN KEY (conversation_id) REFERENCES conversations(id)
                )
                """
            )

            conn.commit()

    def save_conversation(self, context: ConversationContext) -> None:
        """Save a conversation context."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Save conversation
            cursor.execute(
                """
                INSERT OR REPLACE INTO conversations
                (id, user_request, created_at, updated_at, final_response, metadata)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    str(context.conversation_id),
                    context.user_request.text,
                    context.created_at.isoformat(),
                    context.updated_at.isoformat(),
                    context.final_response.model_dump_json()
                    if context.final_response
                    else None,
                    json.dumps(context.user_request.metadata),
                ),
            )

            # Save messages
            for message in context.messages:
                cursor.execute(
                    """
                    INSERT OR REPLACE INTO messages
                    (id, conversation_id, sender, recipient, content, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        str(message.id),
                        str(context.conversation_id),
                        message.sender.value,
                        message.recipient.value if message.recipient else None,
                        message.content,
                        message.timestamp.isoformat(),
                    ),
                )

            # Save tool calls
            for tool_call in context.tool_calls:
                cursor.execute(
                    """
                    INSERT OR REPLACE INTO tool_calls
                    (id, conversation_id, tool, parameters, status, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        str(tool_call.id),
                        str(context.conversation_id),
                        tool_call.tool.value,
                        json.dumps(tool_call.parameters),
                        tool_call.approval_status.value,
                        tool_call.timestamp.isoformat(),
                    ),
                )

            # Save tool results
            for result in context.tool_results:
                cursor.execute(
                    """
                    INSERT OR REPLACE INTO tool_results
                    (id, tool_call_id, tool, success, output, error, execution_time_ms, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        str(result.id),
                        str(result.tool_call_id),
                        result.tool.value,
                        result.success,
                        json.dumps(result.output) if result.output else None,
                        result.error,
                        result.execution_time_ms,
                        result.timestamp.isoformat(),
                    ),
                )

            conn.commit()

    def get_conversation(self, conversation_id: UUID) -> dict[str, Any] | None:
        """Retrieve a conversation by ID."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT id, user_request, created_at, updated_at, final_response, metadata
                FROM conversations WHERE id = ?
                """,
                (str(conversation_id),),
            )

            row = cursor.fetchone()
            if not row:
                return None

            return {
                "id": row[0],
                "user_request": row[1],
                "created_at": row[2],
                "updated_at": row[3],
                "final_response": row[4],
                "metadata": json.loads(row[5]) if row[5] else {},
            }

    def list_conversations(self, limit: int = 100, offset: int = 0) -> list[dict]:
        """List recent conversations."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT id, user_request, created_at, updated_at
                FROM conversations
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
                """,
                (limit, offset),
            )

            return [
                {
                    "id": row[0],
                    "user_request": row[1],
                    "created_at": row[2],
                    "updated_at": row[3],
                }
                for row in cursor.fetchall()
            ]

    def save_decision(
        self,
        conversation_id: UUID,
        decision_type: str,
        decision_data: dict[str, Any],
    ) -> str:
        """Save a decision (routing, approval, etc)."""
        decision_id = str(UUID(int=hash(f"{conversation_id}{decision_type}{datetime.utcnow()}") & 0xFFFFFFFFFFFFFFFF))

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO decisions
                (id, conversation_id, decision_type, decision_data, timestamp)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    decision_id,
                    str(conversation_id),
                    decision_type,
                    json.dumps(decision_data),
                    datetime.utcnow().isoformat(),
                ),
            )
            conn.commit()

        return decision_id

    def get_decisions(
        self,
        conversation_id: UUID,
        decision_type: str | None = None,
    ) -> list[dict]:
        """Get decisions for a conversation."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            if decision_type:
                cursor.execute(
                    """
                    SELECT id, decision_type, decision_data, timestamp
                    FROM decisions
                    WHERE conversation_id = ? AND decision_type = ?
                    ORDER BY timestamp DESC
                    """,
                    (str(conversation_id), decision_type),
                )
            else:
                cursor.execute(
                    """
                    SELECT id, decision_type, decision_data, timestamp
                    FROM decisions
                    WHERE conversation_id = ?
                    ORDER BY timestamp DESC
                    """,
                    (str(conversation_id),),
                )

            return [
                {
                    "id": row[0],
                    "decision_type": row[1],
                    "decision_data": json.loads(row[2]),
                    "timestamp": row[3],
                }
                for row in cursor.fetchall()
            ]

    def close(self) -> None:
        """Close the database connection."""
        pass  # Connection is closed automatically in context manager
