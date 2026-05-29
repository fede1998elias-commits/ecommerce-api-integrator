import os
from google.ads.googleads.client import GoogleAdsClient

CUSTOMER_ID = "8583465819"   # cuenta directa (sin guiones)
MCC_ID      = "5623250333"   # cuenta manager / login_customer_id

_YAML = os.path.join(os.path.dirname(__file__), "google-ads.yaml")

_PERIOD_MAP = {
    7:  "LAST_7_DAYS",
    14: "LAST_14_DAYS",
    30: "LAST_30_DAYS",
}


def _client() -> GoogleAdsClient:
    return GoogleAdsClient.load_from_storage(_YAML)


def fetch_campaigns(days: int = 30) -> list[dict]:
    """Campañas ENABLED con gasto, conversiones y ROAS."""
    period = _PERIOD_MAP.get(days, "LAST_30_DAYS")
    client = _client()
    svc = client.get_service("GoogleAdsService")

    query = f"""
        SELECT
            campaign.id,
            campaign.name,
            campaign.status,
            campaign.advertising_channel_type,
            metrics.cost_micros,
            metrics.impressions,
            metrics.clicks,
            metrics.conversions,
            metrics.conversions_value,
            metrics.ctr,
            metrics.average_cpc
        FROM campaign
        WHERE campaign.status = 'ENABLED'
          AND segments.date DURING {period}
        ORDER BY metrics.cost_micros DESC
    """

    rows = svc.search(customer_id=CUSTOMER_ID, query=query)

    campaigns = []
    for row in rows:
        cost = row.metrics.cost_micros / 1_000_000
        conv_value = row.metrics.conversions_value
        roas = round(conv_value / cost, 2) if cost > 0 else 0.0

        campaigns.append({
            "id":               row.campaign.id,
            "name":             row.campaign.name,
            "channel_type":     row.campaign.advertising_channel_type.name,
            "cost":             round(cost, 2),
            "impressions":      row.metrics.impressions,
            "clicks":           row.metrics.clicks,
            "ctr":              round(row.metrics.ctr * 100, 2),
            "avg_cpc":          round(row.metrics.average_cpc / 1_000_000, 2),
            "conversions":      round(row.metrics.conversions, 1),
            "conversions_value": round(conv_value, 2),
            "roas":             roas,
        })

    return campaigns


def fetch_summary(days: int = 30) -> dict:
    """Totales de cuenta: gasto, conversiones y ROAS agregados."""
    campaigns = fetch_campaigns(days)
    total_cost  = sum(c["cost"] for c in campaigns)
    total_conv  = sum(c["conversions"] for c in campaigns)
    total_value = sum(c["conversions_value"] for c in campaigns)
    return {
        "campaigns_active": len(campaigns),
        "total_cost":       round(total_cost, 2),
        "total_conversions": round(total_conv, 1),
        "total_conversions_value": round(total_value, 2),
        "roas":             round(total_value / total_cost, 2) if total_cost > 0 else 0.0,
        "days":             days,
    }
