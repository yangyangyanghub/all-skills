"""Discover and cache installed CAD COM ProgIDs on Windows."""

from __future__ import annotations

import json
import logging
import os
import re
import threading
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Protocol, Sequence

import winreg


logger = logging.getLogger(__name__)


CAD_PROG_ID_BASES: Dict[str, Sequence[str]] = {
    "autocad": ("AutoCAD.Application",),
    "zwcad": ("ZWCAD.Application",),
    "bricscad": ("BricscadApp.AcadApplication",),
    "gcad": ("GCAD.Application",),
}


@dataclass(frozen=True)
class ProgIdCandidate:
    """A registered or configured COM ProgID and how it was discovered."""

    prog_id: str
    source: str

    def to_dict(self) -> Dict[str, str]:
        return asdict(self)


class RegistryProgIdSource(Protocol):
    """Registry operations used by :class:`ProgIdResolver`."""

    def get_cur_ver(self, base_prog_id: str) -> Optional[str]: ...

    def find_registered(self, base_prog_ids: Sequence[str]) -> List[str]: ...


class WindowsRegistryProgIdSource:
    """Read the ProgIDs that are actually registered in HKCR."""

    _root_keys: Optional[List[str]] = None
    _lock = threading.Lock()

    def get_cur_ver(self, base_prog_id: str) -> Optional[str]:
        try:
            with winreg.OpenKey(
                winreg.HKEY_CLASSES_ROOT, f"{base_prog_id}\\CurVer"
            ) as key:
                value, _ = winreg.QueryValueEx(key, None)
                return str(value).strip() or None
        except OSError:
            return None

    @classmethod
    def _get_root_keys(cls) -> List[str]:
        with cls._lock:
            if cls._root_keys is not None:
                return cls._root_keys

            keys: List[str] = []
            index = 0
            while True:
                try:
                    keys.append(winreg.EnumKey(winreg.HKEY_CLASSES_ROOT, index))
                    index += 1
                except OSError:
                    break

            cls._root_keys = keys
            return keys

    def find_registered(self, base_prog_ids: Sequence[str]) -> List[str]:
        normalized_bases = tuple(base.casefold() for base in base_prog_ids)
        matches = []
        for key_name in self._get_root_keys():
            normalized = key_name.casefold()
            if any(
                normalized == base or normalized.startswith(f"{base}.")
                for base in normalized_bases
            ):
                matches.append(key_name)
        return matches


def _default_cache_path() -> Path:
    settings_dir = Path(__file__).resolve().parents[4]
    return settings_dir / "UserData" / "AutoCADMCP" / "connection_cache.json"


def _version_sort_key(prog_id: str) -> tuple:
    numeric_suffix = re.search(r"(?:\.(\d+))+$", prog_id)
    if numeric_suffix is None:
        return (0, ())
    numbers = tuple(int(value) for value in re.findall(r"\d+", numeric_suffix.group(0)))
    return (1, numbers)


class ProgIdResolver:
    """Resolve finite CAD ProgID candidates from config, registry, and cache."""

    def __init__(
        self,
        cache_path: Optional[Path] = None,
        registry: Optional[RegistryProgIdSource] = None,
    ) -> None:
        self.cache_path = cache_path or _default_cache_path()
        self.registry = registry or WindowsRegistryProgIdSource()
        self._cache_lock = threading.Lock()

    def discover(
        self, cad_type: str, configured_prog_id: str
    ) -> List[ProgIdCandidate]:
        """Return unique candidates, prioritizing verified and registered values."""
        normalized_cad_type = cad_type.casefold()
        bases = list(CAD_PROG_ID_BASES.get(normalized_cad_type, ()))
        if configured_prog_id and not any(
            configured_prog_id.casefold() == base.casefold() for base in bases
        ):
            bases.append(configured_prog_id)

        candidates: List[ProgIdCandidate] = []
        cached = self.get_cached(normalized_cad_type)
        if cached:
            candidates.append(ProgIdCandidate(cached, "cache"))

        for base in bases:
            cur_ver = self.registry.get_cur_ver(base)
            if cur_ver:
                candidates.append(ProgIdCandidate(cur_ver, "curver"))

        registered = self.registry.find_registered(bases)
        for prog_id in sorted(registered, key=_version_sort_key, reverse=True):
            candidates.append(ProgIdCandidate(prog_id, "registry"))

        if configured_prog_id:
            candidates.append(ProgIdCandidate(configured_prog_id, "config"))

        return self._deduplicate(candidates)

    @staticmethod
    def _deduplicate(
        candidates: Iterable[ProgIdCandidate],
    ) -> List[ProgIdCandidate]:
        unique: List[ProgIdCandidate] = []
        seen = set()
        for candidate in candidates:
            key = candidate.prog_id.casefold()
            if not candidate.prog_id or key in seen:
                continue
            seen.add(key)
            unique.append(candidate)
        return unique

    def get_cached(self, cad_type: str) -> Optional[str]:
        with self._cache_lock:
            data = self._read_cache()
        entry = data.get("connections", {}).get(cad_type.casefold(), {})
        prog_id = entry.get("prog_id") if isinstance(entry, dict) else None
        return str(prog_id) if prog_id else None

    def remember(self, cad_type: str, prog_id: str) -> None:
        if not prog_id:
            return
        with self._cache_lock:
            data = self._read_cache()
            connections = data.setdefault("connections", {})
            connections[cad_type.casefold()] = {
                "prog_id": prog_id,
                "verified_at": datetime.now(timezone.utc).isoformat(),
            }
            self._write_cache(data)

    def forget(self, cad_type: str, expected_prog_id: Optional[str] = None) -> None:
        with self._cache_lock:
            data = self._read_cache()
            connections = data.setdefault("connections", {})
            entry = connections.get(cad_type.casefold())
            if not isinstance(entry, dict):
                return
            if expected_prog_id and str(entry.get("prog_id", "")).casefold() != (
                expected_prog_id.casefold()
            ):
                return
            del connections[cad_type.casefold()]
            self._write_cache(data)

    def _read_cache(self) -> Dict[str, object]:
        try:
            with self.cache_path.open("r", encoding="utf-8") as cache_file:
                data = json.load(cache_file)
            if isinstance(data, dict):
                data.setdefault("version", 1)
                if not isinstance(data.get("connections"), dict):
                    data["connections"] = {}
                return data
        except (OSError, json.JSONDecodeError, TypeError, ValueError) as exc:
            logger.debug("Unable to read CAD connection cache: %s", exc)
        return {"version": 1, "connections": {}}

    def _write_cache(self, data: Dict[str, object]) -> None:
        try:
            self.cache_path.parent.mkdir(parents=True, exist_ok=True)
            temporary_path = self.cache_path.with_suffix(
                f"{self.cache_path.suffix}.{os.getpid()}.tmp"
            )
            with temporary_path.open("w", encoding="utf-8", newline="\n") as file:
                json.dump(data, file, ensure_ascii=False, indent=2)
                file.write("\n")
            os.replace(temporary_path, self.cache_path)
        except OSError as exc:
            logger.warning("Unable to write CAD connection cache: %s", exc)


_resolver = ProgIdResolver()


def get_prog_id_resolver() -> ProgIdResolver:
    return _resolver
