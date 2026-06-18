from typing import Any


def best_image(images: list[dict] | None) -> str | None:
    if not images:
        return None
    return max(images, key=lambda i: i.get("width", 0)).get("url")


def normalize_company(raw: dict[str, Any]) -> dict[str, Any]:
    data = raw.get("data", raw)
    hq = data.get("headquarter") or {}
    locations = data.get("locations", [])
    return {
        **data,
        "_enriched": {
            "best_logo": best_image(data.get("logos")),
            "best_cover": best_image(data.get("backgroundCoverImages")),
            "hq_full_address": ", ".join(
                filter(None, [hq.get("line1"), hq.get("city"), hq.get("geographicArea"), hq.get("country")])
            ),
            "office_count": len(locations),
            "countries": sorted({l.get("country") for l in locations if l.get("country")}),
            "is_funded": bool((data.get("fundingData") or {}).get("numFundingRounds")),
            "size_bucket": data.get("staffCountRange"),
            "followers_per_employee": round(
                data.get("followerCount", 0) / data["staffCount"], 1
            ) if data.get("staffCount") else None,
            "founded_year": data.get("founded"),
            "industry": data.get("industries", [None])[0] if data.get("industries") else None,
        },
    }


def normalize_profile(raw: dict[str, Any]) -> dict[str, Any]:
    data = raw.get("data", raw)
    positions = data.get("position") or data.get("fullPositions") or []
    return {
        **data,
        "_enriched": {
            "full_name": " ".join(filter(None, [data.get("firstName"), data.get("lastName")])),
            "current_title": (positions[0].get("title") if positions else None),
            "current_company": (positions[0].get("companyName") if positions else None),
            "position_count": len(positions),
            "has_premium": bool(data.get("isPremium")),
            "profile_pic": data.get("profilePicture"),
            "headline": data.get("headline"),
            "followers": data.get("followerCount", 0),
            "connections": data.get("connectionCount", 0),
        },
    }


def normalize_job(raw: dict[str, Any]) -> dict[str, Any]:
    data = raw.get("data", raw)
    return {
        **data,
        "_enriched": {
            "job_title": data.get("title"),
            "company_name": data.get("company", {}).get("name") if isinstance(data.get("company"), dict) else None,
            "location_country": data.get("location", {}).get("country") if isinstance(data.get("location"), dict) else None,
            "posted_date": data.get("posted"),
            "job_type": data.get("jobType"),
        },
    }


def normalize_post(raw: dict[str, Any]) -> dict[str, Any]:
    data = raw.get("data", raw)
    return {
        **data,
        "_enriched": {
            "engagement": (data.get("likes", 0) or 0) + (data.get("comments", 0) or 0) + (data.get("reposts", 0) or 0),
            "engagement_ratio": round(
                ((data.get("likes", 0) or 0) + (data.get("comments", 0) or 0)) / data.get("impressions", 1), 4
            ) if data.get("impressions") else None,
            "is_video": data.get("media", {}).get("type") == "VIDEO" if isinstance(data.get("media"), dict) else False,
        },
    }


def normalize_article(raw: dict[str, Any]) -> dict[str, Any]:
    data = raw.get("data", raw)
    return {
        **data,
        "_enriched": {
            "title": data.get("title"),
            "published_date": data.get("publishedDate"),
            "views": data.get("views"),
            "comments_count": len(data.get("comments", [])),
        },
    }
