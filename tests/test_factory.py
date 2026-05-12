"""Factory tests — JournalLoggerFactory routing logic."""

import socket

from stogger_systemd import (
    DummyJournalLogger,
    JournalLogger,
    JournalLoggerFactory,
)


class TestJournalLoggerFactory:
    """Factory returns the right logger based on socket availability."""

    def test_returns_journal_logger_when_socket_exists(self, tmp_path):
        """When the journal socket path exists and is a socket, return JournalLogger."""
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
        sock_path = str(tmp_path / "journal.sock")
        sock.bind(sock_path)

        try:
            factory = JournalLoggerFactory(socket_path=sock_path)
            logger = factory()
            assert isinstance(logger, JournalLogger)
        finally:
            sock.close()

    def test_returns_dummy_when_socket_missing(self, tmp_path):
        """When the journal socket path doesn't exist, return DummyJournalLogger."""
        missing_path = str(tmp_path / "nonexistent.sock")
        factory = JournalLoggerFactory(socket_path=missing_path)
        logger = factory()
        assert isinstance(logger, DummyJournalLogger)

    def test_returns_dummy_when_path_is_file_not_socket(self, tmp_path):
        """When the path exists but is a regular file (not a socket), return DummyJournalLogger."""
        file_path = str(tmp_path / "not_a_socket")
        with open(file_path, "w") as f:
            f.write("")

        factory = JournalLoggerFactory(socket_path=file_path)
        logger = factory()
        assert isinstance(logger, DummyJournalLogger)

    def test_configurable_socket_path(self, tmp_path):
        """Factory accepts and uses a custom socket path."""
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
        custom_path = str(tmp_path / "custom.sock")
        sock.bind(custom_path)

        try:
            factory = JournalLoggerFactory(socket_path=custom_path)
            logger = factory()
            assert isinstance(logger, JournalLogger)
            assert logger.socket_path == custom_path
        finally:
            sock.close()

    def test_default_socket_path(self):
        """Default socket path is /run/systemd/journal/socket."""
        factory = JournalLoggerFactory()
        assert factory.socket_path == "/run/systemd/journal/socket"


class TestGetJournalLoggerFactory:
    """Entry point function tests."""

    def test_returns_factory_instance(self):
        from stogger_systemd import get_journal_logger_factory

        factory = get_journal_logger_factory()
        assert isinstance(factory, JournalLoggerFactory)
