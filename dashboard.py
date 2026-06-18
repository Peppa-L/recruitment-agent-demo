# -*- coding: utf-8 -*-
"""
招聘数据可视化看板 — dashboard.py
从 AI 解析结果中聚合数据，生成招聘流程可视化。
"""
import streamlit as st
import pandas as pd
import math
from typing import Dict, Any, List, Optional

COLORS = {
    "简历筛选": "#FFA726", "面试已安排": "#42A5F5",
    "一面通过": "#66BB6A", "一面未通过": "#EF5350",
    "二面已安排": "#AB47BC", "二面通过": "#26A69A",
    "二面未通过": "#EC407A", "Offer沟通中": "#FFCA28",
    "已发Offer": "#5C6BC0", "已入职": "#2E7D32",
    "已淘汰": "#BDBDBD",
}

STAGE_ORDER = [
    "简历筛选", "面试已安排", "一面通过", "一面未通过",
    "二面已安排", "二面通过", "二面未通过",
    "Offer沟通中", "已发Offer", "已入职", "已淘汰"
]


def safe_int(val, default=None):
    """安全转整数，NaN → None"""
    if val is None:
        return default
    try:
        f = float(val)
        if math.isnan(f):
            return default
        return int(f)
    except (ValueError, TypeError):
        return default


def build_pipeline_from_session(parsed_list: List[Dict]) -> pd.DataFrame:
    """从 session_state 累积的 AI 解析结果构建管道 DataFrame。

    核心逻辑：
      - 同一候选人出现在多个场景时，合并为一行
      - 展示完整的「阶段演进轨迹」而非只显示当前阶段
      - 薪资 / 评价 / 决策 取最新非空值
    """
    # 先按 scenario_id 去重（保留最新）
    seen_sids = {}
    for item in parsed_list:
        sid = item.get("scenario_id", item.get("scenario_name", ""))
        if sid:
            seen_sids[sid] = item
        else:
            seen_sids[f"_auto_{len(seen_sids)}"] = item

    # 收集每个候选人的所有片段
    from collections import defaultdict
    candidate_fragments = defaultdict(list)  # name -> [(stage, row_data)]

    for item in seen_sids.values():
        parsed = item.get("parsed", {})
        if not parsed or not parsed.get("candidates"):
            continue
        for cand in parsed.get("candidates", []):
            name = cand.get("name", "").strip()
            if not name or name == "未识别":
                continue

            iv = cand.get("interview_info", {}) or {}
            fb = cand.get("feedback", {}) or {}
            sal = cand.get("salary", {}) or {}
            dec = cand.get("decision", {}) or {}

            candidate_fragments[name].append({
                "position": cand.get("position", ""),
                "stage": cand.get("stage", "简历筛选"),
                "date": iv.get("date", ""),
                "time": iv.get("time", ""),
                "type": iv.get("type", ""),
                "interviewers": iv.get("interviewers", []),
                "score": safe_int(fb.get("score")),
                "overall": fb.get("overall", ""),
                "positive": fb.get("positive", []),
                "negative": fb.get("negative", []),
                "salary_expected": sal.get("expected", ""),
                "salary_budget": sal.get("budget", ""),
                "salary_conclusion": sal.get("conclusion", ""),
                "decision": dec.get("result", ""),
                "next_step": dec.get("next_step", ""),
                "parse_time": item.get("parse_time", ""),
            })

    # 合并每个候选人
    rows = []
    for name, fragments in candidate_fragments.items():
        # 按解析时间排序（旧→新）
        fragments.sort(key=lambda f: f["parse_time"])

        # 去重阶段：同一阶段只保留最后一次出现
        seen_stages = {}
        for f in fragments:
            seen_stages[f["stage"]] = f
        unique_fragments = list(seen_stages.values())
        unique_fragments.sort(key=lambda f: f["parse_time"])

        # 阶段演进轨迹
        stage_path = " → ".join([f["stage"] for f in unique_fragments])

        # ── 智能合并：每个字段从最新片段向旧片段回溯，取第一个非空值 ──
        # 这样后续场景（如二面反馈）不会用空值覆盖前面场景（如一面安排）的有效数据

        def _last_nonempty(field: str, fragments: list, reverse=True):
            """从最新片段向旧回溯，返回第一个非空非 None 值。"""
            items = reversed(fragments) if reverse else fragments
            for f in items:
                val = f.get(field, "")
                if val and str(val).strip():
                    return val
            return ""

        # 职位、阶段：取最新
        latest = fragments[-1]
        merged_position = _last_nonempty("position", fragments)
        merged_stage = latest["stage"]

        # 面试日期/时间/方式：逐字段回溯非空
        merged_date = _last_nonempty("date", fragments)
        merged_time = _last_nonempty("time", fragments)
        merged_type = _last_nonempty("type", fragments)

        # 面试官：全量去重并集（含所有轮次）
        all_interviewers = []
        for f in unique_fragments:
            for iv in f.get("interviewers", []):
                if iv and iv not in all_interviewers:
                    all_interviewers.append(iv)

        # 评价：合并去重 + 取最高分
        all_positive = []
        all_negative = []
        all_overalls = []
        best_score = None
        for f in unique_fragments:
            s = f.get("score")
            if s is not None and (best_score is None or s > best_score):
                best_score = s
            o = f.get("overall", "")
            if o and o not in all_overalls:
                all_overalls.append(o)
            for p in f.get("positive", []):
                if p and p not in all_positive:
                    all_positive.append(p)
            for n in f.get("negative", []):
                if n and n not in all_negative:
                    all_negative.append(n)

        eval_lines = []
        if best_score is not None:
            eval_lines.append(f"评分: {best_score}/100")
        for o in all_overalls:
            eval_lines.append(o)
        for p in all_positive:
            eval_lines.append(f"✅ {p}")
        for n in all_negative:
            eval_lines.append(f"⚠️ {n}")

        # 薪资：每个子字段回溯非空
        sal_exp = _last_nonempty("salary_expected", fragments)
        sal_bud = _last_nonempty("salary_budget", fragments)
        sal_con = _last_nonempty("salary_conclusion", fragments)
        salary_parts = []
        if sal_exp:
            salary_parts.append(f"期望: {sal_exp}")
        if sal_bud:
            salary_parts.append(f"预算: {sal_bud}")
        if sal_con:
            salary_parts.append(sal_con)
        salary_text = " / ".join(salary_parts) if salary_parts else ""

        # 决策 & 下一步：回溯非空
        merged_decision = _last_nonempty("decision", fragments)
        merged_next = _last_nonempty("next_step", fragments)

        rows.append({
            "候选人": name,
            "应聘职位": merged_position,
            "当前阶段": merged_stage,
            "阶段演进": stage_path,
            "面试日期": merged_date,
            "面试时间": merged_time,
            "面试方式": merged_type,
            "面试官": ", ".join(all_interviewers),
            "面试评价": "\n".join(eval_lines) if eval_lines else "",
            "薪资讨论": salary_text,
            "决策": merged_decision,
            "下一步": merged_next,
            "数据来源": "🤖 AI 解析（多段合并）" if len(unique_fragments) > 1 else "🤖 AI 解析",
        })

    return pd.DataFrame(rows)


