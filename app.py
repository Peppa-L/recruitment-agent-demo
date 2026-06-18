# -*- coding: utf-8 -*-
"""
招聘提效 AI Agent — 主程序
============================
面向 HR 的 AI 辅助工具：
  1. 💬 AI 智能解析 — 勾选多段群聊，一键批量解析为结构化招聘数据
  2. 📊 招聘数据看板 — 解析结果自动去重汇总为可视化看板
  3. 📄 简历智能匹配 — 上传简历 + 职位描述，AI 多维匹配评分
"""

import streamlit as st
import pandas as pd
import sys, os, json, time
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# ========== 页面配置 ==========
st.set_page_config(
    page_title="招聘提效 AI Agent",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ========== 初始化 Session State ==========
if "parsed_results" not in st.session_state:
    st.session_state.parsed_results = []
if "chat_input_text" not in st.session_state:
    st.session_state.chat_input_text = ""
if "selected_scenario_ids" not in st.session_state:
    st.session_state.selected_scenario_ids = set()

# ========== 注入 Secrets 到环境变量（自动填充 API Key） ==========
for _key in ["OPENAI_API_KEY", "OPENAI_API_BASE"]:
    if not os.environ.get(_key):
        try:
            _val = st.secrets.get(_key, "")
            if _val:
                os.environ[_key] = _val
        except Exception:
            pass

# ========== 后端 API 配置（从 Secrets / 环境变量读取，前端不暴露） ==========
API_KEY = os.environ.get("OPENAI_API_KEY", "")
API_BASE = os.environ.get("OPENAI_API_BASE", "https://api.deepseek.com/v1")
AI_MODEL = os.environ.get("AI_PARSE_MODEL", "deepseek-chat")

# ========== 侧边栏 ==========
st.sidebar.title("🤖 招聘提效 AI Agent")
st.sidebar.caption("群聊消息 → AI 批量解析 → 自动化录入")

st.sidebar.markdown("---")

# ---- 大按钮导航 ----
if "nav_page" not in st.session_state:
    st.session_state.nav_page = "💬 AI 智能解析"

TAB_OPTIONS = ["💬 AI 智能解析", "📊 招聘数据看板", "📄 简历智能匹配"]

for tab_name in TAB_OPTIONS:
    is_active = (st.session_state.nav_page == tab_name)
    label = f"{'🔷' if is_active else '🔹'} **{tab_name.split(' ', 1)[1]}**"
    if st.sidebar.button(
        label,
        key=f"nav_{tab_name}",
        use_container_width=True,
        type="primary" if is_active else "secondary",
    ):
        st.session_state.nav_page = tab_name
        st.rerun()

page = st.session_state.nav_page

st.sidebar.markdown("---")

# AI 状态指示
if API_KEY:
    st.sidebar.success("✅ AI 已就绪")
else:
    st.sidebar.warning("⚠️ 未配置 API Key\n\n请在 `.streamlit/secrets.toml` 中设置 `OPENAI_API_KEY`")

# 解析历史摘要
parsed_count = len(st.session_state.parsed_results)
if parsed_count:
    st.sidebar.markdown("---")
    st.sidebar.caption(f"📝 已解析 {parsed_count} 段对话（已去重）")
    unique_candidates = set()
    for item in st.session_state.parsed_results:
        for cand in item.get("parsed", {}).get("candidates", []):
            name = cand.get("name", "")
            if name and name != "未识别":
                unique_candidates.add(name)
    if unique_candidates:
        st.sidebar.caption(f"👥 涉及候选人: {', '.join(sorted(unique_candidates))}")

st.sidebar.markdown("---")
st.sidebar.caption("招聘 Agent Demo v2.0")

# ============================================================
# 导入
# ============================================================
from wechat_data import (
    get_all_scenarios, get_all_candidates, get_all_jobs,
    format_chat_for_ai, MEMBERS
)
from dashboard import (
    build_pipeline_from_session, render_full_dashboard, render_candidate_resume
)

# ============================================================
# Tab 1: AI 智能解析（主页面）
# ============================================================
if page == "💬 AI 智能解析":

    st.title("💬 AI 智能解析")
    st.caption("勾选群聊 → 一键批量解析 → 结构化数据自动汇总到看板")

    scenarios = get_all_scenarios()

    # ---- 步骤1：选择对话 ----
    st.markdown("### ① 选择要解析的群聊对话（可多选）")

    # 全选/清空 — 同时更新独立 checkbox 的 session_state 键值
    c_all, c_clear, c_import, c_count = st.columns([1, 1, 1.5, 2])
    with c_all:
        if st.button("✅ 全选", use_container_width=True):
            for i in range(len(scenarios)):
                st.session_state[f"_cb_{i}"] = True
            st.session_state.selected_scenario_ids = {s["description"][:40] for s in scenarios}
            st.rerun()
    with c_clear:
        if st.button("🔄 清空", use_container_width=True):
            for i in range(len(scenarios)):
                st.session_state[f"_cb_{i}"] = False
            st.session_state.selected_scenario_ids = set()
            st.rerun()
    with c_import:
        uploaded_chat_file = st.file_uploader(
            "📂 导入 .txt 数据",
            type=["txt"],
            label_visibility="collapsed",
            help="支持从 chat_data.txt 批量导入",
        )
        if uploaded_chat_file:
            content = uploaded_chat_file.read().decode("utf-8")
            import re
            blocks = re.split(r'===SCENARIO===', content)
            new_chunks = []
            for block in blocks:
                block = block.strip()
                if not block or "===END===" not in block:
                    continue
                block = re.sub(r'===END===.*', '', block, flags=re.DOTALL).strip()
                if not block:
                    continue
                # 提取场景ID
                sid = ""
                for line in block.split("\n")[:5]:
                    if "场景说明" in line:
                        sid = line.strip()
                        break
                if not sid:
                    sid = f"导入_{datetime.now().strftime('%H%M%S')}_{len(new_chunks)}"
                # 去重
                existing_ids = {r.get("scenario_id", "") for r in st.session_state.parsed_results}
                if sid in existing_ids:
                    continue
                new_chunks.append(block)

            if new_chunks:
                separator = "\n\n" + "=" * 50 + "\n\n"
                existing_text = st.session_state.get("chat_input_text", "")
                st.session_state.chat_input_text = (
                    existing_text + separator + separator.join(new_chunks)
                    if existing_text.strip() else separator.join(new_chunks)
                )
                # 清除 uploader 状态，防止 rerun 后重复触发
                st.session_state.pop("_chat_file_uploader_state", None)
                st.success(f"✅ 已导入 {len(new_chunks)} 段对话 → 点击下方「🤖 AI 解析」即可批量处理")
            else:
                st.info("导入的对话均已存在（去重）或文件格式不符")
    with c_count:
        if st.session_state.selected_scenario_ids:
            st.info(f"已勾选 {len(st.session_state.selected_scenario_ids)} 段对话")

    # 多选列表 — 每个 checkbox 独立运作，通过 selected_scenario_ids 追踪选中状态
    for i, sc in enumerate(scenarios):
        sid = sc["description"][:40]  # 唯一 ID
        cb_key = f"_cb_{i}"

        is_checked = sid in st.session_state.selected_scenario_ids

        col_check, col_info, col_preview = st.columns([0.5, 2, 5])
        with col_check:
            # value= 只在首次渲染时生效；后续 Streamlit 以用户交互为准
            checked = st.checkbox("", value=is_checked, key=cb_key, label_visibility="collapsed")
            if checked != is_checked:
                if checked:
                    st.session_state.selected_scenario_ids.add(sid)
                else:
                    st.session_state.selected_scenario_ids.discard(sid)
                st.rerun()

        with col_info:
            candidate_id = sc.get("candidate_id")
            candidate_name = ""
            if candidate_id:
                matched = [c for c in get_all_candidates() if c["id"] == candidate_id]
                if matched:
                    candidate_name = matched[0]["name"]
            st.markdown(f"**场景 {i+1}**")
            st.caption(f"👤 {candidate_name or '候选人'} | 💬 {len(sc['messages'])}条消息")

        with col_preview:
            st.caption(sc["description"][:80])

    st.markdown("---")

    # ---- 步骤2：预览 / 手动粘贴 ----
    st.markdown("### ② 预览选中对话（或粘贴你自己的群聊记录）")

    # 当勾选变化时，自动更新预览
    preview_text = ""
    if st.session_state.selected_scenario_ids:
        for sc in scenarios:
            sid = sc["description"][:40]
            if sid in st.session_state.selected_scenario_ids:
                preview_text += format_chat_for_ai(sc) + "\n\n" + "=" * 50 + "\n\n"
        # 同步到 session_state
        st.session_state.chat_input_text = preview_text

    chat_input = st.text_area(
        "群聊记录（可编辑）",
        value=st.session_state.chat_input_text,
        height=300,
        placeholder="在此粘贴微信/企业微信群聊记录...\n或勾选上方的示例对话自动填充",
        key="chat_input_text",  # 直接绑定 session_state key
    )

    # ---- 步骤3：批量解析 ----
    st.markdown("### ③ 执行 AI 解析")

    parse_col1, parse_col2, parse_col3, parse_col4 = st.columns([1.5, 1.5, 1, 3])
    with parse_col1:
        do_parse = st.button(
            "🤖 AI 解析",
            type="primary",
            use_container_width=True,
            disabled=not (chat_input.strip() and API_KEY),
        )
    with parse_col2:
        if not API_KEY:
            st.warning("⚠️ 请先配置 API Key（在 .streamlit/secrets.toml 中设置 OPENAI_API_KEY）")
        elif not chat_input.strip():
            st.info("👆 勾选对话或粘贴记录")
    with parse_col3:
        show_debug = st.checkbox("🔬 调试", value=False, help="显示 API 原始返回")
    with parse_col4:
        if st.session_state.selected_scenario_ids:
            sid_list = list(st.session_state.selected_scenario_ids)
            st.caption(f"将对 {len(sid_list)} 段对话逐条调用 AI 解析（约 {len(sid_list) * 15} 秒）")

    # ---- 执行解析 ----
    if do_parse:
        from chat_parser import parse_chat_messages

        # 把整段输入按分隔符拆回各场景（如果是从勾选填充的）
        chunks = [c.strip() for c in chat_input.strip().split("=" * 50) if c.strip()]
        if not chunks:
            chunks = [chat_input.strip()]

        # 去重检查
        new_count = 0
        skip_count = 0
        progress_bar = st.progress(0, text="准备解析...")
        status_text = st.empty()

        for idx, chunk in enumerate(chunks):
            # 提取 scenario_id（从 chunk 的第一行提取场景描述）
            sid = ""
            for line in chunk.split("\n")[:3]:
                if "场景说明" in line:
                    sid = line.strip()
                    break
            if not sid:
                sid = f"手动输入_{datetime.now().strftime('%H%M%S')}_{idx}"

            # 去重检查
            existing_ids = {r.get("scenario_id", "") for r in st.session_state.parsed_results}
            if sid in existing_ids:
                skip_count += 1
                progress_bar.progress(
                    (idx + 1) / len(chunks),
                    text=f"⏭️ 跳过重复: {sid[:30]}... ({idx+1}/{len(chunks)})"
                )
                continue

            # AI 解析
            progress_bar.progress(
                (idx + 0.3) / len(chunks),
                text=f"🤖 AI 解析中: {sid[:30]}... ({idx+1}/{len(chunks)})"
            )

            try:
                parsed = parse_chat_messages(
                    chunk[:12000],
                )

                # 提取 API 元数据（调用证据）
                api_meta = parsed.get("_api_meta", {})

                st.session_state.parsed_results.append({
                    "scenario_id": sid,
                    "scenario_name": sid[:40],
                    "parsed": parsed,
                    "parse_time": datetime.now().strftime("%m-%d %H:%M"),
                    "chat_text": chunk,
                    "api_meta": api_meta,  # ← API 调用证据
                })
                new_count += 1

            except Exception as e:
                status_text.error(f"❌ 解析失败 [{sid[:30]}...]: {e}")
                # 继续处理下一个

            progress_bar.progress(
                (idx + 1) / len(chunks),
                text=f"{'✅' if new_count else '⏭️'} 完成 {idx+1}/{len(chunks)}"
            )

            # 避免 API 限速
            if idx < len(chunks) - 1:
                time.sleep(1)

        progress_bar.empty()
        if new_count > 0:
            # 显示最后一条的 API 调用证据
            last_meta = st.session_state.parsed_results[-1].get("api_meta", {})
            model_used = last_meta.get("model", "?")
            latency = last_meta.get("latency_ms", "?")
            st.success(
                f"✅ 解析完成！新增 {new_count} 条，跳过 {skip_count} 条重复。"
                f"（模型: {model_used}，耗时: {latency}ms）"
            )
            if not last_meta:
                st.warning("⚠️ 未检测到 API 调用记录，可能使用了本地回退逻辑")
            st.info("👆 展开下方结果可查看 API 调用证据，开启「🔬 调试」复选框可查看原始返回")
            st.rerun()
        elif skip_count > 0:
            st.warning(f"⏭️ 全部 {skip_count} 条已存在（已去重），无需重复解析。")
        else:
            st.error("❌ 解析失败，请检查 API 配置和网络连接。")

    st.markdown("---")

    # ---- 解析历史 ----
    if st.session_state.parsed_results:
        st.markdown(f"### 📝 解析历史（共 {len(st.session_state.parsed_results)} 条，已去重）")

        for idx, item in enumerate(reversed(st.session_state.parsed_results)):
            actual_idx = len(st.session_state.parsed_results) - 1 - idx
            parsed = item.get("parsed", {})
            candidates = parsed.get("candidates", [])
            summary = parsed.get("summary", {})

            candidate_names = ", ".join([
                c.get("name", "?") for c in candidates
            ]) if candidates else "未识别"

            # 构建 API 证据标签
            api_meta = item.get("api_meta", {})
            if api_meta:
                model_name = api_meta.get("model", "?")
                latency = api_meta.get("latency_ms", "?")
                usage = api_meta.get("usage", {})
                tokens = f"{usage.get('total_tokens', '?')} tokens" if usage else ""
                api_badge = f"🔗 {model_name} | ⚡ {latency}ms | 📊 {tokens}"
            else:
                api_badge = "⚠️ 无 API 调用记录（可能为本地回退）"

            with st.expander(
                f"🤖 {item['scenario_name'][:35]}... — {item['parse_time']} "
                f"| 👤 {candidate_names}",
                expanded=(idx == 0)
            ):
                # API 调用证据
                st.caption(api_badge)

                # 决策摘要
                if summary:
                    decisions = summary.get("key_decisions", [])
                    actions = summary.get("action_items", [])
                    if decisions:
                        st.markdown("**关键决策**: " + " | ".join(decisions))
                    if actions:
                        st.markdown("**待办**: " + " | ".join(actions))

                # 候选人卡片
                for cand in candidates:
                    iv = cand.get("interview_info", {}) or {}
                    fb = cand.get("feedback", {}) or {}
                    sal = cand.get("salary", {}) or {}
                    dec = cand.get("decision", {}) or {}

                    # 构建合并评价
                    eval_lines = []
                    score = fb.get("score")
                    if score is not None:
                        eval_lines.append(f"📊 评分: {score}/100")
                    if fb.get("overall"):
                        eval_lines.append(f"💬 {fb['overall']}")
                    for p in fb.get("positive", []):
                        eval_lines.append(f"✅ {p}")
                    for n in fb.get("negative", []):
                        eval_lines.append(f"⚠️ {n}")

                    # 合并薪资
                    salary_text = ""
                    if sal.get("expected") or sal.get("budget") or sal.get("conclusion"):
                        parts = []
                        if sal.get("expected"):
                            parts.append(f"期望: {sal['expected']}")
                        if sal.get("budget"):
                            parts.append(f"预算: {sal['budget']}")
                        if sal.get("conclusion"):
                            parts.append(f"结论: {sal['conclusion']}")
                        salary_text = " | ".join(parts)

                    with st.container(border=True):
                        c1, c2 = st.columns([2, 1])

                        with c1:
                            st.markdown(f"**👤 {cand.get('name', '未识别')}** — {cand.get('position', '未识别')}")
                            stage = cand.get("stage", "未知")
                            st.caption(f"阶段: {stage}")
                            if eval_lines:
                                for line in eval_lines[:3]:
                                    st.caption(line)

                        with c2:
                            if iv.get("date"):
                                st.caption(f"📅 {iv['date']} {iv.get('time', '')}")
                            if iv.get("interviewers"):
                                st.caption(f"👥 {', '.join(iv['interviewers'])}")
                            if salary_text:
                                st.caption(f"💰 {salary_text}")

                        # 决策
                        if dec.get("result") or dec.get("next_step"):
                            emoji = {"推进": "🟢", "淘汰": "🔴", "待定": "🟡"}.get(dec.get("result", ""), "")
                            st.caption(f"{emoji} 决策: {dec.get('result', '—')} → 下一步: {dec.get('next_step', '—')}")

                # 原始消息 + API 原始返回（调试模式）
                with st.expander("📋 原始消息"):
                    st.code(item.get("chat_text", "")[:3000], language=None)
                if show_debug:
                    raw_resp = parsed.get("_raw_response", "")
                    api_meta_dbg = item.get("api_meta", {})
                    with st.expander("🔬 API 原始返回（调试）"):
                        st.json(api_meta_dbg)
                        st.divider()
                        st.code(raw_resp[:5000] if raw_resp else "(无)", language="json")
                if st.button("🗑️ 删除此条", key=f"del_{actual_idx}"):
                    st.session_state.parsed_results.pop(actual_idx)
                    st.rerun()

        # 清空
        if len(st.session_state.parsed_results) > 1:
            if st.button("🗑️ 清空全部历史"):
                st.session_state.parsed_results = []
                st.session_state.selected_scenario_ids = set()
                st.rerun()

    else:
        st.info("👆 勾选上方的示例群聊对话，然后点击「🤖 AI 解析」批量分析。解析结果将显示在这里，并自动汇总到「📊 招聘数据看板」。")

    # ---- 关联简历 ----
    selected_sids = st.session_state.selected_scenario_ids
    if selected_sids:
        # 找到对应候选人
        related_candidates = []
        for sc in scenarios:
            sid = sc["description"][:40]
            if sid in selected_sids and sc.get("candidate_id"):
                for c in get_all_candidates():
                    if c["id"] == sc["candidate_id"] and c["id"] not in [rc["id"] for rc in related_candidates]:
                        related_candidates.append(c)

        if related_candidates:
            st.markdown("---")
            st.markdown("### 📎 关联候选人简历")
            st.caption("群聊中讨论的候选人，其简历已在库中（AI解析时会自动关联）")
            for rc in related_candidates:
                with st.expander(f"📄 {rc['name']} — {rc['position']}", expanded=False):
                    render_candidate_resume(rc)


# ============================================================
# Tab 2: 招聘数据看板
# ============================================================
elif page == "📊 招聘数据看板":

    st.title("📊 招聘数据看板")
    st.caption("数据来源：🤖 AI 自动从群聊中提取，实时同步，自动去重")

    # 从 session_state 构建管道数据
    pipeline_df = build_pipeline_from_session(st.session_state.parsed_results)

    if pipeline_df.empty:
        st.info("📭 暂无数据。请先在「💬 AI 智能解析」中勾选群聊并解析。")
        st.markdown("### 💡 操作步骤")
        st.markdown("1. 前往「💬 AI 智能解析」Tab")
        st.markdown("2. 勾选要解析的群聊对话（可多选）")
        st.markdown("3. 点击「🤖 AI 解析」等待完成")
        st.markdown("4. 返回本页面查看自动生成的看板")
    else:
        parse_times = [r.get("parse_time", "") for r in st.session_state.parsed_results if r.get("parse_time")]
        last_update = max(parse_times) if parse_times else datetime.now().strftime("%m-%d %H:%M")
        st.caption(f"最后更新: {last_update} | "
                   f"数据来源: 🤖 AI 自动解析 | "
                   f"已去重: {len(st.session_state.parsed_results)}条")

        render_full_dashboard(pipeline_df)

        # 导出
        with st.expander("📥 导出数据"):
            csv = pipeline_df.to_csv(index=False).encode('utf-8-sig')
            st.download_button(
                "下载 CSV",
                csv,
                f"招聘数据_{datetime.now().strftime('%Y%m%d')}.csv",
                "text/csv",
            )


# ============================================================
# Tab 3: 简历智能匹配
# ============================================================
elif page == "📄 简历智能匹配":

    st.title("📄 简历智能匹配")
    st.caption("上传候选人简历 + 输入职位描述 → AI 多维度匹配分析")

    if not API_KEY:
        st.warning("⚠️ 此功能需要配置 API Key（在 .streamlit/secrets.toml 中设置 OPENAI_API_KEY）")
        st.stop()

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📄 上传简历")
        uploaded_file = st.file_uploader(
            "选择简历文件（PDF / DOCX / TXT）",
            type=["pdf", "docx", "txt"],
        )
        if uploaded_file:
            st.success(f"✅ 已上传：{uploaded_file.name}")

        st.markdown("---")
        st.caption("或选择示例候选人：")
        demo_candidates = get_all_candidates()
        demo_names = [c["name"] for c in demo_candidates]
        selected_demo = st.selectbox("示例候选人", options=["— 不选择 —"] + demo_names)

    with col2:
        st.subheader("💼 职位描述")
        job_title = st.text_input("职位名称", placeholder="例如：Python后端工程师")

        demo_jobs = get_all_jobs()
        demo_job_titles = [j["title"] for j in demo_jobs]
        selected_job = st.selectbox(
            "或选择示例职位（自动填充）",
            options=["— 不选择 —"] + demo_job_titles,
        )

        default_desc = ""
        default_req = ""
        if selected_job != "— 不选择 —":
            matched_job = next((j for j in demo_jobs if j["title"] == selected_job), None)
            if matched_job:
                job_title = matched_job["title"]
                default_desc = matched_job["jd_text"]
                default_req = matched_job.get("jd_requirements_json", "")

        job_desc = st.text_area(
            "职位描述",
            value=default_desc,
            height=150,
            placeholder="请描述该职位的工作内容和职责..."
        )
        job_requirements = st.text_area(
            "任职要求（可选）",
            value=default_req,
            height=80,
            placeholder="学历、经验、技能等要求..."
        )

    st.markdown("---")

    if st.button("🚀 开始匹配分析", use_container_width=True, type="primary"):
        if uploaded_file:
            import tempfile
            temp_path = os.path.join(tempfile.gettempdir(), f"resume_{uploaded_file.name}")
            with open(temp_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            try:
                with st.spinner("🔍 正在解析简历..."):
                    from resume_parser import parse_resume_file
                    result = parse_resume_file(temp_path, use_ai=True)
                    parsed_data = result.get("merged", result.get("basic", {}))
                    st.success(f"✅ 简历解析完成（{result.get('parser_method', 'regex')}模式）")
            finally:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
        elif selected_demo != "— 不选择 —":
            matched_cand = next((c for c in demo_candidates if c["name"] == selected_demo), None)
            parsed_data = matched_cand
            st.success(f"✅ 已加载 {selected_demo} 的简历")
        else:
            st.error("❌ 请上传简历或选择示例候选人")
            st.stop()

        if not job_desc:
            st.error("❌ 请填写职位描述")
            st.stop()

        with st.spinner("🤖 AI 多维匹配分析中..."):
            from ai_match import ai_match_resume
            job_dict = {
                "title": job_title,
                "description": job_desc,
                "requirements": job_requirements,
                "salary_range": "见JD",
                "location": "见JD",
                "jd_text": job_desc,
                "jd_requirements_json": job_requirements,
            }
            match_result = ai_match_resume(
                job=job_dict, resume_parsed=parsed_data,
            )
            st.success("✅ 匹配分析完成！")

        st.markdown("---")
        st.header("📊 匹配结果")

        score = match_result.get("score", 0)
        c1, c2, c3 = st.columns([1, 2, 1])
        with c2:
            st.metric("综合匹配评分", f"{score}/100")
            st.progress(score / 100)
            if score >= 80:
                st.success("🌟 高度匹配 — 建议优先安排面试")
            elif score >= 60:
                st.warning("✅ 中等匹配 — 可考虑面试")
            else:
                st.error("⚠️ 匹配度较低 — 建议谨慎考虑")

        st.subheader("各维度评分")
        dimensions = match_result.get("breakdown", {})
        dim_labels = {
            "skill": "技能匹配", "experience": "经验匹配",
            "project": "项目质量", "company": "公司背景",
            "education": "学历匹配", "relevance": "职位相关度",
            "salary": "薪资匹配", "stability": "稳定性"
        }
        if dimensions:
            dim_cols = st.columns(4)
            for i, (dim, val) in enumerate(dimensions.items()):
                with dim_cols[i % 4]:
                    st.metric(dim_labels.get(dim, dim), f"{val}/100")
                    st.progress(val / 100)

        c1, c2 = st.columns(2)
        with c1:
            st.subheader("✅ 优势")
            for h in (match_result.get("highlights") or []):
                st.markdown(f"- {h}")
        with c2:
            st.subheader("⚠️ 关注点")
            for c in (match_result.get("concerns") or []):
                st.markdown(f"- {c}")

        st.subheader("💡 建议")
        for s in (match_result.get("suggestions") or []):
            st.markdown(f"- {s}")
        if match_result.get("summary"):
            st.info(match_result["summary"])


# ========== 页脚 ==========
st.markdown("---")
st.caption("🤖 招聘提效 AI Agent | 勾选群聊 → AI 批量解析 → 自动化数据录入 | Demo v2.0")
