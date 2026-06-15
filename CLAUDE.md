# CLAUDE.md —— 仓库维护说明

给后续维护者（包括 AI 助手）的快速上手指南。

## 这是什么

齐家·共情评估基准的**志愿者协作仓库**，面向公众。目标：邀请志愿者帮我们校准
心理教练对话的「共情（TES）」评估——首轮研究发现这把尺子很不可靠（评分者偏差占
总方差 54%，共情量表 ICC≈0）。

志愿者通过 **Pull Request** 贡献两类内容：

1. **共情锚定示例**（`tasks/01-anchor-book/`）：为每个共情题目补充 1–7 分的对话示例。
2. **补充极端对话**（`tasks/02-new-dialogs/`）：提交明显很好/很差的新对话，拉开分数分布。

整体介绍见 [README.md](README.md)。

## 数据从哪来 · 如何重建

**`data/` 下的内容全部由脚本派生，请勿手工修改。**

- 源数据：内部研究仓库 `rater-analysis` 的 `data/raw/`（问卷、对话、逐人评分、AI 低分导出）。该原始数据**不在本公开仓库内**。
- 重建命令：
  ```bash
  uv run python scripts/build_dataset.py --src /path/to/rater-analysis/data/raw
  ```
- 脚本生成：`data/questionnaire.md`、`data/dialogs/`、`data/scores/`、
  `data/low-rating-pool/`、`tasks/01-anchor-book/anchors/` 的空模板、
  `data/scoring-prompt.md` 占位文件。

**手工维护、脚本不会覆盖的文件：** `README.md`、`CONTRIBUTING.md`、`ROADMAP.md`、
各 task 的 `README.md` / `TEMPLATE.md`、`tasks/02-new-dialogs/submissions/`（志愿者提交）、
`LICENSE`、本文件。

> 改动数据逻辑（如重新聚合、换排序）请改 `scripts/build_dataset.py` 后重新生成，
> 不要直接编辑产物文件。

## 两套不同的评分（重要，别混）

- `data/dialogs/`（20 段）：**36 位人工评分者**，TES 1–7 量尺。
- `data/low-rating-pool/`（109 段）：**AI 评分器**，自有标准（≠1–7），已脱敏。

两者分数**不可直接比较**。详见 [data/README.md](data/README.md)。

## 关键数字

36 位评分者 × 20 段对话 × 9 个共情题目（去重后每格 n=36）；评分者偏差占总方差 54%；
共情量表 ICC≈0；20 段对话整体共情均值都在 4.3–5.7（无 ≥6 高分或 ≤4 低分）。

## 待办

- `data/scoring-prompt.md` 是占位文件，需团队成员上传 AI 评分器的打分 prompt。
- 后续阶段（网页浏览器、提交校验工具）见 [ROADMAP.md](ROADMAP.md)。

## 约定

- **仓库内所有面向人的文字一律使用中文。** 例外：GitHub 界面按钮名（如 Fork、
  Pull Request、Commit changes）保留英文，因为志愿者在 GitHub 上看到的就是英文；
  代码标识符、文件名、CSV 列名保留英文。
- 修改后请校验 Markdown 内部链接不要断（仓库内相对链接应全部可达）。
