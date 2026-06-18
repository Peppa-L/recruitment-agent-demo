# -*- coding: utf-8 -*-
"""
AI 匹配引擎 — ai_match.py
==========================
基于结构化简历 JSON（resume_parsed）和结构化 JD（jd_requirements_json），
调用 LLM 进行多维度深度匹配分析，结果直接写入 applications 表。

与 match_engine.py 的关系：
  - match_engine.py：规则匹配（技能词典、正则、加权）
  - ai_match.py：    LLM 语义匹配（理解上下文、推断、综合判断）
  - 建议：先用 ai_match.py 出分数，再用 match_engine.py 做校验/补充
"""

import re
import json
import os
import traceback
from typing import Optional, Dict, Any, List


# ============================================================
# 配置（优先读 config.py，回退到环境变量）
# ============================================================
# API Key 由 app.py 调用时传入，此处仅做环境变量 fallback
AI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
AI_API_BASE = os.environ.get("OPENAI_API_BASE", "")
AI_MODEL = os.environ.get("AI_MATCH_MODEL", "gpt-4o-mini")


# ============================================================
# Prompt 模板（核心）
# ============================================================

AI_MATCH_PROMPT = """你是一位资深技术招聘专家，擅长通过简历和职位描述进行精准匹配评估。
请仔细分析以下「职位描述」和「候选人简历」，给出客观、专业的匹配评估。

## 职位信息

职位名称：{job_title}
薪资范围：{salary_range}
工作地点：{location}

### 职位要求（结构化）
{jd_requirements}

### 完整职位描述
{jd_text}


## 候选人信息（结构化简历）

### 基本信息
- 姓名：{name}
- 性别：{gender}
- 工作年限：{work_years}年
- 当前地点：{current_location}
- 当前薪资：{current_salary}
- 期望薪资：{expected_salary}
- 跳槽频率：{job_hopping_frequency}

### 教育背景
{education_str}

### 工作经历（按时间倒序）
{work_experience_str}

### 项目经验
{project_experience_str}

### 技能清单
{skills_str}

### 证书
{certifications_str}

### 语言能力
{languages_str}

### 自我评价
{self_assessment}


## 分析要求

请从以下维度逐一分析（每维度 0-100 分）：

1. **技能匹配（skill）**：核心技能是否匹配？技能深度如何？有无可迁移技能？
2. **经验匹配（experience）**：工作年限是否满足？相关经验丰富度？技术深度？
3. **项目质量（project）**：项目经验是否相关？项目复杂度？是否有可验证的成果？
4. **公司背景（company）**：过往公司行业地位？是否大厂/独角兽/行业标杆？背景加分？
5. **学历匹配（education）**：学历层次是否满足？专业相关性？学校档次？
6. **职位相关度（relevance）**：整体背景与职位的契合度？职业发展路径是否一致？
7. **薪资匹配（salary）**：期望薪资是否在职位预算范围内？性价比如何？
8. **稳定性（stability）**：跳槽频率评估？在职时长？职业发展连续性？

## 输出要求

**重要**：全程使用中文回答。技术术语（Python、React 等）除外。

请严格按以下 JSON 格式输出（不要带 markdown 代码块标记）：

```json
{{
  "score": 85,
  "recommendation": "强烈推荐",
  "breakdown": {{
    "skill": 90,
    "experience": 80,
    "project": 85,
    "company": 70,
    "education": 90,
    "relevance": 85,
    "salary": 90,
    "stability": 80
  }},
  "highlights": [
    "5年 Python 开发经验，深度匹配职位要求",
    "有大规模分布式系统项目经验",
    "985 本科，专业对口"
  ],
  "concerns": [
    "期望薪资接近预算上限",
    "最近一份工作仅 8 个月，稳定性需关注"
  ],
  "suggestions": [
    "建议安排技术面试，重点考察系统设计方案",
    "可在面试中确认离职原因和职业规划"
  ],
  "summary": "候选人整体背景优秀，技术匹配度高，建议优先安排面试。"
}}
```

## 评分标准参考

- 90-100：强烈推荐，完美匹配，优先安排面试
- 75-89：  推荐，核心要求满足，建议安排面试
- 60-74：  待定，部分要求不满足，可电话初筛后决定
- 40-59：  不推荐，多项要求不满足，但有一定潜力
- 0-39：   淘汰，与职位要求严重不符

注意：如果简历信息严重不足（如只有姓名和电话，无工作经历），score 应低于 30。
"""


# ============================================================
# 辅助函数：格式化结构化数据为文本
# ============================================================

