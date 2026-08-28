"""
统一视频生成器 - 支持新闻简报和系统演示两种模式
"""
import argparse
import asyncio
import sys
from pathlib import Path


def interactive_menu():
    """交互式菜单"""
    print("\n┌─ 视频生成器 ─────────────────────────────┐")
    print("│                                           │")
    print("│  模式选择：                               │")
    print("│    1. 新闻简报 (3:4 竖版, 口播)           │")
    print("│    2. 系统演示 (16:9 横版)                │")
    print("│    6. 简报模式 (合屏, 无配音, 15s)        │")
    print("│    7. 技术分享 (3:4 竖版, 调研转口播)     │")
    print("│                                           │")
    print("│  功能选项：                               │")
    print("│    3. 配音 (TTS)      [开]                │")
    print("│    4. 字幕            [开]                │")
    print("│    5. 背景音乐        [关]                │")
    print("│                                           │")
    print("│  按数字选择，回车开始生成                  │")
    print("└───────────────────────────────────────────┘\n")

    mode = "news"
    options = {"tts": True, "subs": True, "bgm": False}

    while True:
        choice = input("请选择 (1/2/3/4/5/回车): ").strip()

        if choice == "":
            break
        elif choice == "1":
            mode = "news"
            print("  → 模式: 新闻简报 (3:4)")
        elif choice == "2":
            mode = "walkthrough"
            print("  → 模式: 系统演示 (16:9)")
        elif choice == "3":
            options["tts"] = not options["tts"]
            print(f"  → 配音: {'开' if options['tts'] else '关'}")
        elif choice == "4":
            options["subs"] = not options["subs"]
            print(f"  → 字幕: {'开' if options['subs'] else '关'}")
        elif choice == "5":
            options["bgm"] = not options["bgm"]
            print(f"  → 背景音乐: {'开' if options['bgm'] else '关'}")
        elif choice == "6":
            mode = "brief"
            options["tts"] = False
            options["subs"] = False
            print("  → 模式: 简报模式 (合屏, 无配音)")
        elif choice == "7":
            mode = "tech"
            print("  → 模式: 技术分享 (3:4)")
        else:
            print("  无效选择")

    return mode, options


def parse_args():
    parser = argparse.ArgumentParser(description="统一视频生成器")

    # 模式
    parser.add_argument("--mode", choices=["news", "walkthrough", "brief", "tech"], default="news")

    # 输入
    parser.add_argument("--md", default="daily-brief.md", help="Markdown 文件 (新闻模式)")
    parser.add_argument("--config", help="JSON 配置文件 (演示模式)")
    parser.add_argument("--base-url", default="http://localhost:3000", help="系统地址 (演示模式)")
    parser.add_argument("--storage-state", help="Playwright 登录态文件 (演示模式)")

    # 功能开关
    parser.add_argument("--tts", action="store_true")
    parser.add_argument("--no-tts", action="store_true")
    parser.add_argument("--subs", action="store_true")
    parser.add_argument("--no-subs", action="store_true")
    parser.add_argument("--bgm", nargs="?", const="default", default=None)

    # 输出
    parser.add_argument("--output", default="final.mp4")
    parser.add_argument("--voice", default="zh-CN-YunxiNeural")
    parser.add_argument("--rate", default="+30%")
    parser.add_argument("--port", type=int, default=18909)

    # 跳过选项
    parser.add_argument("--skip-capture", action="store_true")
    parser.add_argument("--skip-render", action="store_true")

    # 简报模式参数
    parser.add_argument("--per-slide", type=float, default=3.5, help="简报模式每屏秒数")

    # 技术分享模式参数
    parser.add_argument("--brand-title", help="技术分享自定义标题")
    parser.add_argument("--brand-accent", help="技术分享自定义强调色")

    # 交互模式
    parser.add_argument("--interactive", "-i", action="store_true")

    return parser.parse_args()


