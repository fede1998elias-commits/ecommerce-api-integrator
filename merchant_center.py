import os
from google.oauth2 import service_account
from googleapiclient.discovery import build

MERCHANT_ID = os.environ.get("MERCHANT_ID", "")
SERVICE_ACCOUNT_FILE = os.environ.get(
    "GOOGLE_SERVICE_ACCOUNT_FILE",
    os.path.join(os.path.dirname(__file__), "service-account.json"),
)
_SCOPES = ["https://www.googleapis.com/auth/content"]


def _client():
    creds = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE,
        scopes=_SCOPES,
    )
    return build("content", "v2.1", credentials=creds)


def fetch_products(max_results: int = 50) -> list[dict]:
    """Productos del catálogo de Merchant Center con precio, disponibilidad y condición."""
    service = _client()
    response = service.products().list(
        merchantId=MERCHANT_ID,
        maxResults=max_results,
    ).execute()

    products = []
    for item in response.get("resources", []):
        price_obj = item.get("price", {})
        products.append({
            "productId":    item.get("id", ""),
            "title":        item.get("title", ""),
            "brand":        item.get("brand", ""),
            "price":        price_obj.get("value", ""),
            "currency":     price_obj.get("currency", ""),
            "availability": item.get("availability", ""),
            "condition":    item.get("condition", ""),
        })
    return products


def fetch_product_statuses() -> list[dict]:
    """Estado de los productos en Shopping: aprobados, rechazados y con problemas."""
    service = _client()

    statuses = []
    page_token = None

    while True:
        kwargs = {"merchantId": MERCHANT_ID, "maxResults": 250}
        if page_token:
            kwargs["pageToken"] = page_token

        response = service.productstatuses().list(**kwargs).execute()

        for item in response.get("resources", []):
            destination_statuses = item.get("destinationStatuses", [])
            issues = item.get("itemLevelIssues", [])

            shopping_status = "unknown"
            for ds in destination_statuses:
                if ds.get("destination") == "Shopping":
                    shopping_status = ds.get("status", "unknown")
                    break

            statuses.append({
                "productId":   item.get("productId", ""),
                "title":       item.get("title", ""),
                "status":      shopping_status,
                "issues":      [
                    {
                        "code":        i.get("code", ""),
                        "description": i.get("description", ""),
                        "servability": i.get("servability", ""),
                    }
                    for i in issues
                ],
                "issues_count": len(issues),
            })

        page_token = response.get("nextPageToken")
        if not page_token:
            break

    return statuses
