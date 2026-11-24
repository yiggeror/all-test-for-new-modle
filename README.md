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

- **当前 Gate**：`v2.2 / Gate 2.2 — 全面审美返工：清除 2D 贴纸感/比例穿帮/头身分离，重做物理光影融合与四季差异化动态`（`v2.1` 已退回重做，详见 [`REVIEW_LOG.md`](REVIEW_LOG.md) Round 9）
- **绝对红线（一票否决）**：严禁硬 P 感 2D 贴纸、严禁违背真实世界比例的巨型动物、严禁头身分离、严禁跨季复用小鸟模板、严禁实心白蛆烟雾与条形码水洼。
- **保持不变的已锁基线**：`320×180`（6× 最近邻整数放大至 `1920×1080` @ 30fps）、四季紧致构图、11 秒无缝循环、**Purrple Cat《Green Tea》（CC BY 4.0 全曲）** 与 48/96/144 秒乐句转场均保持不变。
- **下一步**：编码 AI 提交 `previews/gate_2_2/` 四季样片与原尺寸动作峰值静帧后，我将从构图、比例、光影融合、解剖连贯与跨季多样性全维度严审，彻底过关后再组装发布 v2.2。
