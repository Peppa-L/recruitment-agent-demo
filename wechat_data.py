# -*- coding: utf-8 -*-
"""
微信/企业微信群聊模拟数据模块
==============================
生成真实的招聘场景群聊对话，用于演示 AI 自动解析能力。

数据特点：
  - 口语化表达（符合微信群聊习惯）
  - 关键词可能不完整（如"张工"代替全名、"py"代替"Python"）
  - 信息分散在多条消息中（需要 AI 聚合）
  - 包含闲聊、无关信息（测试 AI 过滤能力）
"""

from datetime import datetime, timedelta
from typing import List, Dict, Any

# ============================================================
# 模拟时间线（从现在往前推）
# ============================================================
NOW = datetime(2026, 6, 18, 10, 0, 0)

# ============================================================
# 群聊参与人
# ============================================================
MEMBERS = {
    "hr_wang":     {"name": "王芳", "role": "HR",       "dept": "人力资源部"},
    "hr_liu":      {"name": "刘静", "role": "HR助理",    "dept": "人力资源部"},
    "tech_li":     {"name": "李总", "role": "技术总监",   "dept": "技术部"},
    "tech_zhao":   {"name": "赵工", "role": "技术主管",   "dept": "技术部"},
    "product_liu": {"name": "刘总", "role": "产品总监",   "dept": "产品部"},
    "data_zhou":   {"name": "周工", "role": "数据负责人", "dept": "数据部"},
    "ops_sun":     {"name": "孙工", "role": "运维主管",   "dept": "运维部"},
}

