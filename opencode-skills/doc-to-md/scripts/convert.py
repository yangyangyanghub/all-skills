# -*- coding: utf-8 -*-
"""通用文档 -> Markdown 转换器
基于 markitdown 18 种格式 + RapidOCR 离线 OCR 兜底
- 自动按扩展名路由
- 文字版 PDF / Office 直接提取
- 扫描版 PDF 自动 OCR
- 图片默认 OCR（--no-ocr 关闭）
- Windows 中文路径安全
"""
import sys
import time
import argparse
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

OCR_THRESHOLD = 50
DPI = 200
MAX_HEIGHT = 3000
OVERLAP = 80

SUPPORTED_EXTS = {
    ".pdf", ".docx", ".pptx", ".xlsx", ".xls", ".csv", ".epub", ".ipynb",
    ".html", ".htm", ".msg", ".mp3", ".wav",
    ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff",
    ".zip", ".txt", ".json", ".xml",
}

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff"}

def log(msg):
    print(msg, flush=True)

def gather_files(target, ext_filter):
    if target.is_file():
        files = [target] if target.suffix.lower() in SUPPORTED_EXTS else []
    else:
        files = sorted(p for p in target.rglob("*")
                       if p.is_file() and p.suffix.lower() in SUPPORTED_EXTS)
    if ext_filter:
        wanted = {("." + e.lower().lstrip(".")) for e in ext_filter}
        files = [f for f in files if f.suffix.lower() in wanted]
    return files

def md_path_for(src, out_dir):
    if out_dir is None:
        return src.with_suffix(".md")
    return out_dir / (src.stem + ".md")

def needs_run(md, force):
    if force:
        return True
    if not md.exists():
        return True
    return md.stat().st_size < 200

def stage1_convert(files, out_dir, force):
    """第一阶段：用 markitdown 库直接转换"""
    from markitdown import MarkItDown
    md_engine = MarkItDown()
    results = []
    for i, src in enumerate(files, 1):
        md = md_path_for(src, out_dir)
        if not needs_run(md, force):
            results.append((src, md, -1, None))
            log(f"[SKIP] ({i}/{len(files)}) {src.name} (已存在)")
            continue
        md.parent.mkdir(parents=True, exist_ok=True)
        try:
            t0 = time.time()
            result = md_engine.convert(str(src))
            text = result.text_content or ""
            md.write_text(text, encoding="utf-8")
            elapsed = time.time() - t0
            results.append((src, md, len(text), None))
            ext = src.suffix.lower()
            if ext == ".pdf" and len(text) < OCR_THRESHOLD:
                tag = "[SCAN]"
            elif ext in IMAGE_EXTS:
                tag = "[IMG] "
            elif len(text) >= OCR_THRESHOLD:
                tag = "[OK]  "
            else:
                tag = "[MIN] "
            log(f"{tag} ({i}/{len(files)}) {src.name} -> {len(text)} chars ({elapsed:.1f}s)")
        except Exception as e:
            results.append((src, md, 0, str(e)))
            log(f"[ERR ] ({i}/{len(files)}) {src.name}: {type(e).__name__}: {e}")
    return results

def split_tall_image(img):
    w, h = img.size
    if h <= MAX_HEIGHT:
        return [img]
    parts = []
    y = 0
    while y < h:
        end = min(y + MAX_HEIGHT, h)
        parts.append(img.crop((0, y, w, end)))
        if end == h:
            break
        y = end - OVERLAP
    return parts

def dedup_overlap(prev_lines, cur_lines, lookback=5):
    if not prev_lines or not cur_lines:
        return cur_lines
    tail = prev_lines[-lookback:]
    for k in range(min(len(tail), len(cur_lines)), 0, -1):
        if cur_lines[:k] == tail[-k:]:
            return cur_lines[k:]
    return cur_lines

def ocr_pdf(pdf, ocr):
    import pypdfium2 as pdfium
    import numpy as np
    doc = pdfium.PdfDocument(str(pdf))
    try:
        page_count = len(doc)
        all_pages = []
        total_lines = 0
        for idx in range(page_count):
            page = doc[idx]
            img = page.render(scale=DPI / 72).to_pil()
            page.close()
            slices = split_tall_image(img)
            page_lines = []
            prev_lines = []
            for sl in slices:
                arr = np.array(sl)
                res = ocr(arr)
                if res is None or not hasattr(res, "txts") or res.txts is None:
                    cur = []
                else:
                    cur = [t for t in res.txts if t and t.strip()]
                cur = dedup_overlap(prev_lines, cur)
                page_lines.extend(cur)
                prev_lines = cur
            total_lines += len(page_lines)
            if page_lines:
                all_pages.append(f"## 第 {idx + 1} 页\n\n" + "\n".join(page_lines))
        return "\n\n".join(all_pages), page_count, total_lines
    finally:
        doc.close()

def ocr_image(img_path, ocr):
    from PIL import Image
    import numpy as np
    img = Image.open(img_path).convert("RGB")
    slices = split_tall_image(img)
    lines = []
    prev_lines = []
    for sl in slices:
        arr = np.array(sl)
        res = ocr(arr)
        if res is None or not hasattr(res, "txts") or res.txts is None:
            cur = []
        else:
            cur = [t for t in res.txts if t and t.strip()]
        cur = dedup_overlap(prev_lines, cur)
        lines.extend(cur)
        prev_lines = cur
    return "\n".join(lines), len(lines)

