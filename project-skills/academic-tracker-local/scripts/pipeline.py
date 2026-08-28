import subprocess, sys, os

SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))

def run(name):
    print(f">>> Deploying module: {name}...")
    subprocess.run([sys.executable, os.path.join(SCRIPTS_DIR, f'{name}.py')], check=True)

def main():
    print("--- STARTING ACADEMIC TRACKER 2.0 (FULL STACK) ---")
    
    # 1. 学术基石 (Core Academic)
    run('fetch_rss')              # 知网/订阅
    run('fetch_semantic_scholar') # 全球引用数据
    run('fetch_arxiv')            # 前沿算法预印本 (NEW!)
    run('fetch_crossref')         # 顶会/期刊元数据 (NEW!)
    
    # 2. 空间科学特化 (Domain Specific)
    run('fetch_nasa_ads')         # NASA 航天/遥感报告
    
    # 3. 全网与代码 (Broad & Open Source)
    run('fetch_web')              # 行业新闻
    run('fetch_github')           # 开源项目
    
    # 4. 统一情报分析
    run('analyze')
    run('push')
    print("--- MISSION COMPLETE ---")

if __name__ == "__main__":
    main()
