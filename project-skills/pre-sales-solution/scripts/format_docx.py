#!/usr/bin/env python3
"""
售前方案 Word 格式化脚本

复用 deep-research 的 format_docx.py 逻辑。
"""

import sys
import os
import subprocess
from pathlib import Path

def main():
    # 查找并调用 deep-research 的 format_docx.py
    skill_dir = Path(__file__).parent.parent.parent  # .opencode/skill/
    deep_research_script = skill_dir / "deep-research" / "scripts" / "format_docx.py"
    
    if not deep_research_script.exists():
        print(f"错误：找不到 deep-research 的格式化脚本: {deep_research_script}")
        sys.exit(1)
    
    # 转发所有参数到 deep-research 的脚本
    cmd = [sys.executable, str(deep_research_script), *sys.argv[1:]]
    print(f"调用 deep-research 格式化脚本...")
    result = subprocess.run(cmd, capture_output=False)
    sys.exit(result.returncode)

if __name__ == "__main__":
    main()
