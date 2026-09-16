# 院支付申请模板 · 结构说明

> 源文件：`邯郸市规划设计院-大额资金支付议事申请单_模板.docx`
> 用途：作为 yuandangwen-zhifu 子 skill 的可填充模板

## 表格结构（8 行 × 6 列）

| 行 | 单元格定位 | 内容 | 备注 |
|---|---|---|---|
| R0 | C0-C5 合并 | 邯郸市规划设计院 | 标题行，加粗居中 |
| R1 | C0-C5 合并 | 大额资金支付议事申请单 | 副标题行，加粗居中 |
| R2-R4 | C0 是 Q事项说明Q 小标签，C1-C5 合并 | 5 段情况说明 + 落款日期 | 主填写区，3 行合并为 1 个长 cell |
| R5 | C0=说明人 / C2=部门负责人 / C4=部门主管院长 | 签字栏 | 留空，手签 |
| R6 | C0=管理部门审核 | 审核栏 | 留空，签章 |
| R7 | C0=备注 | 备注栏 | 留空 |

## 填充流程

1. 读取 .docx 模板
2. 找到 R2-R4 主事项说明 cell（len(cell.text) > 100 的 cell）
3. 清空 cell.paragraphs 列表
4. 按以下顺序写入新段落：
   - 第 1 段（加粗）：`支付<项目名>费用的情况说明`
   - 第 2 段：`一、项目背景` + 项目背景内容
   - 第 3 段：`二、合同费用` + 金额 + 构成
   - 第 4 段：`三、付款方式` + 一次性/分期说明
   - 第 5 段：落款日期
5. 保持签字栏（R5/R6/R7）为空（手签）
6. 保存到目标路径

## 字体样式

- 标题行/副标题行：加粗居中（模板已设置）
- 主事项说明：宋体小四（模板默认）
- 段落首行：缩进 2 字符（按 docx 默认）

## 注意事项

- 付款方式段：默认写 Q一次性支付全部合作费用 X 万元Q，**特殊情况下**才写明理由
- 不要动表头、签字栏的格式（模板已固定）
- 金额大写 + 数字同时给：`人民币 X X 万元整（￥X,XXX.00 元）`
- 标题中的双引号用 Unicode 弯引号或 ASCII 直引号均可，但需统一

## python-docx 关键代码片段

```python
from docx import Document
doc = Document(template_path)
for t in doc.tables:
    for row in t.rows:
        for cell in row.cells:
            if len(cell.text.strip()) > 100:  # 找到主事项说明 cell
                # 清空现有段落
                for p in cell.paragraphs:
                    p._element.getparent().remove(p._element)
                # 写入新内容
                lines = new_text.split(chr(10))
                for i, line in enumerate(lines):
                    p = cell.add_paragraph()
                    if i == 0:
                        run = p.add_run(line)
                        run.bold = True
                    else:
                        p.add_run(line)
                break
doc.save(output_path)
```
