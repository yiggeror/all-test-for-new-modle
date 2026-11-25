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

- **当前 Gate**：**`v2.5 / Gate 3.5 — v2.5 最终 1080p 合片与双渠道发布`**（Gate 2.5 返工包 `6ef7236` 已通过盲看与无损复审 **`PASSED`**，详见 [`REVIEW_LOG.md`](REVIEW_LOG.md) Round 20）
- **当前最新已发布成片（v2.4，逐字节 100% 一致，`132,852,726` 字节）**：
  - **GitHub Release**：<https://github.com/yiggeror/all-test-for-new-modle/releases/tag/v2.4-rainroji-lofi-1080p>
  - **Google Drive**：<https://drive.google.com/file/d/1b5rSQKERX4LZ1RH_VFj7ELRzqb5C5lCW/view?usp=drivesdk>
- **v2.5 已定版亮点**：① 春/秋整冠连续 FBM 风场相位波 ±1px 整数像素叶颤（71.1% / 74.0% 覆盖、零果冻）；② 春猫全程 330 帧留在暖橘受光院落带内舒展扁弧往返（零钻暗影隐身、零竖黑块、零刷新刷怪）；③ 秋景报刊亭前 1:1 真实 3D 站立低头看报路人（胸前双肘自然托报、清晰可读的翻页动作、真实接地投影），配合 88 条双侧空中落叶与路牙地面积叶随风轻动；④ 夏、冬与 v2.4 尾声冬夜雪风渐强音轨 100% 无损沿用（精确 `3:17.23`）。











