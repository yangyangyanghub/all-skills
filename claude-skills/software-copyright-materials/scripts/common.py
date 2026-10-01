#!/usr/bin/env python3
"""Shared helpers for the software copyright materials skill."""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any, Iterable


EXCLUDE_DIRS = {
    ".git",
    ".hg",
    ".svn",
    ".idea",
    ".vscode",
    "__pycache__",
    "node_modules",
    "dist",
    "build",
    ".next",
    ".nuxt",
    ".output",
    "coverage",
    "target",
    "vendor",
    "软件著作权申请资料",
    "software-copyright-materials",
}

CODE_EXTS = {
    ".vue",
    ".ts",
    ".tsx",
    ".js",
    ".jsx",
    ".mjs",
    ".cjs",
    ".css",
    ".scss",
    ".sass",
    ".less",
    ".html",
    ".svelte",
    ".astro",
    ".json",
    ".md",
}

KNOWN_CONFIG_FILES = {
    ".babelrc",
    ".eslintrc",
    ".eslintrc.json",
    ".eslintrc.yaml",
    ".eslintrc.yml",
    ".prettierrc",
    ".prettierrc.json",
    ".prettierrc.yaml",
    ".prettierrc.yml",
    ".swcrc",
    "angular.json",
    "app.json",
    "astro.config.mjs",
    "astro.config.ts",
    "babel.config.js",
    "babel.config.json",
    "Cargo.lock",
    "Cargo.toml",
    "composer.json",
    "docker-compose.yaml",
    "docker-compose.yml",
    "eslint.config.cjs",
    "eslint.config.js",
    "eslint.config.mjs",
    "go.mod",
    "go.sum",
    "jsconfig.json",
    "lerna.json",
    "manifest.json",
    "next.config.js",
    "next.config.mjs",
    "next.config.ts",
    "nuxt.config.js",
    "nuxt.config.ts",
    "nx.json",
    "package-lock.json",
    "package.json",
    "playwright.config.js",
    "playwright.config.ts",
    "postcss.config.cjs",
    "postcss.config.js",
    "prettier.config.cjs",
    "prettier.config.js",
    "prettier.config.mjs",
    "project.json",
    "pyproject.toml",
    "rollup.config.js",
    "rollup.config.mjs",
    "rollup.config.ts",
    "svelte.config.js",
    "stylelintrc.json",
    "tailwind.config.js",
    "tailwind.config.ts",
    "tsconfig.app.json",
    "tsconfig.json",
    "tsconfig.node.json",
    "tslint.json",
    "turbo.json",
    "vite.config.js",
    "vite.config.mjs",
    "vite.config.ts",
    "vitest.config.js",
    "vitest.config.ts",
    "webpack.config.js",
    "webpack.config.ts",
    "workspace.json",
}

FRONTEND_EXTS = {
    ".vue",
    ".ts",
    ".tsx",
    ".js",
    ".jsx",
    ".mjs",
    ".css",
    ".scss",
    ".sass",
    ".less",
    ".html",
    ".svelte",
    ".astro",
}

SUPPLEMENT_CODE_EXTS = {
    ".py",
    ".java",
    ".go",
    ".rs",
    ".cs",
    ".php",
    ".rb",
    ".kt",
    ".swift",
    ".sql",
    ".sh",
    ".json",
}

COPYRIGHT_CODE_EXTS = FRONTEND_EXTS | SUPPLEMENT_CODE_EXTS

LOCK_FILES = {
    "package-lock.json",
    "pnpm-lock.yaml",
    "yarn.lock",
    "bun.lockb",
    "bun.lock",
}


def repo_root_from_script() -> Path:
    return Path(__file__).resolve().parents[3]


def is_excluded(path: Path) -> bool:
    parts = set(path.parts)
    if parts & EXCLUDE_DIRS:
        return True
    name = path.name
    if name.startswith(".") and name not in {".env.example"}:
        return True
    if name in LOCK_FILES:
        return True
    if name.endswith(".map") or name.endswith(".min.js") or name.endswith(".min.css"):
        return True
    return False


