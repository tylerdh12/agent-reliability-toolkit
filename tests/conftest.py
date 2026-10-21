"""Shared pytest config.

Every test in this suite exercises a live agent at AGENT_ENDPOINT. If it isn't
set (as in CI), the tests are marked ``live`` and skipped instead of failing on
"connection refused". Set AGENT_ENDPOINT (see ``make test``) to run them.
"""
import os

import pytest


def pytest_configure(config):
    config.addinivalue_line("markers", "live: needs a running agent at AGENT_ENDPOINT")


def pytest_collection_modifyitems(config, items):
    if os.getenv("AGENT_ENDPOINT"):
        return
    skip = pytest.mark.skip(reason="AGENT_ENDPOINT not set; live agent tests skipped")
    for item in items:
        item.add_marker("live")
        item.add_marker(skip)
