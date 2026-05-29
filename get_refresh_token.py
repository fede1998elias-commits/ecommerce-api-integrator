"""
Genera el refresh_token de Google Ads via OAuth2.
Ejecutar una sola vez: python get_refresh_token.py
"""
import os
import sys
import webbrowser
from urllib.parse import urlencode, urlparse, parse_qs

import requests

CLIENT_ID     = os.environ.get("GOOGLE_CLIENT_ID", "")
CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", "")
SCOPE         = "https://www.googleapis.com/auth/adwords"
REDIRECT_URI  = "urn:ietf:wg:oauth:2.0:oob"  # sin servidor local, código se copia a mano

AUTH_URL   = "https://accounts.google.com/o/oauth2/auth"
TOKEN_URL  = "https://oauth2.googleapis.com/token"
YAML_PATH  = os.path.join(os.path.dirname(__file__), "google-ads.yaml")


def build_auth_url() -> str:
    params = {
        "client_id":     CLIENT_ID,
        "redirect_uri":  REDIRECT_URI,
        "response_type": "code",
        "scope":         SCOPE,
        "access_type":   "offline",
        "prompt":        "consent",  # fuerza la emisión del refresh_token
    }
    return f"{AUTH_URL}?{urlencode(params)}"


def exchange_code(code: str) -> dict:
    resp = requests.post(TOKEN_URL, data={
        "code":          code.strip(),
        "client_id":     CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "redirect_uri":  REDIRECT_URI,
        "grant_type":    "authorization_code",
    })
    resp.raise_for_status()
    return resp.json()


def write_yaml(refresh_token: str) -> None:
    developer_token = os.environ.get("GOOGLE_ADS_DEVELOPER_TOKEN", "TU_DEVELOPER_TOKEN")
    mcc_id = os.environ.get("GOOGLE_ADS_MCC_ID", "TU_MCC_ID")
    content = f"""\
developer_token: {developer_token}
client_id: {CLIENT_ID}
client_secret: {CLIENT_SECRET}
refresh_token: {refresh_token}
login_customer_id: "{mcc_id}"
use_proto_plus: True
"""
    with open(YAML_PATH, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"\ngoogle-ads.yaml actualizado en: {YAML_PATH}")


def main():
    url = build_auth_url()

    print("\n" + "=" * 62)
    print("  OBTENCIÓN DE REFRESH TOKEN — GOOGLE ADS")
    print("=" * 62)
    print("\nPaso 1: Se abrirá el navegador. Iniciá sesión con la cuenta")
    print("        que administra el MCC 562-325-0333.")
    print("\nSi el navegador no se abre, copiá esta URL manualmente:")
    print(f"\n  {url}\n")

    webbrowser.open(url)

    print("\nPaso 2: Autorizá el acceso y copiá el código que te muestra Google.")
    code = input("\nPegá el código acá y presioná Enter: ").strip()

    if not code:
        print("ERROR: No ingresaste ningún código.")
        sys.exit(1)

    print("\nIntercambiando código por tokens...")
    try:
        tokens = exchange_code(code)
    except requests.HTTPError as e:
        print(f"ERROR al intercambiar código: {e.response.text}")
        sys.exit(1)

    refresh_token = tokens.get("refresh_token")
    if not refresh_token:
        print("ERROR: La respuesta no incluye refresh_token.")
        print("Respuesta completa:", tokens)
        sys.exit(1)

    print(f"\nrefresh_token obtenido:\n  {refresh_token}")

    write_yaml(refresh_token)

    print("\n" + "=" * 62)
    print("  Listo. Ya podés iniciar el servidor Flask.")
    print("=" * 62 + "\n")


if __name__ == "__main__":
    main()