# ============================================================
# 模拟候选人简历数据
# ============================================================
CANDIDATES = [
    {
        "id": 1,
        "name": "张明",
        "phone": "13800001111",
        "email": "zhangming@email.com",
        "gender": "男",
        "age": 28,
        "current_location": "北京",
        "position": "Python后端工程师",
        "work_years": 5,
        "current_salary": "28K×14",
        "expected_salary": "35K-40K",
        "education": [
            {"school": "清华大学", "degree": "硕士", "major": "计算机科学与技术", "start": "2017", "end": "2020"},
            {"school": "华中科技大学", "degree": "本科", "major": "软件工程", "start": "2013", "end": "2017"},
        ],
        "work_experience": [
            {
                "company": "字节跳动", "position": "高级后端工程师", "industry": "互联网",
                "start": "2022-03", "end": "至今",
                "description": "负责推荐系统后端服务开发，日处理请求10亿+。主导服务重构，QPS提升40%。技术栈：Python/Django/Go/Redis/Kafka/K8s。"
            },
            {
                "company": "美团", "position": "后端开发工程师", "industry": "互联网",
                "start": "2020-07", "end": "2022-02",
                "description": "参与支付系统微服务化改造，负责订单模块开发。技术栈：Python/FastAPI/MySQL/RabbitMQ/Docker。"
            },
        ],
        "project_experience": [
            {"name": "推荐系统引擎重构", "role": "核心开发", "description": "将单体推荐引擎拆分为微服务，引入Kafka解耦", "tech_stack": ["Python", "Go", "Kafka", "K8s", "Redis"]},
            {"name": "实时数据管道", "role": "技术负责人", "description": "搭建实时数据处理管道，延迟从5s降到200ms", "tech_stack": ["Flink", "Kafka", "ClickHouse", "Python"]},
        ],
        "skills": ["Python", "Go", "Django", "FastAPI", "MySQL", "Redis", "Kafka", "Kubernetes", "Docker", "微服务", "系统设计"],
        "certifications": ["AWS Solutions Architect"],
        "languages": ["英语:CET-6"],
        "self_assessment": "5年互联网大厂后端开发经验，专注高并发系统设计与优化。有从0到1的项目经验，善于技术选型和团队协作。",
        "job_hopping_frequency": "低",
        "raw_summary": "清华硕士，5年后端经验，字节+美团背景，高并发系统经验丰富。适合中高级后端岗位。",
    },
    {
        "id": 2,
        "name": "李芳",
        "phone": "13800002222",
        "email": "lifang@email.com",
        "gender": "女",
        "age": 26,
        "current_location": "上海",
        "position": "前端开发工程师",
        "work_years": 3,
        "current_salary": "22K×13",
        "expected_salary": "28K-32K",
        "education": [
            {"school": "复旦大学", "degree": "本科", "major": "数字媒体技术", "start": "2016", "end": "2020"},
        ],
        "work_experience": [
            {
                "company": "小红书", "position": "前端开发工程师", "industry": "互联网/电商",
                "start": "2021-06", "end": "至今",
                "description": "负责电商模块前端开发，主导组件库升级。技术栈：React/TypeScript/Next.js/Tailwind。"
            },
            {
                "company": "携程", "position": "前端开发实习生→初级工程师", "industry": "互联网/旅游",
                "start": "2020-04", "end": "2021-05",
                "description": "参与机票预订页面重构，负责移动端适配。技术栈：Vue/JavaScript/Webpack/Sass。"
            },
        ],
        "project_experience": [
            {"name": "组件库升级项目", "role": "负责人", "description": "从0搭建公司级React组件库，覆盖50+组件", "tech_stack": ["React", "TypeScript", "Storybook", "Rollup"]},
            {"name": "电商首页改版", "role": "核心开发", "description": "首页性能优化，LCP从4s降到1.5s", "tech_stack": ["Next.js", "SSR", "Tailwind CSS", "Vercel"]},
        ],
        "skills": ["React", "Vue", "TypeScript", "JavaScript", "Next.js", "Tailwind CSS", "Webpack", "Node.js", "Git"],
        "certifications": [],
        "languages": ["英语:CET-6", "日语:N2"],
        "self_assessment": "3年前端开发经验，擅长React生态，注重代码质量和用户体验。有组件库从0到1的建设经验。",
        "job_hopping_frequency": "低",
        "raw_summary": "复旦本科，3年经验，小红书+携程背景。React方向，有组件库建设经验。适合中级前端岗位。",
    },
    {
        "id": 3,
        "name": "王强",
        "phone": "13800003333",
        "email": "wangqiang@email.com",
        "gender": "男",
        "age": 31,
        "current_location": "深圳",
        "position": "高级产品经理",
        "work_years": 6,
        "current_salary": "38K×15",
        "expected_salary": "45K-50K",
        "education": [
            {"school": "北京大学", "degree": "硕士", "major": "工商管理", "start": "2014", "end": "2017"},
            {"school": "武汉大学", "degree": "本科", "major": "信息管理与信息系统", "start": "2010", "end": "2014"},
        ],
        "work_experience": [
            {
                "company": "腾讯", "position": "高级产品经理", "industry": "互联网",
                "start": "2023-01", "end": "至今",
                "description": "负责企业SaaS产品规划，从0到1搭建产品体系，DAU从0增长到50万。"
            },
            {
                "company": "阿里巴巴", "position": "产品经理", "industry": "互联网/电商",
                "start": "2019-08", "end": "2022-12",
                "description": "负责商家后台产品，主导商家工具矩阵重构，商家满意度提升30%。"
            },
            {
                "company": "网易", "position": "助理产品经理", "industry": "互联网",
                "start": "2017-07", "end": "2019-07",
                "description": "参与网易云音乐用户端产品迭代，负责播放器模块优化。"
            },
        ],
        "project_experience": [
            {"name": "企业协作平台0-1建设", "role": "产品负责人", "description": "从需求调研到上线全程负责", "tech_stack": []},
            {"name": "商家后台重构", "role": "产品负责人", "description": "重构商家工具矩阵，提升NPS 30%", "tech_stack": []},
        ],
        "skills": ["产品规划", "需求分析", "数据分析", "SQL", "Axure", "Figma", "用户研究", "项目管理", "Scrum"],
        "certifications": ["PMP", "NPDP产品经理认证"],
        "languages": ["英语:CET-6", "粤语"],
        "self_assessment": "6年互联网大厂产品经验，擅长B端SaaS产品。有从0到1产品建设经验，数据驱动决策能力强。",
        "job_hopping_frequency": "低",
        "raw_summary": "北大MBA，6年产品经验，腾讯+阿里+网易背景。擅长B端SaaS，有0-1经验。适合高级产品岗位。",
    },
    {
        "id": 4,
        "name": "赵丽",
        "phone": "13800004444",
        "email": "zhaoli@email.com",
        "gender": "女",
        "age": 24,
        "current_location": "杭州",
        "position": "数据分析师",
        "work_years": 2,
        "current_salary": "15K×13",
        "expected_salary": "18K-22K",
        "education": [
            {"school": "浙江大学", "degree": "本科", "major": "统计学", "start": "2018", "end": "2022"},
        ],
        "work_experience": [
            {
                "company": "蚂蚁集团", "position": "数据分析师", "industry": "金融科技",
                "start": "2022-07", "end": "至今",
                "description": "负责风控数据分析，搭建业务监控看板。技术栈：SQL/Python/Tableau/QuickBI。"
            },
        ],
        "project_experience": [
            {"name": "风控策略效果评估体系", "role": "核心分析师", "description": "搭建风控策略AB实验评估框架", "tech_stack": ["Python", "SQL", "Tableau"]},
        ],
        "skills": ["SQL", "Python", "Pandas", "NumPy", "Tableau", "QuickBI", "Excel", "统计分析", "AB实验"],
        "certifications": [],
        "languages": ["英语:CET-6"],
        "self_assessment": "2年金融科技数据分析经验，擅长风控分析和数据可视化。统计学专业背景，逻辑严密。",
        "job_hopping_frequency": "低",
        "raw_summary": "浙大统计本科，2年蚂蚁数据分析经验。适合初级到中级数据分析岗位。",
    },
    {
        "id": 5,
        "name": "陈伟",
        "phone": "13800005555",
        "email": "chenwei@email.com",
        "gender": "男",
        "age": 29,
        "current_location": "成都",
        "position": "DevOps工程师",
        "work_years": 4,
        "current_salary": "25K×14",
        "expected_salary": "30K-35K",
        "education": [
            {"school": "电子科技大学", "degree": "本科", "major": "网络工程", "start": "2013", "end": "2017"},
        ],
        "work_experience": [
            {
                "company": "华为", "position": "DevOps工程师", "industry": "ICT",
                "start": "2023-04", "end": "至今",
                "description": "负责云服务CI/CD管道建设，管理200+服务发布。技术栈：K8s/Docker/Jenkins/Terraform/Ansible。"
            },
            {
                "company": "京东", "position": "运维开发工程师", "industry": "互联网/电商",
                "start": "2019-08", "end": "2023-03",
                "description": "负责自动化运维平台开发，发布效率提升60%。技术栈：Python/Go/K8s/Prometheus/Grafana。"
            },
            {
                "company": "中国移动", "position": "系统运维工程师", "industry": "运营商",
                "start": "2017-07", "end": "2019-07",
                "description": "负责业务系统日常运维，参与自动化脚本开发。"
            },
        ],
        "project_experience": [
            {"name": "CI/CD统一平台", "role": "核心开发", "description": "搭建公司级CI/CD平台，覆盖全研发流程", "tech_stack": ["Jenkins", "K8s", "Docker", "Python", "Groovy"]},
            {"name": "监控告警体系升级", "role": "负责人", "description": "从Zabbix迁移到Prometheus+Grafana生态", "tech_stack": ["Prometheus", "Grafana", "Alertmanager", "Go"]},
        ],
        "skills": ["Kubernetes", "Docker", "Jenkins", "Terraform", "Ansible", "Python", "Go", "Prometheus", "Grafana", "CI/CD", "Linux"],
        "certifications": ["CKA (Certified Kubernetes Administrator)", "AWS Solutions Architect"],
        "languages": ["英语:CET-4"],
        "self_assessment": "4年DevOps经验，精通K8s和CI/CD体系。有大规模服务管理经验，注重自动化与稳定性。",
        "job_hopping_frequency": "中",
        "raw_summary": "电子科大本科，4年DevOps经验，华为+京东背景。K8s方向，有大规模集群管理经验。",
    },
    {
        "id": 6,
        "name": "刘洋",
        "phone": "13800006666",
        "email": "liuyang@email.com",
        "gender": "男",
        "age": 26,
        "current_location": "上海",
        "position": "测试开发工程师",
        "work_years": 3,
        "current_salary": "18K×14",
        "expected_salary": "22K-26K",
        "education": [
            {"school": "南京邮电大学", "degree": "本科", "major": "计算机科学与技术", "start": "2017", "end": "2021"},
        ],
        "work_experience": [
            {
                "company": "拼多多", "position": "测试工程师", "industry": "互联网/电商",
                "start": "2021-07", "end": "至今",
                "description": "负责电商业务线的功能测试，编写测试用例，执行回归测试。使用Selenium做简单UI自动化。"
            },
        ],
        "project_experience": [
            {"name": "电商活动页测试", "role": "测试执行", "description": "大促活动页面功能测试和兼容性测试", "tech_stack": ["Selenium", "Charles", "Postman"]},
        ],
        "skills": ["功能测试", "Selenium", "Postman", "Charles", "SQL", "JMeter基础"],
        "certifications": [],
        "languages": ["英语:CET-4"],
        "self_assessment": "3年电商功能测试经验，熟悉测试流程和用例设计。希望向自动化测试方向发展。",
        "job_hopping_frequency": "低",
        "raw_summary": "南邮本科，3年拼多多测试经验。功能测试为主，自动化经验较浅。不匹配自动化测试框架岗位。",
    },
    {
        "id": 7,
        "name": "吴敏",
        "phone": "13800007777",
        "email": "wumin@email.com",
        "gender": "女",
        "age": 27,
        "current_location": "杭州",
        "position": "UI设计师",
        "work_years": 4,
        "current_salary": "30K×13",
        "expected_salary": "35K",
        "education": [
            {"school": "中国美术学院", "degree": "本科", "major": "视觉传达设计", "start": "2015", "end": "2019"},
        ],
        "work_experience": [
            {
                "company": "得物", "position": "资深UI设计师", "industry": "互联网/电商",
                "start": "2022-03", "end": "至今",
                "description": "负责电商C端设计系统维护，搭建组件库。主导双11大促视觉设计。"
            },
            {
                "company": "网易", "position": "UI设计师", "industry": "互联网/游戏",
                "start": "2019-07", "end": "2022-02",
                "description": "参与游戏社区产品UI设计，负责icon和动效设计。"
            },
        ],
        "project_experience": [
            {"name": "设计系统搭建", "role": "主设计师", "description": "从0搭建电商设计组件库，覆盖100+组件", "tech_stack": ["Figma", "Sketch", "Principle"]},
        ],
        "skills": ["Figma", "Sketch", "Adobe XD", "Photoshop", "Illustrator", "Principle", "设计系统", "组件库"],
        "certifications": [],
        "languages": ["英语:CET-6"],
        "self_assessment": "4年UI设计经验，擅长电商和游戏社区产品设计。有设计系统从0搭建经验，注重设计规范化和组件化。",
        "job_hopping_frequency": "低",
        "raw_summary": "国美本科，4年设计经验，网易+得物背景。设计功底扎实，但期望薪资偏高。",
    },
    {
        "id": 8,
        "name": "周杰",
        "phone": "13800008888",
        "email": "zhoujie@email.com",
        "gender": "男",
        "age": 29,
        "current_location": "杭州",
        "position": "Java后端工程师",
        "work_years": 5,
        "current_salary": "32K×16",
        "expected_salary": "35K-40K",
        "education": [
            {"school": "浙江大学", "degree": "硕士", "major": "软件工程", "start": "2017", "end": "2020"},
            {"school": "杭州电子科技大学", "degree": "本科", "major": "计算机科学与技术", "start": "2013", "end": "2017"},
        ],
        "work_experience": [
            {
                "company": "阿里巴巴", "position": "Java开发工程师", "industry": "互联网",
                "start": "2020-07", "end": "至今",
                "description": "负责内部工具平台开发，主要做OA系统和运维管理后台。技术栈：Java/Spring Boot/MyBatis/MySQL。"
            },
        ],
        "project_experience": [
            {"name": "内部运维管理平台", "role": "后端开发", "description": "负责告警管理和工单系统后端开发", "tech_stack": ["Java", "Spring Boot", "MySQL", "Redis"]},
        ],
        "skills": ["Java", "Spring Boot", "MyBatis", "MySQL", "Redis", "RabbitMQ", "Linux"],
        "certifications": [],
        "languages": ["英语:CET-6"],
        "self_assessment": "5年阿里内部工具开发经验，Java基础扎实，熟悉Spring生态。希望接触高并发业务场景。",
        "job_hopping_frequency": "低",
        "raw_summary": "浙大硕士，5年阿里经验但主要是内部工具。高并发经验不足，技术面未通过。",
    },
    {
        "id": 9,
        "name": "林小红",
        "phone": "13800009999",
        "email": "linxiaohong@email.com",
        "gender": "女",
        "age": 30,
        "current_location": "上海",
        "position": "运营经理",
        "work_years": 5,
        "current_salary": "28K×15",
        "expected_salary": "30K-35K",
        "education": [
            {"school": "上海交通大学", "degree": "本科", "major": "新闻传播学", "start": "2012", "end": "2016"},
        ],
        "work_experience": [
            {
                "company": "哔哩哔哩", "position": "内容运营负责人", "industry": "互联网/内容",
                "start": "2023-01", "end": "至今",
                "description": "管理5人内容运营小组，负责社区内容策略和创作者运营。DAU提升40%。"
            },
            {
                "company": "小红书", "position": "社区运营专员→高级运营", "industry": "互联网/社交",
                "start": "2019-03", "end": "2022-12",
                "description": "负责社区话题运营和用户增长，策划多场S级活动，单场活动UV超500万。"
            },
            {
                "company": "美团", "position": "运营实习生→运营专员", "industry": "互联网/生活服务",
                "start": "2016-07", "end": "2019-02",
                "description": "负责商家运营和活动策划，参与618大促运营方案制定。"
            },
        ],
        "project_experience": [
            {"name": "创作者成长体系", "role": "项目负责人", "description": "搭建创作者分层运营体系，创作者留存率提升30%", "tech_stack": []},
            {"name": "社区话题运营S级活动", "role": "运营负责人", "description": "策划执行社区年度话题活动，UV破500万", "tech_stack": []},
        ],
        "skills": ["内容运营", "用户增长", "活动策划", "数据分析", "SQL基础", "团队管理", "社区运营"],
        "certifications": [],
        "languages": ["英语:CET-6"],
        "self_assessment": "5年互联网运营经验，擅长内容社区运营和用户增长。有3年团队管理经验，数据驱动决策。",
        "job_hopping_frequency": "中",
        "raw_summary": "上交本科，5年运营经验，B站+小红书+美团背景。内容运营和团队管理经验丰富。",
    },
    {
        "id": 10,
        "name": "何伟",
        "phone": "13800001010",
        "email": "hewei@email.com",
        "gender": "男",
        "age": 28,
        "current_location": "北京",
        "position": "算法工程师",
        "work_years": 4,
        "current_salary": "42K×15",
        "expected_salary": "45K-50K",
        "education": [
            {"school": "中科院计算所", "degree": "硕士", "major": "计算机视觉", "start": "2018", "end": "2021"},
            {"school": "北京邮电大学", "degree": "本科", "major": "通信工程", "start": "2014", "end": "2018"},
        ],
        "work_experience": [
            {
                "company": "字节跳动", "position": "推荐算法工程师", "industry": "互联网",
                "start": "2023-03", "end": "至今",
                "description": "负责信息流推荐召回和排序模型优化，CTR提升15%。技术栈：Python/PyTorch/TensorFlow/Spark。"
            },
            {
                "company": "商汤科技", "position": "算法研究员", "industry": "AI",
                "start": "2021-07", "end": "2023-02",
                "description": "负责CV模型研究和落地，参与安防场景的目标检测项目。发表一篇CVPR论文。"
            },
        ],
        "project_experience": [
            {"name": "推荐系统召回模型优化", "role": "核心开发", "description": "基于Transformer改进召回模型，召回率提升20%", "tech_stack": ["Python", "PyTorch", "Spark", "Hive"]},
            {"name": "多模态内容理解", "role": "算法负责人", "description": "图文多模态Embedding，提升冷启动内容分发效率", "tech_stack": ["PyTorch", "TensorFlow", "CLIP"]},
        ],
        "skills": ["Python", "PyTorch", "TensorFlow", "Spark", "SQL", "推荐系统", "计算机视觉", "NLP基础", "模型部署"],
        "certifications": [],
        "languages": ["英语:CET-6", "可阅读英文论文"],
        "self_assessment": "4年AI算法经验，商汤CV背景+字节推荐系统经验。有顶会论文和实际业务落地能力。",
        "job_hopping_frequency": "中",
        "raw_summary": "中科院硕士，4年算法经验，商汤+字节背景。推荐系统方向，有CVPR论文，工程能力一般。",
    },
]

