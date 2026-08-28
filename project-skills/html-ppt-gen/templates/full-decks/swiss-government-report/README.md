# swiss-government-report

统一浅底政务 / 售前汇报模板。适合客户汇报、主管部门方案、年度工作报告。

## 视觉规则

- 浅底深字：`#edf2f4` / `#2b2d42`
- 单一红色锚点：`#ef233c`
- 发丝线分隔，强网格组织信息
- 少卡片、无阴影、无渐变、无随机深浅交替
- 标题使用中文宋体系，正文使用中文黑体系

## 使用方式

1. 复制 `deck.html` 到交付目录。
2. 同步复制或引用：
   - `assets/base.css`
   - `assets/themes/swiss-government.css`
   - `assets/runtime.js`
3. 按 `outline.md` 替换页面内容。
4. 打开浏览器验证：
   - 初始只显示第 1 页
   - `ArrowRight` / `Space` 可翻页
   - `ArrowLeft` 可返回
   - `?preview=3` 可直接预览第 3 页
5. 至少截图第 1、2、最后 1 页确认无重叠。

## 禁止

- 不要把多个 `.slide-content` 直接放进 `<body>`。
- 不要移除 `.presentation-container > .slide > .slide-content` 结构。
- 不要添加渐变、阴影或深浅页交替规则。
- 不要为单个项目临时改 runtime。