def render_kpi_cards(df: pd.DataFrame):
    total = len(df)  # 去重合并后就是唯一候选人数
    passed = df[df["当前阶段"].str.contains("通过|Offer|入职", na=False)]
    scheduled = df[df["当前阶段"].str.contains("面试已安排|已安排", na=False)]
    interviewed = df[df["当前阶段"].str.contains("通过|未通过|Offer|入职", na=False)]
    pass_rate = f"{len(passed)/max(len(interviewed), 1)*100:.0f}%" if len(interviewed) > 0 else "—"

    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        st.metric("在招职位", "3", delta="1个紧急")
    with c2:
        st.metric("候选人总数", total, delta=f"+{len(scheduled)} 待面" if len(scheduled) else None)
    with c3:
        st.metric("面试已安排", len(scheduled))
    with c4:
        st.metric("通过率", pass_rate)
    with c5:
        multi_source = len(df[df["数据来源"].str.contains("多段合并", na=False)])
        st.metric("全流程追踪", f"{multi_source}/{total}" if total > 0 else "—",
                  help="经过多轮解析、完整追踪阶段演进的候选人占比")


def render_pipeline_funnel(df: pd.DataFrame):
    st.subheader("招聘管道")
    stage_counts = {}
    for stage in STAGE_ORDER:
        c = len(df[df["当前阶段"] == stage])
        if c > 0:
            stage_counts[stage] = c
    if not stage_counts:
        st.info("暂无数据，请先在「AI 智能解析」中解析聊天记录")
        return
    max_c = max(stage_counts.values())
    for stage, count in stage_counts.items():
        r = count / max_c
        color = COLORS.get(stage, "#78909C")
        c1, c2 = st.columns([1, 3])
        with c1:
            st.markdown(f"**{stage}**")
        with c2:
            st.markdown(f"""
            <div style="display:flex;align-items:center;margin-bottom:6px;">
                <div style="flex-grow:1;background:#e0e0e0;border-radius:4px;height:26px;">
                    <div style="width:{r*100}%;background:{color};border-radius:4px;height:100%;
                         display:flex;align-items:center;padding-left:8px;color:white;font-weight:bold;font-size:0.85em;">
                    </div>
                </div>
                <span style="margin-left:10px;font-weight:bold;min-width:30px;">{count}人</span>
            </div>""", unsafe_allow_html=True)


