"""Tests for Goose stream-json parser.

Test data matches real Goose 1.25 stream-json output where:
- Messages are nested under data["message"]
- Tool names are at toolCall.value.name
- Tool results are at toolResult.value.content
- Text messages stream per-token with the same id
"""

import json

import pytest

from orchestrator_worker.agents.goose_parser import parse_goose_event


class TestTextMessage:
    def test_single_text_content(self):
        """Real Goose format: content nested under data["message"]."""
        raw = json.dumps({
            "type": "message",
            "message": {
                "id": "chatcmpl-abc123",
                "role": "assistant",
                "created": 1700000000,
                "content": [
                    {"type": "text", "text": "Hello, I'll help you."}
                ],
                "metadata": {"userVisible": True, "agentVisible": True},
            },
        })
        events = parse_goose_event(raw)
        assert len(events) == 1
        e = events[0]
        assert e.type == "message"
        assert e.role == "assistant"
        assert e.content_type == "text"
        assert e.text == "Hello, I'll help you."
        assert e.id == "chatcmpl-abc123"
        assert e.created == 1700000000

    def test_per_token_streaming(self):
        """Goose streams text per-token with the same message id."""
        tokens = ["The", " file", " has", " been", " created"]
        events = []
        for token in tokens:
            raw = json.dumps({
                "type": "message",
                "message": {
                    "id": "chatcmpl-abc123",
                    "role": "assistant",
                    "created": 1700000000,
                    "content": [{"type": "text", "text": token}],
                },
            })
            events.extend(parse_goose_event(raw))
        assert len(events) == 5
        # All have the same id for UI-side merging
        assert all(e.id == "chatcmpl-abc123" for e in events)

    def test_multiple_text_content(self):
        raw = json.dumps({
            "type": "message",
            "message": {
                "role": "assistant",
                "content": [
                    {"type": "text", "text": "First part."},
                    {"type": "text", "text": "Second part."},
                ],
            },
        })
        events = parse_goose_event(raw)
        assert len(events) == 2
        assert events[0].text == "First part."
        assert events[1].text == "Second part."

    def test_message_id_falls_back_to_outer_id(self):
        """When content items have no id, use the message-level id."""
        raw = json.dumps({
            "type": "message",
            "message": {
                "id": "msg_001",
                "role": "assistant",
                "content": [
                    {"type": "text", "text": "Hello"}
                ],
            },
        })
        events = parse_goose_event(raw)
        assert events[0].id == "msg_001"


class TestToolCall:
    def test_tool_request_goose_format(self):
        """Real Goose format: name at toolCall.value.name."""
        raw = json.dumps({
            "type": "message",
            "message": {
                "id": "chatcmpl-abc123",
                "role": "assistant",
                "created": 1700000000,
                "content": [
                    {
                        "type": "toolRequest",
                        "id": "call_LZyWqeW98QyfRRCCzP2mmE4X",
                        "toolCall": {
                            "status": "success",
                            "value": {
                                "name": "developer__shell",
                                "arguments": {"command": "ls -la"},
                            },
                        },
                        "_meta": {"goose_extension": "developer"},
                    }
                ],
            },
        })
        events = parse_goose_event(raw)
        assert len(events) == 1
        e = events[0]
        assert e.type == "tool_call"
        assert e.id == "call_LZyWqeW98QyfRRCCzP2mmE4X"
        assert e.name == "developer__shell"
        assert e.arguments == {"command": "ls -la"}

    def test_tool_request_flat_format(self):
        """Compat: name directly at toolCall.name."""
        raw = json.dumps({
            "type": "message",
            "message": {
                "role": "assistant",
                "content": [
                    {
                        "type": "toolRequest",
                        "id": "toolu_001",
                        "toolCall": {
                            "name": "developer__shell",
                            "arguments": {"command": "ls"},
                        },
                    }
                ],
            },
        })
        events = parse_goose_event(raw)
        assert events[0].name == "developer__shell"


