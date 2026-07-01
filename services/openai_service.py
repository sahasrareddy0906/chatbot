import os
import re
import json
import random

from openai import OpenAI
from dotenv import load_dotenv

from services.question_service import (
    insert_questions,
    count_questions
)

load_dotenv()

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)


DIFFICULTY_MAP = {
    "0-2": {
        "label": "beginner",
        "description":
            "Basic syntax, definitions, simple concepts.",
        "question_style":
            "Simple real-world tasks and basic terminology.",
        "example_depth":
            "Shallow, single-step scenarios.",
        "avoid":
            "Avoid architectural design and ambiguous business decisions."
    },

    "2-5": {
        "label": "intermediate",
        "description":
            "Practical application and moderate problem solving.",
        "question_style":
            "Practical scenario-based problems that require reasoning.",
        "example_depth":
            "Moderate complexity with workplace context.",
        "avoid":
            "Avoid basic recall questions and overly theoretical prompts."
    },

    "5+": {
        "label": "advanced",
        "description":
            "Deep concepts, architecture, scalability and performance.",
        "question_style":
            "Strategic, system-level decision making with tradeoffs.",
        "example_depth":
            "Complex scenarios with constraints and senior judgment.",
        "avoid":
            "Avoid trivial definitions and narrow syntax questions."
    }
}


SEGMENT_MAP = {
    "technical":
        "Technical coding and implementation knowledge.",

    "analytical":
        "Logical reasoning and analytical thinking.",

    "domain":
        "Industry-specific domain knowledge.",

    "management":
        "Leadership and management scenarios."
}


