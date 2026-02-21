import pytest

from orchestrator.models.job_run import JobRun
from orchestrator.models.worker import Worker
from orchestrator.services.worker_service import labels_match, poll_for_job


# ---------------------------------------------------------------------------
# Unit tests for labels_match (pure function, no DB needed)
# ---------------------------------------------------------------------------

class TestLabelsMatch:
    def test_no_requirements_matches_any_worker(self):
        assert labels_match(None, {"gpu": "true"}) is True
        assert labels_match({}, {"gpu": "true"}) is True
        assert labels_match(None, None) is True
        assert labels_match({}, {}) is True

    def test_requirements_with_no_worker_labels_fails(self):
        assert labels_match({"gpu": "true"}, None) is False
        assert labels_match({"gpu": "true"}, {}) is False

    def test_exact_match(self):
        assert labels_match({"gpu": "true"}, {"gpu": "true"}) is True

    def test_subset_match(self):
        assert labels_match(
            {"gpu": "true"},
            {"gpu": "true", "region": "us-east"},
        ) is True

    def test_missing_label_fails(self):
        assert labels_match(
            {"gpu": "true", "region": "us-east"},
            {"gpu": "true"},
        ) is False

    def test_wrong_value_fails(self):
        assert labels_match({"gpu": "true"}, {"gpu": "false"}) is False

    def test_multiple_requirements_all_must_match(self):
        required = {"gpu": "true", "region": "us-east"}
        assert labels_match(required, {"gpu": "true", "region": "us-east"}) is True
        assert labels_match(required, {"gpu": "true", "region": "us-west"}) is False


# ---------------------------------------------------------------------------
# Integration tests for poll_for_job label routing
# ---------------------------------------------------------------------------

async def _create_worker(db, name, labels=None, workspace_id="default"):
    worker = Worker(workspace_id=workspace_id, name=name, labels=labels or {})
    db.add(worker)
    await db.commit()
    await db.refresh(worker)
    return worker


async def _create_run(db, name="test-job", required_labels=None, workspace_id="default"):
    run = JobRun(
        workspace_id=workspace_id,
        name=name,
        task_prompt="do something",
        agent_type="goose",
        required_labels=required_labels,
    )
    db.add(run)
    await db.commit()
    await db.refresh(run)
    return run


class TestPollForJobRouting:
    @pytest.mark.asyncio
    async def test_unlabeled_run_matches_any_worker(self, db):
        worker = await _create_worker(db, "worker-1")
        run = await _create_run(db, required_labels=None)

        result = await poll_for_job(db, worker.id)

        assert result is not None
        assert result.run_id == run.id

    @pytest.mark.asyncio
    async def test_labeled_run_matches_labeled_worker(self, db):
        worker = await _create_worker(db, "gpu-worker", labels={"gpu": "true"})
        run = await _create_run(db, required_labels={"gpu": "true"})

        result = await poll_for_job(db, worker.id)

        assert result is not None
        assert result.run_id == run.id

    @pytest.mark.asyncio
    async def test_labeled_run_skipped_by_wrong_worker(self, db):
        worker = await _create_worker(db, "cpu-worker", labels={"gpu": "false"})
        await _create_run(db, required_labels={"gpu": "true"})

        result = await poll_for_job(db, worker.id)

        assert result is None

    @pytest.mark.asyncio
    async def test_worker_gets_first_matching_run(self, db):
        """When multiple runs are queued, worker gets the oldest one it matches."""
        worker = await _create_worker(db, "gpu-worker", labels={"gpu": "true"})

        # First run requires a label this worker doesn't have
        await _create_run(db, name="needs-tpu", required_labels={"tpu": "true"})
        # Second run matches
        matching_run = await _create_run(db, name="needs-gpu", required_labels={"gpu": "true"})

        result = await poll_for_job(db, worker.id)

        assert result is not None
        assert result.run_id == matching_run.id

    @pytest.mark.asyncio
    async def test_unlabeled_worker_gets_unlabeled_run(self, db):
        """A worker with no labels can pick up runs with no label requirements."""
        worker = await _create_worker(db, "plain-worker", labels={})

        # Labeled run — should be skipped
        await _create_run(db, name="gpu-job", required_labels={"gpu": "true"})
        # Unlabeled run — should match
        unlabeled_run = await _create_run(db, name="simple-job", required_labels=None)

        result = await poll_for_job(db, worker.id)

        assert result is not None
        assert result.run_id == unlabeled_run.id

    @pytest.mark.asyncio
    async def test_assigned_run_not_picked_up_again(self, db):
        """Once a run is assigned, another worker shouldn't get it."""
        worker1 = await _create_worker(db, "worker-1")
        worker2 = await _create_worker(db, "worker-2")
        await _create_run(db, required_labels=None)

        result1 = await poll_for_job(db, worker1.id)
        assert result1 is not None

        result2 = await poll_for_job(db, worker2.id)
        assert result2 is None

    @pytest.mark.asyncio
    async def test_unknown_worker_returns_none(self, db):
        await _create_run(db, required_labels=None)
        result = await poll_for_job(db, "nonexistent-worker-id")
        assert result is None

    @pytest.mark.asyncio
    async def test_worker_only_polls_own_workspace(self, db):
        """Workers should only pick up runs from their own workspace."""
        worker = await _create_worker(db, "ws1-worker", workspace_id="default")
        # Run in a different workspace
        await _create_run(db, name="other-ws-job", workspace_id="other-ws")

        result = await poll_for_job(db, worker.id)
        assert result is None

    @pytest.mark.asyncio
    async def test_worker_picks_up_own_workspace_run(self, db):
        """Workers should pick up runs from their own workspace."""
        worker = await _create_worker(db, "ws1-worker", workspace_id="default")
        run = await _create_run(db, name="same-ws-job", workspace_id="default")

        result = await poll_for_job(db, worker.id)
        assert result is not None
        assert result.run_id == run.id