class TestToolResult:
    def test_tool_response_goose_format(self):
        """Real Goose format: result nested under toolResult.value.content."""
        raw = json.dumps({
            "type": "message",
            "message": {
                "id": "msg_abc",
                "role": "user",
                "created": 1700000000,
                "content": [
                    {
                        "type": "toolResponse",
                        "id": "call_LZyWqeW98QyfRRCCzP2mmE4X",
                        "toolResult": {
                            "status": "success",
                            "value": {
                                "content": [
                                    {"type": "text", "text": "file1.py\nfile2.py",
                                     "annotations": {"audience": ["assistant"]}},
                                    {"type": "text", "text": "file1.py\nfile2.py",
                                     "annotations": {"audience": ["user"], "priority": 0.0}},
                                ],
                                "isError": False,
                            },
                        },
                    }
                ],
            },
        })
        events = parse_goose_event(raw)
        assert len(events) == 1
        e = events[0]
        assert e.type == "tool_result"
        assert e.id == "call_LZyWqeW98QyfRRCCzP2mmE4X"
        assert e.status == "success"
        assert "file1.py" in e.output

    def test_tool_response_error(self):
        raw = json.dumps({
            "type": "message",
            "message": {
                "role": "user",
                "content": [
                    {
                        "type": "toolResponse",
                        "id": "toolu_002",
                        "toolResult": {
                            "status": "error",
                            "value": {
                                "content": [
                                    {"type": "text", "text": "command not found"}
                                ],
                                "isError": True,
                            },
                        },
                    }
                ],
            },
        })
        events = parse_goose_event(raw)
        assert len(events) == 1
        assert events[0].status == "error"
        assert events[0].output == "command not found"

    def test_tool_response_empty_text(self):
        """Real Goose sometimes returns empty text in tool results."""
        raw = json.dumps({
            "type": "message",
            "message": {
                "role": "user",
                "content": [
                    {
                        "type": "toolResponse",
                        "id": "call_abc",
                        "toolResult": {
                            "status": "success",
                            "value": {
                                "content": [
                                    {"type": "text", "text": "",
                                     "annotations": {"audience": ["assistant"]}},
                                    {"type": "text", "text": "",
                                     "annotations": {"audience": ["user"]}},
                                ],
                                "isError": False,
                            },
                        },
                    }
                ],
            },
        })
        events = parse_goose_event(raw)
        assert events[0].status == "success"
        assert events[0].output == ""

    def test_tool_response_flat_list_format(self):
        """Compat: toolResult as a flat list of content items."""
        raw = json.dumps({
            "type": "message",
            "message": {
                "role": "tool",
                "content": [
                    {
                        "type": "toolResponse",
                        "id": "toolu_001",
                        "toolResult": [
                            {"type": "text", "text": "file1.py\nfile2.py"}
                        ],
                    }
                ],
            },
        })
        events = parse_goose_event(raw)
        assert events[0].output == "file1.py\nfile2.py"


class TestNotification:
    def test_notification(self):
        raw = json.dumps({
            "type": "notification",
            "extension_id": "toolu_003",
            "message": "Building project...",
        })
        events = parse_goose_event(raw)
        assert len(events) == 1
        e = events[0]
        assert e.type == "notification"
        assert e.extension_id == "toolu_003"
        assert e.message == "Building project..."

    def test_notification_empty_message(self):
        """Real Goose sometimes emits notifications with empty message."""
        raw = json.dumps({
            "type": "notification",
            "extension_id": "call_abc123",
            "message": "",
            "created": 1700000000.0,
        })
        events = parse_goose_event(raw)
        assert len(events) == 1
        assert events[0].message == ""


class TestComplete:
    def test_complete_with_top_level_tokens(self):
        """Real Goose format: total_tokens at top level."""
        raw = json.dumps({
            "type": "complete",
            "total_tokens": 12847,
        })
        events = parse_goose_event(raw)
        assert len(events) == 1
        assert events[0].total_tokens == 12847

    def test_complete_with_usage_nested(self):
        """Also support total_tokens nested under usage for compat."""
        raw = json.dumps({
            "type": "complete",
            "usage": {"total_tokens": 5000},
        })
        events = parse_goose_event(raw)
        assert events[0].total_tokens == 5000

    def test_complete_with_null_tokens(self):
        """Real Goose sometimes emits null total_tokens."""
        raw = json.dumps({
            "type": "complete",
            "total_tokens": None,
        })
        events = parse_goose_event(raw)
        assert events[0].total_tokens is None

    def test_complete_without_tokens(self):
        raw = json.dumps({"type": "complete"})
        events = parse_goose_event(raw)
        assert events[0].total_tokens is None