SEGMENT_INSTRUCTIONS = {
    "technical": {
        "description": "Technical coding and implementation knowledge.",
        "focus": (
            "Focus on practical coding and system design challenges with role-relevant implementation detail."
        ),
        "format": (
            "Clear technical questions with exactly four options and one correct answer."
        ),
        "indian_context": (
            "When relevant, use Indian examples or references from the local tech ecosystem."
        ),
        "examples": {
            "2-5": (
                "A developer needs to optimize a database query for a React+Node application. "
                "Which indexing strategy is most likely to improve response time without increasing write latency?"
            ),
            "5+": (
                "Design a fault-tolerant microservice architecture for an e-commerce checkout flow "
                "that must handle 10,000 concurrent users during a sale event. What is the best first step?"
            )
        }
    },
    "analytical": {
        "description": "Logical reasoning and analytical thinking.",
        "focus": (
            "Evaluate candidate ability to interpret data, identify patterns, and reason through problems."
        ),
        "format": (
            "Questions should present an analytical challenge with one best answer and plausible distractors."
        ),
        "indian_context": (
            "Use Indian business scenarios or numeric examples where they fit naturally."
        ),
        "examples": {
            "2-5": (
                "A report shows decreasing customer retention over three quarters. "
                "Which data point would you investigate first to diagnose the issue?"
            ),
            "5+": (
                "Your team must decide between two competing forecasts for next quarter revenue. "
                "What is the most important factor to validate before choosing a plan?"
            )
        }
    },
    "domain": {
        "description": (
            "Industry and domain-specific knowledge relevant to the role. "
            "Tests whether the candidate understands how their tools "
            "and skills are used in real business contexts — not just "
            "whether they know the tools themselves."
        ),

        "focus": (
            "Place candidates in realistic workplace scenarios. "
            "Test business judgment, domain terminology, industry "
            "workflows, and how technical skills apply in real contexts. "
            "Questions should feel like situations the candidate "
            "would actually face on the job."
        ),

        "format": (
            "Scenario-based questions describing a real business situation. "
            "Options should reflect different professional approaches — "
            "not just factual recall. At least 2 of the 4 options should "
            "be plausible to someone with partial knowledge."
        ),

        "indian_context": (
            "Use Indian business context where relevant: "
            "reference Indian regulatory frameworks (GST, Companies Act), "
            "Indian tech industry norms, INR for currency, "
            "crore/lakh for numbers, Indian company examples "
            "(Infosys, TCS, Flipkart, Razorpay, Zomato) where natural."
        ),

        "critical_rules": (
            "IMPORTANT DOMAIN RULES:\n"
            "1. Every question MUST begin with a realistic business scenario.\n"
            "2. Do NOT ask definitions.\n"
            "3. Do NOT ask 'What is...', 'Which command...', 'Define...', or 'Explain...'.\n"
            "4. The candidate must be placed in a workplace situation.\n"
            "5. The question must test judgment and decision-making.\n"
            "6. The scenario should involve: customers, stakeholders, production systems, "
            "business metrics, compliance, scalability, reliability, costs where relevant.\n"
            "7. The correct answer should represent the best professional decision.\n"
            "8. At least 2 wrong options must sound plausible.\n"
            "\n"
            "CONSTRAINT:\n"
            "- 80% of questions must be scenario-based.\n"
            "- Maximum 20% may be conceptual.\n"
            "- Never generate pure definition questions.\n"
            "\n"
            "GENERATION TRICK:\n"
            "Before generating each question, think about a real incident that could happen "
            "in a company (payment failures, data mismatches, API migrations, compliance audits, "
            "customer complaints, production outages). Convert that incident into an MCQ. "
            "This dramatically improves quality."
        ),

        "examples": {
            "2-5": (
                "A client's monthly MIS report shows total sales of "
                "₹2.4 crore but the finance team's tally shows ₹2.1 crore. "
                "Both systems ran their processes without errors. "
                "As the data analyst, what is your first step?"
            ),

            "5+": (
                "Your company is migrating from a monolithic ERP to "
                "microservices. The finance module processes 50,000 "
                "transactions daily and cannot have downtime. "
                "The CTO wants migration done in 3 months. "
                "What is the biggest risk and how do you mitigate it?"
            ),

            "bad_example": (
                "BAD: 'What is API versioning?' — This is definitional, not scenario-based."
            ),

            "good_example": (
                "GOOD: 'A fintech company processes 20,000 transactions daily. "
                "A new RBI compliance requirement requires customer consent tracking, "
                "but 30 partner banks still use the older API version. "
                "What should the engineering team do first?' — This is scenario-based "
                "with business context and judgment required."
            )
        }
    },
    "management": {
        "description": "Leadership and management scenarios.",
        "focus": (
            "Assess team leadership, stakeholder communication, and project decision-making."
        ),
        "format": (
            "Situational questions with role-based choices reflecting real management tradeoffs."
        ),
        "indian_context": (
            "Use Indian organizational examples or stakeholder settings when appropriate."
        ),
        "examples": {
            "2-5": (
                "A project is falling behind schedule due to unclear requirements. "
                "What should the team lead do first?"
            ),
            "5+": (
                "Senior stakeholders disagree on product scope for a key client. "
                "How do you align the team while preserving delivery timelines?"
            )
        }
    }
}


