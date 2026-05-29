import os
import time
import requests

_URL = "https://www.clarity.ms/export-data/api/v1/project-live-insights"
_CACHE_TTL = 7200  # 2 horas

_cache: dict = {}


def _get_env() -> tuple[str, str]:
    token = os.environ.get("CLARITY_API_TOKEN", "").strip()
    project_id = os.environ.get("CLARITY_PROJECT_ID", "").strip()
    if not token:
        raise ValueError("Variable de entorno CLARITY_API_TOKEN no definida")
    if not project_id:
        raise ValueError("Variable de entorno CLARITY_PROJECT_ID no definida")
    return token, project_id


def _fetch_raw(days: int) -> dict:
    """Llama a la API y devuelve un dict {metricName: information[]} ya indexado.
    Cachea la respuesta 2 horas para no agotar el límite de 10 llamadas/día."""
    now = time.time()
    cached = _cache.get(days)
    if cached and now < cached["expires_at"]:
        return cached["data"]

    token, project_id = _get_env()
    resp = requests.get(
        _URL,
        headers={"Authorization": f"Bearer {token}"},
        params={"projectId": project_id, "numDays": days},
        timeout=15,
    )
    resp.raise_for_status()

    # La API devuelve una lista; la indexamos por metricName para acceso O(1)
    indexed = {item["metricName"]: item["information"] for item in resp.json()}

    _cache[days] = {
        "data": indexed,
        "expires_at": now + _CACHE_TTL,
        "cached_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
    }
    return indexed


def cache_info() -> dict:
    now = time.time()
    return {
        k: {
            "cached_at": v["cached_at"],
            "expires_in_minutes": round((v["expires_at"] - now) / 60, 1),
        }
        for k, v in _cache.items()
        if now < v["expires_at"]
    }


def fetch_summary(days: int = 7) -> dict:
    """Métricas generales del período: sesiones, engagement, rage/dead clicks, errores."""
    m = _fetch_raw(days)

    def first(key):
        return (m.get(key) or [{}])[0]

    traffic    = first("Traffic")
    engagement = first("EngagementTime")
    scroll     = first("ScrollDepth")
    rage       = first("RageClickCount")
    dead       = first("DeadClickCount")
    script_err = first("ScriptErrorCount")
    err_click  = first("ErrorClickCount")
    quickback  = first("QuickbackClick")

    return {
        "sessions":                   int(traffic.get("totalSessionCount", 0)),
        "users":                      int(traffic.get("distinctUserCount", 0)),
        "bot_sessions":               int(traffic.get("totalBotSessionCount", 0)),
        "pages_per_session":          round(float(traffic.get("pagesPerSessionPercentage", 0)), 2),
        "avg_active_time_secs":       int(engagement.get("activeTime", 0)),
        "avg_total_time_secs":        int(engagement.get("totalTime", 0)),
        "avg_scroll_depth_pct":       round(float(scroll.get("averageScrollDepth", 0)), 1),
        "rage_clicks":                int(rage.get("subTotal", 0)),
        "rage_click_sessions_pct":    round(float(rage.get("sessionsWithMetricPercentage", 0)), 2),
        "dead_clicks":                int(dead.get("subTotal", 0)),
        "dead_click_sessions_pct":    round(float(dead.get("sessionsWithMetricPercentage", 0)), 2),
        "script_errors":              int(script_err.get("subTotal", 0)),
        "error_clicks":               int(err_click.get("subTotal", 0)),
        "quickback_clicks":           int(quickback.get("subTotal", 0)),
        "days":                       days,
        "from_cache":                 days in _cache,
    }


def fetch_pages_with_issues(days: int = 7) -> list[dict]:
    """Páginas más visitadas con contexto de problemas del proyecto.
    La API live-insights no desglosa rage/dead clicks por URL,
    por lo que se devuelven las popular pages con las métricas globales de issues."""
    m = _fetch_raw(days)

    rage_total = int((m.get("RageClickCount") or [{}])[0].get("subTotal", 0))
    dead_total = int((m.get("DeadClickCount") or [{}])[0].get("subTotal", 0))

    pages = []
    for item in (m.get("PopularPages") or []):
        pages.append({
            "page":             item.get("url", ""),
            "visits":           int(item.get("visitsCount", 0)),
            "rage_clicks_total_project": rage_total,
            "dead_clicks_total_project": dead_total,
        })

    pages.sort(key=lambda x: x["visits"], reverse=True)
    return pages
