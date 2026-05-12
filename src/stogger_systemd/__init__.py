"""stogger-systemd — systemd journal I/O for stogger."""

from __future__ import annotations

import os
import socket
import stat

JOURNAL_SOCKET_PATH = "/run/systemd/journal/socket"


class JournalSender:
    """Send structured messages to the systemd journal via AF_UNIX socket."""

    def __init__(self, socket_path: str = JOURNAL_SOCKET_PATH) -> None:
        self._socket_path = socket_path
        self._sock: socket.socket | None = None

    def __enter__(self) -> JournalSender:
        self._sock = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
        self._sock.connect(self._socket_path)
        return self

    def __exit__(self, *args: object) -> None:
        if self._sock is not None:
            self._sock.close()
            self._sock = None

    def send(self, fields: dict) -> bool:
        payload = self.format_message(fields)
        try:
            with socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM) as sock:
                sock.connect(self._socket_path)
                sock.sendall(payload)
                return True
        except OSError:
            return False

    @staticmethod
    def format_message(fields: dict) -> bytes:
        parts: list[bytes] = []
        for key, value in fields.items():
            if value is None:
                continue
            if isinstance(value, bytes):
                parts.append(f"{key}\n{len(value)}\n".encode() + value + b"\n")
            else:
                parts.append(f"{key}={value}\n".encode("utf-8"))
        return b"".join(parts)


class JournalLogger:
    """Write log messages to the systemd journal via AF_UNIX socket."""

    def __init__(
        self,
        syslog_identifier: str = "stogger",
        syslog_facility: int = 0,
        socket_path: str = JOURNAL_SOCKET_PATH,
    ) -> None:
        self.syslog_identifier = syslog_identifier
        self.syslog_facility = syslog_facility
        self.socket_path = socket_path
        self._sender = JournalSender(socket_path)

    def msg(self, messages: dict) -> None:
        self._sender.send(messages)


class DummyJournalLogger:
    """No-op journal logger for non-systemd environments."""

    def msg(self, messages: dict) -> None:
        pass


class JournalLoggerFactory:
    """Creates JournalLogger or DummyJournalLogger based on systemd availability."""

    def __init__(self, socket_path: str = JOURNAL_SOCKET_PATH) -> None:
        self.socket_path = socket_path

    def __call__(self):
        if _journal_socket_available(self.socket_path):
            return JournalLogger(socket_path=self.socket_path)
        return DummyJournalLogger()


def _journal_socket_available(path: str = JOURNAL_SOCKET_PATH) -> bool:
    try:
        st = os.stat(path)
    except OSError:
        return False
    return stat.S_ISSOCK(st.st_mode)


def get_journal_logger_factory() -> JournalLoggerFactory:
    """Return a JournalLoggerFactory instance."""
    return JournalLoggerFactory()