ROLE_DOMAIN_TOPICS = {
    "Backend Engineer": {
        "topics": [
            "API versioning strategies in production",
            "Database transaction management",
            "Microservices communication patterns",
            "Service level agreements and uptime",
            "Security vulnerabilities in web applications",
            "Rate limiting and API abuse prevention"
        ],
        "industry_context": (
            "B2B SaaS, fintech, or e-commerce backend systems "
            "in the Indian market"
        )
    },
    "Frontend Engineer": {
        "topics": [
            "Web performance and Core Web Vitals",
            "Cross-browser compatibility issues",
            "Accessibility standards for Indian government portals",
            "Mobile-first design for Indian user base",
            "Progressive Web Apps in low-bandwidth scenarios"
        ],
        "industry_context": (
            "Consumer-facing web products with diverse Indian "
            "user demographics and varying internet speeds"
        )
    },
    "Full Stack Engineer": {
        "topics": [
            "End-to-end feature delivery ownership",
            "API contract design between frontend and backend",
            "Deployment strategies and rollback",
            "Technical debt management",
            "Cross-functional team collaboration"
        ],
        "industry_context": (
            "Product startups and mid-sized tech companies "
            "building full-stack web applications in India"
        )
    },
    "Data Engineer": {
        "topics": [
            "Data pipeline reliability and SLAs",
            "Data quality monitoring and alerting",
            "Cost optimisation on cloud data platforms",
            "GDPR and data privacy in Indian context (DPDP Act)",
            "Stakeholder reporting and data literacy",
            "ETL vs ELT architectural decisions"
        ],
        "industry_context": (
            "Indian enterprises with large data volumes: "
            "banking, retail, telecom, e-commerce"
        )
    },
    "Data Scientist": {
        "topics": [
            "Model deployment and monitoring in production",
            "Communicating model results to non-technical stakeholders",
            "Bias and fairness in ML models for Indian demographics",
            "Business impact measurement of ML initiatives",
            "Feature store design and management",
            "A/B testing methodology"
        ],
        "industry_context": (
            "Indian fintech, healthtech, and e-commerce companies "
            "deploying ML at scale"
        )
    },
    "DevOps Engineer": {
        "topics": [
            "Incident response and postmortem culture",
            "Cloud cost optimisation on AWS/GCP",
            "Compliance requirements for Indian financial services",
            "On-call rotation and escalation policies",
            "Disaster recovery planning",
            "Multi-region deployment for Indian and global users"
        ],
        "industry_context": (
            "Indian tech companies with cloud infrastructure "
            "serving both domestic and global customers"
        )
    },
    "Database Administrator": {
        "topics": [
            "Database performance degradation root cause analysis",
            "Backup and recovery SLAs for Indian banking regulations",
            "Data archival and retention policies",
            "Database security and audit logging",
            "Capacity planning for growing Indian startups",
            "Zero-downtime migration strategies"
        ],
        "industry_context": (
            "Indian BFSI sector and large enterprise database "
            "management with RBI compliance requirements"
        )
    },
    "QA Engineer": {
        "topics": [
            "Test coverage strategy for release decisions",
            "Bug triage and priority classification",
            "Quality gates in CI/CD pipelines",
            "Testing strategy for payment gateways in India",
            "Regression testing for frequent releases",
            "Performance testing benchmarks"
        ],
        "industry_context": (
            "Indian product companies with frequent release "
            "cycles and regulatory compliance needs"
        )
    },
    "Business Analyst": {
        "topics": [
            "Stakeholder conflict resolution in requirement gathering",
            "Change management during digital transformation",
            "ROI calculation for IT projects in Indian enterprises",
            "Agile vs waterfall for Indian government projects",
            "Process mining and inefficiency identification",
            "Business case preparation for Indian management"
        ],
        "industry_context": (
            "Indian IT services, banking, and enterprise "
            "digital transformation projects"
        )
    },
    "HR Technology Specialist": {
        "topics": [
            "HRMS implementation challenges in Indian companies",
            "Labour law compliance in Indian payroll systems",
            "Employee data privacy under DPDP Act",
            "HR analytics for attrition prediction",
            "ATS integration with Indian job boards",
            "Digital onboarding for distributed Indian workforce"
        ],
        "industry_context": (
            "Indian enterprises managing large workforces "
            "with statutory compliance requirements"
        )
    }
}

MANAGEMENT_SCENARIOS = {
    "Backend Engineer": [
        "technical debt vs feature delivery trade-offs",
        "onboarding a new junior engineer while under deadline",
        "handling production incidents and postmortem culture",
        "pushing back on unrealistic timelines from product managers",
        "managing knowledge silos when a key engineer leaves",
        "code review culture and quality standards enforcement",
        "cross-team API contract negotiation",
        "balancing refactoring with new feature development"
    ],

    "Frontend Engineer": [
        "design vs engineering trade-offs",
        "browser compatibility decisions",
        "performance vs feature delivery",
        "accessibility vs deadline pressure",
        "stakeholder management",
        "scope creep handling",
        "UI review cycles"
    ],

    "Full Stack Engineer": [
        "owning end-to-end feature delivery",
        "deployment risk management",
        "startup technical debt prioritisation",
        "handling production issues",
        "communicating technical constraints",
        "cross-functional collaboration"
    ],

    "Data Engineer": [
        "pipeline failure communication",
        "data quality incidents",
        "reliability vs velocity",
        "data ownership disputes",
        "business stakeholder communication"
    ],

    "Data Scientist": [
        "model limitations communication",
        "ethical AI concerns",
        "business expectation management",
        "model deployment alignment",
        "stakeholder prioritisation"
    ],

    "DevOps Engineer": [
        "incident response leadership",
        "unsafe deployment requests",
        "on-call burnout",
        "cloud cost communication",
        "SLA breach management"
    ],

    "Database Administrator": [
        "downtime communication",
        "data access control decisions",
        "migration risk communication",
        "backup failure handling",
        "data loss response"
    ],

    "QA Engineer": [
        "go-live decisions with critical bugs",
        "testing under deadlines",
        "quality communication",
        "automation adoption",
        "regression risk management"
    ],

    "Business Analyst": [
        "conflicting stakeholder requirements",
        "scope creep",
        "client expectation management",
        "business vs technical conflicts",
        "change management"
    ],

    "HR Technology Specialist": [
        "HRMS adoption resistance",
        "payroll failures",
        "HR data privacy communication",
        "vendor management",
        "HR technology roadmap decisions"
    ]
}