def iter_project_files(project: Path, exts: set[str] | None = None) -> Iterable[Path]:
    project = project.resolve()
    for root, dirs, files in os.walk(project):
        root_path = Path(root)
        dirs[:] = [d for d in dirs if not is_excluded(root_path / d)]
        for filename in files:
            path = root_path / filename
            if is_excluded(path):
                continue
            if exts is not None and path.suffix.lower() not in exts:
                continue
            yield path


def rel(path: Path, root: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


# 典型乱码字符集（UTF-8 字节被误按 GBK 解码产生的生僻字，用于检测与修复）
_GARBLED_CHARS = set("瀛楀吀鑴閬鏁鏋鏌鏉鏇鏆")


def _has_garbled_text(text: str) -> bool:
    """检测文本是否含乱码：损坏字符计数 或 可往返还原的乱码行数（双重编码特征）"""
    if sum(1 for c in text if c in _GARBLED_CHARS or _is_corrupt_char(c)) > 10:
        return True
    mojibake_lines = 0
    for line in text.splitlines():
        if any("\u4e00" <= c <= "\u9fff" for c in line) and _roundtrip_repair(line) is not None:
            mojibake_lines += 1
            if mojibake_lines > 3:
                return True
    return False


def _is_corrupt_char(c: str) -> bool:
    """判断字符是否为乱码/损坏字符（典型乱码集、PUA 私用区、替换符）"""
    if c in _GARBLED_CHARS:
        return True
    o = ord(c)
    return o == 0xFFFD or 0xE000 <= o <= 0xF8FF  # U+FFFD 与 PUA 私用区


def _is_clean_chinese_text(cand: str) -> bool:
    """修复结果必须只含 ASCII、CJK 汉字、CJK 标点、全角符号，且至少含一个汉字。

    这是防止误修复的关键闸门：合法短中文（如"状态""女"）的 GBK 字节虽可能构成
    合法 UTF-8，但还原结果是希伯来/希腊/组合符号等非 CJK 字符，会被本闸门拒绝，
    从而保留原行；真正的双重编码乱码还原后是正常中文，可通过闸门。
    """
    has_cjk = False
    for c in cand:
        o = ord(c)
        if o < 0x80:
            continue
        if 0x4E00 <= o <= 0x9FFF:
            has_cjk = True
            continue
        if 0x3000 <= o <= 0x303F or 0xFF00 <= o <= 0xFFEF:
            continue
        return False
    return has_cjk


def _roundtrip_repair(line: str) -> str | None:
    """尝试把一行按 GBK 编码回原始字节再按 UTF-8 解码；成功且结果为干净中文则返回。

    双重编码乱码的数学特征：乱码文本能完整通过 gbk→utf-8 往返并变成正常中文。
    验收闸门：结果必须全为 ASCII/CJK 且含汉字（防止把"状态"等合法短中文误修复）。
    """
    for enc in ("gbk", "gb18030"):
        try:
            candidate = line.encode(enc).decode("utf-8")
        except (UnicodeEncodeError, UnicodeDecodeError):
            continue
        if candidate != line and _is_clean_chinese_text(candidate) and not any(_is_corrupt_char(c) for c in candidate):
            return candidate
    return None


def _repair_run(part: str) -> str | None:
    """修复一个非 ASCII 段：整段往返 → 去损坏字符后往返 → 最长可修复前缀（覆盖率≥60%）。"""
    seg = _roundtrip_repair(part)
    if seg is not None:
        return seg
    cleaned = "".join(c for c in part if not _is_corrupt_char(c))
    if cleaned and cleaned != part:
        seg = _roundtrip_repair(cleaned)
        if seg is not None:
            return seg
    # 最长可修复前缀：丢失字节只影响段尾，前缀仍可还原；覆盖率不足则视为非乱码
    for i in range(len(part) - 1, 1, -1):
        seg = _roundtrip_repair(part[:i])
        if seg is not None:
            if i >= max(2, int(len(part) * 0.6)):
                return seg
            return None
    return None


def _repair_mojibake(text: str) -> str:
    """逐行修复双重编码乱码（UTF-8 字节被误按 GBK 解码后再存为 UTF-8）。

    触发条件：行内含损坏特征字符（乱码集/PUA/替换符），或整行/分段能通过 gbk→utf-8
    往返还原为干净中文。验收闸门 _is_clean_chinese_text 保证合法短中文（如"状态""女"）
    不会被误修复（其往返结果是希伯来/希腊字符，被闸门拒绝）。
    """
    out = []
    for line in text.split("\n"):
        has_corrupt = any(_is_corrupt_char(c) for c in line)
        if not has_corrupt and not any("\u4e00" <= c <= "\u9fff" for c in line):
            out.append(line)
            continue
        if not has_corrupt:
            fixed = _roundtrip_repair(line)
            if fixed is None and any("\u4e00" <= c <= "\u9fff" for c in line):
                # 整行往返失败（含丢失字节）：尝试分段前缀修复；合法中文段不会命中
                parts = re.split(r"([\x00-\x7f]+)", line)
                segs = []
                hit = False
                for part in parts:
                    if not part or all("\x00" <= c <= "\x7f" for c in part):
                        segs.append(part)
                        continue
                    seg = _repair_run(part)
                    if seg is not None:
                        hit = True
                    segs.append(seg if seg is not None else part)
                if hit:
                    fixed = "".join(segs)
            out.append(fixed if fixed is not None else line)
            continue
        fixed = _roundtrip_repair(line)
        if fixed is not None:
            out.append(fixed)
            continue
        # 整行失败：按 ASCII/非ASCII 分段，逐段修复；不可修复段取最长可修复前缀，最后才删除
        parts = re.split(r"([\x00-\x7f]+)", line)
        repaired_parts = []
        for part in parts:
            if not part or all("\x00" <= c <= "\x7f" for c in part):
                repaired_parts.append(part)
                continue
            seg = _repair_run(part)
            repaired_parts.append(seg if seg is not None else "")
        out.append("".join(repaired_parts))
    return "\n".join(out)


def read_text(path: Path, limit: int | None = None) -> str:
    data = path.read_bytes()
    if limit is not None:
        data = data[:limit]
    # 优先 UTF-8；解码成功但内容乱码时尝试修复双重编码
    for encoding in ("utf-8", "utf-8-sig"):
        try:
            text = data.decode(encoding)
        except UnicodeDecodeError:
            continue
        if _has_garbled_text(text):
            repaired = _repair_mojibake(text)
            if not _has_garbled_text(repaired):
                return repaired
            text = repaired  # 部分修复：残留乱码行由 should_skip_file 兜底
        return text
    # 尝试 GBK/GB18030
    for encoding in ("gb18030", "gbk"):
        try:
            text = data.decode(encoding)
            if not _has_garbled_text(text):
                return text
        except UnicodeDecodeError:
            continue
    # 兜底：UTF-8 替换模式
    return data.decode("utf-8", errors="replace")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(read_text(path))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def count_text_lines(path: Path, skip_blank: bool = True) -> int:
    try:
        text = read_text(path)
    except Exception:
        return 0
    if not text:
        return 0
    if skip_blank:
        return sum(1 for line in text.splitlines() if line.strip())
    return len(text.splitlines())


def is_known_config_file(path: Path) -> bool:
    """Return True for well-known config files that shouldn't count as source code."""
    return path.name in KNOWN_CONFIG_FILES


def looks_binary(path: Path) -> bool:
    try:
        chunk = path.read_bytes()[:4096]
    except Exception:
        return True
    return b"\x00" in chunk


def normalize_title(value: str) -> str:
    value = re.sub(r"[-_]+", " ", value).strip()
    value = re.sub(r"\s+", " ", value)
    return value or "待命名软件"


def safe_filename(value: str) -> str:
    value = re.sub(r'[\\/:*?"<>|]+', "_", value).strip()
    return value or "软件"


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def ensure_utf8() -> None:
    """强制当前进程与子进程使用 UTF-8，避免 Windows 默认 GBK 在解码/输出时抛 UnicodeDecodeError。

    在脚本入口调用一次即可：对标准流 reconfigure 为 utf-8，并为子进程设置 PYTHONIOENCODING。
    配合 subprocess.run(..., encoding="utf-8", errors="replace") 使用可彻底规避 GBK 解码崩溃。
    """
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")
    try:
        import sys

        for stream in (sys.stdout, sys.stderr):
            try:
                stream.reconfigure(encoding="utf-8")
            except Exception:
                pass
    except Exception:
        pass