def render_candidate_table(df: pd.DataFrame):
    st.subheader("候选人列表")
    if df.empty:
        st.info("暂无数据，请先在「AI 智能解析」中解析聊天记录")
        return
    cols = ["候选人", "应聘职位", "当前阶段", "阶段演进", "面试日期", "面试官", "面试评价", "薪资讨论", "下一步"]
    cols = [c for c in cols if c in df.columns]
    st.dataframe(
        df[cols], width="stretch", hide_index=True,
        column_config={
            "候选人": st.column_config.TextColumn("候选人", width="small"),
            "应聘职位": st.column_config.TextColumn("应聘职位", width="small"),
            "当前阶段": st.column_config.TextColumn("当前阶段", width="small"),
            "阶段演进": st.column_config.TextColumn("阶段演进", width="large"),
            "面试日期": st.column_config.TextColumn("面试日期", width="small"),
            "面试官": st.column_config.TextColumn("面试官", width="medium"),
            "面试评价": st.column_config.TextColumn("面试评价", width="large"),
            "薪资讨论": st.column_config.TextColumn("薪资讨论", width="medium"),
            "下一步": st.column_config.TextColumn("下一步", width="medium"),
        },
    )


def render_interview_schedule(df: pd.DataFrame):
    st.subheader("面试日程")
    scheduled = df[df["面试日期"].notna() & (df["面试日期"] != "")].copy()
    if scheduled.empty:
        st.info("暂无已安排的面试")
        return
    scheduled = scheduled.sort_values("面试日期")
    for _, row in scheduled.iterrows():
        with st.container(border=True):
            c1, c2, c3 = st.columns([1, 2, 1])
            with c1:
                st.markdown(f"### {row['面试日期']}")
                st.caption(f"⏰ {row.get('面试时间', '待定')}")
                st.caption(f"📹 {row.get('面试方式', '')}")
            with c2:
                st.markdown(f"**{row['候选人']}** — {row['应聘职位']}")
                st.caption(f"面试官: {row.get('面试官', '待定')}")
                fb = str(row.get("面试评价", ""))
                if fb and fb != "nan":
                    st.caption(fb[:150])
            with c3:
                stage = row.get("当前阶段", "")
                color = COLORS.get(stage, "#78909C")
                st.markdown(
                    f"<span style='background:{color};color:white;padding:4px 12px;"
                    f"border-radius:12px;font-size:0.85em;'>{stage}</span>",
                    unsafe_allow_html=True)


def render_full_dashboard(pipeline_df: pd.DataFrame):
    """渲染完整的招聘看板"""
    render_kpi_cards(pipeline_df)
    st.markdown("---")
    t1, t2, t3 = st.tabs(["管道漏斗", "候选人列表", "面试日程"])
    with t1:
        render_pipeline_funnel(pipeline_df)
    with t2:
        render_candidate_table(pipeline_df)
    with t3:
        render_interview_schedule(pipeline_df)


def render_candidate_resume(candidate: Dict[str, Any]):
    """渲染候选人简历卡片"""
    with st.container(border=True):
        c1, c2, c3 = st.columns([2, 1, 1])
        with c1:
            st.markdown(f"### {candidate['name']} — {candidate['position']}")
            edu = candidate.get("education", [])
            if edu:
                e = edu[0]
                st.caption(f"🎓 {e.get('school','')} · {e.get('degree','')} · {e.get('major','')}")
        with c2:
            st.metric("工作年限", f"{candidate.get('work_years', 0)}年")
            st.caption(f"📍 {candidate.get('current_location', '')}")
        with c3:
            st.metric("当前薪资", candidate.get("current_salary", ""))
            st.caption(f"期望: {candidate.get('expected_salary', '')}")

        with st.expander("💼 工作经历", expanded=True):
            for exp in candidate.get("work_experience", []):
                st.markdown(f"**{exp.get('company','')}** — {exp.get('position','')}")
                st.caption(f"{exp.get('start','')} ~ {exp.get('end','')} | {exp.get('industry','')}")
                st.markdown(f"_{exp.get('description','')[:200]}_")
                st.markdown("---")

        c1, c2 = st.columns(2)
        with c1:
            skills = candidate.get("skills", [])
            if skills:
                st.markdown("**技能**: " + " ".join([f"`{s}`" for s in skills[:10]]))
        with c2:
            certs = candidate.get("certifications", [])
            langs = candidate.get("languages", [])
            if certs:
                st.markdown(f"**证书**: {', '.join(certs)}")
            if langs:
                st.markdown(f"**语言**: {', '.join(langs)}")

        projects = candidate.get("project_experience", [])
        if projects:
            with st.expander("项目经验"):
                for p in projects:
                    st.markdown(f"**{p.get('name','')}** — {p.get('role','')}")
                    st.markdown(f"_{p.get('description','')}_")
                    tech = p.get("tech_stack", [])
                    if tech:
                        st.caption(f"技术栈: {', '.join(tech)}")
                    st.markdown("---")
        if candidate.get("self_assessment"):
            st.markdown(f"💬 *{candidate['self_assessment']}*")
