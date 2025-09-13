import os
import json
import hashlib
import sqlite3
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from flask import Flask, render_template, request, redirect, url_for, flash
from dotenv import load_dotenv

from reapi_client import SkipTraceClient, MatchRequirements

# Load environment variables
load_dotenv()

DB_PATH = os.path.join(os.path.dirname(__file__), "cache.db")

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "change-this-secret")

# App settings
CACHE_TTL_SECONDS = int(os.getenv("CACHE_TTL_SECONDS", "604800"))  # default 7 days
COST_SAVER_MODE = os.getenv("COST_SAVER_MODE", "true").lower() == "true"
TEST_MODE = os.getenv("TEST_MODE", "false").lower() == "true"

# Initialize the API client
client = SkipTraceClient(
    base_url=os.getenv("REAPI_BASE_URL", "https://api.realestateapi.com"),
    api_key=os.getenv("REAPI_API_KEY"),
    user_id=os.getenv("REAPI_USER_ID", "test_user")
)


def init_db():
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS cache (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL,
            expires_at INTEGER NOT NULL
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS property_detail_cache (
            property_id TEXT PRIMARY KEY,
            value TEXT NOT NULL,
            expires_at INTEGER NOT NULL
        )
        """
    )
    con.commit()
    con.close()


# Initialize database and check configuration at import time (Flask 3.x safe)
init_db()
if not client.api_key:
    app.logger.warning("REAPI_PROPERTY_API_KEY is not set. Set it in .env to make live calls.")


def cache_set(key: str, value: Dict[str, Any], ttl_seconds: int = CACHE_TTL_SECONDS) -> None:
    expires_at = int((datetime.utcnow() + timedelta(seconds=ttl_seconds)).timestamp())
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute(
        "REPLACE INTO cache (key, value, expires_at) VALUES (?, ?, ?)",
        (key, json.dumps(value), expires_at),
    )
    con.commit()
    con.close()


def cache_get(key: str) -> Optional[Dict[str, Any]]:
    now_ts = int(datetime.utcnow().timestamp())
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("SELECT value, expires_at FROM cache WHERE key = ?", (key,))
    row = cur.fetchone()
    con.close()
    if not row:
        return None
    value_str, expires_at = row
    if expires_at < now_ts:
        return None
    try:
        return json.loads(value_str)
    except Exception:
        return None


def detail_cache_set(property_id: str, value: Dict[str, Any], ttl_seconds: int = CACHE_TTL_SECONDS) -> None:
    expires_at = int((datetime.utcnow() + timedelta(seconds=ttl_seconds)).timestamp())
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute(
        "REPLACE INTO property_detail_cache (property_id, value, expires_at) VALUES (?, ?, ?)",
        (property_id, json.dumps(value), expires_at),
    )
    con.commit()
    con.close()


def detail_cache_get(property_id: str) -> Optional[Dict[str, Any]]:
    now_ts = int(datetime.utcnow().timestamp())
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("SELECT value, expires_at FROM property_detail_cache WHERE property_id = ?", (property_id,))
    row = cur.fetchone()
    con.close()
    if not row:
        return None
    value_str, expires_at = row
    if expires_at < now_ts:
        return None
    try:
        return json.loads(value_str)
    except Exception:
        return None


 


@app.route("/")
def index():
    return render_template(
        "index.html",
        cost_saver_mode=COST_SAVER_MODE,
        test_mode=TEST_MODE,
    )


@app.route("/search", methods=["POST"])
def search():
    form = request.form
    
    # Get form data
    first_name = form.get("first_name") or None
    last_name = form.get("last_name") or None
    email = form.get("email") or None
    phone = form.get("phone") or None
    address = form.get("address") or None
    city = form.get("city") or None
    state = form.get("state") or None
    zip_code = form.get("zip_code") or None
    
    # Get match requirements
    require_phone = "require_phone" in form
    require_email = "require_email" in form
    
    # Build cache key from form data
    search_key = hashlib.md5(
        json.dumps(
            {
                "first_name": first_name,
                "last_name": last_name,
                "email": email,
                "phone": phone,
                "address": address,
                "city": city,
                "state": state,
                "zip_code": zip_code,
                "require_phone": require_phone,
                "require_email": require_email,
            },
            sort_keys=True,
        ).encode("utf-8")
    ).hexdigest()
    
    # Check cache first
    data = cache_get(search_key)
    
    if not data:
        try:
            # Set up match requirements
            match_requirements = MatchRequirements(
                phones=require_phone,
                emails=require_email,
                operator="and" if require_phone and require_email else "or"
            )
            
            # Make the skip trace API call
            result = client.skip_trace(
                first_name=first_name,
                last_name=last_name,
                email=email,
                phone=phone,
                address=address,
                city=city,
                state=state,
                zip_code=zip_code,
                match_requirements=match_requirements
            )
            
            # Cache the result
            cache_set(search_key, result, ttl_seconds=86400)  # Cache for 1 day
            
            # Transform the API response to match our template's expected format
            transformed_result = {
                'match': result.get('match', False),
                'requestId': result.get('requestId', ''),
                'requestDate': result.get('requestDate', ''),
                'credits': result.get('credits', 0),
                'identity': {
                    'names': [],
                    'address': {},
                    'addressHistory': [],
                    'phones': [],
                    'emails': []
                },
                'demographics': {}
            }
            
            # Map identity data
            if 'output' in result and 'identity' in result['output']:
                identity = result['output']['identity']
                
                # Map names
                if 'names' in identity:
                    transformed_result['identity']['names'] = [{
                        'first_name': name.get('firstName', ''),
                        'last_name': name.get('lastName', ''),
                        'full_name': name.get('fullName', ''),
                        'type': name.get('type', 'primary'),
                        'last_seen': name.get('lastSeen', '')
                    } for name in identity.get('names', [])]
                
                # Map address
                if 'address' in identity:
                    addr = identity['address']
                    transformed_result['identity']['address'] = {
                        'formattedAddress': addr.get('formattedAddress', ''),
                        'street': f"{addr.get('house', '')} {addr.get('preDir', '')} {addr.get('street', '')} {addr.get('postDir', '')} {addr.get('strType', '')}".strip(),
                        'city': addr.get('city', ''),
                        'state': addr.get('state', ''),
                        'zip': addr.get('zip', ''),
                        'last_seen': addr.get('lastSeen', '')
                    }
                
                # Map address history
                if 'addressHistory' in identity:
                    transformed_result['identity']['addressHistory'] = [{
                        'formattedAddress': addr.get('formattedAddress', ''),
                        'last_seen': addr.get('lastSeen', '')
                    } for addr in identity.get('addressHistory', [])]
                
                # Map phones
                if 'phones' in identity:
                    transformed_result['identity']['phones'] = [{
                        'number': phone.get('phone', ''),
                        'phoneType': phone.get('phoneType', ''),
                        'isConnected': phone.get('isConnected', False),
                        'last_seen': phone.get('lastSeen', '')
                    } for phone in identity.get('phones', [])]
                
                # Map emails
                if 'emails' in identity:
                    transformed_result['identity']['emails'] = [{
                        'email': email.get('email', ''),
                        'emailType': email.get('emailType', 'personal')
                    } for email in identity.get('emails', [])]
            
            # Map demographics
            if 'output' in result and 'demographics' in result['output']:
                demo = result['output']['demographics']
                transformed_result['demographics'] = {
                    'age': demo.get('age', ''),
                    'gender': demo.get('gender', ''),
                    'dob': demo.get('dob', '')
                }
            
            # Add match confidence
            data_points = 0
            if transformed_result['identity'].get('phones'):
                data_points += 1
            if transformed_result['identity'].get('emails'):
                data_points += 1
            if transformed_result['identity'].get('address'):
                data_points += 1
            
            if data_points >= 2:
                transformed_result['match_confidence'] = 'high'
            elif data_points == 1:
                transformed_result['match_confidence'] = 'medium'
            else:
                transformed_result['match_confidence'] = 'low'
            
            return render_template("results.html", result=transformed_result)
            
        except Exception as e:
            app.logger.error(f"Error performing skip trace: {str(e)}")
            return render_template(
                "index.html",
                error=f"Error performing skip trace: {str(e)}",
                cost_saver_mode=COST_SAVER_MODE,
                test_mode=TEST_MODE,
            )
    else:
        # Return cached result
        return render_template("results.html", result=data)
    for pid in property_ids:
        detail = details_by_id.get(pid)
        results.append({
            "id": pid,
            "address": _extract_address(detail) if detail else None,
            "foreclosureInfo": (detail or {}).get("foreclosureInfo"),
            "preForeclosure": (detail or {}).get("preForeclosure"),
        })

    return render_template(
        "results.html",
        results=results,
        raw_search=data,
        fetched_details=fetch_details,
        cost_saver_mode=COST_SAVER_MODE,
    )


def _iso_date(d: str) -> str:
    # expects YYYY-MM-DD; return ISO timestamp with Z
    try:
        dt = datetime.strptime(d, "%Y-%m-%d")
        return dt.strftime("%Y-%m-%dT00:00:00.000Z")
    except ValueError:
        return d


def _hash_key(obj: Dict[str, Any]) -> str:
    s = json.dumps(obj, sort_keys=True)
    return hashlib.sha1(s.encode("utf-8")).hexdigest()


def _extract_address(detail: Optional[Dict[str, Any]]) -> Optional[str]:
    if not detail:
        return None
    addr = detail.get("address") or {}
    parts = [addr.get("address"), addr.get("city"), addr.get("state"), addr.get("zip")]
    return ", ".join([p for p in parts if p]) or None


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000, debug=True)
