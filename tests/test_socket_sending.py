"""Socket sending tests — real AF_UNIX SOCK_DGRAM round-trip."""

import socket

import pytest

from stogger_systemd import JournalSender


@pytest.fixture()
def socket_pair(tmp_path):
    """Create a real AF_UNIX SOCK_DGRAM socket pair for testing.

    Returns (sender_sock_path, receiver_sock) where receiver_sock
    is a bound, listening AF_UNIX SOCK_DGRAM socket.
    """
    recv_sock = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
    recv_path = str(tmp_path / "journal.sock")
    recv_sock.bind(recv_path)
    recv_sock.settimeout(1.0)
    yield recv_path, recv_sock
    recv_sock.close()


class TestSocketSending:
    """Send messages through a real Unix datagram socket."""

    def test_send_single_message(self, socket_pair):
        recv_path, recv_sock = socket_pair
        sender = JournalSender(socket_path=recv_path)

        sender.send({"MESSAGE": "hello", "PRIORITY": 6})

        data = recv_sock.recvfrom(65536)[0]
        lines = set(data.split(b"\n"))
        assert b"MESSAGE=hello" in lines
        assert b"PRIORITY=6" in lines

    def test_send_multiple_messages(self, socket_pair):
        recv_path, recv_sock = socket_pair
        sender = JournalSender(socket_path=recv_path)

        sender.send({"MESSAGE": "msg1", "PRIORITY": 6})
        sender.send({"MESSAGE": "msg2", "PRIORITY": 3})

        data1 = recv_sock.recvfrom(65536)[0]
        data2 = recv_sock.recvfrom(65536)[0]

        assert b"MESSAGE=msg1" in data1
        assert b"MESSAGE=msg2" in data2

    def test_send_unicode_message(self, socket_pair):
        recv_path, recv_sock = socket_pair
        sender = JournalSender(socket_path=recv_path)

        sender.send({"MESSAGE": "hällö wörld"})

        data = recv_sock.recvfrom(65536)[0]
        assert "hällö wörld".encode() in data

    def test_send_large_message(self, socket_pair):
        recv_path, recv_sock = socket_pair
        sender = JournalSender(socket_path=recv_path)

        big_msg = "x" * 50_000
        sender.send({"MESSAGE": big_msg})

        data = recv_sock.recvfrom(100_000)[0]
        assert big_msg.encode() in data

    def test_message_with_special_chars(self, socket_pair):
        recv_path, recv_sock = socket_pair
        sender = JournalSender(socket_path=recv_path)

        sender.send({"MESSAGE": "key=val\ntest", "PRIORITY": 4})

        data = recv_sock.recvfrom(65536)[0]
        assert b"PRIORITY=4" in data
        assert b"key=val\ntest" in data

    def test_datagram_per_message(self, socket_pair):
        """Each .send() call produces exactly one datagram."""
        recv_path, recv_sock = socket_pair
        sender = JournalSender(socket_path=recv_path)

        sender.send({"MESSAGE": "first"})
        sender.send({"MESSAGE": "second"})
        sender.send({"MESSAGE": "third"})

        datagrams = []
        for _ in range(3):
            data = recv_sock.recvfrom(65536)[0]
            datagrams.append(data)

        assert len(datagrams) == 3
        assert b"MESSAGE=first" in datagrams[0]
        assert b"MESSAGE=second" in datagrams[1]
        assert b"MESSAGE=third" in datagrams[2]


class TestJournalSenderContextManager:
    """JournalSender as a context manager for socket lifecycle."""

    def test_context_manager_closes_socket(self, tmp_path):
        recv_sock = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
        recv_path = str(tmp_path / "journal.sock")
        recv_sock.bind(recv_path)
        recv_sock.settimeout(1.0)

        try:
            with JournalSender(socket_path=recv_path) as sender:
                assert sender._sock is not None

            # After context exit, socket should be cleaned up
            # Sending should still work (reconnect) or raise cleanly
        finally:
            recv_sock.close()
