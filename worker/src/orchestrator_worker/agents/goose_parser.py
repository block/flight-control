"""Parse Goose stream-json output into normalized AgentEvents.

Goose 1.x stream-json format:
  {"type": "message", "message": {"role": "...", "content": [...]}}
  {"type": "notification", "extension_id": "...", "message": "..."}
  {"type": "complete", "total_tokens": N}

Tool calls nest name/arguments under toolCall.value:
  {"type": "toolRequest", "id": "...", "toolCall": {"status": "success",
    "value": {"name": "developer__shell", "arguments": {"command": "ls"}}}}

Tool results nest content under toolResult.value.content or toolResult.status:
  {"type": "toolResponse", "id": "...", "toolResult": {"status": "success",
    "value": {"content": [...], "isError": false}}}

Text messages stream per-token with the same id — merging is done UI-side.
"""

import json
import time

from orchestrator_worker.agents.events import AgentEvent


def parse_goose_event(raw_json: str) -> list[AgentEvent]:
    """Parse a single Goose stream-json line into one or more AgentEvents.

    A single message can have multiple content items, so we return a list.
    """
    data = json.loads(raw_json)
    msg_type = data.get("type")
    now = time.time()

    if msg_type == "message":
        return _parse_message(data, now)
    elif msg_type == "notification":
        return [_parse_notification(data, now)]
    elif msg_type == "complete":
        return [_parse_complete(data, now)]
    else:
        return []


def _parse_message(data: dict, now: float) -> list[AgentEvent]:
    """Parse a Goose message with its content array."""
    events = []

    # Goose nests the message payload; fall back to top-level for compat
    msg = data.get("message", data)
    role = msg.get("role", "assistant")
    created = msg.get("created", data.get("created", now))

    for item in msg.get("content", []):
        content_type = item.get("type")

        if content_type == "text":
            events.append(
                AgentEvent(
                    type="message",
                    id=item.get("id") or msg.get("id"),
                    role=role,
                    content_type="text",
                    text=item.get("text", ""),
                    created=created,
                )
            )
        elif content_type == "toolRequest":
            tool_call = item.get("toolCall", {})
            # Goose nests under toolCall.value.{name, arguments}
            value = tool_call.get("value", tool_call)
            events.append(
                AgentEvent(
                    type="tool_call",
                    id=item.get("id"),
                    name=value.get("name", "unknown"),
                    arguments=value.get("arguments"),
                    created=created,
                )
            )
        elif content_type == "toolResponse":
            tool_result = item.get("toolResult", {})
            output_parts = []
            is_error = False

            if isinstance(tool_result, dict):
                # Goose nests under toolResult.value.content
                value = tool_result.get("value", tool_result)
                is_error = value.get("isError", False)
                content = value.get("content", [])
                if isinstance(content, list):
                    for part in content:
                        if isinstance(part, dict) and part.get("type") == "text":
                            text = part.get("text", "")
                            if text:
                                output_parts.append(text)
                elif not content and tool_result.get("text"):
                    output_parts.append(tool_result["text"])
            elif isinstance(tool_result, list):
                for part in tool_result:
                    if isinstance(part, dict) and part.get("type") == "text":
                        output_parts.append(part.get("text", ""))
                    elif isinstance(part, str):
                        output_parts.append(part)

            # Also check isError at item level
            if item.get("isError"):
                is_error = True

            events.append(
                AgentEvent(
                    type="tool_result",
                    id=item.get("id"),
                    status="error" if is_error else "success",
                    output="\n".join(output_parts),
                    created=created,
                )
            )

    return events


def _parse_notification(data: dict, now: float) -> AgentEvent:
    return AgentEvent(
        type="notification",
        extension_id=data.get("extension_id"),
        message=data.get("message", ""),
        created=data.get("created", now),
    )


def _parse_complete(data: dict, now: float) -> AgentEvent:
    # Goose puts total_tokens at top level; also check under "usage" for compat
    total_tokens = data.get("total_tokens")
    if total_tokens is None:
        total_tokens = data.get("usage", {}).get("total_tokens")
    return AgentEvent(
        type="complete",
        total_tokens=total_tokens,
        created=data.get("created", now),
    )
