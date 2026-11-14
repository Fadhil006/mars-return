import hashlib

import pytest

from scripts.prepare_demo import fetch_verified


def test_download_checksums_and_preserves_existing_files(tmp_path):
    source = tmp_path / "source"
    source.write_bytes(b"synthetic source bytes")
    target = tmp_path / "raw/verified"
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    fetch_verified(source.as_uri(), target, digest)
    assert target.read_bytes() == source.read_bytes()
    fetch_verified(source.as_uri(), target, digest)
    with pytest.raises(ValueError, match="existing"):
        fetch_verified(source.as_uri(), target, "0"*64)
    assert target.read_bytes() == source.read_bytes()


def test_failed_download_never_becomes_source(tmp_path):
    source = tmp_path / "source"
    source.write_bytes(b"synthetic")
    target = tmp_path / "raw/verified"
    with pytest.raises(ValueError, match="Downloaded"):
        fetch_verified(source.as_uri(), target, "0"*64)
    assert not target.exists()
    assert not list(target.parent.iterdir())
