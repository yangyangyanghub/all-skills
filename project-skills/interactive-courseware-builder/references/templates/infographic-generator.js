// Infographic Generator Pipeline — 信息图生成管线
// 图片生成决策（v1.6.0）：① 知识图表类 → 内联 SVG 手绘（恒走、零成本）；
//   ② 非知识图表类（写实/艺术/照片）→ 用 question 工具弹窗（硬规约 #18，见 workflow-design.md §2.3）

// ===== 第一步决策：SVG vs 其余（最重要，先判断这个）=====
// 知识图表（概念图/流程图/关系网络/示意图/公式图/带中文标签/需精确排版）
//   → **内联 SVG 手绘**，不用 AI 生图。
//   理由：中文精确、零成本、自包含、布局可控；AI 生图的中文文字极易乱码/错字。
// 写实/艺术图（实景照片/人物/复杂光影纹理/真实场景）
//   → 走下方第二步的**弹窗**。

// ===== 第二步：图片来源弹窗（硬规约 #18）=====
// （必做，question 工具 multiple:true 可多选）——勾选允许的来源类别：
//   ① 搜索网络图片   —— 零成本，真实照片/场景（CC0）
//   ② 内联 SVG 手绘   —— 零成本，矢量/自包含；不支持写实/场景图（注意：SVG≠Canvas）
//   ③ AI 生图         —— 生成写实/艺术/场景图；统一走 image-service 技能（无需选引擎）

// ===== 命令模板（「AI 生图」路径 —— image-service 技能）=====
// 在 Bash 中执行（脚本路径相对项目根）:
//
// python .opencode/skills/image-service/core/text_to_image.py \
//   "prompt text here, all Chinese text labels, educational infographic style" \
//   -r 16:9 -o deploy/img/xxx.png
//
// 信息图形态（规则D）用场景脚本:
//   python .opencode/skills/image-service/scenes/infographic/zlab_infographic.py \
//     -l {布局} -s {风格} -n "标题" -c "内容" -o deploy/img/xxx.png
//
// 参数说明:
//   -r / 比例  : 16:9（信息图推荐）/ 1:1（对照图）/ 4:3（概念图），共 10 种
//   -o         : 输出目录，写到 deploy/img/（对应 IMG_PREFIX='img/'）
//   注意：含中文文字的图生成后用 image-service 的 core/image_to_text.py -m ocr 校验；OCR 不过改提示词重生成，勿反复图生图叠加伪影
//   注意：并发 ≤8 张；多图建议串行保风格一致

// ===== Prompt 撰写规范 =====
// 1. 保留中文标注文本 — 在 prompt 末尾附加 ", all Chinese text labels"
// 2. 在 prompt 末尾附加 ", educational infographic style" 指定风格
// 3. 信息内容必须数据准确 — 高程数值、箭头方向、公式符号不可出错
// 4. 每个 prompt 必须包含具体的版式指令: "left side shows X, right side shows Y"
// 5. 末尾附加 "All text in the image must be in Simplified Chinese. No English text."（规则D）

// ===== Prompt 模板 =====
// 示例: 光合作用过程信息图（示例仅作结构示范，替换为你的学科主题）
//   "Educational infographic about the process of photosynthesis (光合作用):
//    1) Light absorption (吸收光能)
//    2) Water splitting (水分解)
//    3) Carbon dioxide fixation (固定二氧化碳)
//    4) Glucose production (生成葡萄糖)
//    5) Oxygen release (释放氧气)
//    Layout: 5 stages arranged as a flow with icons and brief Chinese explanations,
//    all Chinese text labels, educational infographic style"

// 示例: 凸透镜成像对照图（示例仅作结构示范，替换为你的学科主题）
//   "Educational comparison infographic: Convex lens imaging for objects at different distances.
//    Left side: Object beyond focal point - real inverted image (实像倒立),
//    with light rays converging through the lens.
//    Right side: Object within focal point - virtual upright image (虚像正立),
//    with light rays diverging.
//    Clear labels in Chinese: 实像, 虚像, 倒立, 正立,
//    all Chinese text labels, educational infographic style"

// ===== 生成后验证（不可省略） =====
// 每张信息图生成后必须验证:
//   1. Read工具查看图片内容 — 检查数值、箭头方向、文字是否准确
//   2. 如果发现错误（数值错、箭头反、文字缺），修改prompt重新生成
//   3. 绝不发布"差不多"的图片 — 错误信息图比没有图更危险
//   4. 版本号递增: v1 → v2 → v3，每次修改都更新版本号

// ===== HTML嵌入方式 =====
// <img src="img/infographic_pX_vN.png" alt="描述" style="max-width:100%;height:auto;border-radius:10px;border:1px solid var(--line)">
// 注意: src 路径必须用 img/ 前缀（IMG_PREFIX='img/'），禁止 deploy/ 前缀（CloudStudio 部署后文件在根目录平铺）

// ===== 封面背景图生成 =====
// 封面背景图走同样的弹窗（勾「AI 生图」→ image-service）:
//   python .opencode/skills/image-service/core/text_to_image.py \
//     "Wide panoramic abstract theme background matching the subject, no central text, ..." \
//     -r 16:9 -o deploy/img
