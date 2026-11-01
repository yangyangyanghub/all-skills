# AutoCADMCP 本地安装记录

来源：`E:\code\rea-work\jzxz\jzxz-agent-extract\02-技能\AutoCADMCP`（建筑学长电脑版 1.1.27 提取包）
安装时间：2026-10-29
安装位置：`C:\Users\HP\.config\opencode\skills\AutoCADMCP`

## 一、为跑通所做的两处改动

### 1. 依赖版本组合（唯一可用组合）

| 包 | 版本 | 说明 |
|---|---|---|
| `mcp` | **1.30.0（必须 <2）** | `decorators.py` 用 `from mcp.server.fastmcp import FastMCP`；mcp 2.x 已把 FastMCP 改名为 MCPServer 并移除此路径 |
| `pywin32` | 最新 | COM 连接 CAD |
| `pillow` | 最新 | `scripts/render_*_preview.py`、`prepare_reference_review.py` |
| `pydantic` | 2.x | 简写解析 |

**不要安装 `fastmcp` 独立包**：它会拉高 `mcp` 到 2.x，直接破坏 `decorators.py` 的导入。
（实测：`fastmcp 4.1.4` → mcp 2.3.0 报错；`fastmcp 2.14.7` + mcp 1.30 报 `IdentityAssertionParams` 缺失。）

安装命令：

```powershell
python -m pip install "mcp<2" pywin32 pillow
```

### 2. `src/server.py` 第 13 行打了 1 行兼容补丁

```diff
- from fastmcp import FastMCP
+ from mcp.server.fastmcp import FastMCP
```

原因：`server.py` 原本导入独立包 `fastmcp`，而 `src/mcp_tools/decorators.py` 导入 `mcp.server.fastmcp`。
两处必须是**同一个类**，否则注册的工具与装饰器用的基类不一致。改为统一走 `mcp` 内置 FastMCP 后，两者一致，且不再需要独立 `fastmcp` 包。

升级上游技能时记得重新应用这一行。

## 二、已在 opencode.json 注册

`C:\Users\HP\.config\opencode\opencode.json` → `mcp.autocad`：

```jsonc
"autocad": {
  "type": "local",
  "command": [
    "C:\\Users\\HP\\scoop\\shims\\python.exe",
    "C:\\Users\\HP\\.config\\opencode\\skills\\AutoCADMCP\\cad_mcp_launcher.py"
  ],
  "enabled": true,
  "timeout": 300
}
```

改完需重启 opencode，7 个工具才会出现在工具列表。

## 三、实测结果（AutoCAD 2023 + CASS11 环境）

一次性跑通全链路：

| 步骤 | 结果 |
|---|---|
| `connect` | ✅ 4.2 秒，ProgID `AutoCAD.Application.24.2`（CAD 已在运行时） |
| `status` | ✅ `{"autocad": "connected"}` |
| `manage_files new` | ✅ 新建空白图 |
| `draw_entities` 4 个图元 | ✅ 4/4 created，返回 handle |
| `export_data` | ✅ 4 实体；矩形 `Area=48000000`（8000×6000 正确）、圆 `Radius=600` 正确 |
| `manage_files save` | ✅ 写出 `mcp_test.dwg` |

**首次 connect 耗时 330 秒**——因为 CAD 没启动，adapter 用 `Dispatch` 冷启动了 AutoCAD。
CAD 已在运行时，connect 只要 4 秒。**所以流程上先让用户/脚本把 CAD 打开，再 connect。**

## 四、两个必须记住的坑

### 坑 1：先 `new` 再建图层 —— 顺序反了会静默落到 0 层

正确顺序：`manage_files new` → `manage_layers create` → `draw_entities`。

`manage_files new` 会切到一个**空白文档**，之前在外层文档建的图层不在新文档里。顺序反了，图元全部落到 `0` 层，`success` 仍然是 true，不报错不警告。

两种顺序的 `export_data` 的 `count` 都是 7，**必须逐实体看 `Layer` 字段**才能发现。

实测对照（同一批 7 个图元，2026-10-29）：

| 顺序 | 各图层 | 落在 0 层 |
|---|---|---|
| layers → new → draw | 全为 0 | **7** |
| new → layers → draw | A-WALL 1 / A-DIM 1 / A-DOOR 2 / A-WALL-IN 1 / A-TEXT 2 | **0** |

### 坑 2：`opencode.json` 的 MCP `timeout` 单位是毫秒

第一次注册时写了 `"timeout": 300`，服务器起不来——opencode schema 明写 `Timeout in ms ... Defaults to 5000`，300 ms 连初始化（实测 2.2 s）都不够。改成 `60000`。

排查方法：用标准 MCP 客户端直接走 stdio 握手，如果 `initialize` + `tools/list` 都正常，说明服务器没问题，问题在宿主侧配置。

### 坑 3：`lineweight` 必须是整数

```
manage_layers: create|TEST-WALL|white|0.3   ← 失败
   Validation error: Input should be a valid integer, got a number with a fractional part

manage_layers: create|TEST-WALL|white|30    ← 成功（单位 1/100 mm，即 0.30 mm）
```

## 五、能力边界（原技能自带，供判断）

- 通用几何校验 ≠ 专业合规。结构、水电、暖通**没有**自动校验器，必须人工复核并声明。
- `export_data` 读的是**当前 CAD 文档内存状态**，不是磁盘 DWG 重新解析——不证明用户后续手工修改的结果。
- 落图前闸门是**流程约束**（无 `authorize_drawing` 硬闸门）：校验 → 看预览 → 有原图时对照审查 → `status` 确认 → 才画第一笔。
- 源文件版权归原厂商，仅本地研究/自用，不要分发。