# ============================================================
# 招聘职位
# ============================================================
JOBS = [
    {
        "id": 1,
        "title": "Python后端工程师",
        "department": "技术部",
        "jd_text": "负责公司核心业务系统后端开发，参与架构设计。要求：3-5年Python经验，熟悉Django/FastAPI，有高并发经验优先。",
        "salary_range": "30K-45K",
        "location": "北京",
        "urgency": "紧急",
        "jd_requirements_json": '{"hard_skills":["Python","Django/FastAPI","MySQL/PostgreSQL","Redis"],"soft_skills":["团队协作","沟通能力"],"years":5,"education":"本科及以上","preferred":["高并发经验","大厂背景","Go语言"]}',
    },
    {
        "id": 2,
        "title": "前端开发工程师",
        "department": "技术部",
        "jd_text": "负责Web端产品开发，参与组件库建设。要求：2-4年前端经验，精通React或Vue，有TypeScript经验。",
        "salary_range": "25K-35K",
        "location": "上海",
        "urgency": "普通",
        "jd_requirements_json": '{"hard_skills":["React/Vue","TypeScript","CSS/HTML"],"soft_skills":["审美能力","沟通能力"],"years":3,"education":"本科及以上","preferred":["组件库经验","SSR","全栈能力"]}',
    },
    {
        "id": 3,
        "title": "高级产品经理",
        "department": "产品部",
        "jd_text": "负责B端SaaS产品规划和落地。要求：5-8年产品经验，有B端经验，数据驱动。",
        "salary_range": "40K-55K",
        "location": "深圳",
        "urgency": "紧急",
        "jd_requirements_json": '{"hard_skills":["产品规划","数据分析","SQL","原型设计"],"soft_skills":["领导力","跨部门协作"],"years":6,"education":"本科及以上","preferred":["B端SaaS经验","0-1经验","技术背景"]}',
    },
]

