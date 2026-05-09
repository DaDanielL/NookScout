"""Scheduler entrypoint tests."""

import pytest

from app.jobs import scheduler


def test_scheduler_placeholder_exits_successfully(capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = scheduler.main()

    assert exit_code == 0
    assert "scheduler scaffold is ready" in capsys.readouterr().out
