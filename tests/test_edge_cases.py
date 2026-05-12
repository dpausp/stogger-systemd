"""Edge case tests — graceful degradation and error handling."""

import socket

from stogger_systemd import JournalSender


class TestSocketDoesNotExist:
    """Graceful degradation when socket doesn't exist."""

    def test_send_does_not_raise_on_missing_socket(self, tmp_path):
        sender = JournalSender(socket_path=str(tmp_path / "nope.sock"))
        # Should not raise — graceful degradation
        sender.send({"MESSAGE": "test"})

    def test_send_returns_false_on_failure(self, tmp_path):
        sender = JournalSender(socket_path=str(tmp_path / "nope.sock"))
        result = sender.send({"MESSAGE": "test"})
        assert result is False


class TestSocketSendFailure:
    """Handling send failures (e.g., permission denied, buffer full)."""

    def test_send_to_readonly_socket_graceful(self, tmp_path):
        """Send to a socket that doesn't accept datagrams gracefully."""
        # Create a socket and immediately close it so send fails
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
        sock_path = str(tmp_path / "closed.sock")
        sock.bind(sock_path)
        sock.close()

        sender = JournalSender(socket_path=sock_path)
        # Should not raise
        sender.send({"MESSAGE": "test"})


class TestVeryLargeMessages:
    """Large message handling."""

    def test_very_large_single_value(self, tmp_path):
        """Single field with a very large value."""
        recv_sock = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
        recv_path = str(tmp_path / "journal.sock")
        recv_sock.bind(recv_path)
        recv_sock.settimeout(1.0)

        try:
            sender = JournalSender(socket_path=recv_path)
            big = "A" * 100_000
            sender.send({"MESSAGE": big})
            # Datagram may be truncated by OS, but send should not crash
        finally:
            recv_sock.close()

    def test_many_fields(self, tmp_path):
        """Many fields in a single message."""
        recv_sock = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
        recv_path = str(tmp_path / "journal.sock")
        recv_sock.bind(recv_path)
        recv_sock.settimeout(1.0)

        try:
            sender = JournalSender(socket_path=recv_path)
            fields = {f"FIELD_{i:04d}": f"value_{i}" for i in range(100)}
            fields["MESSAGE"] = "many fields"
            sender.send({"MESSAGE": "many fields", **fields})

            data = recv_sock.recvfrom(65536)[0]
            assert b"MESSAGE=many fields" in data
        finally:
            recv_sock.close()


class TestMinimalMessage:
    """Messages with minimal fields."""

    def test_message_only(self, tmp_path):
        """Message with only MESSAGE key."""
        recv_sock = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
        recv_path = str(tmp_path / "journal.sock")
        recv_sock.bind(recv_path)
        recv_sock.settimeout(1.0)

        try:
            sender = JournalSender(socket_path=recv_path)
            sender.send({"MESSAGE": "just a message"})

            data = recv_sock.recvfrom(65536)[0]
            assert data == b"MESSAGE=just a message\n"
        finally:
            recv_sock.close()

    def test_empty_message_value(self, tmp_path):
        """Message with empty string value."""
        recv_sock = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
        recv_path = str(tmp_path / "journal.sock")
        recv_sock.bind(recv_path)
        recv_sock.settimeout(1.0)

        try:
            sender = JournalSender(socket_path=recv_path)
            sender.send({"MESSAGE": ""})

            data = recv_sock.recvfrom(65536)[0]
            assert data == b"MESSAGE=\n"
        finally:
            recv_sock.close()
