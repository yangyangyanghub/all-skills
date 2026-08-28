# dify-knowledge 使用说明

本文档说明如何为 `dify-knowledge` skill 配置环境变量，重点面向 Windows。

## 1. 需要准备什么

至少需要以下信息：

- Dify 服务地址，例如：`http://127.0.0.1/v1`
- Dify 的 dataset API Key，例如：`dataset-xxxxxx`
- 政策标准知识库 ID
- 院规章制度知识库 ID

对应环境变量如下：

| 变量名 | 说明 | 示例 |
|---|---|---|
| `DIFY_API_BASE_URL` | Dify 服务地址 | `http://127.0.0.1/v1` |
| `DIFY_API_KEY` | Dataset API Key | `dataset-xxxxxx` |
| `DIFY_DATASET_POLICY` | 政策标准知识库 ID | `385d9d8d-xxxx-xxxx-xxxx-xxxxxxxxxxxx` |
| `DIFY_DATASET_INTERNAL` | 院规章制度知识库 ID | `fd284a4a-xxxx-xxxx-xxxx-xxxxxxxxxxxx` |

## 2. Windows 下推荐做法

如果你已经使用我生成的脚本，可以直接用下面这 3 个文件：

| 文件 | 作用 | 适用场景 |
|---|---|---|
| `set-dify-env.ps1` | 写入当前 PowerShell 会话 | 先测试、临时使用 |
| `set-dify-env.cmd` | 写入当前 cmd 会话 | 你主要用 cmd |
| `set-dify-env-user.ps1` | 写入当前用户级环境变量 | 长期使用，重开终端后仍可用 |

### 脚本方式（推荐）

#### 当前 PowerShell 会话

```powershell
. "D:\Desktop\dify-knowledge\dify-knowledge\set-dify-env.ps1"
```

#### 当前 cmd 会话

```cmd
call D:\Desktop\dify-knowledge\dify-knowledge\set-dify-env.cmd
```

#### 持久写入当前用户环境变量

```powershell
& "D:\Desktop\dify-knowledge\dify-knowledge\set-dify-env-user.ps1"
```

执行后请关闭并重新打开终端，再使用相关技能或命令。

### 方案 A：PowerShell 临时生效（推荐先测试）

只对当前 PowerShell 窗口有效，关闭窗口后失效。

```powershell
$env:DIFY_API_BASE_URL = "http://127.0.0.1/v1"
$env:DIFY_API_KEY = "dataset-请替换成你的真实Key"
$env:DIFY_DATASET_POLICY = "请替换成知识库1 ID"
$env:DIFY_DATASET_INTERNAL = "请替换成知识库2 ID"
```

检查是否生效：

```powershell
echo $env:DIFY_API_BASE_URL
echo $env:DIFY_DATASET_POLICY
```

### 方案 B：PowerShell 持久生效（适合长期使用）

执行下面命令后，对新开的终端窗口生效：

```powershell
[System.Environment]::SetEnvironmentVariable("DIFY_API_BASE_URL", "http://127.0.0.1/v1", "User")
[System.Environment]::SetEnvironmentVariable("DIFY_API_KEY", "dataset-请替换成你的真实Key", "User")
[System.Environment]::SetEnvironmentVariable("DIFY_DATASET_POLICY", "请替换成知识库1 ID", "User")
[System.Environment]::SetEnvironmentVariable("DIFY_DATASET_INTERNAL", "请替换成知识库2 ID", "User")
```

设置完成后：

1. 关闭当前终端
2. 重新打开终端或相关工具
3. 再执行检查命令

```powershell
[System.Environment]::GetEnvironmentVariable("DIFY_API_BASE_URL", "User")
[System.Environment]::GetEnvironmentVariable("DIFY_DATASET_POLICY", "User")
```

### 方案 C：cmd 持久生效

如果你主要用的是 Windows 命令提示符：

```cmd
setx DIFY_API_BASE_URL "http://127.0.0.1/v1"
setx DIFY_API_KEY "dataset-请替换成你的真实Key"
setx DIFY_DATASET_POLICY "请替换成知识库1 ID"
setx DIFY_DATASET_INTERNAL "请替换成知识库2 ID"
```

注意：`setx` 执行后，对当前窗口不会立即生效，需要重新打开一个新的 cmd 或 PowerShell 窗口。

## 3. Windows 图形界面设置方法

如果你不想敲命令：

1. 打开“开始菜单”
2. 搜索：`环境变量`
3. 打开“编辑系统环境变量”
4. 点“环境变量”
5. 在“用户变量”区域点“新建”
6. 依次添加这 4 个变量：
   - `DIFY_API_BASE_URL`
   - `DIFY_API_KEY`
   - `DIFY_DATASET_POLICY`
   - `DIFY_DATASET_INTERNAL`
7. 保存后，重启终端或相关程序

## 4. 如何验证 Dify 是否能通

在 PowerShell 里执行：

```powershell
curl.exe -s -X POST "$env:DIFY_API_BASE_URL/datasets/$env:DIFY_DATASET_POLICY/retrieve" `
  -H "Authorization: Bearer $env:DIFY_API_KEY" `
  -H "Content-Type: application/json" `
  -d '{"query":"测试","retrieval_model":{"search_method":"semantic_search","top_k":3,"score_threshold_enabled":true,"score_threshold":0.15}}'
```

如果返回 JSON，说明基本配置没问题。

## 5. 生成 Word 文档的可选配置

默认建议先用 Markdown。

如果你确实需要 `.docx`：

1. 确认电脑装了 Python
2. 安装 `python-docx`

```powershell
python -m pip install python-docx
```

检查安装是否成功：

```powershell
python -c "from docx import Document; print('ok')"
```

## 6. 常见问题

### 1）提示缺少环境变量

说明 4 个变量没有配置完整，或你修改后没有重开终端。

### 2）提示 401 / 403

通常是 `DIFY_API_KEY` 不对，或者没有对应知识库权限。

### 3）提示 404

通常是知识库 ID 配错了。

### 4）服务连不上

先检查：

- Dify 服务是否启动
- `DIFY_API_BASE_URL` 是否正确
- 是否被防火墙或反向代理拦截

### 5）能生成 Markdown，不能生成 Word

通常是 Python 或 `python-docx` 没装好。这种情况下先用 Markdown 即可。

## 7. 建议

- Windows 下优先用 PowerShell 配置和测试
- 不要把真实 API Key 提交到 Git 仓库
- 不要把真实 API Key 直接写回 `SKILL.md`
- 如果更换 Dify 服务地址或知识库，只改环境变量，不改技能正文
