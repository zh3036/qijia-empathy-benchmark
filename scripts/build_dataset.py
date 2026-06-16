#!/usr/bin/env python3
"""
build_dataset.py —— 从内部研究数据派生出面向志愿者的公开数据集。

读取原始研究文件（问卷、对话、逐人评分、AI 低分导出），生成干净、便于提 PR 的
文件，写入仓库的 data/ 和 tasks/ 目录。

预期的源文件位于 --src（默认：../rater-analysis/data/raw）：
  问卷内容.csv            问卷定义（3 个维度，JSON 文本）
  问卷对话内容0305.csv     20 段人工评分对话（教练/家长轮次）
  问卷0305.csv            约 1.8 万行逐人评分（长表格式）
  insight-low-rating.json AI 评分、已脱敏的低分对话（109 段）

用法：
  uv run python scripts/build_dataset.py            # 在仓库根目录运行
  uv run python scripts/build_dataset.py --src /path/to/raw
"""

import argparse
import csv
import json
import math
from collections import defaultdict
from pathlib import Path

csv.field_size_limit(10**7)

REPO_ROOT = Path(__file__).resolve().parents[1]

# TES 共情量表的 9 个评分题目（q1–q9）。evaluation_notes 为自由文本，已排除。
TES_ITEMS = ["q1", "q2", "q3", "q4", "q5", "q6", "q7", "q8", "q9"]
ITEM_SLUG = {
    "q1": "concern", "q2": "expressiveness", "q3": "resonance", "q4": "warmth",
    "q5": "attunement", "q6": "cognitive-framework", "q7": "understanding-feelings",
    "q8": "acceptance-feelings", "q9": "responsiveness",
}
# 题目简称（中文），用于表格对照；文件名仍用上面的英文 slug。
ITEM_CN = {
    "q1": "关切", "q2": "表现力", "q3": "情感共鸣", "q4": "温暖", "q5": "内在同频",
    "q6": "理解认知框架", "q7": "理解感受", "q8": "接纳感受", "q9": "回应性",
}


