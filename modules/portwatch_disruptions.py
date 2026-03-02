#!/usr/bin/env python3
"""portwatch_disruptions — IMF/Oxford PortWatch port disruption data. Source: https://portwatch.imf.org/. Free, no auth."""
import requests
import os
import json
import time
from datetime import datetime

CACHE_DIR = os.path.join(os.path.dirname(__file__), '..', 'cache')
os.makedirs(CACHE_DIR, exist_ok=True)
BASE = "https://services.arcgis.com"  # PortWatch uses ArcGIS
HEADERS = {"User-Agent": "QuantClaw/1.0"}

# PortWatch published feature service endpoints
PORTWATCH_BASE = "https://portwatch.imf.org"

def get_port_disruptions(**kwargs):
    """Fetch current global port disruption data from PortWatch."""
    cache_file = os.path.join(CACHE_DIR, "portwatch_disruptions.json")
    if os.path.exists(cache_file) and (time.time() - os.path.getmtime(cache_file)) < 3600:
        with open(cache_file) as f:
            return json.load(f)
    try:
        # PortWatch uses ArcGIS feature services
        url = "https://services9.arcgis.com/WQEzPKMGiGOHbHqR/arcgis/rest/services/PortWatch_Port_Disruptions/FeatureServer/0/query"
        params = {"where": "1=1", "outFields": "*", "f": "json", "resultRecordCount": 200,
                  "orderByFields": "disruption_score DESC"}
        resp = requests.get(url, params=params, headers=HEADERS, timeout=30)
        if resp.status_code == 200:
            data = resp.json()
            features = [f.get("attributes", {}) for f in data.get("features", [])]
            result = {"source": "IMF PortWatch", "count": len(features),
                      "disruptions": features, "fetch_time": datetime.now().isoformat()}
            with open(cache_file, "w") as f:
                json.dump(result, f, indent=2)
            return result
        # Fallback: try main API
        resp2 = requests.get(f"{PORTWATCH_BASE}/api/v1/ports", headers=HEADERS, timeout=15)
        if resp2.status_code == 200:
            return {"source": "IMF PortWatch", "data": resp2.json(),
                    "fetch_time": datetime.now().isoformat()}
        return {"error": f"PortWatch returned {resp.status_code}/{resp2.status_code}",
                "note": "PortWatch API may require browser session or different endpoint"}
    except Exception as e:
        return {"error": str(e), "source": "portwatch"}

def get_congestion_index(port=None, **kwargs):
    """Fetch port congestion index. port: port name or LOCODE."""
    try:
        url = "https://services9.arcgis.com/WQEzPKMGiGOHbHqR/arcgis/rest/services/PortWatch_Port_Congestion/FeatureServer/0/query"
        where_clause = f"port_name LIKE '%{port}%'" if port else "1=1"
        params = {"where": where_clause, "outFields": "*", "f": "json", "resultRecordCount": 50}
        resp = requests.get(url, params=params, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        features = [f.get("attributes", {}) for f in data.get("features", [])]
        return {"port": port, "count": len(features), "congestion": features,
                "fetch_time": datetime.now().isoformat()}
    except Exception as e:
        return {"error": str(e), "port": port}

def get_shipping_delays(**kwargs):
    """Fetch global shipping delay indicators."""
    try:
        url = "https://services9.arcgis.com/WQEzPKMGiGOHbHqR/arcgis/rest/services/PortWatch_Shipping_Delays/FeatureServer/0/query"
        params = {"where": "1=1", "outFields": "*", "f": "json", "resultRecordCount": 100}
        resp = requests.get(url, params=params, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        features = [f.get("attributes", {}) for f in data.get("features", [])]
        return {"count": len(features), "delays": features,
                "fetch_time": datetime.now().isoformat()}
    except Exception as e:
        return {"error": str(e)}

def get_data(ticker=None, **kwargs):
    return get_port_disruptions(**kwargs)

if __name__ == "__main__":
    result = get_port_disruptions()
    if "error" not in result:
        print(f"Port disruptions: {result.get('count', 0)} records")
    else:
        print(f"Error: {result['error']}")