# ============================================================
# 微信群聊对话（核心数据）
# ============================================================

# --- 场景1：HR与技术总监讨论张明简历 ---
CHAT_SCENARIO_1 = {
    "group_name": "技术部招聘沟通群",
    "participants": ["hr_wang", "tech_li", "tech_zhao"],
    "description": "HR 王芳推送候选人张明的简历，与技术总监李总、技术主管赵工商议是否约面试",
    "messages": [
        {"time": NOW - timedelta(days=5, hours=3), "sender": "hr_wang", "content": "李总、赵工，刚收到一个后端简历，清华硕士，字节+美团背景，5年经验，我看了下感觉还挺匹配的，你们帮忙评估一下？"},
        {"time": NOW - timedelta(days=5, hours=2, minutes=50), "sender": "hr_wang", "content": "[文件] 张明_简历.pdf"},
        {"time": NOW - timedelta(days=5, hours=2, minutes=30), "sender": "tech_li", "content": "清华硕？可以啊，我看看"},
        {"time": NOW - timedelta(days=5, hours=1), "sender": "tech_li", "content": "简历看完了，整体不错。字节做的推荐系统后端，这个跟我们业务场景很像。而且有Kafka、K8s经验，跟我们技术栈匹配"},
        {"time": NOW - timedelta(days=5, hours=0, minutes=45), "sender": "tech_zhao", "content": "我补充一下，他之前美团做的支付系统，那个微服务化改造跟我们今年的重构方向也对口。这人技术深度应该可以"},
        {"time": NOW - timedelta(days=5, hours=0, minutes=30), "sender": "hr_wang", "content": "那要不我安排个面试？他期望35-40K，在我们预算范围内"},
        {"time": NOW - timedelta(days=5, hours=0, minutes=20), "sender": "tech_li", "content": "可以，安排吧。时间的话……下周二三我下午都行，你跟他约一下"},
        {"time": NOW - timedelta(days=5, hours=0, minutes=10), "sender": "tech_zhao", "content": "我也参加，想重点问下他推荐系统那块的设计思路"},
        {"time": NOW - timedelta(days=4, hours=6), "sender": "hr_wang", "content": "好的，已约！张明下周二6月16日下午2点，线上视频面试 @李总 @赵工"},
        {"time": NOW - timedelta(days=4, hours=5), "sender": "tech_li", "content": "收到👍"},
        {"time": NOW - timedelta(days=4, hours=4), "sender": "tech_zhao", "content": "OK，我加到日历里了"},
    ],
    "candidate_id": 1,
    "job_id": 1,
    "expected_parsed": {
        "candidate_name": "张明",
        "position": "Python后端工程师",
        "stage": "面试已安排",
        "interview_date": "2026-06-16",
        "interview_time": "14:00",
        "interview_type": "线上视频",
        "interviewers": ["李总", "赵工"],
        "salary_discussion": "期望35-40K，在预算内",
        "key_feedback": ["清华硕士，背景优秀", "推荐系统经验与业务匹配", "微服务经验与重构方向对口"],
    },
}

