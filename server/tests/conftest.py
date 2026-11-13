"""Pytest fixtures shared by the backend suite."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from server.api import create_app  # noqa: E402
from server.mission import load_region  # noqa: E402

REGION_DIR = REPO_ROOT / "data" / "region"
FIXTURES_DIR = REPO_ROOT / "shared" / "fixtures"


@pytest.fixture(scope="session")
def repo_root() -> Path:
    return REPO_ROOT


@pytest.fixture(scope="session")
def region_dir() -> Path:
    if not (REGION_DIR / "manifest.json").exists():
        pytest.skip("data/region is not prepared; run server/preprocess.py --synthetic-fallback")
    return REGION_DIR


@pytest.fixture(scope="session")
def synthetic_region(region_dir: Path):
    return load_region(region_dir)


@pytest.fixture
def api_app(region_dir: Path):
    return create_app(data_dir=str(region_dir), plan_ttl_seconds=1800, plan_store_max=32)


@pytest.fixture
def client(api_app):
    with TestClient(api_app) as test_client:
        yield test_client


@pytest.fixture(scope="session")
def fixtures_dir() -> Path:
    return FIXTURES_DIR