def _format_education(edu_list: List[Dict]) -> str:
    if not edu_list:
        return "未提供"
    lines = []
    for e in edu_list:
        if not isinstance(e, dict):
            continue
        line = f"- {e.get('school', '')} | {e.get('degree', '')} | {e.get('major', '')} | {e.get('start', '')}-{e.get('end', '')}"
        lines.append(line)
    return "\n".join(lines) if lines else "未提供"


def _format_work_experience(work_list: List[Dict]) -> str:
    if not work_list:
        return "未提供"
    lines = []
    for w in work_list:
        if not isinstance(w, dict):
            continue
        line = f"- {w.get('company', '')} | {w.get('position', '')} | {w.get('start', '')}-{w.get('end', '')}"
        if w.get('description'):
            line += f"\n  描述：{w['description'][:200]}"
        lines.append(line)
    return "\n".join(lines) if lines else "未提供"


def _format_projects(proj_list: List[Dict]) -> str:
    if not proj_list:
        return "未提供"
    lines = []
    for p in proj_list:
        if not isinstance(p, dict):
            continue
        line = f"- {p.get('name', '')} | {p.get('role', '')}"
        if p.get('description'):
            line += f"\n  描述：{p['description'][:150]}"
        if p.get('tech_stack'):
            line += f"\n  技术栈：{', '.join(p['tech_stack']) if isinstance(p['tech_stack'], list) else p['tech_stack']}"
        lines.append(line)
    return "\n".join(lines) if lines else "未提供"


def _format_skills(skills) -> str:
    if isinstance(skills, list):
        return ", ".join(skills) if skills else "未提供"
    return str(skills) if skills else "未提供"


def _format_certifications(certs) -> str:
    if isinstance(certs, list):
        return ", ".join(certs) if certs else "无"
    return str(certs) if certs else "无"


def _format_languages(langs) -> str:
    if isinstance(langs, list):
        return "; ".join(langs) if langs else "未提供"
    return str(langs) if langs else "未提供"


# ============================================================
# 核心：构建 Prompt
# ============================================================

def build_match_prompt(
    job: Dict[str, Any],
    resume_parsed: Dict[str, Any],
) -> str:
    """
    根据结构化 JD 和结构化简历，构建 LLM 匹配分析 Prompt。

    参数：
        job: 职位信息 dict，来自 jobs 表（含 jd_text, jd_requirements_json）
        resume_parsed: 结构化简历 dict，来自 resume_parsed 字段
                       或 parse_resume_file() 返回的 merged 字段

    返回：
        str: 完整 Prompt
    """
    # ---- 职位信息 ----
    job_title = job.get("title", "未知职位")
    salary_range = job.get("salary_range", "未提供")
    location = job.get("location", "未提供")

    # JD 要求（优先用结构化 JSON，fallback 到 jd_text）
    jd_requirements = job.get("jd_requirements_json", "")
    if not jd_requirements:
        jd_text = job.get("jd_text", "")
        jd_requirements = jd_text[:2000] if jd_text else "未提供详细要求"
    else:
        # 如果是 JSON 字符串，格式化一下
        try:
            if isinstance(jd_requirements, str):
                jd_req_dict = json.loads(jd_requirements)
                jd_requirements = json.dumps(jd_req_dict, ensure_ascii=False, indent=2)
        except (json.JSONDecodeError, TypeError):
            pass

    jd_text = job.get("jd_text", "未提供")

    # ---- 候选人信息 ----
    name = resume_parsed.get("name", "未知")
    gender = resume_parsed.get("gender", "未知")
    work_years = resume_parsed.get("work_years") or 0
    current_location = resume_parsed.get("current_location", "未提供")
    current_salary = resume_parsed.get("current_salary", "未提供")
    expected_salary = resume_parsed.get("expected_salary", "未提供")
    job_hopping = resume_parsed.get("job_hopping_frequency", "未知")

    education_str = _format_education(resume_parsed.get("education", []))
    work_experience_str = _format_work_experience(resume_parsed.get("work_experience", []))
    project_experience_str = _format_projects(resume_parsed.get("project_experience", []))
    skills_str = _format_skills(resume_parsed.get("skills", []))
    certifications_str = _format_certifications(resume_parsed.get("certifications", []))
    languages_str = _format_languages(resume_parsed.get("languages", []))

    self_assessment = resume_parsed.get("self_assessment", "未提供")[:300]

    # ---- 填充 Prompt ----
    prompt = AI_MATCH_PROMPT.format(
        job_title=job_title,
        salary_range=salary_range,
        location=location,
        jd_requirements=jd_requirements,
        jd_text=jd_text[:3000],  # 防止超长
        name=name,
        gender=gender,
        work_years=work_years,
        current_location=current_location,
        current_salary=current_salary,
        expected_salary=expected_salary,
        job_hopping_frequency=job_hopping,
        education_str=education_str,
        work_experience_str=work_experience_str,
        project_experience_str=project_experience_str,
        skills_str=skills_str,
        certifications_str=certifications_str,
        languages_str=languages_str,
        self_assessment=self_assessment,
    )

    return prompt