# --- 场景2：面试后反馈 ---
CHAT_SCENARIO_2 = {
    "group_name": "技术部招聘沟通群",
    "participants": ["hr_wang", "tech_li", "tech_zhao"],
    "description": "张明面试结束后的反馈沟通",
    "messages": [
        {"time": NOW - timedelta(days=2, hours=1), "sender": "hr_wang", "content": "刚面完张明，两位觉得怎么样？我这边先记一下反馈"},
        {"time": NOW - timedelta(days=2, hours=0, minutes=55), "sender": "tech_zhao", "content": "技术很强，推荐系统设计那块问得比较深，他都能答上来。分布式一致性也理解得不错，做过实际项目的人就是不一样"},
        {"time": NOW - timedelta(days=2, hours=0, minutes=50), "sender": "tech_li", "content": "我这边整体给85分吧。系统设计能力符合预期，沟通也挺好。唯一的小顾虑是他Go的经验偏浅，我们后面一些新服务要用Go写"},
        {"time": NOW - timedelta(days=2, hours=0, minutes=40), "sender": "hr_wang", "content": "Go的话他能学起来吗？字节那边应该也有Go的氛围吧"},
        {"time": NOW - timedelta(days=2, hours=0, minutes=35), "sender": "tech_zhao", "content": "应该问题不大，Python转Go很快的，他又不是没写过。主要看学习意愿"},
        {"time": NOW - timedelta(days=2, hours=0, minutes=30), "sender": "tech_li", "content": "嗯，那这样，我觉得可以过。让他进二面吧，二面让架构组的张工也参加，重点考察下系统设计"},
        {"time": NOW - timedelta(days=2, hours=0, minutes=25), "sender": "hr_wang", "content": "收到。张明期望35-40K，我们预算上限45K，如果二面也过了，到时候offer给多少合适？"},
        {"time": NOW - timedelta(days=2, hours=0, minutes=20), "sender": "tech_li", "content": "看他二面表现吧，如果确实优秀可以给到38-40K。但不能超过40，我们部门预算卡得紧"},
        {"time": NOW - timedelta(days=2, hours=0, minutes=15), "sender": "hr_wang", "content": "明白。那我安排二面，暂定周四下午？@赵工 你帮忙约一下架构组的张工"},
        {"time": NOW - timedelta(days=2, hours=0, minutes=10), "sender": "tech_zhao", "content": "OK，我跟他打个招呼"},
    ],
    "candidate_id": 1,
    "job_id": 1,
    "expected_parsed": {
        "candidate_name": "张明",
        "position": "Python后端工程师",
        "stage": "通过一面，待安排二面",
        "interview_score": 85,
        "key_feedback": ["技术能力强", "系统设计能力好", "Go经验偏浅但不影响"],
        "salary_discussion": "offer预算38-40K，上限40K",
        "next_step": "安排二面，架构组张工参加",
        "interview_date": "本周四下午（暂定）",
    },
}

