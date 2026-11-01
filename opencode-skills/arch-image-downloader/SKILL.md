---
name: arch-image-downloader
description: 当用户需要从建筑网站下载项目图片时使用此技能。支持 ArchDaily、谷德（gooood）和有方（archiposition）三大建筑媒体平台。也适用于用户提供建筑文章链接并希望提取其中所有项目图片的情况，如果能从页面直接知晓图片信息，则正确命名图片。不适用于与建筑网站无关的通用图片抓取，或从 Pinterest、Instagram 等社交平台下载图片。
---

# Architecture Image Downloader

> **在出图流程里的位置**：本技能是 `design-ai-workflow` 四层控制的第 3 层「质感」的上游——先采到意向图，才有氛围稿依据。
> 采到图之后如果要把某张参考图变成风格描述，走 `design-ai-workflow/references/style/infer-style.md`（反推描述词）。

Download high-resolution project images from major Chinese architecture media sites. Supports ArchDaily (archdaily.cn), Gooood (gooood.cn), and Archiposition (archiposition.com / 有方空间).

## Quick Start

```bash
python scripts/download.py <article_url> [options]
```

Minimal usage:

```bash
python scripts/download.py "https://www.archdaily.cn/cn/xxxxx"
```

The script downloads all project images to a `downloaded_images/` folder in the current directory, automatically selecting the highest-resolution variant available.

## Workflow

### Single Page Download

1. Provide the full URL of the architecture article.
2. The script fetches the page, identifies all project images, cleans URLs to their highest-resolution form, and downloads them sequentially.
3. A summary report is printed at the end (total found, downloaded, skipped, failed).

```bash
python scripts/download.py "https://www.gooood.cn/some-project.htm" --output ./my_project
```

### Batch Download (Multiple Pages)

Provide a text file with one URL per line:

```bash
python scripts/download.py --batch urls.txt --output ./batch_gallery
```

The file format is simple — one URL per line, blank lines and lines starting with `#` are ignored:

```
# 住宅项目
https://www.archdaily.cn/cn/1041852/...
https://www.gooood.cn/some-project.htm

# 公共建筑
https://www.archiposition.com/items/5a0b0222ea
```

### Concurrent Downloads

Speed up large batches with parallel workers:

```bash
python scripts/download.py --batch urls.txt --workers 4
```

Default is 1 worker (sequential). Recommended range: 2–4. Higher values may trigger rate limiting.

## Command-Line Options

| Option | Default | Description |
|--------|---------|-------------|
| `url` | (required) | Article URL, or omit when using `--batch` |
| `--output`, `-o` | `downloaded_images` | Directory to save images |
| `--batch`, `-b` | — | Path to a text file with multiple URLs |
| `--workers`, `-w` | `1` | Number of concurrent download threads |
| `--retry`, `-r` | `3` | Maximum retry attempts per image |
| `--min-size`, `-s` | `0` | Skip images smaller than this many KB |
| `--skip-existing` | enabled | Skip files that already exist locally |
| `--no-skip-existing` | — | Re-download even if file already exists |
| `--timeout` | `15` | HTTP request timeout in seconds |

## Site-Specific Behaviour

### ArchDaily (archdaily.cn)

- **Thumbnail upgrade:** URLs containing `/thumb_jpg/` or `/newsletter/` are rewritten to `/large_jpg/` for the highest resolution.
- **Fallback chain:** If `/large_jpg/` returns a non-200 response, the script tries `/slideshow/` as a secondary path.
- **Lazy loading:** Images loaded via `data-src` are captured.

### Gooood (gooood.cn)

- **Parameter stripping:** Query-string parameters (watermarks, resize directives) are removed to retrieve the original full-size image.
- **Lazy loading:** Images loaded via `lazy-src` and `data-lazy` are captured.

### Archiposition / 有方 (archiposition.com)

- **Anti-hotlink bypass:** The `Referer` header is set to the article URL, which satisfies the site's hotlink protection (avoids 403 errors).
- **Parameter stripping:** Same as Gooood — removing query-string parameters yields the original image.

## Filtering and Deduplication

The script automatically skips non-project images:

- Site logos, favicons, and SVG files
- QR codes, avatars, and icon graphics
- Images with filenames containing "no-result", "group", etc.

With `--skip-existing` enabled (the default), files that already exist in the output directory are not re-downloaded. This makes interrupted batch jobs resumable.

## Output Summary

After every run, the script prints a structured summary:

```
===== Download Summary =====
Target:       https://www.archdaily.cn/cn/1041852/...
Found:        42 image tags
Downloaded:   38
Skipped:       3 (already exist)
Failed:        1
Output:       ./arch_gallery
============================
```

## Error Handling

- **Network failures:** Each image retries up to `--retry` times with exponential backoff (1s, 2s, 4s).
- **HTTP errors:** Non-200 responses are logged and skipped without halting the entire job.
- **ArchDaily degradation:** Large-image URLs that fail are automatically downgraded to the slideshow variant.
- **Timeout:** Configurable via `--timeout` (default 15 seconds per image).

## Dependencies

| Library | Purpose | License |
|---------|---------|---------|
| requests | HTTP fetching | Apache-2.0 |
| beautifulsoup4 | HTML parsing | MIT |

Install: `pip install requests beautifulsoup4`
