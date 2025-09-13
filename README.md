# Foreclosure Finder (RealEstateAPI)

A minimal, low-cost Flask app to search for pre-foreclosure and foreclosure properties using RealEstate API. It uses the recommended pattern:

- Property Search with `ids_only: true` to get IDs at low/no cost.
- Optional Property Detail Bulk to fetch full foreclosure details only when you explicitly request them.
- SQLite caching to avoid re-paying for the same detail calls within a TTL.
- `TEST_MODE` to send `live=false` on search (depends on your key’s support).
- `COST_SAVER_MODE` to avoid auto-fetching details.

## Project layout

- `app.py`: Flask app and routes
- `reapi_client.py`: RealEstate API client wrapper (Search, Detail Bulk)
- `templates/`: HTML templates (`index.html`, `results.html`)
- `.env.example`: Example environment configuration
- `requirements.txt`: Python dependencies

## Prerequisites

- Python 3.10+
- RealEstate API property data key (from your Notion page shared by Lukas)

## Setup

1. Create a virtual environment and install dependencies:

   ```powershell
   python -m venv .venv
   .venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```

2. Copy `.env.example` to `.env` and set your values:

   ```ini
   REAPI_BASE_URL=https://api.realestateapi.com
   REAPI_SEARCH_PATH=/v1/property/search
   REAPI_DETAIL_BULK_PATH=/v1/property/detail/bulk
   REAPI_PROPERTY_API_KEY=YOUR_PROPERTY_API_KEY_HERE

   FLASK_ENV=development
   SECRET_KEY=change-this-secret
   CACHE_TTL_SECONDS=604800
   COST_SAVER_MODE=true
   TEST_MODE=false
   ```

   Notes:
   - Keep `COST_SAVER_MODE=true` to avoid detail calls by default.
   - Turn `TEST_MODE=true` to send `live=false` for search calls if your key supports trial/testing without credits.

3. Run the app:

   ```powershell
   python app.py
   ```

   Open http://127.0.0.1:5000/ in your browser.

## Usage Tips (Keeping Costs Low)

- Use city/state + date ranges to narrow results.
- Keep `ids_only: true` (the app sets this by default).
- Leave "Fetch Property Details" unchecked to browse IDs without spending credits. When ready, enable it to fetch details in bulk for the current result set.
- The app caches property details in `cache.db` for `CACHE_TTL_SECONDS` (7 days by default).
- If you need very fresh data for a particular property, toggle cost saver OFF (in `.env`) and explicitly re-fetch details.

## Data fields

- Property Search returns a limited subset optimized for speed. Full foreclosure data is available via Property Detail (or Detail Bulk). The app expects the detail response to include `foreclosureInfo` and related fields.

## Environment variables

- `REAPI_BASE_URL` — default `https://api.realestateapi.com`
- `REAPI_SEARCH_PATH` — e.g. `/v1/property/search`
- `REAPI_DETAIL_BULK_PATH` — e.g. `/v1/property/detail/bulk`
- `REAPI_PROPERTY_API_KEY` — your key
- `CACHE_TTL_SECONDS` — cache time for results & details (default 604800 = 7 days)
- `COST_SAVER_MODE` — if `true`, UI won’t auto-fetch details
- `TEST_MODE` — if `true`, search calls use `live=false` (as supported)

## Notes and Next Steps

- If you need to verify a known foreclosure, search narrow (address or radius) then enable details to retrieve `foreclosureInfo`.
- Add more UI filters as needed (lender, notice type, etc.).
- Consider adding paging and progress indicators for large result sets.

## Disclaimer

This project is a simple reference integration. Confirm endpoint paths, authentication headers, and field names against the latest RealEstate API documentation and your plan’s access. Adjust `reapi_client.py` if your account uses a different auth header (e.g., only `x-api-key`).
