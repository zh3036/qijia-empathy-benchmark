# 如何贡献

感谢参与！**不需要任何编程基础**，所有操作都能在 GitHub 网页上完成。

## 第一步：选一个任务

| 任务 | 你要做的事 | 说明 |
|---|---|---|
| ① 共情锚定示例 | 在已有的题目文件里，为某个分数填一段对话例子 | [tasks/01-anchor-book/](tasks/01-anchor-book/README.md) |
| ② 补充极端对话 | 新建一个文件，放入一段明显很好/很差的对话 | [tasks/02-new-dialogs/](tasks/02-new-dialogs/README.md) |

## 第二步：找素材

在 [`data/`](data/README.md) 里翻：

- [`data/dialogs/`](data/dialogs/index.md) —— 20 段已评分对话，按共情均值排序。
- [`data/low-rating-pool/`](data/low-rating-pool/index.md) —— 109 段 AI 评分的低分对话（任务二的现成素材）。
- [`data/scores/empathy-by-dialog.md`](data/scores/empathy-by-dialog.md) —— 每段对话每个题目的分数。

## 第三步：提交一个 Pull Request（PR）

PR 是 GitHub 上“把你的修改提议给仓库”的标准方式。**全程在网页上点鼠标完成，不需要 git、不需要命令行、不需要把代码下载到本地。**

### 任务一：修改一个已有文件

1. 在本仓库页面右上角点 **Fork**（如弹出确认页，点 **Create fork**）——你得到一份属于自己的拷贝。
2. 在**你自己的**拷贝里，用顶部的文件列表点进 `tasks` → `01-anchor-book` → `anchors`，点开你要改的题目文件（如 `q4-warmth.md`）。
3. 点文件右上角的 ✏️ **铅笔图标**（Edit this file），直接在网页里编辑：把某个分数下的 `_（待补充）_` 替换成你的例子。
4. 拉到页面底部，点绿色按钮 **Commit changes…**，在弹窗里点 **Commit changes** 确认（GitHub 会自动为你新建一个分支，名字无所谓）。
5. GitHub 顶部会出现一条提示 **Compare & pull request**，点它（或切到 **Pull requests** 标签 → **New pull request**）。
6. **关键一步**：确认方向是 **base repository = 原仓库 / base: `main`** ← **head repository = 你的用户名/仓库**。默认通常就是对的。
7. 标题会自动填好，点 **Create pull request**。会弹出一个简短清单（PR 模板），照着勾选/填写即可。提交。

### 任务二：新建一个文件

同上，但第 2–4 步改为：进入 `tasks` → `02-new-dialogs` → `submissions`，点 **Add file → Create new file**，在文件名框里输入文件名（如 `good-情绪命名.md`，文件名用中文没问题，**不要**带路径或斜杠），按模板填好内容，再 **Commit changes**，然后同样走第 5–7 步提 PR。

提交后，维护者会看到一个清晰的前后对比（diff），合并它，或留言请你微调。

> 不熟悉 PR？GitHub 官方图解：<https://docs.github.com/zh/pull-requests/collaborating-with-pull-requests/proposing-changes-to-your-work-with-pull-requests/creating-a-pull-request-from-a-fork>

## 什么是好的贡献

- **来源可查。** 每个例子都注明出处（`data/dialogs/` 的对话编号，或 `data/low-rating-pool/` 的对话文件）。
- **片段精炼。** 锚定示例用 2–3 轮对话就够，别整段贴。
- **理由清楚。** 用一句话说明“为什么是这个分数 / 为什么明显好或差”。
- **聚焦共情。** 我们当前只做共情（TES）维度（见 [`data/questionnaire.md`](data/questionnaire.md)）。

## 一段一个 PR

每个 PR 尽量只做一件小事（填一个分数槽，或提一段对话）。小 PR 更快被合并。

## 关于这些对话

这些是心理咨询/教练场景的对话，涉及家庭、孩子、情绪。`data/low-rating-pool/` 已脱敏。请以尊重的态度对待对话中的当事人，不要在仓库外传播或截图。**不要提交任何含真实可识别身份信息的内容。**
