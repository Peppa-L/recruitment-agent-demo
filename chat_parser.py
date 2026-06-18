# -*- coding: utf-8 -*-
"""
AI 群聊消息解析引擎 — chat_parser.py
======================================
将微信/企业微信群聊中的非结构化招聘对话，通过 LLM 解析为结构化招聘数据。

核心能力：
  1. 候选人识别：从口语化描述中提取候选人姓名、联系方式
  2. 招聘阶段判断：简历筛选/面试安排/面试反馈/Offer/入职
  3. 面试信息提取：时间、方式、面试官、反馈、评分
  4. 薪资讨论提取：候选人期望、内部预算、最终结论
  5. 关键决策追踪：通过/淘汰/待定/二面

设计特点：
  - Prompt Engineering 优化：处理口语化、省略、代词指代等非结构化表达
  - 多轮对话理解：聚合分散在多条消息中的信息
  - 无关内容过滤：自动忽略闲聊、广告等非招聘相关内容
  - 置信度标注：对不确定的字段标注置信度
"""

import re
import json
import os
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime


# ============================================================
# 配置
# ============================================================
try:
    from config import get_api_config
    _cfg = get_api_config()
    AI_API_KEY = _cfg.get("api_key", "")
    AI_API_BASE = _cfg.get("api_base", "")
    AI_MODEL = _cfg.get("model", "gpt-4o-mini")
except Exception:
    AI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
    AI_API_BASE = os.environ.get("OPENAI_API_BASE", "")
    AI_MODEL = os.environ.get("AI_PARSE_MODEL", "gpt-4o-mini")


# ============================================================
# Prompt 模板
# ============================================================

CHAT_PARSE_PROMPT = """你是一位资深的招聘流程管理专家，专门从企业微信/微信群的招聘沟通中提取结构化数据。

## 你的任务

阅读以下群聊记录，提取其中所有与招聘相关的关键信息，并输出标准的 JSON 格式。

## 群聊背景

这是一家互联网公司的招聘沟通群。参与人员包括：
- HR（王芳、刘静）
- 技术总监（李总）
- 技术主管（赵工）
- 产品总监（刘总）
- 数据负责人（周工）
- 运维主管（孙工）

他们通过群聊讨论候选人、安排面试、反馈结果。

## 提取规则

### 1. 候选人信息
- 从聊天中找出被讨论的候选人姓名、应聘职位
- 如果消息中提到简历文件（如"[文件] xxx_简历.pdf"），从文件名提取姓名和方向
- 如果使用简称/昵称（如"张工"、"那个做后端的"），尝试推断全名
- 如果能从对话中推断联系方式，一并提取

### 2. 招聘阶段（stage）
必须是以下之一：
- "简历筛选"：正在评估简历，尚未决定是否面试
- "面试已安排"：已确定面试时间和方式
- "一面通过"：一面反馈正面，进入下一轮
- "一面未通过"：一面反馈负面
- "二面已安排" / "二面通过" / "二面未通过"
- "Offer沟通中"：在讨论薪资和offer细节
- "已发Offer" / "已入职" / "已淘汰"

### 3. 面试信息
- interview_date：面试日期（格式 YYYY-MM-DD）
- interview_time：面试时间（如 "14:00"）
- interview_type：面试方式（线上视频/线下/电话）
- interviewers：面试官姓名列表
- interview_round：第几轮面试（1/2/3）

### 4. 面试反馈
- interview_score：评分（0-100的数字），如果对话中明确提到了分数
- feedback_positive：正面评价列表
- feedback_negative：负面评价/顾虑列表
- overall_assessment：整体评估文字

### 5. 薪资讨论
- candidate_expected_salary：候选人期望薪资
- budget_range：内部预算范围
- salary_conclusion：薪资讨论的结论

### 6. 关键决策
- decision：HR/面试官的最终决策（"推进"/"淘汰"/"待定"）
- next_step：下一步行动
- next_step_deadline：如有时间要求

### 7. 其他
- mentioned_skills：对话中提到的技能关键词
- concerns：招聘方提出的顾虑
- has_irrelevant_info：是否包含与招聘无关的闲聊（true/false）
- irrelevant_topics：闲聊话题列表

## 重要注意事项

1. **信息可能分散在多条消息中**，请综合分析整段对话
2. **口语化表达要理解**：
   - "还行吧" = 基本认可，中等偏正面
   - "问题不大" = 有顾虑但可以克服
   - "先面一下看看" = 待面试后决定
   - "卡得紧" = 预算有限
3. **缺少的信息字段填空字符串或null**，不要编造
4. **日期推断**：如果对话中说"下周二"，请根据消息时间推算具体日期
5. **多候选人识别**：如果对话中讨论了多个候选人，分别提取
6. **忽略真正的闲聊**：点外卖、天气、八卦等与招聘无关的内容，标记但不提取

## 群聊记录

{chat_text}

## 输出格式

请严格按照以下 JSON 格式输出（不要带 markdown 代码块标记）：

{
  "candidates": [
    {
      "name": "候选人姓名",
      "position": "应聘职位",
      "phone": "联系电话（如有）",
      "email": "邮箱（如有）",
      "current_company": "当前公司（如有提及）",
      "stage": "当前招聘阶段",
      "stage_confidence": "high/medium/low",
      "interview_info": {
        "date": "YYYY-MM-DD 或 null",
        "time": "HH:MM 或 null",
        "type": "线上视频/线下/电话 或 null",
        "round": 1,
        "interviewers": ["面试官1", "面试官2"],
        "location": "面试地点（如有）"
      },
      "feedback": {
        "score": 85,
        "positive": ["正面评价1", "正面评价2"],
        "negative": ["顾虑1"],
        "overall": "整体评估摘要"
      },
      "salary": {
        "expected": "期望薪资",
        "budget": "预算范围",
        "conclusion": "薪资结论"
      },
      "decision": {
        "result": "推进/淘汰/待定",
        "reason": "决策理由",
        "next_step": "下一步行动",
        "next_step_deadline": "时间要求（如有）"
      },
      "skills_mentioned": ["技能1"],
      "concerns": ["关注点1"],
      "key_quotes": ["关键引语1"]
    }
  ],
  "summary": {
    "total_candidates_discussed": 1,
    "main_topic": "本次对话的主要议题",
    "key_decisions": ["主要决策汇总"],
    "action_items": ["待办事项"],
    "has_irrelevant_info": false,
    "irrelevant_topics": []
  }
}

只输出 JSON，不要带任何额外说明。"""


