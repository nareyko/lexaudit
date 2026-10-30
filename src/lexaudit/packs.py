"""Installable rule packs (MIT YAML bundles)."""

from __future__ import annotations

import os
import shutil
import zipfile
from pathlib import Path

import yaml


def packs_cache_dir() -> Path:
    override = os.environ.get("LEXAUDIT_PACK_DIR")
    if override:
        return Path(override)
    base = os.environ.get("XDG_CACHE_HOME") or str(Path.home() / ".cache")
    return Path(base) / "lexaudit" / "packs"


def bundled_packs_root() -> Path | None:
    here = Path(__file__).resolve()
    # Wheel layout: lexaudit/packs_data/<pack>
    wheel_data = here.parent / "packs_data"
    if wheel_data.is_dir():
        return wheel_data
    for parent in [here.parents[1], here.parents[2], here.parents[3]]:
        candidate = parent / "packs"
        if candidate.is_dir():
            return candidate
    return None


def list_packs() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    root = bundled_packs_root()
    if root is None:
        return rows
    for pack_dir in sorted(p for p in root.iterdir() if p.is_dir() and not p.name.startswith("_")):
        meta_path = pack_dir / "pack.yaml"
        if not meta_path.is_file():
            continue
        data = yaml.safe_load(meta_path.read_text(encoding="utf-8")) or {}
        if not isinstance(data, dict):
            continue
        rows.append(
            {
                "id": data.get("id") or pack_dir.name,
                "version": data.get("version"),
                "path": str(pack_dir),
                "license": data.get("license"),
                "locales": data.get("locales") or [],
            }
        )
    return rows


def install_pack(pack_id: str, *, dest: Path | None = None, force: bool = False) -> Path:
    """Copy a bundled pack into the user/project pack cache; return rules dir."""
    root = bundled_packs_root()
    if root is None:
        msg = "no bundled packs/ directory found"
        raise FileNotFoundError(msg)
    src = root / pack_id
    if not src.is_dir():
        # accept zip from dist/packs
        zip_path = root.parent / "dist" / "packs" / f"{pack_id}.zip"
        if zip_path.is_file():
            target = (dest or packs_cache_dir()) / pack_id
            if target.exists() and force:
                shutil.rmtree(target)
            target.mkdir(parents=True, exist_ok=True)
            with zipfile.ZipFile(zip_path) as zf:
                zf.extractall(target)
            return _rules_dir(target)
        msg = f"unknown pack {pack_id!r}; known: {[p['id'] for p in list_packs()]}"
        raise FileNotFoundError(msg)
    target = (dest or packs_cache_dir()) / pack_id
    if target.exists():
        if not force:
            return _rules_dir(target)
        shutil.rmtree(target)
    shutil.copytree(src, target)
    return _rules_dir(target)


def _rules_dir(pack_dir: Path) -> Path:
    meta_path = pack_dir / "pack.yaml"
    rules_subdir = "calques"
    if meta_path.is_file():
        data = yaml.safe_load(meta_path.read_text(encoding="utf-8")) or {}
        if isinstance(data, dict) and data.get("rules_dir"):
            rules_subdir = str(data["rules_dir"])
    path = pack_dir / rules_subdir
    if not path.is_dir():
        msg = f"pack {pack_dir} has no rules dir {rules_subdir}"
        raise FileNotFoundError(msg)
    return path


def verify_pack(pack_id: str, *, dest: Path | None = None) -> Path:
    path = (dest or packs_cache_dir()) / pack_id
    if not path.is_dir():
        msg = f"pack not installed: {pack_id}"
        raise FileNotFoundError(msg)
    return _rules_dir(path)
