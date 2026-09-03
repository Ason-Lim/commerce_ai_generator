import os
import requests
import json
from sqlalchemy import text
from app.db.engine_provider import get_engine
from datetime import date, timedelta
from dotenv import load_dotenv

load_dotenv()

def normalize_datalab_keywords(keywords):
    """
    네이버 DataLab API에 전달할 검색어 목록을 안전하게 정리합니다.

    None, 빈 문자열, 'null', 'none' 같은 잘못된 값은 제거하고
    중복 검색어도 제거합니다.
    """
    if keywords is None:
        return []

    if isinstance(keywords, str):
        keywords = [keywords]

    normalized = []
    seen = set()

    for keyword in keywords:
        if keyword is None:
            continue

        value = str(keyword).strip()

        if not value:
            continue

        if value.lower() in {
            "none",
            "null",
            "undefined",
        }:
            continue

        if value in seen:
            continue

        seen.add(value)
        normalized.append(value)

    return normalized

def get_naver_datalab_credentials():
    return (
        os.getenv("NAVER_CLIENT_ID"),
        os.getenv("NAVER_CLIENT_SECRET"),
    )


def call_naver_datalab_search_trend(
    keywords,
    start_date=None,
    end_date=None,
    time_unit="date",
):
    """
    네이버 DataLab 검색어 트렌드 API 호출.
    keywords: ["사과", "고당도 사과"] 형태
    """

    keywords = normalize_datalab_keywords(
        keywords
    )

    if not keywords:
        return {
            "startDate": "",
            "endDate": "",
            "timeUnit": time_unit,
            "results": [],
            "skipped": True,
            "reason": "empty_keywords",
        }

    if end_date is None:
        end_date = date.today()

    if start_date is None:
        start_date = end_date - timedelta(days=30)

    start_date = str(start_date)
    end_date = str(end_date)

    client_id, client_secret = get_naver_datalab_credentials()

    url = "https://openapi.naver.com/v1/datalab/search"

    headers = {
        "X-Naver-Client-Id": client_id,
        "X-Naver-Client-Secret": client_secret,
        "Content-Type": "application/json",
    }

    if not all(
        isinstance(keyword, str)
        and keyword.strip()
        for keyword in keywords
    ):
        raise ValueError(
            f"유효하지 않은 DataLab 검색어: {keywords!r}"
        )

    body = {
        "startDate": start_date,
        "endDate": end_date,
        "timeUnit": time_unit,
        "keywordGroups": [
            {
                "groupName": keyword,
                "keywords": [keyword],
            }
            for keyword in keywords
        ],
    }

    response = requests.post(
        url,
        headers=headers,
        json=body,
        timeout=10,
    )

    if response.status_code != 200:
        raise Exception(
            f"네이버 DataLab API 오류: {response.status_code} / {response.text}"
        )

    return response.json()


def summarize_search_trend(trend_data):
    """DataLab 응답을 간단한 관심도 요약으로 변환"""

    results = trend_data.get("results", [])

    summary = []

    for result in results:
        group_name = result.get("title") or result.get("groupName") or "-"
        data = result.get("data", [])

        if not data:
            summary.append({
                "keyword": group_name,
                "latest_ratio": 0,
                "avg_ratio": 0,
                "trend_direction": "unknown",
            })
            continue

        ratios = [
            float(row.get("ratio") or 0)
            for row in data
        ]

        latest_ratio = ratios[-1]
        avg_ratio = sum(ratios) / len(ratios)

        if len(ratios) >= 7:
            recent_avg = sum(ratios[-7:]) / 7
            previous_avg = (
                sum(ratios[-14:-7]) / 7
                if len(ratios) >= 14
                else avg_ratio
            )
        else:
            recent_avg = latest_ratio
            previous_avg = avg_ratio

        if recent_avg > previous_avg * 1.15:
            direction = "up"
        elif recent_avg < previous_avg * 0.85:
            direction = "down"
        else:
            direction = "flat"

        summary.append({
            "keyword": group_name,
            "latest_ratio": round(latest_ratio, 2),
            "avg_ratio": round(avg_ratio, 2),
            "trend_direction": direction,
        })

    return summary


