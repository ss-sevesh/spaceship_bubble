"""
conftest.py — pytest configuration for casimir_tools test suite.

Defines a 'slow' marker for tests that call full Matsubara summation
(casimir_energy_finite_T with large n_max).  These are skipped by default
in fast CI runs; include them with:

    pytest --run-slow        # run ALL tests including slow (local)
    pytest -m slow           # run only slow tests
    pytest                   # fast tests only — slow are skipped by default

Usage in tests:
    @pytest.mark.slow
    def test_matsubara_convergence():
        ...
"""

import pytest


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--run-slow",
        action="store_true",
        default=False,
        help="Include tests marked @pytest.mark.slow (Matsubara summation tests).",
    )


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line(
        "markers",
        "slow: marks tests that run full Matsubara summation (skipped in fast CI).",
    )


def pytest_collection_modifyitems(
    config: pytest.Config, items: list[pytest.Item]
) -> None:
    """Skip slow tests unless --run-slow is passed."""
    if config.getoption("--run-slow"):
        return   # --run-slow passed: run everything
    skip_slow = pytest.mark.skip(reason="Pass --run-slow to include Matsubara tests.")
    for item in items:
        if "slow" in item.keywords:
            item.add_marker(skip_slow)