def stage2_ocr(stage1_results, out_dir, ocr_images):
    """第二阶段：扫描版 PDF 和图片 OCR"""
    need_ocr = []
    for (src, md, chars, err) in stage1_results:
        if err is not None or chars == -1:
            continue
        ext = src.suffix.lower()
        if ext == ".pdf" and chars < OCR_THRESHOLD:
            need_ocr.append((src, md, "pdf"))
        elif ext in IMAGE_EXTS and ocr_images:
            need_ocr.append((src, md, "image"))

    if not need_ocr:
        log("\n无需 OCR")
        return 0, 0, 0

    log(f"\n=== 第二阶段：OCR {len(need_ocr)} 个文件 ===")
    log("初始化 RapidOCR...")
    from rapidocr import RapidOCR
    ocr = RapidOCR()
    log("RapidOCR 就绪\n")

    ok = empty = err = 0
    for i, (src, md, kind) in enumerate(need_ocr, 1):
        t0 = time.time()
        try:
            if kind == "pdf":
                text, pages, lines = ocr_pdf(src, ocr)
                extra = f"{pages}页/{lines}行"
            else:
                text, lines = ocr_image(src, ocr)
                extra = f"图片/{lines}行"
            # 图片 OCR：附加到 markitdown 已写入的元数据后
            if kind == "image" and md.exists() and md.stat().st_size > 0:
                old = md.read_text(encoding="utf-8")
                text = old.rstrip() + "\n\n## OCR 识别文本\n\n" + text
            md.write_text(text, encoding="utf-8")
            elapsed = time.time() - t0
            if lines >= 3:
                ok += 1
                tag = "[OK]   "
            else:
                empty += 1
                tag = "[EMPTY]"
            kb = md.stat().st_size / 1024
            log(f"{tag} ({i}/{len(need_ocr)}) {src.name} -> {extra}/{kb:.1f}KB ({elapsed:.1f}s)")
        except Exception as e:
            err += 1
            elapsed = time.time() - t0
            log(f"[ERR]   ({i}/{len(need_ocr)}) {src.name} ({elapsed:.1f}s) {type(e).__name__}: {e}")
    return ok, empty, err

def main():
    ap = argparse.ArgumentParser(description="Document -> Markdown universal converter")
    ap.add_argument("target", help="File or folder path")
    ap.add_argument("--ext", default=None, help="Comma-separated extensions filter, e.g. pdf,docx")
    ap.add_argument("--no-ocr", action="store_true", help="Disable OCR for scanned PDFs and images")
    ap.add_argument("--force", action="store_true", help="Overwrite existing .md")
    ap.add_argument("--out-dir", default=None, help="Output directory (default: alongside source)")
    args = ap.parse_args()

    target = Path(args.target)
    if not target.exists():
        log(f"路径不存在: {target}")
        sys.exit(1)

    out_dir = Path(args.out_dir) if args.out_dir else None
    if out_dir:
        out_dir.mkdir(parents=True, exist_ok=True)

    ext_filter = [e.strip() for e in args.ext.split(",")] if args.ext else None
    files = gather_files(target, ext_filter)
    if not files:
        log(f"未找到支持的文件: {target}")
        sys.exit(0)

    # 摸底统计
    from collections import Counter
    ext_stats = Counter(f.suffix.lower() for f in files)
    log(f"找到 {len(files)} 个文件:")
    for ext, n in sorted(ext_stats.items(), key=lambda x: -x[1]):
        log(f"  {ext}: {n}")
    log(f"输出: {out_dir if out_dir else '与源文件同目录'}")
    log(f"OCR: {'禁用' if args.no_ocr else '启用（扫描版 PDF + 图片）'}")
    log("=" * 80)
    log("=== 第一阶段：直接转换 ===")

    t0 = time.time()
    s1 = stage1_convert(files, out_dir, args.force)

    s1_ok = sum(1 for r in s1 if r[3] is None and r[2] >= OCR_THRESHOLD)
    s1_scan = sum(1 for r in s1 if r[3] is None and 0 <= r[2] < OCR_THRESHOLD
                  and r[0].suffix.lower() == ".pdf")
    s1_img = sum(1 for r in s1 if r[3] is None and r[0].suffix.lower() in IMAGE_EXTS and r[2] != -1)
    s1_skip = sum(1 for r in s1 if r[2] == -1)
    s1_err = sum(1 for r in s1 if r[3] is not None)
    log(f"\n第一阶段: 文字版直接转 {s1_ok}, 扫描版待 OCR {s1_scan}, 图片 {s1_img}, 跳过 {s1_skip}, 失败 {s1_err}")

    if args.no_ocr:
        log("已禁用 OCR")
        ocr_ok = ocr_empty = ocr_err = 0
    else:
        ocr_ok, ocr_empty, ocr_err = stage2_ocr(s1, out_dir, ocr_images=True)

    total = time.time() - t0
    log("\n" + "=" * 80)
    log(f"全部完成 (耗时 {total/60:.1f} 分钟)")
    log(f"  直接提取: {s1_ok}")
    log(f"  OCR 成功: {ocr_ok}")
    log(f"  OCR 空白(可能无文字): {ocr_empty}")
    log(f"  失败: {s1_err + ocr_err}")
    log(f"  跳过(已存在): {s1_skip}")

if __name__ == "__main__":
    main()