# --------------------------------------------------------------------------- #
# 辅助函数
# --------------------------------------------------------------------------- #
def read_csv(path: Path):
    with open(path, encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def trimmed_mean(values, trim_frac=0.1):
    """截尾均值：去掉两端各 trim_frac 比例后取平均。"""
    if not values:
        return None
    s = sorted(values)
    k = int(math.floor(len(s) * trim_frac))
    core = s[k: len(s) - k] if len(s) - 2 * k > 0 else s
    return sum(core) / len(core)


def mean(values):
    return sum(values) / len(values) if values else None


def fmt(x, nd=2):
    return "—" if x is None else f"{x:.{nd}f}"


def write(path: Path, text: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


# --------------------------------------------------------------------------- #
# 1. 问卷（仅 TES）
# --------------------------------------------------------------------------- #
def load_tes_questionnaire(src: Path):
    rows = read_csv(src / "问卷内容.csv")
    for r in rows:
        d = json.loads(r["content"])
        if "TES" in d.get("name", ""):
            items = {}
            for inp in d["inputs"]:
                vn = inp.get("variableName")
                if vn in TES_ITEMS:
                    items[vn] = {
                        "question": inp["question"],
                        "description": inp["description"],
                        "choices": inp["choices"],
                    }
            return d["name"], items
    raise SystemExit("在 问卷内容.csv 中未找到 TES 维度")


def write_questionnaire(name, items, out: Path):
    lines = [
        f"# 评分量表：{name}",
        "",
        "本仓库聚焦 **共情（TES）** 维度——也是目前最需要校准的量表"
        "（首轮评分者一致性偏低，ICC 接近 0）。下面是 9 个被评分的题目，"
        "每题量尺为 **1（很低）—— 7（很高）**。",
        "",
        "> **术语：** 量表沿用心理咨询领域的标准措辞，文中的「咨询师」即本项目对话中"
        "被评估的「教练」（AI 教练），「来访者」即对话中的家长/用户，两者同指。",
        "",
        "> 原研究还包含「无条件积极关注」和「咨访同盟（WAI）」两个维度，"
        "本志愿者任务暂不涉及，故未收录。",
        "",
    ]
    for q in TES_ITEMS:
        it = items[q]
        lines += [
            f"## {q} · {it['question']}",
            "",
            it["description"],
            "",
            "量尺：1 2 3 4 5 6 7（1 = 很低，7 = 很高）",
            "",
        ]
    write(out, "\n".join(lines))
    return items


# --------------------------------------------------------------------------- #
# 2. 评分：聚合 + 原始（仅 TES）
# --------------------------------------------------------------------------- #
def load_scores(src: Path):
    rows = read_csv(src / "问卷0305.csv")
    # 去除意外的重复提交：部分评分者对同一 (评分者, 对话, 题目) 有多条几乎相同、
    # 仅相差毫秒的记录（前端 bug）。每个 (评分者, 对话, 题目) 只保留最新一条，
    # 确保每位评分者只计一次。
    latest = {}  # (user, name, qid) -> (answer_time, value, dialog_id)
    name_to_id = {}
    for r in rows:
        if r["dimension_id"] != "1":
            continue
        qid = r["question_id"]
        if qid not in TES_ITEMS:
            continue
        val = r["answer_value"].strip()
        if not val.isdigit():
            continue
        v = int(val)
        if not 1 <= v <= 7:
            continue
        name = r["dialog_name"]
        name_to_id[name] = r["dialog_id"]
        k = (r["user_id"], name, qid)
        t = r.get("answer_time", "")
        if k not in latest or t > latest[k][0]:
            latest[k] = (t, v, r["dialog_id"])

    raw = []
    by_di = defaultdict(lambda: defaultdict(list))
    for (user, name, qid), (_, v, did) in latest.items():
        by_di[name][qid].append(v)
        raw.append((user, name, did, qid, v))
    return raw, by_di, name_to_id


def dialog_sort_key(name):
    return (0, int(name)) if name.isdigit() else (1, name)


def write_scores(by_di, raw, out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    names = sorted(by_di.keys(), key=dialog_sort_key)

    # 聚合数据
    agg_rows = []
    for name in names:
        row = {"dialog_name": name}
        all_vals = []
        for q in TES_ITEMS:
            vals = by_di[name][q]
            all_vals += vals
            row[f"{q}_mean"] = mean(vals)
            row[f"{q}_trim"] = trimmed_mean(vals)
            row[f"{q}_n"] = len(vals)
        row["tes_overall_mean"] = mean(all_vals)
        row["tes_overall_trim"] = trimmed_mean(all_vals)
        agg_rows.append(row)

    # 写出聚合 CSV
    csv_path = out_dir / "empathy-by-dialog.csv"
    cols = (["dialog_name"]
            + [f"{q}_{s}" for q in TES_ITEMS for s in ("mean", "trim", "n")]
            + ["tes_overall_mean", "tes_overall_trim"])
    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for row in agg_rows:
            w.writerow({k: (fmt(v) if isinstance(v, float) else v)
                        for k, v in row.items()})

    # 写出可读的 Markdown（逐题截尾均值）
    md = ["# 共情（TES）逐对话评分（聚合）",
          "",
          "共 **36 位评分者**。每格为该题的**截尾均值**（去掉最高/最低各 10% 后取平均），"
          "按整体均值排序。每格的有效评分人数 n（≤36）见 "
          "[`empathy-by-dialog.csv`](empathy-by-dialog.csv)；原始逐人评分见 "
          "[`empathy-raw.csv`](empathy-raw.csv)。",
          "",
          "| 对话 | " + " | ".join(TES_ITEMS) + " | **整体** |",
          "|---|" + "---|" * (len(TES_ITEMS) + 1)]
    for row in sorted(agg_rows, key=lambda r: -(r["tes_overall_trim"] or 0)):
        cells = [f"`{row['dialog_name']}`"]
        cells += [fmt(row[f"{q}_trim"], 1) for q in TES_ITEMS]
        cells += [f"**{fmt(row['tes_overall_trim'], 2)}**"]
        md.append("| " + " | ".join(cells) + " |")
    md += ["", "题目对照：" + "，".join(f"{q}={ITEM_CN[q]}" for q in TES_ITEMS)]
    write(out_dir / "empathy-by-dialog.md", "\n".join(md))

    # 写出原始逐人评分 CSV
    with open(out_dir / "empathy-raw.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["rater_id", "dialog_name", "dialog_id", "item", "score"])
        w.writerows(sorted(raw, key=lambda x: (dialog_sort_key(x[1]), x[3], x[0])))

    return {r["dialog_name"]: r for r in agg_rows}


# --------------------------------------------------------------------------- #
# 3. 对话（20 段人工评分）
# --------------------------------------------------------------------------- #
def write_dialogs(src: Path, agg_by_name, name_to_id, out_dir: Path):
    rows = read_csv(src / "问卷对话内容0305.csv")
    by_name = {}
    for r in rows:
        by_name[r["name"]] = r
    names = sorted(by_name.keys(), key=dialog_sort_key)

    index = ["# 20 段人工评分对话",
             "",
             "这 20 段对话由 36 位评分者用共情（TES）量表评过分。下表按"
             "**整体共情均值**排序——均值都在 4.3–5.7，没有明显的高分（≥6）或低分（≤4）样本，"
             "这正是志愿者任务要补充的。点击查看完整对话。",
             "",
             "| 对话 | 轮次 | TES 整体均值 | 文件 |",
             "|---|---|---|---|"]
    rows_for_index = []
    for name in names:
        r = by_name[name]
        turns = json.loads(r["content"])
        fname = f"dialog-{int(name):02d}.md" if name.isdigit() else f"dialog-{name}.md"
        agg = agg_by_name.get(name, {})
        overall = agg.get("tes_overall_trim")

        body = [f"# 对话 {name}",
                "",
                f"- 内部 id：`{r['id']}`",
                f"- 轮次：{len(turns)}",
                f"- 共情（TES）整体均值：**{fmt(overall, 2)}**"
                f"（逐题分见 [`../scores/empathy-by-dialog.md`](../scores/empathy-by-dialog.md)）",
                "",
                "---",
                ""]
        for t in turns:
            coach = (t.get("coach") or "").strip()
            parent = (t.get("parent") or "").strip()
            body.append(f"**第 {t.get('turn')} 轮**")
            body.append("")
            if coach:
                body.append(f"> 🧑‍🏫 **教练：** {coach}")
                body.append("")
            if parent:
                body.append(f"> 🙋 **来访者：** {parent}")
                body.append("")
        write(out_dir / fname, "\n".join(body))
        rows_for_index.append((name, len(turns), overall, fname))

    for name, nturns, overall, fname in sorted(
            rows_for_index, key=lambda x: -(x[2] or 0)):
        index.append(f"| `{name}` | {nturns} | {fmt(overall, 2)} | "
                     f"[{fname}]({fname}) |")
    write(out_dir / "index.md", "\n".join(index))
    return len(names)


# --------------------------------------------------------------------------- #
# 4. 低分对话池（AI 评分、已脱敏）—— 任务二的素材库
# --------------------------------------------------------------------------- #
def write_low_rating_pool(src: Path, out_dir: Path):
    data = json.load(open(src / "insight-low-rating.json", encoding="utf-8"))["data"]
    conv_dir = out_dir / "conversations"
    conv_dir.mkdir(parents=True, exist_ok=True)

    def dim(rec, key):
        det = rec.get("detail") or {}
        sd = det.get("ai_scoring_detail") or {}
        return (sd.get("dimension_scores") or {}).get(key)

    enriched = []
    for rec in data:
        det = rec.get("detail") or {}
        enriched.append({
            "cid": det.get("conversation_id") or rec.get("list_info", {}).get("conversation_id"),
            "title": (det.get("title") or "").strip(),
            "ai_rating": det.get("ai_rating"),
            "tes": dim(rec, "TES"),
            "wai": dim(rec, "WAI"),
            "prd": dim(rec, "PRD"),
            "rounds": det.get("round_count"),
            "masked": det.get("is_masked"),
            "messages": det.get("conversation_messages") or [],
            "insight": (det.get("insight_content") or "").strip(),
        })
    # 按 TES 升序排列（共情最差的排最前）—— 对任务二最有用
    enriched.sort(key=lambda e: (e["tes"] is None, e["tes"] if e["tes"] is not None else 99))

    role_label = {"user": "🙋 来访者", "assistant": "🧑‍🏫 教练",
                  "parent": "🙋 来访者", "coach": "🧑‍🏫 教练"}

    index = ["# 低分对话池（AI 评分，已脱敏）",
             "",
             "**注意：这是与上面 20 段对话不同的另一组数据。** 这里的 "
             f"**{len(enriched)} 段对话**由 **AI 评分器**打分（非 36 位人工评分者），"
             "已自动脱敏（`is_masked=True`），可公开。",
             "",
             "它的用途是**任务二的「找差对话」素材库**：这些对话整体评分偏低，"
             "你可以从中挑选共情（TES）明显很差的片段，作为新的低分对话提交。"
             "下表按 **AI 的 TES 分**升序排列（越靠前共情越差）。",
             "",
             "> AI 的评分标准与人工 1–7 量尺不同，仅供筛选参考，不要直接当作 1–7 分。",
             "",
             "| # | 标题 | AI综合 | TES | WAI | PRD | 轮次 | 文件 |",
             "|---|---|---|---|---|---|---|---|"]
    for i, e in enumerate(enriched, 1):
        fname = f"low-{i:03d}.md"
        body = [f"# {e['title'] or '(无标题)'}",
                "",
                f"- 对话 id：`{e['cid']}`",
                f"- AI 综合评分：{fmt(e['ai_rating'])}　|　TES：{fmt(e['tes'])}　|　"
                f"WAI：{fmt(e['wai'])}　|　PRD：{fmt(e['prd'])}",
                f"- 轮次：{e['rounds']}　|　已脱敏：{e['masked']}",
                ""]
        if e["insight"]:
            body += ["> **AI 洞察摘要：** " + e["insight"][:400], ""]
        body += ["---", ""]
        for m in e["messages"]:
            role = role_label.get(m.get("role"), m.get("role", "?"))
            content = (m.get("content") or "").strip()
            if content:
                body.append(f"**{role}：** {content}")
                body.append("")
        write(conv_dir / fname, "\n".join(body))
        index.append(
            f"| {i} | {e['title'] or '—'} | {fmt(e['ai_rating'])} | "
            f"{fmt(e['tes'])} | {fmt(e['wai'])} | {fmt(e['prd'])} | "
            f"{e['rounds']} | [{fname}](conversations/{fname}) |")
    write(out_dir / "index.md", "\n".join(index))
    return len(enriched)


# --------------------------------------------------------------------------- #
# 5. 锚定示例模板（每个 TES 题目一个）+ 评分 prompt 占位文件
# --------------------------------------------------------------------------- #
def write_anchor_templates(items, out_dir: Path):
    for q in TES_ITEMS:
        it = items[q]
        slug = ITEM_SLUG[q]
        lines = [
            f"# 锚定示例：{it['question']} · {q}",
            "",
            f"**题目描述：** {it['description']}",
            "",
            "> 注：题目描述里的「咨询师」即对话中被评估的「教练」（AI 教练），两者同指。",
            "",
            "**量尺：** 1（很低）—— 7（很高）",
            "",
            "为每个分数填入 1 段 2–3 轮对话摘录，把对应分数下的 `_（待补充）_` 替换成下面这种格式："
            "（详见本任务的 [README](../README.md) 和 [TEMPLATE](../TEMPLATE.md)）",
            "",
            "```markdown",
            "来源对话：#10，第 2 轮",
            "",
            "> **教练：** （摘录……）",
            "> **来访者：** （摘录……）",
            "",
            "为什么是这个分数：（一句话理由）",
            "```",
            "",
        ]
        for score in range(1, 8):
            tag = "　⭐（最缺，优先）" if score in (1, 2, 7) else ""
            lines += [f"## {score} 分示例{tag}", "", "_（待补充）_", ""]
        write(out_dir / f"{q}-{slug}.md", "\n".join(lines))

    # 锚定示例总览
    idx = ["# 锚定示例进度",
           "",
           "每个共情题目一个文件。认领一个分数槽，填入示例，提 PR。",
           "",
           "| 题目 | 文件 |",
           "|---|---|"]
    for q in TES_ITEMS:
        idx.append(f"| {q} · {items[q]['question']} | "
                   f"[{q}-{ITEM_SLUG[q]}.md]({q}-{ITEM_SLUG[q]}.md) |")
    write(out_dir / "index.md", "\n".join(idx))


def write_scoring_prompt_placeholder(out: Path):
    write(out, "\n".join([
        "# 评分 Prompt（待上传）",
        "",
        "> 🚧 **占位文件 —— 由团队成员补充。**",
        "",
        "本文件用于存放 **AI 评分器的打分 prompt**（即让模型按共情量表给对话打分时"
        "使用的系统/指令 prompt）。",
        "",
        "首轮 20 段对话的分数来自 **36 位人工评分者**，并非 AI；而 "
        "[`../low-rating-pool/`](low-rating-pool/index.md) 的分数来自一个 AI 评分器。"
        "该 AI 评分器使用的 prompt 尚未收录。",
        "",
        "**待办（团队成员）：** 将实际使用的评分 prompt 粘贴到下方。",
        "",
        "```",
        "（在此粘贴评分 prompt）",
        "```",
    ]))


# --------------------------------------------------------------------------- #
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default=str(REPO_ROOT.parent / "rater-analysis" / "data" / "raw"))
    args = ap.parse_args()
    src = Path(args.src)
    if not src.exists():
        raise SystemExit(f"源数据目录不存在：{src}")

    data = REPO_ROOT / "data"
    name, items = load_tes_questionnaire(src)
    write_questionnaire(name, items, data / "questionnaire.md")

    raw, by_di, name_to_id = load_scores(src)
    agg = write_scores(by_di, raw, data / "scores")

    n_dialogs = write_dialogs(src, agg, name_to_id, data / "dialogs")
    n_low = write_low_rating_pool(src, data / "low-rating-pool")

    write_anchor_templates(items, REPO_ROOT / "tasks" / "01-anchor-book" / "anchors")
    write_scoring_prompt_placeholder(data / "scoring-prompt.md")

    print(f"✓ 问卷：{len(items)} 个 TES 题目")
    print(f"✓ 对话：{n_dialogs} 段")
    print(f"✓ 聚合 + 原始评分：{len(raw)} 条 TES 评分")
    print(f"✓ 低分对话池：{n_low} 段对话")
    print(f"✓ 锚定示例模板：{len(items)} 个")
    print("✓ 评分 prompt 占位文件")


if __name__ == "__main__":
    main()
