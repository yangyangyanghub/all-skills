# 交付闸门：三档状态机 + 证据绑定

> 解决的问题：**AI 自己给自己打分。**
> 做法来源：建筑学长 `interior-3d-web/固定编辑器/交付阶段校验.cjs`——它把"交付"从一句口头承诺变成可机器校验的状态机。本文件把同一套逻辑移植到图纸交付。

## 一、三档交付状态（不许含糊）

| stage | 含义 | 准入条件 |
|---|---|---|
| `review` | 核对稿：只核对结构和尺度，不含成品表达 | 允许存在未验证项；**不得标为可交付** |
| `design-draft` | 草案：按估算生成，含未确认参数 | 必须写明哪些是估算；**不得标为可交付** |
| `design-final` | 终稿：可交付 | 三查全 pass、控制图存在、证据齐全、差异已写 |

**没有"差不多"这一档。** 拿不准就是 `design-draft`。

## 二、证据绑定：每个交付项必须带这五样

```json
{
  "file": "终稿绝对路径",
  "drawing": "render-interior",
  "delivery": "deliverable",
  "control_input": "白模绝对路径",
  "checks": { "element_count": "pass", "floor_count": "pass", "layout": "pass" },
  "evidence": ["预览或对照截图绝对路径"],
  "differences": "实测与预期的具体差异，至少 8 个字"
}
```

| 字段 | 为什么必须有 |
|---|---|
| `control_input` | 没有控制图的图不可能是终稿。空值 = 自动降级 |
| `checks` | 三查逐项记录 pass/fail/unverified；`unverified` 不许当 pass |
| `evidence` | 截图/对照图路径，且必须是真实图片文件（脚本校验文件头魔数） |
| `differences` | 防"看起来没问题"。写不出差异说明没真核对 |
| `delivery` | deliverable / intent-only 二选一；intent-only 必须写理由 |

这五样缺一样，`check_delivery.py` 直接判 fail。

## 三、校验怎么跑

```powershell
python scripts\check_delivery.py --manifest 交付清单.json
```

退出码：`0` 通过，`1` 有阻塞问题。

**它能自动查的**：状态机合法性、字段完整性、引用文件是否存在、图片文件头是否真实、差异说明长度、deliverable 与 checks 的矛盾。

**它不能查的**（必须人看）：照片相似度、造型对不对、截图是否真是本次产物。

所以脚本通过 ≠ 可以交付。脚本只负责把"自欺"这一层拦住。

## 四、五条硬规则

1. **`design-final` 且任一 check 为 `unverified` → fail。** 不确定就是不确定。
2. **`delivery: deliverable` 但 `control_input` 为空 → fail。** 没有几何控制的图不可能准。
3. **`delivery: intent-only` 但 `intent_reason` 少于 10 字 → fail。** 降级必须说清为什么。
4. **`evidence` 里的文件不存在或不是 PNG/JPEG/WebP → fail。** 防止"我截了图"但其实没截。
5. **`differences` 少于 8 字 → fail。** "无差异"不算，要写具体。

## 五、示例

### 通过的例子

```json
{
  "task": "某公寓客厅",
  "stage": "design-final",
  "images": [
    {
      "file": "E:\\out\\客厅-暖调中古.png",
      "drawing": "render-interior",
      "delivery": "deliverable",
      "control_input": "E:\\in\\白模.png",
      "checks": { "element_count": "pass", "floor_count": "pass", "layout": "pass" },
      "evidence": ["E:\\out\\客厅-暖调中古.png"],
      "differences": "窗外景观为模型生成，非本项目真实场地；沙发形态由 L 形改为两个单元组合"
    }
  ]
}
```

### 会被判 fail 的例子

```json
{
  "stage": "design-final",
  "images": [{
    "file": "E:\\out\\总平.png",
    "drawing": "birdseye",
    "delivery": "deliverable",
    "control_input": null,
    "checks": { "element_count": "unverified" },
    "evidence": ["E:\\out\\不存在的图.png"],
    "differences": ""
  }]
}
```

四处都错：没有控制图却标可交付、三查未验证、证据文件不存在、差异为空。

## 六、和 acceptance.md 的分工

| 文件 | 管什么 |
|---|---|
| [acceptance.md](acceptance.md) | 人怎么查、查哪些项、失败案例库 |
| 本文件 | 查完的结论怎么记录、怎么被机器拦住 |
