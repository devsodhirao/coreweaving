import hashlib
import json
import runpy
import shutil
import stat
import subprocess
import sys
import zipfile
from pathlib import Path

import pytest

from coreweaving.corpus import Corpus

ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = "weave-snapshot-4db7c17b2869.zip"


def test_locked_setup_restores_the_original_corpus_without_network(tmp_path):
    destination = tmp_path / "data/docs"
    destination.mkdir(parents=True)
    (tmp_path / "scripts").mkdir()
    shutil.copyfile(ROOT / "scripts/fetch_docs.py", tmp_path / "scripts/fetch_docs.py")
    for name in ("manifest.json", ARCHIVE):
        shutil.copyfile(ROOT / "data/docs" / name, destination / name)
    manifest_bytes = (destination / "manifest.json").read_bytes()
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "import runpy, socket, sys\n"
            "def offline(*args, **kwargs):\n"
            "    raise AssertionError('Locked setup must not use the network')\n"
            "socket.socket.connect = offline\n"
            "sys.argv = ['scripts/fetch_docs.py', '--locked', '--weave-only']\n"
            "runpy.run_path(sys.argv[0], run_name='__main__')\n",
        ],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "351 pages; 0 failures" in result.stdout
    assert (destination / "manifest.json").read_bytes() == manifest_bytes
    corpus = Corpus(destination)
    assert len(corpus.pages) == 351
    assert corpus.snapshot_id == "4db7c17b28698bcc2680da22d687f7c4783ecf5e5255e16177b9197e56da14b4"


@pytest.fixture
def restore(tmp_path, monkeypatch):
    function = runpy.run_path(str(ROOT / "scripts/fetch_docs.py"))["restore_locked_weave"]
    destination = tmp_path / "docs"
    destination.mkdir()
    monkeypatch.setitem(function.__globals__, "DESTINATION", destination)
    return function, destination


def test_corrupt_distributed_archive_is_rejected_before_writes(restore, monkeypatch):
    function, destination = restore
    archive = destination / ARCHIVE
    archive.write_bytes((ROOT / "data/docs" / ARCHIVE).read_bytes() + b"corruption")
    monkeypatch.setitem(function.__globals__, "SNAPSHOT_ARCHIVE", archive)
    pages = json.loads((ROOT / "data/docs/manifest.json").read_text())["pages"]
    with pytest.raises(ValueError, match="checksum mismatch"):
        function([page for page in pages if page["collection"] == "weave"])
    assert not (destination / "weave").exists()


@pytest.mark.parametrize(
    ("name", "mode", "content", "size", "digest", "message"),
    [
        ("../escape.md", stat.S_IFREG, b"page", 4, "valid", "Unsafe"),
        ("/tmp/escape.md", stat.S_IFREG, b"page", 4, "valid", "Unsafe"),
        ("weave/page.md", stat.S_IFLNK, b"page", 4, "valid", "Unsafe"),
        ("weave/page.md", stat.S_IFREG, b"page", 5, "valid", "size mismatch"),
        ("weave/page.md", stat.S_IFREG, b"page", 4, "wrong", "page hash mismatch"),
    ],
)
def test_archive_members_are_validated_before_writes(
    restore, monkeypatch, name, mode, content, size, digest, message
):
    function, destination = restore
    archive = destination / ARCHIVE
    member = zipfile.ZipInfo(name)
    member.external_attr = (mode | 0o644) << 16
    with zipfile.ZipFile(archive, "w") as bundle:
        bundle.writestr(member, content)
    monkeypatch.setitem(function.__globals__, "SNAPSHOT_ARCHIVE", archive)
    monkeypatch.setitem(
        function.__globals__,
        "SNAPSHOT_ARCHIVE_SHA256",
        hashlib.sha256(archive.read_bytes()).hexdigest(),
    )
    page = {
        "file": name,
        "bytes": size,
        "sha256": hashlib.sha256(content).hexdigest() if digest == "valid" else digest,
    }
    with pytest.raises(ValueError, match=message):
        function([page])
    assert list(destination.iterdir()) == [archive]


def test_unlisted_member_is_rejected(restore):
    function, destination = restore
    pages = json.loads((ROOT / "data/docs/manifest.json").read_text())["pages"]
    with pytest.raises(ValueError, match="members do not match"):
        function([page for page in pages if page["collection"] == "weave"][1:])
    assert not list(destination.iterdir())


@pytest.mark.parametrize("link_kind", ["root", "directory", "file"])
def test_restore_rejects_destination_symlinks(restore, tmp_path, link_kind):
    function, destination = restore
    outside = tmp_path / "outside"
    outside.mkdir()
    pages = [
        page
        for page in json.loads((ROOT / "data/docs/manifest.json").read_text())["pages"]
        if page["collection"] == "weave"
    ]
    if link_kind == "root":
        destination.rmdir()
        destination.symlink_to(outside, target_is_directory=True)
    elif link_kind == "directory":
        (destination / "weave").symlink_to(outside, target_is_directory=True)
    else:
        (destination / "weave").mkdir()
        (destination / pages[0]["file"]).symlink_to(outside / "page.md")
    with pytest.raises(ValueError, match="must not be a symlink"):
        function(pages)
    assert not list(outside.iterdir())
