# 数据说明

这里是志愿者要翻阅的全部素材。

## ⚠️ 两套不同的评分，别搞混

| | 来源 | 评分者 | 量尺 | 用途 |
|---|---|---|---|---|
| **20 段对话** (`dialogs/`) | 首轮研究 | **36 位人工评分者** | TES 1–7 | 任务一锚定示例的主要来源 |
| **109 段对话** (`low-rating-pool/`) | 线上低分导出 | **AI 评分器** | AI 自有标准（≠1–7） | 任务二“找差对话”的素材库 |

两者的分数**不可直接比较**。AI 分仅用于帮你筛选“哪些对话大概率很差”。

## 文件清单

| 路径 | 内容 |
|---|---|
| [`questionnaire.md`](questionnaire.md) | 共情（TES）9 个题目：名称、描述、1–7 量尺。本仓库只做共情维度。 |
| [`dialogs/`](dialogs/index.md) | 20 段人工评分对话，每段一个文件，含该对话的共情均值。`index.md` 按分数排序。 |
| [`scores/`](scores/README.md) | 评分数据：聚合表（逐对话逐题均值）+ 原始逐人评分。 |
| [`low-rating-pool/`](low-rating-pool/index.md) | 109 段 AI 评分的低分对话（已脱敏），按 AI 的 TES 分升序。任务二素材。 |
| [`scoring-prompt.md`](scoring-prompt.md) | 🚧 占位文件——AI 评分器的打分 prompt，待团队成员上传。 |

## 隐私

- `low-rating-pool/` 的对话 `is_masked=True`，姓名等已自动替换（如 `xx11`、`[REDACTED]`）。
- `dialogs/` 为 AI 教练系统产生的对话，已去除内部字段（来源、训练集标记、运行 id），只保留对话正文。
- 请勿提交任何含真实可识别身份信息的新内容。

## 复现

所有派生文件由 [`../scripts/build_dataset.py`](../scripts/build_dataset.py) 从原始研究数据生成：

```bash
uv run python scripts/build_dataset.py --src /path/to/raw
```