# ============================================================
# LLM 调用
# ============================================================

def _call_llm(prompt: str, api_key: str = None, api_base: str = None,
              model: str = None, timeout: int = 300) -> tuple:
    """调用 LLM API（OpenAI 兼容格式）。
    返回: (response_text, metadata_dict)
      metadata: {model, latency_ms, usage, api_base}
    """
    from openai import OpenAI
    start = datetime.now()

    client = OpenAI(
        api_key=api_key or AI_API_KEY,
        base_url=api_base or AI_API_BASE,
    )

    response = client.chat.completions.create(
        model=model or AI_MODEL,
        messages=[
            {
                "role": "system",
                "content": "你是一位资深招聘流程管理专家，擅长从非结构化对话中提取结构化招聘数据。只输出JSON，不输出其他内容。"
            },
            {"role": "user", "content": prompt},
        ],
        temperature=0.1,
        max_tokens=8192,
        timeout=timeout,
    )

    elapsed = (datetime.now() - start).total_seconds() * 1000
    usage = {}
    if hasattr(response, 'usage') and response.usage:
        usage = {
            "prompt_tokens": getattr(response.usage, 'prompt_tokens', None),
            "completion_tokens": getattr(response.usage, 'completion_tokens', None),
            "total_tokens": getattr(response.usage, 'total_tokens', None),
        }

    metadata = {
        "model": model or AI_MODEL,
        "api_base": api_base or AI_API_BASE,
        "latency_ms": int(elapsed),
        "usage": usage,
        "timestamp": datetime.now().isoformat(),
    }

    return response.choices[0].message.content, metadata


def _clean_json_response(text: str) -> str:
    """清理 LLM 返回的 JSON，兼容多种可能的输出格式"""
    text = text.strip()
    # 去掉 ```json ... ``` 包裹
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*\n?", "", text)
        text = re.sub(r"\n?```\s*$", "", text)
    # 尝试找到 JSON 对象/数组
    json_match = re.search(r"\{.*\}|\[.*\]", text, re.DOTALL)
    if json_match:
        text = json_match.group(0)
    text = text.strip()
    # 兼容：LLM 可能照搬了模板中的双花括号 {{ -> {
    if text.startswith("{{") and text.endswith("}}"):
        text = text[1:-1]
    return text