# ============================================================
# 核心：调用 LLM
# ============================================================

def _call_llm(prompt: str, api_key: str = None, api_base: str = None,
              model: str = None, timeout: int = 300) -> str:
    """调用 LLM API（OpenAI 兼容格式）"""
    from openai import OpenAI

    client = OpenAI(
        api_key=api_key or AI_API_KEY,
        base_url=api_base or AI_API_BASE,
    )

    response = client.chat.completions.create(
        model=model or AI_MODEL,
        messages=[
            {"role": "system", "content": "你是一位资深技术招聘专家，擅长简历与职位描述的精准匹配分析。只输出 JSON，不输出其他内容。"},
            {"role": "user", "content": prompt},
        ],
        temperature=0.2,       # 低温度保证稳定性
        max_tokens=4096,
        timeout=timeout,
    )

    return response.choices[0].message.content


def _clean_json_response(text: str) -> str:
    """清理 LLM 返回的 JSON，去掉 markdown 标记等"""
    text = text.strip()
    # 去掉 ```json ... ``` 包裹
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*\n?", "", text)
        text = re.sub(r"\n?```\s*$", "", text)
    # 去掉可能的解释文字（在 JSON 前后）
    json_match = re.search(r"\{.*\}", text, re.DOTALL)
    if json_match:
        text = json_match.group(0)
    return text.strip()


# ============================================================
# 核心：执行 AI 匹配
# ============================================================

def ai_match_resume(
    job: Dict[str, Any],
    resume_parsed: Dict[str, Any],
    api_key: str = None,
    api_base: str = None,
    model: str = None,
) -> Dict[str, Any]:
    """
    对单个简历和职位执行 AI 匹配分析。

    参数：
        job: 职位信息 dict
        resume_parsed: 结构化简历 dict（来自 resume_parsed 字段）
        api_key, api_base, model: LLM 配置（可选）

    返回：
        dict: {
            "score": int (0-100),
            "recommendation": str,
            "breakdown": dict (8个维度),
            "highlights": list[str],
            "concerns": list[str],
            "suggestions": list[str],
            "summary": str,
            "raw_response": str,   # LLM 原始返回（用于调试）
        }
    """
    key = api_key or AI_API_KEY
    if not key:
        raise ValueError(
            "AI 匹配需要 LLM API Key。请设置环境变量 OPENAI_API_KEY，"
            "或传入 api_key 参数。"
        )

    # 构建 Prompt
    prompt = build_match_prompt(job, resume_parsed)

    # 调用 LLM
    raw_response = _call_llm(prompt, key, api_base, model)
    cleaned = _clean_json_response(raw_response)

    try:
        result = json.loads(cleaned)
    except json.JSONDecodeError as e:
        raise ValueError(
            f"AI 返回的内容无法解析为 JSON:\n{str(e)}\n\n"
            f"清理后的内容（前500字符）:\n{cleaned[:500]}\n\n"
            f"原始返回（前500字符）:\n{raw_response[:500]}"
        )

    # 校验和规范化
    result["score"] = max(0, min(100, int(result.get("score", 0))))
    if "breakdown" not in result:
        result["breakdown"] = {}
    for dim in ["skill", "experience", "project", "company",
                "education", "relevance", "salary", "stability"]:
        if dim not in result["breakdown"]:
            result["breakdown"][dim] = 0
        else:
            result["breakdown"][dim] = max(0, min(100, int(result["breakdown"][dim])))

    if "highlights" not in result:
        result["highlights"] = []
    if "concerns" not in result:
        result["concerns"] = []
    if "suggestions" not in result:
        result["suggestions"] = []
    if "summary" not in result:
        result["summary"] = ""
    if "recommendation" not in result:
        score = result["score"]
        if score >= 90:
            result["recommendation"] = "强烈推荐"
        elif score >= 75:
            result["recommendation"] = "推荐"
        elif score >= 60:
            result["recommendation"] = "待定"
        else:
            result["recommendation"] = "不推荐"

    result["raw_response"] = raw_response  # 保留原始返回

    return result