async def run_news_mode(args, options):
    """运行新闻简报模式"""
    from build_news_video import main as news_main

    sys.argv = [
        "build_news_video.py",
        "--md", args.md,
        "--voice", args.voice,
        "--rate", args.rate,
        "--output", args.output,
        "--port", str(args.port),
    ]

    if not options["tts"]:
        sys.argv.append("--skip-tts")
    if not options["subs"]:
        sys.argv.append("--skip-subs")
    if args.bgm:
        sys.argv.extend(["--bgm", args.bgm])
    if args.skip_capture:
        sys.argv.append("--skip-capture")
    if args.skip_render:
        sys.argv.append("--skip-render")

    await news_main()


async def run_walkthrough_mode(args, options):
    """运行系统演示模式"""
    from build_walkthrough import main as walkthrough_main

    if not args.config:
        print("[!] 系统演示模式需要 --config 参数指定 JSON 配置文件")
        sys.exit(1)

    sys.argv = [
        "build_walkthrough.py",
        "--config", args.config,
        "--base-url", args.base_url,
        "--voice", args.voice,
        "--rate", args.rate,
        "--output", args.output,
    ]

    if args.storage_state:
        sys.argv.extend(["--storage-state", args.storage_state])

    if not options["tts"]:
        sys.argv.append("--skip-tts")
    if not options["subs"]:
        sys.argv.append("--skip-subs")
    if args.bgm:
        sys.argv.extend(["--bgm", args.bgm])
    if args.skip_capture:
        sys.argv.append("--skip-capture")
    if args.skip_render:
        sys.argv.append("--skip-render")

    await walkthrough_main()


def run_brief_mode(args, options):
    """运行简报模式（合屏、无配音、BGM、15s内）"""
    from build_news_brief import main as brief_main

    sys.argv = [
        "build_news_brief.py",
        "--md", args.md,
        "--output", args.output,
        "--per-slide", str(args.per_slide),
    ]

    if args.bgm:
        sys.argv.extend(["--bgm", args.bgm])
    if args.skip_render:
        sys.argv.append("--skip-render")

    brief_main()


async def run_tech_mode(args, options):
    """运行技术分享模式"""
    from build_tech_share import main as tech_main

    sys.argv = [
        "build_tech_share.py",
        "--md", args.md,
        "--voice", args.voice,
        "--rate", args.rate,
        "--output", args.output,
        "--port", str(args.port),
    ]

    if args.brand_title:
        sys.argv.extend(["--brand-title", args.brand_title])
    if args.brand_accent:
        sys.argv.extend(["--brand-accent", args.brand_accent])

    if not options["tts"]:
        sys.argv.append("--skip-tts")
    if options["bgm"] and args.bgm:
        sys.argv.extend(["--bgm", args.bgm])
    if args.skip_capture:
        sys.argv.append("--skip-capture")
    if args.skip_render:
        sys.argv.append("--skip-render")

    await tech_main()


async def main():
    args = parse_args()

    if args.interactive:
        mode, options = interactive_menu()
    else:
        mode = args.mode
        options = {
            "tts": not args.no_tts,
            "subs": not args.no_subs,
            "bgm": args.bgm is not None,
        }
        if args.tts:
            options["tts"] = True
        if args.no_tts:
            options["tts"] = False
        if args.subs:
            options["subs"] = True
        if args.no_subs:
            options["subs"] = False

    # 简报模式默认关闭配音和字幕
    if mode == "brief":
        options["tts"] = False
        options["subs"] = False

    print("\n" + "="*50)
    print("视频生成器")
    print("="*50)
    print(f"  模式: {mode}")
    print(f"  配音: {'✓' if options['tts'] else '✗'}")
    print(f"  字幕: {'✓' if options['subs'] else '✗'}")
    print(f"  BGM:  {'✓' if options['bgm'] else ''}")
    print("="*50 + "\n")

    if mode == "news":
        await run_news_mode(args, options)
    elif mode == "walkthrough":
        await run_walkthrough_mode(args, options)
    elif mode == "brief":
        run_brief_mode(args, options)
    elif mode == "tech":
        await run_tech_mode(args, options)


if __name__ == "__main__":
    asyncio.run(main())