def get_search_trend_summary(
    keywords,
    start_date=None,
    end_date=None,
    time_unit="date",
):
    keywords = normalize_datalab_keywords(
        keywords
    )

    if not keywords:
        return []

    trend_data = call_naver_datalab_search_trend(
        keywords=keywords,
        start_date=start_date,
        end_date=end_date,
        time_unit=time_unit,
    )

    return summarize_search_trend(
        trend_data
    )

def get_keyword_trend_score(keyword):
    """
    단일 검색어의 최근 DataLab 관심도 점수를 반환합니다.
    검색어가 없거나 조회에 실패하면 0.0을 반환합니다.
    """
    normalized_keywords = normalize_datalab_keywords(
        [keyword]
    )

    if not normalized_keywords:
        return 0.0

    try:
        result = get_search_trend_summary(
            normalized_keywords
        )

        if not result:
            return 0.0

        return float(
            result[0].get(
                "latest_ratio",
                0.0,
            )
            or 0.0
        )

    except Exception as exc:
        print(
            "[DATALAB SCORE ERROR]",
            {
                "keyword": normalized_keywords[0],
                "error": str(exc),
            },
        )

        return 0.0

        if not result:
            return 0

        return float(result[0]["latest_ratio"])

    except Exception:
        return 0
    
    
def get_cached_keyword_trend(keyword):
    sql = text("""
        SELECT keyword, trend_score, trend_direction, searched_at, raw_payload
        FROM keyword_trend_cache
        WHERE keyword = :keyword
          AND searched_at = CURRENT_DATE
    """)

    with get_engine().connect() as conn:
        row = conn.execute(sql, {"keyword": keyword}).mappings().first()

    return dict(row) if row else None


def save_keyword_trend_cache(keyword, summary, raw_payload):
    trend_score = summary.get("latest_ratio", 0)
    trend_direction = summary.get("trend_direction", "unknown")

    sql = text("""
        INSERT INTO keyword_trend_cache (
            keyword,
            trend_score,
            trend_direction,
            searched_at,
            raw_payload,
            updated_at
        ) VALUES (
            :keyword,
            :trend_score,
            :trend_direction,
            CURRENT_DATE,
            CAST(:raw_payload AS JSONB),
            NOW()
        )
        ON CONFLICT (keyword) DO UPDATE SET
            trend_score = EXCLUDED.trend_score,
            trend_direction = EXCLUDED.trend_direction,
            searched_at = EXCLUDED.searched_at,
            raw_payload = EXCLUDED.raw_payload,
            updated_at = NOW()
    """)

    with get_engine().begin() as conn:
        conn.execute(sql, {
            "keyword": keyword,
            "trend_score": trend_score,
            "trend_direction": trend_direction,
            "raw_payload": json.dumps(raw_payload, ensure_ascii=False),
        })


def get_keyword_trend_with_cache(keyword):
    normalized_keywords = normalize_datalab_keywords(
        [keyword]
    )

    if not normalized_keywords:
        return {
            "keyword": "",
            "latest_ratio": 0.0,
            "avg_ratio": 0.0,
            "trend_direction": "unknown",
            "from_cache": False,
            "error": "empty_keyword",
        }

    keyword = normalized_keywords[0]

    cached = get_cached_keyword_trend(
        keyword
    )

    if cached:
        return {
            "keyword": cached["keyword"],
            "latest_ratio": float(
                cached.get("trend_score")
                or 0.0
            ),
            "avg_ratio": 0.0,
            "trend_direction": (
                cached.get("trend_direction")
                or "unknown"
            ),
            "from_cache": True,
        }

    raw_data = call_naver_datalab_search_trend(
        [keyword]
    )

    summary_list = summarize_search_trend(
        raw_data
    )

    if not summary_list:
        return {
            "keyword": keyword,
            "latest_ratio": 0.0,
            "avg_ratio": 0.0,
            "trend_direction": "unknown",
            "from_cache": False,
        }

    summary = summary_list[0]

    save_keyword_trend_cache(
        keyword,
        summary,
        raw_data,
    )

    summary["from_cache"] = False

    return summary