# ============================================================
# 核心：匹配结果写入数据库
# ============================================================

def save_match_result(
    candidate_id: int,
    job_id: int,
    match_result: Dict[str, Any],
    db_module=None,
) -> int:
    """
    将 AI 匹配结果写入 applications 表。
    如果已存在记录则更新，否则插入新记录。

    参数：
        candidate_id: 候选人 ID
        job_id: 职位 ID
        match_result: ai_match_resume() 的返回值
        db_module: db.py 模块（可选，默认动态导入）

    返回：
        int: applications 表记录 ID
    """
    if db_module is None:
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "db", os.path.join(os.path.dirname(__file__), "db.py")
        )
        db_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(db_module)

    conn = db_module._get_conn()
    cur = conn.cursor()

    # 检查是否已存在
    cur.execute(
        "SELECT id FROM applications WHERE candidate_id=? AND job_id=?",
        (candidate_id, job_id)
    )
    existing = cur.fetchone()

    breakdown_json = json.dumps(match_result.get("breakdown", {}), ensure_ascii=False)
    highlights_json = json.dumps(match_result.get("highlights", []), ensure_ascii=False)
    concerns_json = json.dumps(match_result.get("concerns", []), ensure_ascii=False)
    report_json = json.dumps(match_result, ensure_ascii=False)

    if existing:
        # 更新
        app_id = existing[0]
        cur.execute("""
            UPDATE applications
            SET match_score=?, match_dimensions=?, ai_highlights=?,
                ai_concerns=?, ai_recommendation=?, ai_report=?,
                updated_at=CURRENT_TIMESTAMP
            WHERE id=?
        """, (
            match_result["score"],
            breakdown_json,
            highlights_json,
            concerns_json,
            match_result["recommendation"],
            report_json,
            app_id,
        ))
    else:
        # 插入
        cur.execute("""
            INSERT INTO applications
            (candidate_id, job_id, match_score, match_dimensions,
             ai_highlights, ai_concerns, ai_recommendation, ai_report,
             status, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'pending', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        """, (
            candidate_id,
            job_id,
            match_result["score"],
            breakdown_json,
            highlights_json,
            concerns_json,
            match_result["recommendation"],
            report_json,
        ))
        app_id = cur.lastrowid

    conn.commit()
    conn.close()

    return app_id


# ============================================================
# 高级：批量匹配
# ============================================================

def batch_ai_match(
    job: Dict[str, Any],
    candidates: List[Dict[str, Any]],  # each has 'id' and 'resume_parsed'
    api_key: str = None,
    api_base: str = None,
    model: str = None,
    delay_seconds: float = 0.5,  # API 限速保护
) -> List[Dict[str, Any]]:
    """
    批量对多个候选人进行 AI 匹配。

    参数：
        job: 职位信息
        candidates: [{"id": 1, "resume_parsed": {...}}, ...]
        delay_seconds: 每次 API 调用之间的延迟（秒）

    返回：
        [{"candidate_id": 1, "app_id": 5, "score": 85, ...}, ...]
    """
    import time

    results = []
    for i, cand in enumerate(candidates):
        cand_id = cand["id"]
        resume_parsed = cand.get("resume_parsed", {})

        # 如果 resume_parsed 是字符串，尝试解析为 JSON
        if isinstance(resume_parsed, str):
            try:
                resume_parsed = json.loads(resume_parsed)
            except (json.JSONDecodeError, TypeError):
                # 解析失败，跳过
                results.append({
                    "candidate_id": cand_id,
                    "error": "resume_parsed 解析失败",
                    "score": 0,
                })
                continue

        try:
            match_result = ai_match_resume(
                job, resume_parsed, api_key, api_base, model
            )
            app_id = save_match_result(cand_id, job["id"], match_result)

            results.append({
                "candidate_id": cand_id,
                "app_id": app_id,
                "score": match_result["score"],
                "recommendation": match_result["recommendation"],
                "highlights": match_result["highlights"][:3],
                "concerns": match_result["concerns"][:3],
            })
        except Exception as e:
            results.append({
                "candidate_id": cand_id,
                "error": str(e),
                "score": 0,
            })

        # 限速保护（不是最后一个）
        if i < len(candidates) - 1 and delay_seconds > 0:
            time.sleep(delay_seconds)

    return results


# ============================================================
# 工具：从数据库加载数据并执行匹配
# ============================================================

