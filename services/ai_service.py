"""
AI enrichment service — algorithmic scoring, no external API needed.
Drop this file into services/ alongside linkedin_client.py
"""
from __future__ import annotations
import math
from typing import Any


def score_influence(profile: dict, followers: dict | None = None, posts: list | None = None, recs: list | None = None) -> dict:
    follower_count = (followers or {}).get("followersCount", 0) or 0
    connection_count = (followers or {}).get("connectionsCount", 500) or 500
    post_list = posts or []
    rec_list = recs or []

    s_followers = min(35, round(math.log10(follower_count + 1) * 10))
    s_connections = min(15, round((connection_count / 500) * 10))
    s_content = min(20, len(post_list) * 2)
    fields = ["headline", "summary", "profilePicture", "geo", "educations", "positions"]
    filled = sum(1 for f in fields if profile.get(f))
    s_completeness = round((filled / len(fields)) * 20)
    s_recs = min(10, len(rec_list) * 2)
    total = min(100, s_followers + s_connections + s_content + s_completeness + s_recs)
    tier_map = [(80, "elite"), (60, "top"), (40, "established"), (20, "rising"), (0, "micro")]
    tier = next(t for threshold, t in tier_map if total >= threshold)
    return {
        "score": total,
        "tier": tier,
        "breakdown": {
            "followers": s_followers,
            "connections": s_connections,
            "content": s_content,
            "completeness": s_completeness,
            "recommendations": s_recs,
        },
    }


def analyze_career_trajectory(positions: list[dict]) -> dict | None:
    if not positions:
        return None
    current_year = 2026
    sorted_pos = sorted(positions, key=lambda p: p.get("start", {}).get("year", 0))
    durations = []
    for p in sorted_pos:
        start = p.get("start", {}).get("year", current_year)
        end = p.get("end", {}).get("year") or current_year
        durations.append(max(0, end - start))
    avg_duration = round(sum(durations) / len(durations)) if durations else 2
    current = sorted_pos[-1]
    current_start = current.get("start", {}).get("year", current_year)
    current_duration = current_year - current_start
    seniority = [
        ("intern", 0), ("junior", 1), ("associate", 2), ("senior", 3),
        ("lead", 4), ("principal", 5), ("director", 6), ("vp", 7),
        ("cto", 8), ("ceo", 9), ("founder", 9),
    ]
    def level(title):
        t = (title or "").lower()
        for kw, lvl in seniority:
            if kw in t:
                return lvl
        return 2
    levels = [level(p.get("title", "")) for p in sorted_pos]
    is_upward = len(levels) > 1 and levels[-1] > levels[0]
    return {
        "avgTenureYears": avg_duration,
        "currentRoleDurationYears": current_duration,
        "totalRoles": len(sorted_pos),
        "careerProgression": "upward" if is_upward else "lateral",
        "likelyNextMove": "open_to_move" if current_duration >= avg_duration else "stable",
        "estimatedNextMoveIn": f"{max(0, avg_duration - current_duration)} years",
        "currentTitle": current.get("title"),
        "currentCompany": current.get("companyName"),
    }


POSITIVE = {"excited","thrilled","proud","amazing","great","love","fantastic","excellent",
            "congratulations","achieved","grateful","honored","delighted","happy","wonderful",
            "incredible","milestone","promoted","launched","thriving"}
NEGATIVE = {"disappointed","frustrated","difficult","challenging","failed","unfortunately",
            "struggle","hard","problem","issue","bad","terrible","wrong","regret",
            "layoff","cut","decline","warning"}


def analyze_sentiment(texts: list[str]) -> dict:
    if not texts:
        return {"overall": "neutral", "score": 0.0, "confidence": 0.0, "breakdown": []}
    results = []
    total = 0.0
    for text in texts:
        words = set(text.lower().split())
        pos = len(words & POSITIVE)
        neg = len(words & NEGATIVE)
        score = float(pos - neg)
        total += score
        results.append({
            "excerpt": text[:120] + ("..." if len(text) > 120 else ""),
            "score": score,
            "sentiment": "positive" if score > 0 else ("negative" if score < 0 else "neutral"),
        })
    avg = total / len(texts)
    return {
        "overall": "positive" if avg > 0.3 else ("negative" if avg < -0.3 else "neutral"),
        "score": round(avg, 2),
        "confidence": round(min(1.0, len(texts) / 10), 2),
        "postsAnalyzed": len(texts),
        "breakdown": results,
    }


def compute_proximity(profile_a: dict, profile_b: dict) -> dict:
    score = 0
    reasons: list[str] = []
    ia = (profile_a.get("industryName") or "").lower()
    ib = (profile_b.get("industryName") or "").lower()
    if ia and ib and ia == ib:
        score += 30
        reasons.append(f"Same industry: {ia}")
    la = (profile_a.get("geoLocationName") or "").lower()
    lb = (profile_b.get("geoLocationName") or "").lower()
    if la and lb and la == lb:
        score += 20
        reasons.append(f"Same location: {la}")
    a_words = {w for w in (profile_a.get("headline") or "").lower().split() if len(w) > 3}
    b_words = {w for w in (profile_b.get("headline") or "").lower().split() if len(w) > 3}
    shared_kw = a_words & b_words
    if shared_kw:
        pts = min(30, len(shared_kw) * 10)
        score += pts
        reasons.append(f"Shared keywords: {', '.join(list(shared_kw)[:3])}")
    a_edu = {(e.get("schoolName") or "").lower() for e in (profile_a.get("educations") or [])}
    b_edu = {(e.get("schoolName") or "").lower() for e in (profile_b.get("educations") or [])}
    shared_edu = (a_edu & b_edu) - {""}
    if shared_edu:
        score += 20
        reasons.append(f"Shared school: {list(shared_edu)[0]}")
    score = min(100, score)
    return {
        "proximityScore": score,
        "reasons": reasons,
        "recommendation": "Strong match" if score >= 60 else ("Moderate match" if score >= 30 else "Weak match"),
    }


LEVEL_KEYWORDS = [
    ("ceo", "executive"), ("cto", "executive"), ("cfo", "executive"),
    ("coo", "executive"), ("chief", "executive"), ("founder", "executive"), ("president", "executive"),
    ("vp", "vp"), ("vice president", "vp"), ("svp", "vp"), ("evp", "vp"),
    ("director", "director"), ("head of", "director"),
    ("manager", "manager"), ("lead", "manager"), ("principal", "manager"),
]

def classify_level(title: str) -> str:
    t = (title or "").lower()
    for kw, level in LEVEL_KEYWORDS:
        if kw in t:
            return level
    return "ic"

def build_org_chart(people: list[dict]) -> dict:
    chart: dict[str, list] = {"executive": [], "vp": [], "director": [], "manager": [], "ic": []}
    for p in people:
        title = p.get("title") or p.get("headline") or ""
        level = classify_level(title)
        chart[level].append({
            "name": (p.get("fullName") or f"{p.get('firstName','')} {p.get('lastName','')}").strip(),
            "title": title,
            "linkedinUrl": p.get("profileURL") or p.get("url") or "",
        })
    return chart