def strip_markdown(text):
    if not isinstance(text, str):
        return text

    cleaned = re.sub(r"```(?:json)?", "", text, flags=re.IGNORECASE)
    cleaned = re.sub(r"`", "", cleaned)
    return cleaned.strip()


def shuffle_options(question: dict) -> dict:
    """
    Shuffle options A-D randomly and update correct_answer accordingly.
    """
    options = [
        ('A', question.get('option_a', '')),
        ('B', question.get('option_b', '')),
        ('C', question.get('option_c', '')),
        ('D', question.get('option_d', ''))
    ]

    original_correct = question.get('correct_answer', 'A')

    # Shuffle the options randomly
    random.shuffle(options)

    # Build shuffled question
    shuffled = {
        'question_text': question['question_text'],
        'option_a': options[0][1],
        'option_b': options[1][1],
        'option_c': options[2][1],
        'option_d': options[3][1],
    }

    # Find where the originally correct option ended up
    for new_pos, (old_letter, option_text) in enumerate(options):
        if old_letter == original_correct:
            shuffled['correct_answer'] = chr(ord('A') + new_pos)
            break

    return shuffled


def build_management_prompt(role: str, count: int) -> str:
    scenarios = MANAGEMENT_SCENARIOS.get(role, [])
    scenario_list = "\n".join(f"- {scenario}" for scenario in scenarios)

    prompt = f"""
You are an expert exam writer creating senior management questions for the Indian tech industry.

Generate exactly {count} questions.
Questions are for candidates with 5+ years of experience.
Every question must be scenario based and at least two sentences long.
Use realistic Indian tech workplace situations and draw from the following role-specific scenarios:
{scenario_list}
All four options must be plausible.
One option should be clearly the best answer.
Do not include obviously stupid options.
Return JSON only.
No markdown, no explanation, no text outside the JSON array.

Return format:
[
  {{
    "question_text": "...",
    "option_a": "...",
    "option_b": "...",
    "option_c": "...",
    "option_d": "...",
    "correct_answer": "A"
  }}
]
"""

    return prompt.strip()


def generate_management_questions(role: str, count: int = 10) -> list:
    prompt = build_management_prompt(role, count)

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You are a strict JSON-only generator."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.8,
            max_tokens=4000
        )

        raw = response.choices[0].message.content.strip()
        raw = strip_markdown(raw)

        try:
            questions = json.loads(raw)
        except json.JSONDecodeError:
            # Try to recover from fenced code block wrappers
            raw = re.sub(r"^```(?:json)?\s*", "", raw, flags=re.IGNORECASE)
            raw = re.sub(r"\s*```$", "", raw, flags=re.IGNORECASE)
            questions = json.loads(raw)

        valid_questions = []

        for q in questions:
            if not isinstance(q, dict):
                continue

            question_text = strip_markdown(q.get("question_text", "")).strip()
            option_a = strip_markdown(q.get("option_a", "")).strip()
            option_b = strip_markdown(q.get("option_b", "")).strip()
            option_c = strip_markdown(q.get("option_c", "")).strip()
            option_d = strip_markdown(q.get("option_d", "")).strip()
            correct_answer = str(q.get("correct_answer", "")).strip().upper()

            if not question_text or len(question_text) <= 80:
                continue

            if correct_answer not in {"A", "B", "C", "D"}:
                continue

            if not all([option_a, option_b, option_c, option_d]):
                continue

            valid_questions.append({
                "question_text": question_text,
                "option_a": option_a,
                "option_b": option_b,
                "option_c": option_c,
                "option_d": option_d,
                "correct_answer": correct_answer
            })

        # Shuffle options for randomization
        shuffled_questions = [shuffle_options(q) for q in valid_questions]
        return shuffled_questions
    except Exception as e:
        print(f"OpenAI error: {e}")
        return []

