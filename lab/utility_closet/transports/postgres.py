"""
postgres.py — Postgres-backed transport for comms channels.

Stores messages in infra.channel_messages (the existing table, now in
the infra schema). Provides persistent history with SQL querying.
"""

from __future__ import annotations

import json
import logging
from lab.utility_closet.agent_base import get_logger
import os
from typing import Optional

from ..comms import Channel, ChannelMessage, Transport

log = get_logger(__name__)


class PostgresTransport(Transport):
    """Persistent message store using the infra.channel_messages table."""

    def __init__(self, db_url: Optional[str] = None):
        super().__init__()
        self._db_url = db_url or os.getenv("IGOR_HOME_DB_URL")
        self._conn = None

    def _get_conn(self):
        if self._conn is None or self._conn.closed:
            import psycopg2

            self._conn = psycopg2.connect(self._db_url)
            # Set search_path to find channel_messages in infra schema
            cur = self._conn.cursor()
            cur.execute("SET search_path TO infra,clan,public")
            cur.close()
            self._conn.commit()
        return self._conn

    def send(self, channel: Channel, message: ChannelMessage) -> bool:
        try:
            conn = self._get_conn()
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO channel_messages (ts, author, type, content, channel) "
                "VALUES (%s, %s, %s, %s, %s)",
                (
                    message.timestamp,
                    message.source,
                    message.content_type,
                    message.payload,
                    channel.address,
                ),
            )
            conn.commit()
            cur.close()
            return True
        except Exception as exc:
            log.error("PostgresTransport send error: %s", exc)
            try:
                self._conn.rollback()
            except Exception:
                pass
            self._conn = None
            return False

    def read(
        self,
        channel: Channel,
        limit: int = 50,
        since: Optional[str] = None,
    ) -> list[ChannelMessage]:
        try:
            conn = self._get_conn()
            cur = conn.cursor()
            if since:
                cur.execute(
                    "SELECT ts, author, type, content, channel "
                    "FROM channel_messages "
                    "WHERE channel = %s AND ts > %s "
                    "ORDER BY id DESC LIMIT %s",
                    (channel.address, since, limit),
                )
            else:
                cur.execute(
                    "SELECT ts, author, type, content, channel "
                    "FROM channel_messages "
                    "WHERE channel = %s "
                    "ORDER BY id DESC LIMIT %s",
                    (channel.address, limit),
                )
            rows = cur.fetchall()
            cur.close()
            return [
                ChannelMessage(
                    channel=row[4],
                    source=row[1],
                    timestamp=row[0],
                    content_type=row[2] or "text/plain",
                    payload=row[3],
                )
                for row in rows
            ]
        except Exception as exc:
            log.error("PostgresTransport read error: %s", exc)
            return []

    def close(self) -> None:
        if self._conn and not self._conn.closed:
            try:
                self._conn.close()
            except Exception:
                pass
            self._conn = None
