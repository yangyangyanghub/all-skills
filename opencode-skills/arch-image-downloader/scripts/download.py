#!/usr/bin/env python3
"""Architecture image downloader for ArchDaily, Gooood, and Archiposition.

Downloads high-resolution project images from architecture article pages.
Supports batch processing, concurrent downloads, retry with backoff,
deduplication, and minimum file-size filtering.

Usage:
    python download.py <url> [options]
    python download.py --batch urls.txt [options]
"""

from __future__ import annotations

import argparse
import os
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from pathlib import Path
from threading import Lock
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)

_SKIP_KEYWORDS = frozenset([
    ".svg", "logo", "qrcode", "icon", "avatar", "no-result", "group",
])

_LAZY_ATTRS = ("data-src", "lazy-src", "data-lazy", "data-original", "data-url")

# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------


@dataclass
class DownloadStats:
    """Thread-safe accumulator for download statistics."""

    total_found: int = 0
    downloaded: int = 0
    skipped: int = 0
    failed: int = 0
    _lock: Lock = field(default_factory=Lock, repr=False)

    def inc(self, attr: str, n: int = 1) -> None:
        with self._lock:
            setattr(self, attr, getattr(self, attr) + n)


# ---------------------------------------------------------------------------
# URL cleaning
# ---------------------------------------------------------------------------


def clean_image_url(img_url: str, domain: str) -> str:
    """Strip tracking parameters and upgrade to the highest-resolution variant."""
    clean = img_url.split("?")[0]

    if "archdaily" in domain:
        if "/thumb_jpg/" in clean:
            clean = clean.replace("/thumb_jpg/", "/large_jpg/")
        elif "/newsletter/" in clean:
            clean = clean.replace("/newsletter/", "/large_jpg/")

    return clean


def _is_skip_url(url: str) -> bool:
    """Return True if the URL matches a known non-project-image pattern."""
    lower = url.lower()
    return any(kw in lower for kw in _SKIP_KEYWORDS)


# ---------------------------------------------------------------------------
# File naming
# ---------------------------------------------------------------------------


def safe_filename(index: int, url: str, max_length: int = 100) -> str:
    """Produce a Windows-safe, reasonably short file name."""
    base = os.path.basename(url.split("?")[0])
    base = re.sub(r'[\\/*?:\s"<>|]', "_", base)
    name, ext = os.path.splitext(base)
    if len(ext) > 5 or not ext:
        ext = ".jpg"
    return f"{index}_{name[:max_length]}{ext}"


# ---------------------------------------------------------------------------
# HTTP helpers
# ---------------------------------------------------------------------------


def _build_headers(article_url: str) -> dict[str, str]:
    return {
        "User-Agent": _DEFAULT_USER_AGENT,
        "Referer": article_url,
    }


def _fetch_with_retry(
    url: str,
    headers: dict,
    timeout: int,
    max_retries: int,
    stream: bool = False,
) -> requests.Response | None:
    """GET *url* with exponential-backoff retries. Returns None on failure."""
    for attempt in range(1, max_retries + 1):
        try:
            resp = requests.get(url, headers=headers, timeout=timeout, stream=stream)
            if resp.status_code == 200:
                return resp
            if attempt < max_retries:
                time.sleep(2 ** (attempt - 1))
        except requests.RequestException:
            if attempt < max_retries:
                time.sleep(2 ** (attempt - 1))
    return None


# ---------------------------------------------------------------------------
# Core page scraping
# ---------------------------------------------------------------------------


def extract_image_urls(article_url: str, headers: dict) -> list[str]:
    """Fetch an article page and return a list of cleaned image URLs."""
    domain = urlparse(article_url).netloc.lower()
    resp = requests.get(article_url, headers=headers, timeout=30)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")
    raw_urls: list[str] = []

    for img in soup.find_all("img"):
        img_url = None
        for attr in _LAZY_ATTRS:
            img_url = img.get(attr)
            if img_url:
                break
        if not img_url:
            img_url = img.get("src")
        if not img_url:
            continue

        img_url = urljoin(article_url, img_url)

        if _is_skip_url(img_url):
            continue

        img_url = clean_image_url(img_url, domain)
        raw_urls.append(img_url)

    return raw_urls


# ---------------------------------------------------------------------------
# Single-image download task
# ---------------------------------------------------------------------------


def _download_one(
    index: int,
    img_url: str,
    article_url: str,
    output_dir: Path,
    headers: dict,
    timeout: int,
    max_retries: int,
    min_size_kb: int,
    skip_existing: bool,
    domain: str,
    stats: DownloadStats,
) -> None:
    """Download a single image, updating *stats* accordingly."""
    filename = safe_filename(index, img_url)
    dest = output_dir / filename

    if skip_existing and dest.exists() and dest.stat().st_size > 0:
        stats.inc("skipped")
        print(f"  [{index:>3}] 已跳过(已存在): {filename}")
        return

    resp = _fetch_with_retry(img_url, headers, timeout, max_retries)

    # ArchDaily fallback: try slideshow path if large_jpg failed
    if resp is None and "archdaily" in domain and "/large_jpg/" in img_url:
        fallback = img_url.replace("/large_jpg/", "/slideshow/")
        resp = _fetch_with_retry(fallback, headers, timeout, max_retries)

    if resp is None:
        stats.inc("failed")
        print(f"  [{index:>3}] 下载失败: {img_url}")
        return

    # Minimum-size filter
    content = resp.content
    if min_size_kb > 0 and len(content) < min_size_kb * 1024:
        stats.inc("skipped")
        print(f"  [{index:>3}] 跳过(小于 {min_size_kb}KB): {filename}")
        return

    dest.write_bytes(content)
    stats.inc("downloaded")
    print(f"  [{index:>3}] 已下载: {filename}  ({len(content) / 1024:.0f} KB)")


