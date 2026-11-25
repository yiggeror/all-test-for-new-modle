# Rainroji Lo-Fi Four Seasons v2 — 用户需求与验收主控台

> **当前分支**：`feat/lofi-seasons-v2`
> **参考原型仓库**：[`yiggeror/Rainroji`](https://github.com/yiggeror/Rainroji)（`deliver/four-seasons-1080p` 分支）
> **最终交付目标**：一部完整的 **1920×1080（横屏 16:9，整数倍无损放大低像素网格）**、配有**高适配度精选 Lo-Fi 音乐**与**细腻生活感循环动态**的四季像素短片，并通过 **GitHub Release + Google Drive** 交付完整单文件成品视频。

---

## 协作分工（请编码 AI 首先阅读）

本仓库在同一工作区采用 **双角色迭代协作**：

| 角色 | 职责边界 | 负责维护的文件 |
|---|---|---|
| **用户 / 艺术总监（严格验收官）** | 提出高审美标准需求、审图审片、挑刺打回、把关配乐与成片质量；**非必要不编写业务代码** | `README.md`、`USER_BRIEF.md`、`REVIEW_LOG.md`、`references/` |
| **开发 / 渲染工程师（编码 AI）** | 拉取/参考 `Rainroji` 原型，完成场景重构、低像素风格化、氛围动态制作、配乐筛选混音、1080p 成片输出与交付 | `DEV_STATUS.md`、`project/`（或 `film/`）、`previews/`、`CREDITS.md` |

---

## 必读文档入口

1. **[`USER_BRIEF.md`](USER_BRIEF.md)** — **完整用户需求、审美红线、分场景改造细则、配乐规范与硬核验收清单（开工必读）**
2. **[`REVIEW_LOG.md`](REVIEW_LOG.md)** — **逐轮审片反馈与打回/放行记录（每次迭代后更新）**
3. **[`references/screenshots/`](references/screenshots/)** — **用户提供的 4 张核心景别与像素颗粒感参考截图**（`01_spring_ref.jpg` ~ `04_winter_ref.jpg`）
4. **`DEV_STATUS.md`**（由编码 AI 创建维护）— 汇报当前 Gate 进度、预览图/视频路径、参数对比与待确认项

---

## 当前阶段状态

- **状态**：**`COMPLETED / v2.9 FINAL PASSED`**（全片已于 2026-11-25 完成春/夏/冬四处主光源物理支撑补全的无损 8× 复核与正式发布成品五段全速实看实听终审，正式双渠道交付见 [`DELIVERY.md`](DELIVERY.md) 与 [`REVIEW_LOG.md`](REVIEW_LOG.md) Round 34）
- **v2.9 正式双渠道链接（逐字节 100% 一致，`141,477,520` 字节，SHA-256 `f9bc6f87...0dbd9afe`）**：
  - **GitHub Release**：<https://github.com/yiggeror/all-test-for-new-modle/releases/tag/v2.9-rainroji-lofi-1080p>
  - **Google Drive**：<https://drive.google.com/file/d/1Q3Fo0iPCv7TX2ZOEQtlQYj2yAP6wIgMr/view?usp=drivesdk>
- **v2.9 终版亮点**：`1920×1080`（`320×180` 6× 最近邻整数放大）· 30 fps · `5,917` 帧 · `3:17.23`（严格不加时）；春（街灯 + 院灯）、夏（雨夜街灯）、冬（雪夜街灯）四处主光源全面补齐在 `320×180` 下 100% 连续可读的老式挑臂、斜撑、抱箍与搪瓷灯罩，并无损保留锁定版秋景 v2.7 倚树少女 + 有机秋风 + 独立落叶、冬夜 v2.8 暖窗贴桌自然翻书、春暖地单猫、夏红霓虹水洼及 v2.4 尾声冬夜雪风渐强音轨。
















