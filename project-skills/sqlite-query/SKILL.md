---
name: sqlite-query
description: 通过 SSH 连接容器内的 SQLite 数据库并执行查询。当用户提到"sqlite 查询"、"查看项目数据"、"数据库里有哪些表"、"查询 new-api 数据"，或需要查询 Docker 容器内 SQLite 文件时使用此技能。适用于本地数据库文件不在 MySQL 中的场景。
---

# SQLite Query - 容器 SQLite 查询

通过 SSH 隧道连接 Docker 容器，查询容器内的 SQLite 数据库文件。

## 触发场景

- 用户问"查一下项目数据"、"数据库里有哪些表"
- 项目使用本地 SQLite 而非外部数据库
- 用户提到 new-api、One-API 或类似项目的内部数据
- 需要查看 `.db` 文件内容

## 快速使用

### 1. 显示所有表

```bash
python .opencode/skill/sqlite-query/scripts/sqlite_query.py ".tables"
```

### 2. 执行 SQL 查询

```bash
python .opencode/skill/sqlite-query/scripts/sqlite_query.py "SELECT * FROM table_name LIMIT 10"
python .opencode/skill/sqlite-query/scripts/sqlite_query.py "SELECT COUNT(*) FROM tokens"
python .opencode/skill/sqlite-query/scripts/sqlite_query.py ".schema tokens"
```

参数：
- `-n 50`：限制返回行数
- `--raw`：输出原始结果（含元信息）

## 配置说明

配置文件：`config/settings.json`

```json
{
  "ssh": {
    "host": "服务器地址",
    "port": 22,
    "username": "用户名",
    "password": "密码",
    "key_file": null
  },
  "sqlite": {
    "db_path": "容器内数据库路径",
    "container_name": "容器名称"
  }
}
```

## 自然语言查询流程

1. **理解用户意图**：分析用户想查什么数据
2. **查看表结构**：使用 `.tables` 和 `.schema` 了解数据结构
3. **生成 SQL**：编写正确的 SELECT 查询
4. **执行查询**：使用 `sqlite_query.py` 执行
5. **解读结果**：用通俗语言解释查询结果

## 常用查询示例

### 查看 tokens 表数据

```bash
python .opencode/skill/sqlite-query/scripts/sqlite_query.py "SELECT id, name, key FROM tokens LIMIT 5"
```

### 查看用户数据

```bash
python .opencode/skill/sqlite-query/scripts/sqlite_query.py "SELECT * FROM users LIMIT 10"
```

### 统计信息

```bash
python .opencode/skill/sqlite-query/scripts/sqlite_query.py "SELECT COUNT(*) as count FROM tokens"
```

## 安全提示

- `config/settings.json` 包含敏感信息，**不要提交到 Git**
- 只执行 SELECT 查询，避免 UPDATE/DELETE/INSERT/DROP 操作

## 依赖安装

```bash
pip install paramiko
```