def match_and_save(
    candidate_id: int,
    job_id: int,
    api_key: str = None,
    api_base: str = None,
    model: str = None,
    db_path: str = None,
) -> Dict[str, Any]:
    """
    一站式：从数据库加载 candidates 和 jobs，执行 AI 匹配，保存结果。

    参数：
        candidate_id: 候选人 ID
        job_id: 职位 ID
        api_key, api_base, model: LLM 配置
        db_path: 数据库路径（可选）

    返回：
        dict: ai_match_resume() 的结果
    """
    import sqlite3
    import sys, os

    # 动态导入 db.py
    if db_path is None:
        db_path = os.path.join(os.path.dirname(__file__), "recruitment.db")

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    # 加载候选人
    cur = conn.execute("SELECT * FROM candidates WHERE id=?", (candidate_id,))
    cand_row = cur.fetchone()
    if not cand_row:
        raise ValueError(f"候选人不存在: id={candidate_id}")
    cand_dict = dict(cand_row)

    # 解析 resume_parsed
    resume_parsed = {}
    if cand_dict.get("resume_parsed"):
        try:
            resume_parsed = json.loads(cand_dict["resume_parsed"])
        except (json.JSONDecodeError, TypeError):
            resume_parsed = {}

    # 如果 resume_parsed 为空，用基本信息构造
    if not resume_parsed:
        resume_parsed = {
            "name": cand_dict.get("name", ""),
            "phone": cand_dict.get("phone", ""),
            "email": cand_dict.get("email", ""),
            "work_years": cand_dict.get("work_years", 0),
            "skills": [s.strip() for s in cand_dict.get("skills", "").split(",") if s.strip()],
            "education": [{"school": cand_dict.get("education", ""), "degree": "", "major": "", "start": "", "end": ""}],
            "work_experience": [{"company": cand_dict.get("recent_company", ""), "position": cand_dict.get("recent_position", ""), "start": "", "end": ""}] if cand_dict.get("recent_position") else [],
            "project_experience": [],
            "certifications": [],
            "languages": [],
            "self_assessment": "",
            "current_salary": "",
            "expected_salary": "",
            "job_hopping_frequency": "未知",
            "gender": "未知",
            "current_location": "",
        }

    # 加载职位
    cur = conn.execute("SELECT * FROM jobs WHERE id=?", (job_id,))
    job_row = cur.fetchone()
    if not job_row:
        raise ValueError(f"职位不存在: id={job_id}")
    job_dict = dict(job_row)

    conn.close()

    # 执行匹配
    match_result = ai_match_resume(job_dict, resume_parsed, api_key, api_base, model)

    # 保存结果
    app_id = save_match_result(candidate_id, job_id, match_result)

    match_result["app_id"] = app_id
    return match_result


# ============================================================
# CLI 入口（方便测试）
# ============================================================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="AI 简历匹配工具")
    parser.add_argument("--candidate-id", type=int, required=True, help="候选人 ID")
    parser.add_argument("--job-id", type=int, required=True, help="职位 ID")
    parser.add_argument("--api-key", type=str, default=None, help="LLM API Key")
    parser.add_argument("--api-base", type=str, default=None, help="LLM API Base URL")
    parser.add_argument("--model", type=str, default=None, help="LLM 模型名")
    parser.add_argument("--show-prompt", action="store_true", help="只显示 Prompt，不调用 API")

    args = parser.parse_args()

    # 加载数据
    import sqlite3

    conn = sqlite3.connect(
        os.path.join(os.path.dirname(__file__), "recruitment.db")
    )
    conn.row_factory = sqlite3.Row

    cur = conn.execute("SELECT * FROM candidates WHERE id=?", (args.candidate_id,))
    cand_row = cur.fetchone()
    if not cand_row:
        print(f"错误：候选人不存在 id={args.candidate_id}")
        exit(1)

    cur = conn.execute("SELECT * FROM jobs WHERE id=?", (args.job_id,))
    job_row = cur.fetchone()
    if not job_row:
        print(f"错误：职位不存在 id={args.job_id}")
        exit(1)

    conn.close()

    cand_dict = dict(cand_row)
    job_dict = dict(job_row)

    # 解析 resume_parsed
    resume_parsed = {}
    if cand_dict.get("resume_parsed"):
        try:
            resume_parsed = json.loads(cand_dict["resume_parsed"])
        except Exception:
            pass

    if not resume_parsed:
        print("警告：resume_parsed 为空，将使用基本信息构造")
        # 构造最小 resume_parsed...

    if args.show_prompt:
        prompt = build_match_prompt(job_dict, resume_parsed)
        print(prompt)
    else:
        result = match_and_save(
            args.candidate_id, args.job_id,
            api_key=args.api_key,
            api_base=args.api_base,
            model=args.model,
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))