# ---------------------------------------------------------------------------
# Article-level orchestration
# ---------------------------------------------------------------------------


def download_article(
    article_url: str,
    output_dir: Path,
    workers: int = 1,
    max_retries: int = 3,
    min_size_kb: int = 0,
    skip_existing: bool = True,
    timeout: int = 15,
) -> DownloadStats:
    """Download all project images from a single article URL."""
    output_dir.mkdir(parents=True, exist_ok=True)
    headers = _build_headers(article_url)
    domain = urlparse(article_url).netloc.lower()
    stats = DownloadStats()

    print(f"\n正在抓取: {article_url}")

    try:
        image_urls = extract_image_urls(article_url, headers)
    except Exception as exc:
        print(f"  页面抓取失败: {exc}")
        return stats

    stats.total_found = len(image_urls)
    print(f"  识别到 {len(image_urls)} 张项目图片，开始下载...\n")

    if workers <= 1:
        for i, url in enumerate(image_urls, start=1):
            _download_one(
                i, url, article_url, output_dir, headers,
                timeout, max_retries, min_size_kb, skip_existing, domain, stats,
            )
    else:
        with ThreadPoolExecutor(max_workers=workers) as pool:
            futures = {
                pool.submit(
                    _download_one,
                    i, url, article_url, output_dir, headers,
                    timeout, max_retries, min_size_kb, skip_existing, domain, stats,
                ): i
                for i, url in enumerate(image_urls, start=1)
            }
            for future in as_completed(futures):
                future.result()  # propagate exceptions

    return stats


# ---------------------------------------------------------------------------
# Batch processing
# ---------------------------------------------------------------------------


def _parse_batch_file(batch_path: Path) -> list[str]:
    """Read a text file, returning non-blank, non-comment lines as URLs."""
    urls: list[str] = []
    for line in batch_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith("#"):
            urls.append(stripped)
    return urls


# ---------------------------------------------------------------------------
# Summary report
# ---------------------------------------------------------------------------


def _print_summary(target_label: str, output_dir: Path, stats: DownloadStats) -> None:
    print(f"\n{'=' * 40}")
    print(f"  Download Summary")
    print(f"{'=' * 40}")
    print(f"  Target:       {target_label}")
    print(f"  Found:        {stats.total_found}")
    print(f"  Downloaded:   {stats.downloaded}")
    print(f"  Skipped:      {stats.skipped}")
    print(f"  Failed:       {stats.failed}")
    print(f"  Output:       {output_dir}")
    print(f"{'=' * 40}\n")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Download high-res architecture project images from "
                    "ArchDaily, Gooood, and Archiposition.",
    )
    p.add_argument("url", nargs="?", default=None, help="Article URL")
    p.add_argument("-o", "--output", default="downloaded_images",
                   help="Output directory (default: downloaded_images)")
    p.add_argument("-b", "--batch", default=None,
                   help="Text file with one URL per line")
    p.add_argument("-w", "--workers", type=int, default=1,
                   help="Concurrent download threads (default: 1)")
    p.add_argument("-r", "--retry", type=int, default=3,
                   help="Max retries per image (default: 3)")
    p.add_argument("-s", "--min-size", type=int, default=0,
                   help="Skip images smaller than N KB (default: 0)")
    p.add_argument("--skip-existing", dest="skip_existing",
                   action="store_true", default=True,
                   help="Skip files that already exist (default)")
    p.add_argument("--no-skip-existing", dest="skip_existing",
                   action="store_false",
                   help="Re-download even if file exists")
    p.add_argument("--timeout", type=int, default=15,
                   help="HTTP timeout in seconds (default: 15)")
    return p


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.batch is None and args.url is None:
        parser.error("Please provide a URL or use --batch with a URL list file.")

    output_dir = Path(args.output)

    if args.batch:
        batch_path = Path(args.batch)
        if not batch_path.exists():
            print(f"Error: batch file not found: {batch_path}", file=sys.stderr)
            sys.exit(1)

        urls = _parse_batch_file(batch_path)
        print(f"从 {batch_path} 读取到 {len(urls)} 个链接")

        agg = DownloadStats()
        for i, url in enumerate(urls, start=1):
            print(f"\n[{i}/{len(urls)}]", end="")
            stats = download_article(
                url, output_dir, args.workers, args.retry,
                args.min_size, args.skip_existing, args.timeout,
            )
            agg.total_found += stats.total_found
            agg.downloaded += stats.downloaded
            agg.skipped += stats.skipped
            agg.failed += stats.failed

        _print_summary(f"{len(urls)} pages (batch)", output_dir, agg)

    else:
        stats = download_article(
            args.url, output_dir, args.workers, args.retry,
            args.min_size, args.skip_existing, args.timeout,
        )
        _print_summary(args.url, output_dir, stats)


if __name__ == "__main__":
    main()
