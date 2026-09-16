# 变更调查流向执法地类判定审核助手

市局侧审核助手：读国土调查云河北分中心的图斑举证，按规则判定，输出审核意见。

## 快速开始

```bash
# 前置：开调试浏览器并登录（见 SKILL.md）

# 离线批量审核
python scripts/load_parcels.py "图斑列表.xlsx" -o out/parcels.json
python scripts/judge.py out/parcels.json -o out/results.json
python scripts/review.py out/results.json

# 在线单图斑审核
node scripts/system_adapter.mjs list
node scripts/system_adapter.mjs detail 0
node scripts/system_adapter.mjs evidence
```

## 目录结构

```
├── SKILL.md                    技能入口
├── data/rule-dictionary.json   规则字典（受控枚举 + 别名归一）
├── references/field-mapping.md 字段映射参考（哪些列空、哪些在系统里）
├── scripts/                    取数 + 判定 + 输出
└── tests/                      测试
```

## 设计原则

- **三层解耦**：取数 / 判定 / 输出。页面改版只修取数层。
- **只读**：绝不修改系统数据。
- **不下定性结论**：只报「不一致」和「举证缺失」。
- **证据不足标存疑**：导出表缺举证字段时不误报「不一致」。
- **可追溯**：每条结论指向规则 id + 字段值。

## 规则维护

规则变了改 `data/rule-dictionary.json`，跑 `python tests/test_rule_dictionary.py` 校验。

> 系统实际枚举与明白纸文本有别名差异（见 `aliases` 字段）。改枚举前务必用真实数据跑一遍 `test_judge.py` 和端到端，纸面推演会漏掉列名差异、枚举别名、证据可得性三类问题。
