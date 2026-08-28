import json
import re
import subprocess
import sys
from datetime import date
from pathlib import Path


def findWorkspaceRoot() -> Path:
  currentPath = Path(__file__).resolve()
  for parent in currentPath.parents:
    if (parent / ".opencode").exists():
      return parent
  raise RuntimeError("未找到工作区根目录")


def runQueryScript(workspaceRoot: Path) -> dict:
  queryScriptPath = workspaceRoot / "temp" / "query_tokens_detail.py"
  if not queryScriptPath.exists():
    raise FileNotFoundError(f"缺少查询脚本: {queryScriptPath}")

  result = subprocess.run(
    [sys.executable, str(queryScriptPath)],
    cwd=workspaceRoot,
    capture_output=True,
    text=True,
    encoding="utf-8",
    check=False,
  )

  if result.returncode != 0:
    raise RuntimeError(result.stderr.strip() or result.stdout.strip() or "查询脚本执行失败")

  match = re.search(r"JSON_START\s*(\{.*?\})\s*JSON_END", result.stdout, re.S)
  if not match:
    raise RuntimeError("查询结果中未找到 JSON 数据")

  return json.loads(match.group(1))


def parseSnapshotDate(filePath: Path) -> date | None:
  try:
    return date.fromisoformat(filePath.stem)
  except ValueError:
    return None


def extractSnapshotJson(filePath: Path) -> dict:
  content = filePath.read_text(encoding="utf-8")
  match = re.search(r"```json\s*(\{.*?\})\s*```", content, re.S)
  if not match:
    raise RuntimeError(f"快照文件缺少 JSON 区块: {filePath}")
  return json.loads(match.group(1))


def findBaselineSnapshot(tokensDir: Path, targetDate: date) -> tuple[Path | None, dict | None]:
  candidates: list[tuple[date, Path]] = []
  for filePath in tokensDir.glob("*.md"):
    snapshotDate = parseSnapshotDate(filePath)
    if snapshotDate is None:
      continue
    if snapshotDate >= targetDate:
      continue
    candidates.append((snapshotDate, filePath))

  if not candidates:
    return None, None

  _, latestPath = max(candidates, key=lambda item: item[0])
  return latestPath, extractSnapshotJson(latestPath)


def buildBaselineMap(baselineData: dict | None) -> dict[str, float]:
  if not baselineData:
    return {}

  ranking = baselineData.get("ranking")
  if isinstance(ranking, list):
    return {
      str(item.get("name")): float(item.get("used_quota_m", 0) or 0)
      for item in ranking
      if item.get("name")
    }

  rows = baselineData.get("rows")
  if isinstance(rows, list):
    return {
      str(item.get("name")): float(item.get("used_quota_m", 0) or 0)
      for item in rows
      if item.get("name")
    }

  return {}


def formatDelta(deltaValue: float) -> str:
  if deltaValue >= 0:
    return f"+{deltaValue:.2f}"
  return f"{deltaValue:.2f}"


def buildReport(
  currentData: dict,
  baselinePath: Path | None,
  baselineData: dict | None,
  targetDate: date,
  workspaceRoot: Path,
) -> str:
  baselineMap = buildBaselineMap(baselineData)

  ranking = []
  for row in (currentData.get("rows", []) or []):
    name = row.get("name") or "N/A"
    usedQuota = round(float(row.get("used_quota_m", 0) or 0), 2)
    deltaValue = round(usedQuota - baselineMap.get(name, 0), 2)
    ranking.append({
      "name": name,
      "used_quota_m": usedQuota,
      "delta_m": deltaValue,
    })

  ranking.sort(key=lambda item: item["delta_m"], reverse=True)

  totalUsed = round(float(currentData.get("total_used_m", 0) or 0), 2)
  baselineTotal = 0.0
  if baselineData:
    baselineTotal = round(float(baselineData.get("total_used_m", 0) or 0), 2)
  totalDelta = round(totalUsed - baselineTotal, 2)

  lines = [
    "# 每日 API 统计（含新增列）",
    "",
    f"> 统计日期：{targetDate.isoformat()}",
  ]

  if baselinePath:
    baselineRelative = baselinePath.relative_to(workspaceRoot).as_posix()
    lines.append(f"> 对比基准：{baselineRelative}")
  else:
    lines.append("> 对比基准：无历史快照（本次按首份快照处理）")

  lines.extend([
    "",
    "## 统计摘要",
    "",
    f"- **今日新增总量**: {totalDelta:.2f}M tokens",
    f"- **今日总消耗**: {totalUsed:.2f}M tokens",
  ])

  if baselinePath:
    lines.append(f"- **昨日总消耗**: {baselineTotal:.2f}M tokens")

  lines.extend([
    f"- **Key总数**: {currentData.get('total_keys', 0)}",
    "",
    "## 排行榜",
    "",
    "| 排名 | 名称 | 总消耗（M) | **较昨日新增（M)** |",
    "| ---: | --- | ---: | ---: |",
  ])

  for index, item in enumerate(ranking, start=1):
    lines.append(
      f"| {index} | {item['name']} | {item['used_quota_m']:.2f} | {formatDelta(item['delta_m'])} |"
    )

  rawData = {
    "snapshot_date": targetDate.isoformat(),
    "baseline_snapshot": baselinePath.stem if baselinePath else None,
    "total_used_m": totalUsed,
    "total_delta_m": totalDelta,
    "total_keys": currentData.get("total_keys", 0),
    "ranking": ranking,
  }

  lines.extend([
    "",
    "## 原始数据",
    "",
    "```json",
    json.dumps(rawData, ensure_ascii=False, indent=2),
    "```",
    "",
  ])

  return "\n".join(lines)


def main() -> int:
  workspaceRoot = findWorkspaceRoot()
  tokensDir = workspaceRoot / "assets" / "tokens"
  tokensDir.mkdir(parents=True, exist_ok=True)

  targetDate = date.today()
  currentData = runQueryScript(workspaceRoot)
  baselinePath, baselineData = findBaselineSnapshot(tokensDir, targetDate)

  reportContent = buildReport(currentData, baselinePath, baselineData, targetDate, workspaceRoot)
  outputPath = tokensDir / f"{targetDate.isoformat()}.md"
  outputPath.write_text(reportContent, encoding="utf-8")

  print(f"报告已生成: {outputPath}")
  if baselinePath:
    print(f"对比基准: {baselinePath}")
  else:
    print("对比基准: 无历史快照")

  return 0


if __name__ == "__main__":
  raise SystemExit(main())
