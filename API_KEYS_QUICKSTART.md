# QuantClaw Data - API Keys Quick Start Guide

## 🚀 Quick Start

All API keys are now loaded from environment variables. Here's what you need to know:

### For Developers

**Import and use API keys:**
```python
from api_config import FRED_API_KEY, FINNHUB_API_KEY

# Use in your code
response = requests.get(url, params={'api_key': FRED_API_KEY})
```

**Check if a key is configured:**
```python
from api_config import is_configured, get_api_key

if is_configured('FRED'):
    key = get_api_key('FRED')
    # Make API call
else:
    print("FRED API key not configured")
```

### For System Administrators

**Add a new API key:**
```bash
# Edit .env file
echo "NEW_SERVICE_API_KEY=your_key_here" >> .env

# Verify it's loaded
python3 modules/api_config.py
```

**Check configured services:**
```bash
python3 modules/api_config.py
```

**Test API connectivity:**
```bash
python3 test_api_keys.py
```

## 📋 Available API Keys

| Service | Environment Variable | Status |
|---------|---------------------|--------|
| FRED | `FRED_API_KEY` | ✅ Configured |
| Finnhub | `FINNHUB_API_KEY` | ✅ Configured |
| EIA | `EIA_API_KEY` | ⚠️ Using DEMO_KEY |
| Census | `CENSUS_API_KEY` | ✅ Configured |
| Polygon | `POLYGON_API_KEY` | ✅ Configured |
| Etherscan | `ETHERSCAN_API_KEY` | ✅ Configured |
| USDA NASS | `USDA_NASS_API_KEY` | ✅ Configured |
| Financial Datasets | `FINANCIAL_DATASETS_API_KEY` | ✅ Configured |
| BLS | `BLS_API_KEY` | ℹ️ Optional |
| BOK | `BOK_API_KEY` | ❌ Not configured |
| Comtrade | `COMTRADE_API_KEY` | ❌ Not configured |
| Crunchbase | `CRUNCHBASE_API_KEY` | ❌ Not configured |

## 🔧 Common Tasks

### Test if your API keys work
```bash
python3 test_api_keys.py
```

### List configured services
```python
from api_config import list_configured_services
print(list_configured_services())
# Output: ['FRED', 'FINNHUB', 'CENSUS', 'POLYGON', 'ETHERSCAN', 'USDA_NASS', 'FINANCIAL_DATASETS']
```

### Add a new service
1. Register for API key with the service
2. Add to `.env` file: `SERVICE_API_KEY=your_key`
3. Add to `modules/api_config.py` if not already there
4. Use in your modules: `from api_config import SERVICE_API_KEY`

## 🛠️ Troubleshooting

**Problem:** Module can't find API key  
**Solution:** Check `.env` file exists and contains the key

**Problem:** API returns 401 Unauthorized  
**Solution:** Key might be invalid. Run `python3 test_api_keys.py` to test

**Problem:** Import error after update  
**Solution:** Check `api_migration.log` for details

## 📚 Documentation

- **Full migration details:** `API_MIGRATION_COMPLETE.md`
- **Shared config module:** `modules/api_config.py`
- **Test script:** `test_api_keys.py`
- **Patch script:** `patch_api_keys.py`

## ✅ Best Practices

1. **Never commit API keys to git** - They're in `.env` which is gitignored
2. **Use `api_config` module** - Single source of truth for all keys
3. **Check if configured** - Use `is_configured()` before making API calls
4. **Rotate keys regularly** - Just update `.env` file, no code changes needed
5. **Keep backups** - Original files in `backups_api_migration/`

---

**Need help?** Check `API_MIGRATION_COMPLETE.md` for full documentation.