# ============================================================
# 核心解析函数
# ============================================================

def parse_chat_messages(
    chat_text: str,
    api_key: str = None,
    api_base: str = None,
    model: str = None,
) -> Dict[str, Any]:
    """
    解析微信群聊记录，提取结构化招聘数据。

    参数：
        chat_text: 群聊记录文本（可以是 format_chat_for_ai() 的输出）
        api_key: LLM API Key
        api_base: LLM API Base URL
        model: LLM 模型名

    返回：
        dict: 结构化解析结果，格式见 Prompt 模板
    """
    key = api_key or AI_API_KEY
    if not key:
        try:
            from config import get_api_config as _gac
            key = _gac().get("api_key", "")
        except Exception:
            pass
    if not key:
        raise ValueError(
            "AI 解析需要 LLM API Key。请设置环境变量 OPENAI_API_KEY，"
            "或传入 api_key 参数。"
        )

    # 构建 Prompt
    prompt = CHAT_PARSE_PROMPT.replace("{chat_text}", chat_text[:12000])

    # 调用 LLM（返回 (content, metadata) 元组）
    raw_response, api_meta = _call_llm(prompt, key, api_base, model)
    cleaned = _clean_json_response(raw_response)

    try:
        result = json.loads(cleaned)
    except json.JSONDecodeError as e:
        # 尝试二次清理：有时 JSON 嵌套在文本说明中
        # 尝试找到最外层的完整 {...} 或 [...]
        brace_depth = 0
        start_idx = -1
        for i, ch in enumerate(cleaned):
            if ch == '{' or ch == '[':
                if brace_depth == 0:
                    start_idx = i
                brace_depth += 1
            elif ch == '}' or ch == ']':
                brace_depth -= 1
                if brace_depth == 0 and start_idx >= 0:
                    extracted = cleaned[start_idx:i+1]
                    try:
                        result = json.loads(extracted)
                        break
                    except json.JSONDecodeError:
                        continue
        else:
            raise ValueError(
                f"AI 返回的内容无法解析为 JSON:\n{str(e)}\n\n"
                f"清理后（前 600 字符）:\n{cleaned[:600]}\n\n"
                f"原始返回（前 600 字符）:\n{raw_response[:600]}\n\n"
                f"💡 提示：请检查 API Key 和 Base URL 是否正确配置，"
                f"模型是否支持 JSON 输出。DeepSeek 请选择 'deepseek-chat'。"
            )

    # 添加元数据（包含 API 调用证据）
    result["_parse_timestamp"] = datetime.now().isoformat()
    result["_parser_version"] = "v2"
    result["_raw_response"] = raw_response
    result["_api_meta"] = api_meta  # ← 新增：API 调用证据

    return result


# ============================================================
# 批量解析
# ============================================================

def batch_parse_scenarios(
    scenarios: List[Dict[str, Any]],
    api_key: str = None,
    api_base: str = None,
    model: str = None,
    delay_seconds: float = 0.5,
) -> List[Dict[str, Any]]:
    """
    批量解析多个群聊场景。

    参数：
        scenarios: 场景列表（来自 wechat_data.py）
        api_key, api_base, model: LLM 配置
        delay_seconds: API 调用间隔

    返回：
        [{"scenario": {...}, "parsed": {...}}, ...]
    """
    import time
    from wechat_data import format_chat_for_ai

    results = []
    for i, scenario in enumerate(scenarios):
        chat_text = format_chat_for_ai(scenario)

        try:
            parsed = parse_chat_messages(chat_text, api_key, api_base, model)
            results.append({
                "scenario": scenario,
                "parsed": parsed,
                "success": True,
            })
        except Exception as e:
            results.append({
                "scenario": scenario,
                "parsed": None,
                "success": False,
                "error": str(e),
            })

        if i < len(scenarios) - 1 and delay_seconds > 0:
            time.sleep(delay_seconds)

    return results


# ============================================================
# 本地规则解析（无需 API 的回退方案）
# ============================================================

