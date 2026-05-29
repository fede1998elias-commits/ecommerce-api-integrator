import os
import requests

# La API pública de Connectif usa Authorization: ApiKey {KEY_SECRET}
# donde KEY_SECRET ya tiene el formato "KeyID:KeySecret".
# api.connectif.cloud expone metadata de workflows y lookup individual de contactos.
# Las estadísticas (aperturas, clics, conversiones, revenue) NO están disponibles
# en esta versión de la API con el scope actual del token.

_BASE = "https://api.connectif.cloud"


def _headers() -> dict:
    secret = os.environ.get("CONNECTIF_KEY_SECRET", "").strip()
    if not secret:
        raise ValueError("Variable de entorno CONNECTIF_KEY_SECRET no definida")
    return {
        "Accept": "application/json",
        "Authorization": f"apiKey {secret}",
    }


def _get(path: str, params: dict = None) -> dict | list:
    resp = requests.get(
        f"{_BASE}/{path.lstrip('/')}",
        headers=_headers(),
        params=params or {},
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json()


def _paginate(path: str, params: dict = None, max_results: int = 200) -> list:
    """Itera páginas mientras haya `links.next` hasta max_results."""
    params = {**(params or {}), "pageSize": min(max_results, 50)}
    results = []
    url = f"{_BASE}/{path.lstrip('/')}"
    headers = _headers()

    while url and len(results) < max_results:
        resp = requests.get(url, headers=headers, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        results.extend(data.get("results", []))
        next_url = data.get("links", {}).get("next")
        url = next_url if next_url else None
        params = {}  # la URL de next ya trae los params

    return results[:max_results]


def fetch_campaigns(limit: int = 20) -> list[dict]:
    """Workflows de Connectif ordenados por fecha de creación desc.
    La API no expone estadísticas (aperturas/clics/conversiones/revenue)."""
    items = _paginate("workflows", params={"limit": limit}, max_results=limit)

    campaigns = []
    for item in items:
        campaigns.append({
            "id":          item.get("id", ""),
            "name":        item.get("name", ""),
            "folder":      item.get("folder", ""),
            "status":      item.get("status", ""),
            "created_at":  item.get("createdAt", ""),
            "updated_at":  item.get("updatedAt", ""),
            "activated_at": item.get("activatedAt", ""),
            "finalized_at": item.get("finalizedAt", ""),
            "tags":        item.get("tags", []),
            # stats no disponibles en esta versión de la API
            "stats_available": False,
        })
    return campaigns


def fetch_contacts_summary() -> dict:
    """Resumen de contactos.
    La API actual no expone endpoints de estadísticas agregadas de contactos.
    Solo permite lookup individual por email (/contacts/{email})."""
    return {
        "available":  False,
        "message":    (
            "La API de Connectif (api.connectif.cloud) no expone estadísticas "
            "agregadas de contactos. Solo permite lookup individual por email. "
            "Para obtener totales (activos, bajas, nuevos) es necesario acceder "
            "al panel de Connectif o usar su funcionalidad de exportación."
        ),
    }


def fetch_automations() -> list[dict]:
    """Workflows de Connectif con status 'active' o 'scheduled'.
    Incluye tanto campañas programadas como flujos automatizados.
    La API no distingue el tipo de workflow ni expone estadísticas."""
    all_workflows = _paginate("workflows", max_results=200)

    automation_statuses = {"active", "scheduled", "paused"}
    automations = []
    for item in all_workflows:
        if item.get("status", "") in automation_statuses:
            automations.append({
                "id":          item.get("id", ""),
                "name":        item.get("name", ""),
                "folder":      item.get("folder", ""),
                "status":      item.get("status", ""),
                "created_at":  item.get("createdAt", ""),
                "updated_at":  item.get("updatedAt", ""),
                "activated_at": item.get("activatedAt", ""),
                "tags":        item.get("tags", []),
                "stats_available": False,
            })
    return automations
