不能直接出。位图施工图不是施工图，是施工图的照片——没有图元、没有图层、没有真实尺寸，甲方改一个门宽就得重画。

**能交付的路线只有一条：CAD 落图（AutoCADMCP）。**

AI 可以做的：
- 生成 plan.json（几何真源，毫米精度）
- 校验几何（validate_plan.py）
- 落真图元到 DWG（draw_entities，按图层分阶段）
- 导出交付物（.dwg + plan.json + 校验文件 + 预览图）

**不能承诺的：**
- 结构/水电/暖通无自动校验器，不得写"符合规范"
- 专业规范（防火间距、疏散宽度等）需人工审图
- 文字内容、线型规范、排版美观需用户自己扫一眼 DWG

**交付物清单（最少 6 件）：**
1. .dwg 文件
2. plan.json
3. plan_validation.json
4. 预览图
5. 预览 .manifest.json
6. 有原图再加对照图 + _reference_review.json

**流程关键点：**
- `manage_files new` → `manage_layers create` → `draw_entities`（顺序反了会静默落到 0 层）
- `lineweight` 必须是整数（1/100 mm），0.3mm 写成 30
- 核对以 `export_data` 的几何数值为主（面积、周长、长度），不靠目测

结论：AI 能出底稿并落真 DWG，但专业合规和最终审图必须人工介入。
