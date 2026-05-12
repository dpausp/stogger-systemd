"""Fallback tests — DummyJournalLogger behavior."""

from stogger_systemd import DummyJournalLogger


class TestDummyJournalLogger:
    """DummyJournalLogger must never crash and never send."""

    def test_msg_does_not_raise(self):
        logger = DummyJournalLogger()
        logger.msg({"MESSAGE": "test", "PRIORITY": 6})

    def test_msg_with_empty_dict(self):
        logger = DummyJournalLogger()
        logger.msg({})

    def test_msg_with_large_dict(self):
        logger = DummyJournalLogger()
        logger.msg({f"KEY_{i}": f"value_{i}" for i in range(1000)})

    def test_msg_returns_none(self):
        logger = DummyJournalLogger()
        result = logger.msg({"MESSAGE": "test"})
        assert result is None

    def test_msg_with_special_values(self):
        logger = DummyJournalLogger()
        logger.msg({"MESSAGE": "null\x00byte", "PRIORITY": "\n"})
