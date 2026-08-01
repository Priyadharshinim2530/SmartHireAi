# ats.py
"""
Rule-based ATS (Applicant Tracking System) scoring engine.

Extracts skills/keywords from both the job post and the resume, then scores
overlap plus experience fit. Transparent and explainable — every point in
the score can be traced back to a specific match.
"""
import re
import json

STOPWORDS = {
    "the", "and", "a", "an", "to", "of", "in", "on", "for", "with", "is",
    "are", "as", "at", "by", "be", "this", "that", "will", "we", "you",
    "our", "your", "or", "from", "have", "has", "it", "their", "who",
    "job", "role", "work", "working", "team", "years", "year", "experience",
    "skills", "skill", "required", "requirements", "responsibilities",
    "about", "including", "etc", "using", "such", "into", "across", "per",
}

TOKEN_RE = re.compile(r"[A-Za-z][A-Za-z0-9+#./-]{1,}")


def tokenize(text):
    if not text:
        return []
    tokens = [t.lower().strip(".,-") for t in TOKEN_RE.findall(text)]
    return [t for t in tokens if t and t not in STOPWORDS and len(t) > 1]


def parse_skill_list(csv_text):
    if not csv_text:
        return []
    return [s.strip().lower() for s in csv_text.split(",") if s.strip()]


def score_resume(seeker, job):
    """
    Returns (score: float 0-100, breakdown: dict) comparing a Seeker's
    profile/resume against a Job posting.
    """
    required_skills = parse_skill_list(job.required_skills)
    seeker_skills = set(parse_skill_list(seeker.skills))
    resume_tokens = set(tokenize(seeker.resume_text or "") | set(tokenize(seeker.summary or "")))
    resume_pool = seeker_skills | resume_tokens

    # 1) Skill match (50 points)
    matched_skills = []
    missing_skills = []
    for skill in required_skills:
        skill_tokens = set(tokenize(skill)) or {skill}
        if skill in resume_pool or skill_tokens & resume_pool:
            matched_skills.append(skill)
        else:
            missing_skills.append(skill)

    skill_score = 0.0
    if required_skills:
        skill_score = (len(matched_skills) / len(required_skills)) * 50

    # 2) Keyword overlap with job description (30 points)
    jd_tokens = set(tokenize(job.description))
    overlap = jd_tokens & resume_pool
    keyword_score = 0.0
    if jd_tokens:
        keyword_score = min(len(overlap) / max(len(jd_tokens), 1), 1.0) * 30

    # 3) Experience fit (20 points)
    exp_score = 0.0
    min_exp = job.min_experience or 0
    seeker_exp = seeker.experience_years or 0
    if min_exp <= 0:
        exp_score = 20.0
    elif seeker_exp >= min_exp:
        exp_score = 20.0
    else:
        exp_score = max(0.0, (seeker_exp / min_exp)) * 20

    total = round(skill_score + keyword_score + exp_score, 1)
    total = max(0.0, min(100.0, total))

    breakdown = {
        "skill_score": round(skill_score, 1),
        "keyword_score": round(keyword_score, 1),
        "experience_score": round(exp_score, 1),
        "matched_skills": matched_skills,
        "missing_skills": missing_skills,
        "matched_keywords": sorted(list(overlap))[:20],
    }
    return total, breakdown


def breakdown_to_json(breakdown):
    return json.dumps(breakdown)


def breakdown_from_json(raw):
    try:
        return json.loads(raw) if raw else {}
    except (ValueError, TypeError):
        return {}