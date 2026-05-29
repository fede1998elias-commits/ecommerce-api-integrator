import os
from datetime import datetime, timedelta
from google.oauth2 import service_account
from googleapiclient.discovery import build

SITE_URL = os.environ.get("SEARCH_CONSOLE_SITE_URL", "")
SERVICE_ACCOUNT_FILE = os.environ.get(
    "GOOGLE_SERVICE_ACCOUNT_FILE",
    os.path.join(os.path.dirname(__file__), "service-account.json"),
)
_SCOPES = ["https://www.googleapis.com/auth/webmasters.readonly"]


def _client():
    creds = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE,
        scopes=_SCOPES,
    )
    return build("searchconsole", "v1", credentials=creds)


def _date_range(days: int) -> tuple[str, str]:
    # Search Console tiene un lag de ~2 días en los datos
    end = datetime.today() - timedelta(days=2)
    start = end - timedelta(days=days - 1)
    return start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d")


def fetch_search_performance(days: int = 30) -> list[dict]:
    """Rendimiento de búsqueda agrupado por query + página, ordenado por clics."""
    start_date, end_date = _date_range(days)
    service = _client()

    body = {
        "startDate": start_date,
        "endDate": end_date,
        "dimensions": ["query", "page"],
        "rowLimit": 25000,
        "orderBy": [{"fieldName": "clicks", "sortOrder": "DESCENDING"}],
    }

    response = service.searchanalytics().query(siteUrl=SITE_URL, body=body).execute()

    rows = []
    for row in response.get("rows", []):
        keys = row.get("keys", [])
        rows.append({
            "query":       keys[0] if len(keys) > 0 else "",
            "page":        keys[1] if len(keys) > 1 else "",
            "clicks":      row.get("clicks", 0),
            "impressions": row.get("impressions", 0),
            "ctr":         round(row.get("ctr", 0) * 100, 2),
            "position":    round(row.get("position", 0), 1),
        })
    return rows


def fetch_top_queries(days: int = 30, limit: int = 20) -> list[dict]:
    """Top queries por clics agrupadas solo por query."""
    start_date, end_date = _date_range(days)
    service = _client()

    body = {
        "startDate": start_date,
        "endDate": end_date,
        "dimensions": ["query"],
        "rowLimit": limit,
        "orderBy": [{"fieldName": "clicks", "sortOrder": "DESCENDING"}],
    }

    response = service.searchanalytics().query(siteUrl=SITE_URL, body=body).execute()

    rows = []
    for row in response.get("rows", []):
        rows.append({
            "query":       row.get("keys", [""])[0],
            "clicks":      row.get("clicks", 0),
            "impressions": row.get("impressions", 0),
            "ctr":         round(row.get("ctr", 0) * 100, 2),
            "position":    round(row.get("position", 0), 1),
        })
    return rows


def fetch_top_pages(days: int = 30, limit: int = 20) -> list[dict]:
    """Top páginas por clics agrupadas solo por página."""
    start_date, end_date = _date_range(days)
    service = _client()

    body = {
        "startDate": start_date,
        "endDate": end_date,
        "dimensions": ["page"],
        "rowLimit": limit,
        "orderBy": [{"fieldName": "clicks", "sortOrder": "DESCENDING"}],
    }

    response = service.searchanalytics().query(siteUrl=SITE_URL, body=body).execute()

    rows = []
    for row in response.get("rows", []):
        rows.append({
            "page":        row.get("keys", [""])[0],
            "clicks":      row.get("clicks", 0),
            "impressions": row.get("impressions", 0),
            "ctr":         round(row.get("ctr", 0) * 100, 2),
            "position":    round(row.get("position", 0), 1),
        })
    return rows