# --- 场景3：前端候选人李芳 ---
CHAT_SCENARIO_3 = {
    "group_name": "技术部招聘沟通群",
    "participants": ["hr_liu", "tech_li", "tech_zhao"],
    "description": "HR助理刘静推送前端候选人李芳，讨论是否面试",
    "messages": [
        {"time": NOW - timedelta(days=4, hours=5), "sender": "hr_liu", "content": "李总赵工好，这边筛选了一个前端候选人，复旦本科，小红书做了两年多，React方向。之前携程也待过一年多。你们看下？"},
        {"time": NOW - timedelta(days=4, hours=4, minutes=50), "sender": "hr_liu", "content": "[文件] 李芳_前端工程师_简历.pdf"},
        {"time": NOW - timedelta(days=4, hours=4, minutes=30), "sender": "tech_zhao", "content": "我看了下，小红书做电商模块的对吧？我们这边刚好也在做电商相关的。那个组件库升级的项目挺亮眼的，从0搭的"},
        {"time": NOW - timedelta(days=4, hours=4, minutes=15), "sender": "tech_li", "content": "嗯，复旦的背景也不错。不过她经验3年偏少，而且携程那段只有1年。稳定性怎么样？"},
        {"time": NOW - timedelta(days=4, hours=4, minutes=10), "sender": "hr_liu", "content": "携程是实习+转正，干了1年多，小红书到现在2年多了。整体还算稳定，跳槽不频繁"},
        {"time": NOW - timedelta(days=4, hours=3, minutes=50), "sender": "tech_zhao", "content": "组件库经验对我们挺有价值的，我们自己的组件库一直想升级，缺人。而且她还会Next.js和SSR，技术面挺广"},
        {"time": NOW - timedelta(days=4, hours=3, minutes=30), "sender": "tech_li", "content": "那就约个面试吧，看看实际水平。她期望多少？"},
        {"time": NOW - timedelta(days=4, hours=3, minutes=20), "sender": "hr_liu", "content": "期望28-32K，在预算范围内（这个职位25-35K）"},
        {"time": NOW - timedelta(days=4, hours=3, minutes=10), "sender": "tech_li", "content": "OK安排吧，让赵工主面，我就不参加了"},
        {"time": NOW - timedelta(days=3, hours=6), "sender": "hr_liu", "content": "已约好，周四6月11日下午3点，赵工你那边OK吗？"},
        {"time": NOW - timedelta(days=3, hours=5), "sender": "tech_zhao", "content": "没问题，我到时候准备几个前端架构设计的问题"},
    ],
    "candidate_id": 2,
    "job_id": 2,
    "expected_parsed": {
        "candidate_name": "李芳",
        "position": "前端开发工程师",
        "stage": "面试已安排",
        "interview_date": "2026-06-11",
        "interview_time": "15:00",
        "interviewer": "赵工",
        "salary_discussion": "期望28-32K，预算25-35K",
        "key_feedback": ["组件库经验有价值", "技术面广（React/Next.js/SSR）", "经验3年偏少但背景匹配"],
    },
}

