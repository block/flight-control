import pytest

from orchestrator_worker.log_streamer import LogStreamer


@pytest.mark.asyncio
async def test_add_line_buffers_with_sequence(mock_client):
    streamer = LogStreamer(mock_client, "run-1")

    await streamer.add_line("stdout", "line one")
    await streamer.add_line("stderr", "line two")

    assert len(streamer._buffer) == 2
    assert streamer._buffer[0] == {"stream": "stdout", "line": "line one", "sequence": 1}
    assert streamer._buffer[1] == {"stream": "stderr", "line": "line two", "sequence": 2}


@pytest.mark.asyncio
async def test_flush_sends_batch(mock_client):
    streamer = LogStreamer(mock_client, "run-1")

    await streamer.add_line("stdout", "hello")
    await streamer.add_line("stdout", "world")
    await streamer.flush()

    mock_client.post_logs.assert_called_once_with(
        "run-1",
        [
            {"stream": "stdout", "line": "hello", "sequence": 1},
            {"stream": "stdout", "line": "world", "sequence": 2},
        ],
    )
    assert len(streamer._buffer) == 0


@pytest.mark.asyncio
async def test_flush_empty_buffer_is_noop(mock_client):
    streamer = LogStreamer(mock_client, "run-1")

    await streamer.flush()

    mock_client.post_logs.assert_not_called()


@pytest.mark.asyncio
async def test_flush_failure_re_enqueues(mock_client):
    mock_client.post_logs.side_effect = Exception("network error")
    streamer = LogStreamer(mock_client, "run-1")

    await streamer.add_line("stdout", "important")
    await streamer.flush()

    # Lines should be back in the buffer
    assert len(streamer._buffer) == 1
    assert streamer._buffer[0]["line"] == "important"


@pytest.mark.asyncio
async def test_flush_failure_preserves_order(mock_client):
    call_count = 0

    async def fail_then_succeed(*args):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise Exception("transient failure")

    mock_client.post_logs.side_effect = fail_then_succeed
    streamer = LogStreamer(mock_client, "run-1")

    await streamer.add_line("stdout", "first")
    await streamer.flush()  # Fails, re-enqueues "first"

    await streamer.add_line("stdout", "second")
    await streamer.flush()  # Succeeds

    batch = mock_client.post_logs.call_args[0][1]
    assert batch[0]["line"] == "first"
    assert batch[1]["line"] == "second"
    assert batch[0]["sequence"] < batch[1]["sequence"]