MIN_QUESTIONS_PER_COMBO = 30


def build_prompt(
    role,
    segment,
    experience_band,
    count,
    topic=None
):

    difficulty = DIFFICULTY_MAP.get(
        experience_band,
        DIFFICULTY_MAP["0-2"]
    )

    seg_info = SEGMENT_INSTRUCTIONS.get(segment, {})
    role_info = ROLE_DOMAIN_TOPICS.get(role, {})
    topic_name = topic if topic else role

    example = seg_info.get("examples", {}).get(experience_band, "")
    example_str = (
        f"\nExample question at this level:\n\"{example}\""
        if example else ""
    )

    role_str = ""
    if segment == "domain" and role_info:
        topics = role_info.get("topics", [])
        industry_context = role_info.get("industry_context", "")

        if topics:
            topics_list = "\n".join(f"  - {topic}" for topic in topics)
            role_str += f"DOMAIN TOPICS TO DRAW FROM:\n{topics_list}\n"

        if industry_context:
            role_str += f"\nINDUSTRY CONTEXT: {industry_context}\n"

    domain_str = ""
    if segment == "domain":
        critical_rules = seg_info.get('critical_rules', '')
        domain_str = (
            f"\n{seg_info.get('indian_context', '')}\n"
            f"\n{critical_rules}"
        )

    prompt = f"""
You are an expert technical recruiter generating exam questions
for the Indian job market.

EXAM CONFIGURATION:
- Role: {role}
- Topic: {topic_name}
- Segment: {segment}
- Experience Band: {experience_band}
- Number of Questions: {count}

DIFFICULTY LEVEL: {difficulty['label'].upper()}
{difficulty['description']}
Style: {difficulty['question_style']}
Depth: {difficulty['example_depth']}
Avoid: {difficulty['avoid']}

SEGMENT REQUIREMENTS:
{seg_info.get('description', '')}
Focus: {seg_info.get('focus', '')}
Format: {seg_info.get('format', '')}
{example_str}
{role_str}{domain_str}

STRICT RULES:
1. Generate exactly {count} questions
2. Every question must have exactly 4 options: A, B, C, D
3. correct_answer must be exactly "A", "B", "C", or "D"
4. All 4 options must be plausible — no obviously wrong answers
5. Questions must be unique — no repetition
6. Difficulty must precisely match {difficulty['label']} level
7. Use Indian workplace context where relevant
8. Return ONLY a valid JSON array — no explanation,
   no markdown, no extra text

RETURN FORMAT:
[
  {{
    "question_text": "...",
    "option_a": "...",
    "option_b": "...",
    "option_c": "...",
    "option_d": "...",
    "correct_answer": "A"
  }}
]
"""

    return prompt.strip()