def _extract_name_from_filename(text: str) -> Optional[str]:
    """从简历文件名提取候选人姓名"""
    match = re.search(r"\[文件\]\s*(\S+?)[_\-—]*(?:简历|前端|后端|产品|数据|DevOps|工程师|经理|分析师)", text)
    if match:
        return match.group(1)
    match = re.search(r"(\S{2,4})[_\-\s]*简历", text)
    if match:
        return match.group(1)
    return None


def _extract_date(text: str) -> Optional[str]:
    """从文本中提取日期"""
    patterns = [
        r"(\d{4}[-/年]\d{1,2}[-/月]\d{1,2})",
        r"(\d{1,2}月\d{1,2}日?)",
        r"(下周[一二三四五六日])",
        r"(周[一二三四五六日])",
    ]
    for p in patterns:
        m = re.search(p, text)
        if m:
            return m.group(1)
    return None


def local_rule_parse(chat_text: str) -> Dict[str, Any]:
    """
    本地规则解析（不调用 LLM 的快速回退）。
    仅提取基本信息，精度不如 AI 解析但可作为降级方案。
    """
    result = {
        "candidates": [],
        "summary": {
            "total_candidates_discussed": 0,
            "main_topic": "",
            "key_decisions": [],
            "action_items": [],
            "has_irrelevant_info": False,
            "irrelevant_topics": [],
            "_method": "local_rules",
        }
    }

    # 提取候选人姓名
    name = _extract_name_from_filename(chat_text)
    if not name:
        # 尝试从内容中提取
        name_match = re.search(r"(?:候选人|应聘者|推(?:荐|了)一个?)\s*(\S{2,4})", chat_text)
        if name_match:
            name = name_match.group(1)

    if name:
        candidate = {"name": name, "position": "", "stage": "未知"}

        # 提取职位
        pos_match = re.search(r"(?:应聘?|招|做)\s*(\S{2,10}(?:工程师|经理|分析师|专员|设计师|开发))", chat_text)
        if pos_match:
            candidate["position"] = pos_match.group(1)

        # 提取日期
        date = _extract_date(chat_text)
        if date:
            candidate["interview_info"] = {"date": date}

        # 判断阶段
        if re.search(r"(?:约|安排|定了|已约)(?:个?面试|面|一下)", chat_text):
            candidate["stage"] = "面试已安排"
        elif re.search(r"(?:面完|面了|面试.*?结束|刚才.*?面)", chat_text):
            candidate["stage"] = "面试完成"
        elif re.search(r"(?:过了|通过|可以.*?过|推进)", chat_text):
            candidate["stage"] = "通过"
        elif re.search(r"(?:看看|评估|筛一下)", chat_text):
            candidate["stage"] = "简历筛选"

        result["candidates"].append(candidate)
        result["summary"]["total_candidates_discussed"] = 1

    return result


# ============================================================
# 结果格式化（用于前端展示）
# ============================================================

