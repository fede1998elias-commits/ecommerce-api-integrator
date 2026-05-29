# ecommerce-api-integrator

A Flask-based analytics dashboard that aggregates data from 8 e-commerce and marketing APIs into a single, session-protected web interface.

## Integrations

| Source | Data |
|---|---|
| **Google Analytics 4** | Sessions, users, transactions, product funnel (views → cart → purchase), revenue |
| **Google Ads** | Active campaigns, spend, conversions, ROAS |
| **Meta Ads** | Campaigns, spend, impressions, clicks, CPM, CPC, purchase conversions, ROAS |
| **VTEX** | Orders (OMS), enriched order data, product catalog |
| **Google Merchant Center** | Product catalog, approval statuses, disapproval issues |
| **Google Search Console** | Search performance, top queries, top pages, impressions, CTR |
| **Microsoft Clarity** | Dead clicks, rage clicks, excessive scroll, quick-back clicks, script errors |
| **Connectif** | Email/automation workflows, campaign status |

## Requirements

- Python 3.10+
- Google service account JSON with access to GA4, Merchant Center, and Search Console
- Google Ads `google-ads.yaml` credentials file
- API keys for VTEX, Clarity, Connectif, and Meta Ads (see `.env.example`)

## Setup

```bash
git clone https://github.com/your-username/ecommerce-api-integrator.git
cd ecommerce-api-integrator

python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

pip install -r requirements.txt

cp .env.example .env
# Edit .env with your credentials

# Place your Google service account JSON at the project root
# Place your google-ads.yaml at the project root
```

## Credentials

The project requires two credential files that are **not tracked by git**:

- `<your-service-account>.json` — Google service account with roles: GA4 Viewer, Merchant Center reader, Search Console reader. Update the filename reference in `server.py`, `merchant_center.py`, and `search_console.py`.
- `google-ads.yaml` — Google Ads OAuth2 config. See [google-ads-python docs](https://github.com/googleads/google-ads-python).

All other secrets go in `.env` (see `.env.example`).

## Running

```bash
python server.py
```

Server starts at `http://localhost:5000`. Login required.

## API Endpoints

All endpoints require an active session (login via `POST /login`).

### GA4
| Endpoint | Params | Description |
|---|---|---|
| `GET /api/products` | `start_date`, `end_date` | Product funnel: views, cart, purchases, revenue, conversion rates |
| `GET /api/compare` | `start_date`, `end_date` | Current vs previous period comparison with deltas |
| `GET /api/product_trend` | `name` | Weekly trend for a specific product (last 56 days) |

### Google Ads
| Endpoint | Params | Description |
|---|---|---|
| `GET /api/campaigns` | `days` (7/14/30) | Active campaigns with spend, conversions, ROAS |
| `GET /api/campaigns/summary` | `days` (7/14/30) | Account-level totals |

### Meta Ads
| Endpoint | Params | Description |
|---|---|---|
| `GET /api/meta/campaigns` | `days` | Campaigns with spend, impressions, clicks, conversions, ROAS |
| `GET /api/meta/summary` | `days` | Account-level totals |

### VTEX
| Endpoint | Params | Description |
|---|---|---|
| `GET /api/vtex/orders` | `days`, `with_items` | OMS orders |
| `GET /api/vtex/orders/enriched` | `days` | Orders with product-level detail |
| `GET /api/vtex/products` | `page`, `pageSize` | Product catalog |

### Merchant Center
| Endpoint | Params | Description |
|---|---|---|
| `GET /api/merchant/products` | `max_results` | Product catalog with price and availability |
| `GET /api/merchant/statuses` | — | Approval statuses and disapproval issues |

### Search Console
| Endpoint | Params | Description |
|---|---|---|
| `GET /api/search/performance` | `days` | All queries with clicks, impressions, CTR, position |
| `GET /api/search/queries` | `days`, `limit` | Top queries |
| `GET /api/search/pages` | `days`, `limit` | Top pages |

### Clarity
| Endpoint | Params | Description |
|---|---|---|
| `GET /api/clarity/summary` | `days` | Aggregated UX metrics |
| `GET /api/clarity/issues` | `days` | Pages with UX issues (dead/rage clicks, etc.) |

### Connectif
| Endpoint | Params | Description |
|---|---|---|
| `GET /api/connectif/campaigns` | `limit` | Email/automation workflows |
| `GET /api/connectif/automations` | — | Active and paused automations |
| `GET /api/connectif/contacts` | — | Contact summary |

## Project Structure

```
├── server.py              # Flask app, all /api/* endpoints, session auth
├── google_ads.py          # Google Ads client — fetch_campaigns / fetch_summary
├── meta_ads.py            # Meta Ads (Facebook) client
├── vtex.py                # VTEX OMS and catalog client
├── merchant_center.py     # Google Merchant Center client
├── search_console.py      # Google Search Console client
├── clarity.py             # Microsoft Clarity client
├── connectif.py           # Connectif email automation client
├── get_refresh_token.py   # Utility to refresh Google Ads OAuth token
├── static/
│   ├── index.html         # Dashboard frontend
│   └── login.html         # Login page
├── .env.example           # Required environment variables template
└── requirements.txt
```