# --- 场景4：产品经理候选人王强 ---
CHAT_SCENARIO_4 = {
    "group_name": "产品&技术招聘群",
    "participants": ["hr_wang", "product_liu", "tech_li"],
    "description": "HR王芳推送高级产品经理候选人王强，产品总监刘总和技术总监李总一起评估",
    "messages": [
        {"time": NOW - timedelta(days=6, hours=4), "sender": "hr_wang", "content": "@刘总 你们部门那个高级产品的HC，我这边筛到一个不错的。北大MBA，之前在腾讯做企业SaaS，阿里做过商家后台，网易也待过。6年经验"},
        {"time": NOW - timedelta(days=6, hours=3, minutes=50), "sender": "hr_wang", "content": "[文件] 王强_高级产品经理_简历.pdf"},
        {"time": NOW - timedelta(days=6, hours=3, minutes=30), "sender": "product_liu", "content": "腾讯做企业SaaS的？这个吻合度很高啊，我们就是要做B端协同工具的产品"},
        {"time": NOW - timedelta(days=6, hours=3, minutes=15), "sender": "product_liu", "content": "刚仔细看了，阿里那段商家后台也很有价值，我们商户端的产品还在规划阶段，可以借鉴"},
        {"time": NOW - timedelta(days=6, hours=3), "sender": "tech_li", "content": "有技术背景吗？我们做SaaS产品需要跟技术团队深度配合，最好懂一些技术"},
        {"time": NOW - timedelta(days=6, hours=2, minutes=50), "sender": "hr_wang", "content": "他本科是信息管理，会SQL和数据分析，做过技术类产品。不算纯技术背景但沟通技术需求应该没问题"},
        {"time": NOW - timedelta(days=6, hours=2, minutes=30), "sender": "product_liu", "content": "有数据能力加分！转我一份详细简历，我先内部看看。期望薪资多少？"},
        {"time": NOW - timedelta(days=6, hours=2, minutes=20), "sender": "hr_wang", "content": "期望45-50K，做B端SaaS的PM都在这个价位。我们预算40-55K，够用"},
        {"time": NOW - timedelta(days=6, hours=2), "sender": "product_liu", "content": "那先约个初面吧，我和他聊聊SaaS产品的方法论。时间下周一或周二都行"},
        {"time": NOW - timedelta(days=5, hours=4), "sender": "hr_wang", "content": "好的，我约好了通知大家。王强下周一6月15日上午10点，线上"},
        {"time": NOW - timedelta(days=5, hours=3), "sender": "product_liu", "content": "收到，我准备几个B端产品设计的问题"},
    ],
    "candidate_id": 3,
    "job_id": 3,
    "expected_parsed": {
        "candidate_name": "王强",
        "position": "高级产品经理",
        "stage": "面试已安排",
        "interview_date": "2026-06-15",
        "interview_time": "10:00",
        "interviewer": "刘总（产品总监）",
        "salary_discussion": "期望45-50K，预算40-55K",
        "key_feedback": ["B端SaaS经验高度匹配", "阿里商家后台经验可借鉴", "有数据分析能力", "技术产品经验加分"],
    },
}

# --- 场景5：数据分析师赵丽（混合讨论+其他候选人闲聊）---
CHAT_SCENARIO_5 = {
    "group_name": "数据&技术招聘沟通群",
    "participants": ["hr_wang", "data_zhou", "hr_liu"],
    "description": "HR推数据分析师赵丽，对话中包含闲聊和无关信息，测试AI过滤能力",
    "messages": [
        {"time": NOW - timedelta(days=3, hours=6), "sender": "hr_wang", "content": "周工，你们数据组不是一直在招人吗？我这边筛了一个浙大统计的，之前在蚂蚁做风控数据分析"},
        {"time": NOW - timedelta(days=3, hours=5, minutes=55), "sender": "data_zhou", "content": "蚂蚁的？那风控经验应该不错。发我看看"},
        {"time": NOW - timedelta(days=3, hours=5, minutes=50), "sender": "hr_wang", "content": "[文件] 赵丽_数据分析师_简历.pdf"},
        {"time": NOW - timedelta(days=3, hours=5, minutes=30), "sender": "data_zhou", "content": "嗯，SQL和Python都会，Tableau也会用。不过我们主要用QuickBI，不知道她上手快不快"},
        {"time": NOW - timedelta(days=3, hours=5, minutes=20), "sender": "hr_liu", "content": "Tableau和QuickBI差不多吧，应该上手很快"},
        {"time": NOW - timedelta(days=3, hours=5, minutes=15), "sender": "hr_liu", "content": "对了，中午谁要点外卖？楼下新开了家川菜"},
        {"time": NOW - timedelta(days=3, hours=5, minutes=10), "sender": "data_zhou", "content": "哈哈我先不用，在减肥😅"},
        {"time": NOW - timedelta(days=3, hours=5), "sender": "hr_wang", "content": "歪楼了歪楼了 回到正题，赵丽你们觉得能面吗"},
        {"time": NOW - timedelta(days=3, hours=4, minutes=50), "sender": "data_zhou", "content": "可以，2年经验做初级到中级都可以。蚂蚁的背景应该数据分析基本功扎实。不过期望薪资18-22K稍微高了点，我们初级预算15-20K"},
        {"time": NOW - timedelta(days=3, hours=4, minutes=30), "sender": "hr_wang", "content": "那20K能接受吗？我可以谈"},
        {"time": NOW - timedelta(days=3, hours=4, minutes=20), "sender": "data_zhou", "content": "20K可以，但要看面试表现。如果确实优秀给22K也行，我跟老大争取一下"},
        {"time": NOW - timedelta(days=3, hours=4), "sender": "hr_wang", "content": "好的，那我去约面试。周工你下周什么时候有空？"},
        {"time": NOW - timedelta(days=3, hours=3, minutes=50), "sender": "data_zhou", "content": "下周三四下午吧"},
        {"time": NOW - timedelta(days=2, hours=6), "sender": "hr_wang", "content": "约好了，下周三6月17日下午2点半，线上"},
    ],
    "candidate_id": 4,
    "job_id": None,  # 数据岗，不在jobs表里，展示AI对非标准岗位的处理
    "expected_parsed": {
        "candidate_name": "赵丽",
        "position": "数据分析师",
        "stage": "面试已安排",
        "interview_date": "2026-06-17",
        "interview_time": "14:30",
        "interviewer": "周工",
        "salary_discussion": "期望18-22K，预算15-20K，20K可接受",
        "key_feedback": ["蚂蚁风控经验好", "基本功扎实", "初级预算可谈"],
        "has_irrelevant_info": True,  # 标记包含无关闲聊
    },
}