def format_parsed_for_display(parsed: Dict[str, Any]) -> str:
    """
    将 AI 解析结果格式化为可读的 Markdown 文本。
    """
    if not parsed or "candidates" not in parsed:
        return "解析失败或无候选人在对话中"

    lines = []

    # 摘要
    summary = parsed.get("summary", {})
    if summary:
        lines.append("## 📋 对话摘要")
        lines.append(f"- **讨论候选人数量**: {summary.get('total_candidates_discussed', 0)}")
        if summary.get("main_topic"):
            lines.append(f"- **主要议题**: {summary['main_topic']}")
        if summary.get("key_decisions"):
            lines.append("- **关键决策**:")
            for d in summary["key_decisions"]:
                lines.append(f"  - {d}")
        if summary.get("action_items"):
            lines.append("- **待办事项**:")
            for a in summary["action_items"]:
                lines.append(f"  - {a}")
        if summary.get("has_irrelevant_info"):
            lines.append(f"- ⚠️ 检测到无关闲聊: {', '.join(summary.get('irrelevant_topics', []))}")

    lines.append("")
    lines.append("---")

    # 候选人详情
    for i, cand in enumerate(parsed.get("candidates", []), 1):
        lines.append(f"## 👤 候选人 {i}: {cand.get('name', '未知')}")

        # 基本信息
        lines.append(f"- **应聘职位**: {cand.get('position', '未提及')}")
        lines.append(f"- **当前公司**: {cand.get('current_company', '未提及')}")

        # 阶段
        stage = cand.get("stage", "未知")
        confidence = cand.get("stage_confidence", "")
        stage_display = f"**{stage}**"
        if confidence:
            stage_display += f" (置信度: {confidence})"
        lines.append(f"- **当前阶段**: {stage_display}")

        # 面试信息
        interview = cand.get("interview_info", {})
        if interview:
            date_str = interview.get("date", "")
            time_str = interview.get("time", "")
            type_str = interview.get("type", "")
            round_num = interview.get("round", "")
            interviewers = interview.get("interviewers", [])

            if any([date_str, time_str, type_str, interviewers]):
                lines.append(f"- **面试信息**:")
                if date_str:
                    lines.append(f"  - 日期: {date_str}")
                if time_str:
                    lines.append(f"  - 时间: {time_str}")
                if type_str:
                    lines.append(f"  - 方式: {type_str}")
                if round_num:
                    lines.append(f"  - 轮次: 第{round_num}轮")
                if interviewers:
                    lines.append(f"  - 面试官: {', '.join(interviewers)}")

        # 反馈
        feedback = cand.get("feedback", {})
        if feedback:
            score = feedback.get("score")
            positive = feedback.get("positive", [])
            negative = feedback.get("negative", [])
            overall = feedback.get("overall", "")

            if score is not None:
                lines.append(f"- **面试评分**: {score}/100")
            if positive:
                lines.append(f"- **正面评价**:")
                for p in positive:
                    lines.append(f"  - ✅ {p}")
            if negative:
                lines.append(f"- **顾虑/负面**:")
                for n in negative:
                    lines.append(f"  - ⚠️ {n}")
            if overall:
                lines.append(f"- **整体评估**: {overall}")

        # 薪资
        salary = cand.get("salary", {})
        if salary and any(salary.values()):
            expected = salary.get("expected", "")
            budget = salary.get("budget", "")
            conclusion = salary.get("conclusion", "")
            if expected:
                lines.append(f"- **期望薪资**: {expected}")
            if budget:
                lines.append(f"- **预算范围**: {budget}")
            if conclusion:
                lines.append(f"- **薪资结论**: {conclusion}")

        # 决策
        decision = cand.get("decision", {})
        if decision:
            result = decision.get("result", "")
            reason = decision.get("reason", "")
            next_step = decision.get("next_step", "")
            deadline = decision.get("next_step_deadline", "")

            if result:
                emoji = {"推进": "🟢", "淘汰": "🔴", "待定": "🟡"}.get(result, "⚪")
                lines.append(f"- **决策**: {emoji} {result}")
            if reason:
                lines.append(f"  - 理由: {reason}")
            if next_step:
                lines.append(f"  - 下一步: {next_step}")
            if deadline:
                lines.append(f"  - 截止时间: {deadline}")

        # 技能
        skills = cand.get("skills_mentioned", [])
        if skills:
            lines.append(f"- **提及技能**: {', '.join(skills)}")

        # 关键引语
        quotes = cand.get("key_quotes", [])
        if quotes:
            lines.append(f"- **关键原话**:")
            for q in quotes:
                lines.append(f"  > {q}")

        lines.append("")
        lines.append("---")

    return "\n".join(lines)


# ============================================================
# CLI 入口
# ============================================================

if __name__ == "__main__":
    import argparse
    from wechat_data import get_all_scenarios, format_chat_for_ai

    parser = argparse.ArgumentParser(description="AI 群聊招聘信息解析工具")
    parser.add_argument("--scenario", type=int, default=1, help="场景编号 (1-6)")
    parser.add_argument("--api-key", type=str, default=None, help="LLM API Key")
    parser.add_argument("--local", action="store_true", help="使用本地规则解析（不调用API）")
    parser.add_argument("--show-chat", action="store_true", help="仅显示聊天记录")

    args = parser.parse_args()

    scenarios = get_all_scenarios()
    if args.scenario < 1 or args.scenario > len(scenarios):
        print(f"错误：场景编号须在 1-{len(scenarios)} 之间")
        exit(1)

    scenario = scenarios[args.scenario - 1]
    chat_text = format_chat_for_ai(scenario)

    if args.show_chat:
        print(chat_text)
        exit(0)

    if args.local:
        result = local_rule_parse(chat_text)
    else:
        result = parse_chat_messages(chat_text, api_key=args.api_key)

    print(json.dumps(result, ensure_ascii=False, indent=2))
