"""Wire format tests — JournalSender message formatting."""

from stogger_systemd import JournalSender


class TestFormatSimpleValues:
    """Simple string and integer values."""

    def test_single_string_field(self):
        result = JournalSender.format_message({"MESSAGE": "hello world"})
        assert result == b"MESSAGE=hello world\n"

    def test_single_integer_field(self):
        result = JournalSender.format_message({"PRIORITY": 6})
        assert result == b"PRIORITY=6\n"

    def test_multi_field_message(self):
        fields = {
            "MESSAGE": "test message",
            "PRIORITY": 6,
            "SYSLOG_IDENTIFIER": "myapp",
        }
        result = JournalSender.format_message(fields)
        lines = result.split(b"\n")
        # 3 fields + trailing empty string from final \n
        assert len(lines) == 4
        assert b"MESSAGE=test message" in lines
        assert b"PRIORITY=6" in lines
        assert b"SYSLOG_IDENTIFIER=myapp" in lines

    def test_code_line_and_file(self):
        fields = {
            "MESSAGE": "error occurred",
            "PRIORITY": 3,
            "CODE_FILE": "app.py",
            "CODE_LINE": 42,
            "CODE_FUNC": "main",
        }
        result = JournalSender.format_message(fields)
        lines = set(result.split(b"\n"))
        assert b"CODE_FILE=app.py" in lines
        assert b"CODE_LINE=42" in lines
        assert b"CODE_FUNC=main" in lines


class TestFormatSpecialValues:
    """Values with special characters."""

    def test_value_with_newline(self):
        result = JournalSender.format_message({"MESSAGE": "line1\nline2"})
        assert b"MESSAGE=line1\nline2" in result

    def test_value_with_equals_sign(self):
        result = JournalSender.format_message({"MESSAGE": "key=value"})
        assert b"MESSAGE=key=value" in result

    def test_value_with_unicode(self):
        result = JournalSender.format_message({"MESSAGE": "hällö wörld \u2603"})
        assert "hällö wörld \u2603".encode() in result

    def test_empty_value(self):
        result = JournalSender.format_message({"MESSAGE": ""})
        assert result == b"MESSAGE=\n"

    def test_value_with_special_chars_combined(self):
        result = JournalSender.format_message({"MESSAGE": "err=1\nstack=trace\u2713"})
        assert "err=1\nstack=trace\u2713".encode() in result


class TestFormatBinarySafe:
    """Binary-safe handling — values that contain null bytes or raw bytes."""

    def test_value_with_null_byte(self):
        result = JournalSender.format_message({"MESSAGE": "before\x00after"})
        assert b"before\x00after" in result

    def test_all_fields_stripping_newlines_from_values(self):
        """Embedded newlines in values are preserved as-is.

        The wire format is KEY=VALUE\n — values containing newlines will
        produce multiple lines, but the payload is correct for the journal
        protocol which uses separate iov entries per field. This test verifies
        that both field key-value pairs appear in the output.
        """
        fields = {
            "MESSAGE": "multi\nline",
            "PRIORITY": 4,
        }
        result = JournalSender.format_message(fields)
        assert b"MESSAGE=multi\nline\n" in result
        assert b"PRIORITY=4\n" in result


class TestFormatEdgeCases:
    """Edge cases in formatting."""

    def test_single_field_only_message(self):
        result = JournalSender.format_message({"MESSAGE": "hello"})
        assert result == b"MESSAGE=hello\n"
        assert result.rstrip(b"\n") == b"MESSAGE=hello"

    def test_empty_dict(self):
        result = JournalSender.format_message({})
        assert result == b""

    def test_value_is_bool_true(self):
        result = JournalSender.format_message({"ENABLED": True})
        assert result == b"ENABLED=True\n"

    def test_value_is_bool_false(self):
        result = JournalSender.format_message({"ENABLED": False})
        assert result == b"ENABLED=False\n"

    def test_value_is_float(self):
        result = JournalSender.format_message({"DURATION": 1.5})
        assert result == b"DURATION=1.5\n"

    def test_large_message(self):
        big_val = "x" * 100_000
        result = JournalSender.format_message({"MESSAGE": big_val})
        assert result == f"MESSAGE={big_val}\n".encode()