def generate_questions(
    role,
    segment,
    experience_band,
    count=10,
    topic=None
):

    prompt = build_prompt(
        role,
        segment,
        experience_band,
        count,
        topic=topic
    )

    try:

        response = client.chat.completions.create(
            model="gpt-4o-mini",

            messages=[
                {
                    "role": "system",
                    "content":
                        "You are a strict JSON-only generator."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],

            temperature=0.7,
            max_tokens=3000
        )

        raw = response.choices[0].message.content.strip()

        if raw.startswith("```"):

            raw = raw.split("```")[1]

            if raw.startswith("json"):
                raw = raw[4:]

        raw = raw.strip()

        questions = json.loads(raw)

        for q in questions:

            required = [
                "question_text",
                "option_a",
                "option_b",
                "option_c",
                "option_d",
                "correct_answer"
            ]

            for field in required:

                if field not in q:
                    raise ValueError(
                        f"Missing field: {field}"
                    )

        # Shuffle options for randomization
        questions = [shuffle_options(q) for q in questions]

        return questions

    except json.JSONDecodeError as e:

        print(f"JSON parse error: {e}")

        return []

    except Exception as e:

        print(f"OpenAI error: {e}")

        return []


def generate_and_store_questions(
    role,
    segment,
    experience_band,
    count=10,
    skill=None
):

    prompt_topic = skill if skill else role

    existing = count_questions(
        role,
        segment,
        experience_band
    )

    if existing >= MIN_QUESTIONS_PER_COMBO:

        return {
            "status": "skipped",
            "existing_count": existing,
            "new_count": 0
        }

    if segment == "management":
        questions = generate_management_questions(
            role=role,
            count=count
        )
    else:
        questions = generate_questions(
            role,
            segment,
            experience_band,
            count,
            topic=prompt_topic
        )

    if not questions:

        return {
            "status": "failed"
        }

    stored = insert_questions(
        questions,
        role,
        segment,
        experience_band
    )

    return {
        "status": "success",
        "existing_count": existing,
        "new_count": len(stored),
        "total_count": existing + len(stored)
    }

def build_resume_extraction_prompt(resume_text: str) -> str:
    """
    Builds the prompt for OpenAI to extract structured data
    from raw resume text.
    """
    # Truncate very long resumes to control token cost
    # 6000 chars is roughly 1500 tokens — enough for most resumes
    truncated_text = resume_text[:6000]

    prompt = f"""
You are an expert resume parser for technical recruitment
in the Indian job market.

Extract structured information from the resume text below.
Be precise and only extract what is explicitly stated or
strongly implied — do not invent information.

RESUME TEXT:
\"\"\"
{truncated_text}
\"\"\"

EXTRACTION RULES:
1. List ALL technical skills mentioned — programming languages,
   frameworks, tools, databases, cloud platforms
2. Estimate total years of professional experience based on
   work history dates. If unclear, estimate conservatively.
3. List soft skills only if explicitly mentioned
   (e.g. "led a team of 5", "managed stakeholder communication")
4. Extract education — degree, institution, year if available
5. Extract company names and job titles from work history
6. Identify the candidate's apparent seniority level based on
   role titles and years of experience
7. Note any certifications mentioned
8. Do NOT include personal contact information
   (phone, address, email) in the output

Return ONLY valid JSON. No markdown. No explanation.

FORMAT:
{{
  "technical_skills": ["Python", "React", "PostgreSQL", ...],
  "soft_skills": ["Team Leadership", "Stakeholder Management", ...],
  "years_of_experience": 3.5,
  "seniority_level": "junior",
  "education": [
    {{
      "degree": "B.Tech Computer Science",
      "institution": "...",
      "year": "2021"
    }}
  ],
  "work_history": [
    {{
      "company": "...",
      "title": "...",
      "duration": "Jan 2021 - Present",
      "key_responsibilities": "Brief one-line summary"
    }}
  ],
  "certifications": ["AWS Certified Developer", ...],
  "summary": "2-3 sentence professional summary based on the resume"
}}
"""
    return prompt.strip()


def extract_resume_data(resume_text: str) -> dict | None:
    """
    Call OpenAI to extract structured data from resume text.
    """
    prompt = build_resume_extraction_prompt(resume_text)

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a precise resume parsing assistant. "
                        "Extract only factual information from the "
                        "resume text. Never invent skills or "
                        "experience not present in the text. "
                        "Return ONLY valid JSON, no other text."
                    )
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.3,
            # Low temperature — this is extraction, not creative generation
            # We want consistent, factual output not variety
            max_tokens=2000
        )

        raw = response.choices[0].message.content.strip()

        # Safety clean
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        raw = raw.strip()

        data = json.loads(raw)

        # Validate required fields exist
        required = [
            "technical_skills", "years_of_experience",
            "seniority_level", "summary"
        ]
        for field in required:
            if field not in data:
                data[field] = None if field != "technical_skills" else []

        return data

    except json.JSONDecodeError as e:
        print(f"Resume extraction JSON parse error: {e}")
        print(f"Raw: {raw[:300]}")
        return None
    except Exception as e:
        print(f"Resume extraction error: {e}")
        return None