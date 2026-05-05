"""stogger-systemd — systemd journal I/O for stogger."""


class JournalLogger:
    """Write log messages to the systemd journal via journal.send()."""

    def __init__(self, syslog_identifier: str = "stogger", syslog_facility: int = 0) -> None:
        self.syslog_identifier = syslog_identifier
        self.syslog_facility = syslog_facility

    def msg(self, messages: dict) -> None:
        from systemd import journal  # noqa: PLC0415  # ty: ignore[unresolved-import]

        journal.send(**messages)


class DummyJournalLogger:
    """No-op journal logger for non-systemd environments."""

    def msg(self, messages: dict) -> None:
        pass


class JournalLoggerFactory:
    """Creates JournalLogger or DummyJournalLogger based on systemd availability."""

    def __call__(self):
        try:
            from systemd import journal  # noqa: PLC0415, F401  # ty: ignore[unresolved-import]
        except ImportError:
            return DummyJournalLogger()
        return JournalLogger()


def get_journal_logger_factory() -> JournalLoggerFactory:
    """Return a JournalLoggerFactory instance."""
    return JournalLoggerFactory()