# --- 场景6：DevOps候选人陈伟 ---
CHAT_SCENARIO_6 = {
    "group_name": "技术部运维招聘群",
    "participants": ["hr_wang", "ops_sun", "tech_li"],
    "description": "HR推DevOps候选人陈伟，讨论中面试官信息不全，测试AI对不完整信息的处理",
    "messages": [
        {"time": NOW - timedelta(days=4, hours=8), "sender": "hr_wang", "content": "孙工，你们运维那个HC，有个华为的DevOps，电子科大的，之前在京东也做过。4年经验"},
        {"time": NOW - timedelta(days=4, hours=7, minutes=50), "sender": "hr_wang", "content": "[文件] 陈伟_DevOps工程师_简历.pdf"},
        {"time": NOW - timedelta(days=4, hours=7, minutes=30), "sender": "ops_sun", "content": "华为云服务的？那CI/CD应该搞得很熟了。有CKA证书是吧，我们正好缺K8s的人"},
        {"time": NOW - timedelta(days=4, hours=7, minutes=15), "sender": "tech_li", "content": "京东那段做自动化运维平台的？这个可以，我们运维自动化程度还不够，他能帮上忙"},
        {"time": NOW - timedelta(days=4, hours=7), "sender": "hr_wang", "content": "不过他跳槽稍微频繁了点，移动1年→京东3年半→华为1年多，最近两段都不到两年"},
        {"time": NOW - timedelta(days=4, hours=6, minutes=50), "sender": "ops_sun", "content": "移动是毕业后第一份工作，1年算正常。京东3年半够稳定。华为这段如果是被动离职也可以理解，毕竟今年华为那边变动挺大"},
        {"time": NOW - timedelta(days=4, hours=6, minutes=30), "sender": "tech_li", "content": "嗯，这个跳槽频率在互联网算中等吧，问题不大。先面一下看看"},
        {"time": NOW - timedelta(days=4, hours=6, minutes=15), "sender": "hr_wang", "content": "OK那我约面试。他期望30-35K"},
        {"time": NOW - timedelta(days=4, hours=6), "sender": "ops_sun", "content": "这个价位OK，我们预算35K以内都行。他什么时候能面？"},
        {"time": NOW - timedelta(days=4, hours=5, minutes=45), "sender": "hr_wang", "content": "我去跟他确认，好了同步群里"},
    ],
    "candidate_id": 5,
    "job_id": None,
    "expected_parsed": {
        "candidate_name": "陈伟",
        "position": "DevOps工程师",
        "stage": "简历评估通过，待约面试",
        "salary_discussion": "期望30-35K，预算35K以内",
        "key_feedback": ["华为CI/CD经验丰富", "有CKA证书", "自动化运维平台经验", "跳槽频率中等，可接受"],
        "concerns": ["跳槽略频繁"],
    },
}

# ============================================================
# 全部场景汇总
# ============================================================
ALL_SCENARIOS = [
    CHAT_SCENARIO_1,
    CHAT_SCENARIO_2,
    CHAT_SCENARIO_3,
    CHAT_SCENARIO_4,
    CHAT_SCENARIO_5,
    CHAT_SCENARIO_6,
]


def get_all_scenarios() -> List[Dict[str, Any]]:
    """获取所有群聊场景"""
    return ALL_SCENARIOS


def get_all_candidates() -> List[Dict[str, Any]]:
    """获取所有候选人简历数据"""
    return CANDIDATES


def get_all_jobs() -> List[Dict[str, Any]]:
    """获取所有招聘职位"""
    return JOBS


def get_members() -> Dict[str, Dict]:
    """获取成员信息"""
    return MEMBERS


def format_chat_for_display(scenario: Dict) -> str:
    """将场景消息格式化为可读的聊天记录文本（用于展示和AI解析）"""
    lines = []
    lines.append(f"群聊名称：{scenario['group_name']}")
    lines.append(f"场景说明：{scenario['description']}")
    lines.append(f"参与人：{', '.join(scenario['participants'])}")
    lines.append("-" * 50)

    for msg in scenario["messages"]:
        sender_info = MEMBERS.get(msg["sender"], {"name": msg["sender"]})
        sender_name = sender_info["name"]
        time_str = msg["time"].strftime("%m-%d %H:%M")
        lines.append(f"[{time_str}] {sender_name}: {msg['content']}")

    return "\n".join(lines)


def format_chat_for_ai(scenario: Dict) -> str:
    """
    格式化为AI解析用的聊天记录。
    返回一个结构化的文本，适合作为LLM的输入。
    """
    lines = []
    lines.append(f"【群聊名称】{scenario['group_name']}")
    lines.append(f"【场景说明】{scenario['description']}")
    lines.append("")

    for msg in scenario["messages"]:
        sender_info = MEMBERS.get(msg["sender"], {"name": msg["sender"], "role": "未知"})
        sender_name = sender_info["name"]
        sender_role = sender_info["role"]
        time_str = msg["time"].strftime("%Y-%m-%d %H:%M")
        lines.append(f"[{time_str}] {sender_name}({sender_role}): {msg['content']}")

    return "\n".join(lines)


# 当直接运行时，打印所有场景预览
if __name__ == "__main__":
    for i, scenario in enumerate(ALL_SCENARIOS, 1):
        print(f"\n{'='*60}")
        print(f"场景 {i}")
        print(f"{'='*60}")
        print(format_chat_for_display(scenario))
        print()