class TestMixedMessage:
    def test_text_and_tool_call_in_one_message(self):
        raw = json.dumps({
            "type": "message",
            "message": {
                "role": "assistant",
                "content": [
                    {"type": "text", "text": "Let me check that."},
                    {
                        "type": "toolRequest",
                        "id": "toolu_001",
                        "toolCall": {
                            "status": "success",
                            "value": {
                                "name": "developer__read_file",
                                "arguments": {"path": "README.md"},
                            },
                        },
                    },
                ],
            },
        })
        events = parse_goose_event(raw)
        assert len(events) == 2
        assert events[0].type == "message"
        assert events[1].type == "tool_call"
        assert events[1].name == "developer__read_file"


class TestRealGooseOutput:
    """Tests using actual captured Goose 1.25 stream-json output."""

    def test_real_message(self):
        raw = '{"type":"message","message":{"id":null,"role":"assistant","created":1771715535,"content":[{"type":"text","text":"4"}],"metadata":{"userVisible":true,"agentVisible":true}}}'
        events = parse_goose_event(raw)
        assert len(events) == 1
        assert events[0].type == "message"
        assert events[0].text == "4"
        assert events[0].role == "assistant"

    def test_real_tool_call(self):
        raw = '{"type":"message","message":{"id":"chatcmpl-abc","role":"assistant","created":1771715822,"content":[{"type":"toolRequest","id":"call_LZy","toolCall":{"status":"success","value":{"name":"developer__shell","arguments":{"command":"ls"}}},"_meta":{"goose_extension":"developer"}}],"metadata":{"userVisible":true,"agentVisible":true}}}'
        events = parse_goose_event(raw)
        assert len(events) == 1
        assert events[0].type == "tool_call"
        assert events[0].name == "developer__shell"
        assert events[0].arguments == {"command": "ls"}

    def test_real_tool_result(self):
        raw = '{"type":"message","message":{"id":"msg_abc","role":"user","created":1771715822,"content":[{"type":"toolResponse","id":"call_LZy","toolResult":{"status":"success","value":{"content":[{"type":"text","text":"","annotations":{"audience":["assistant"]}},{"type":"text","text":"","annotations":{"audience":["user"],"priority":0.0}}],"isError":false}}}],"metadata":{"userVisible":true,"agentVisible":true}}}'
        events = parse_goose_event(raw)
        assert len(events) == 1
        assert events[0].type == "tool_result"
        assert events[0].status == "success"

    def test_real_complete(self):
        raw = '{"type":"complete","total_tokens":null}'
        events = parse_goose_event(raw)
        assert events[0].type == "complete"
        assert events[0].total_tokens is None


class TestEdgeCases:
    def test_unknown_type_returns_empty(self):
        raw = json.dumps({"type": "unknown_thing", "data": "foo"})
        events = parse_goose_event(raw)
        assert events == []

    def test_empty_content_array(self):
        raw = json.dumps({
            "type": "message",
            "message": {"role": "assistant", "content": []},
        })
        events = parse_goose_event(raw)
        assert events == []

    def test_invalid_json_raises(self):
        with pytest.raises(Exception):
            parse_goose_event("not json at all")

    def test_legacy_flat_format_still_works(self):
        """If message data is at top level (no nesting), still parse it."""
        raw = json.dumps({
            "type": "message",
            "role": "assistant",
            "content": [
                {"type": "text", "id": "msg_001", "text": "Hello"}
            ],
        })
        events = parse_goose_event(raw)
        assert len(events) == 1
        assert events[0].text == "Hello"


class TestAgentEventSerialization:
    def test_to_dict_drops_none(self):
        from orchestrator_worker.agents.events import AgentEvent

        e = AgentEvent(type="message", text="hello")
        d = e.to_dict()
        assert "text" in d
        assert "id" not in d
        assert "name" not in d

    def test_to_json_roundtrip(self):
        from orchestrator_worker.agents.events import AgentEvent

        e = AgentEvent(type="tool_call", id="t1", name="shell", arguments={"cmd": "ls"})
        j = e.to_json()
        parsed = json.loads(j)
        assert parsed["type"] == "tool_call"
        assert parsed["name"] == "shell"
        assert parsed["arguments"] == {"cmd": "ls"}
        assert "role" not in parsed  # None values dropped
