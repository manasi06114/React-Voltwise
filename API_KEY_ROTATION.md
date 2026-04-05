# VoltWise - API Key Rotation System

## Overview

The VoltWise Energy Grid project now includes an intelligent **API Key Rotation System** that automatically rotates between multiple Gemini API keys when usage quotas are exhausted.

## How It Works

### 1. **Multiple API Keys**

Store multiple API keys in your `.env` file:

```
GEMINI_API_KEY=key1_here
GEMINI_API_KEY=key2_here
GEMINI_API_KEY=key3_here
GEMINI_API_KEY=key4_here
... (as many as you need)
```

### 2. **Key Manager** (`key_manager.py`)

The `APIKeyManager` class:

- ✅ Loads all API keys from the `.env` file
- ✅ Randomly selects available keys (not quota-exhausted)
- ✅ Tracks failed/exhausted keys in memory
- ✅ Rotates to available keys when quotas are hit
- ✅ Resets failed keys list when all are exhausted

### 3. **Automatic Error Detection** (`model.py`)

The `GeminiGridAgent` now:

- ✅ Catches quota/rate-limit errors
- ✅ Raises `ApiKeyError` exception when a key is exhausted
- ✅ Allows the backend to catch and rotate keys

### 4. **Error Handling** (`backend_api.py`)

The `/env/gemini-step` endpoint:

- ✅ Attempts to predict using current key
- ✅ On `ApiKeyError`: marks key as failed
- ✅ Automatically rotates to next random available key
- ✅ Retries up to `total_keys` times
- ✅ Returns `503 Service Unavailable` only if all keys are exhausted

## API Endpoints

### Check API Key Status

```bash
GET /api-keys/status
```

Response:

```json
{
  "total_keys": 6,
  "available_keys": 5,
  "failed_keys": 1,
  "current_key_index": 2
}
```

### Health Check (with Key Status)

```bash
GET /health
```

Response:

```json
{
  "status": "ok",
  "gemini_agent": true,
  "api_key_manager": {
    "total_keys": 6,
    "available_keys": 5,
    "failed_keys": 1
  }
}
```

### Gemini Step (with Auto-Rotation)

```bash
POST /env/gemini-step
Body: {"task": "medium"}
```

Response includes rotation info:

```json
{
  "observation": {...},
  "reward": 10.5,
  "action": 1,
  "action_source": "gemini",
  "api_key_rotation": {
    "attempt": 0,
    "success": true
  }
}
```

## Algorithm Details

### Key Selection

```python
# Randomly select from AVAILABLE keys (not in failed set)
available_keys = [k for k in all_keys if k not in failed_keys]
selected_key = random.choice(available_keys)
```

### On API Error

```python
for attempt in range(total_keys):
    try:
        # Use current key
        response = agent.predict(observation)
    except ApiKeyError:
        # Mark key as failed
        key_manager.mark_key_failed(current_key)
        # Get new random key (next iteration)
        current_key = key_manager.get_key()
```

### Key Reset

When all keys are exhausted:

```python
if len(failed_keys) == len(all_keys):
    # Reset and try again
    failed_keys.clear()
    print("🔄 Resetting all keys")
```

## Usage Example

### Running the Project

**Backend (with key rotation):**

```bash
cd c:\Users\Devansh\OneDrive\Desktop\voltwise
uvicorn energy-grid-env.api.backend_api:app --reload --port 8000
```

**Frontend:**

```bash
cd c:\Users\Devansh\OneDrive\Desktop\voltwise\energy-grid-env\frontend\dashboard
npm run dev  # Runs on port 5173
```

### Testing the API

```bash
# 1. Create a session
curl -X POST http://localhost:8000/env/reset -H "Content-Type: application/json" -d '{"task": "medium"}'

# 2. Check API key status
curl http://localhost:8000/api-keys/status

# 3. Let Gemini AI make a decision (auto-rotates on key failure)
curl -X POST http://localhost:8000/env/gemini-step -H "Content-Type: application/json" -d '{"task": "medium"}'

# 4. Check health including key manager status
curl http://localhost:8000/health
```

## Console Output

When a key is rotated, you'll see:

```
⚠️  API Key failed. Failed count: 1/6
🔄 API Key exhausted (attempt 0/6): Quota exceeded for quota metric
✅ Loaded 6 API keys
⚠️  API Key failed. Failed count: 2/6
```

## File Structure

```
energy-grid-env/
├── api/
│   ├── backend_api.py      (Updated with key rotation)
│   ├── key_manager.py       (NEW - API key manager)
│   └── __init__.py
├── agent/
│   └── model.py            (Updated with ApiKeyError)
└── .env                     (Contains all API keys)
```

## Benefits

1. **Automatic Failover** - No manual key management needed
2. **Scalability** - Works with any number of API keys
3. **Resilience** - Continues working even when keys hit quotas
4. **Monitoring** - Track key usage via `/api-keys/status` endpoint
5. **Random Selection** - Distributes load across keys
6. **Transparent** - Dashboard works without any changes

## Monitoring

The dashboard automatically shows when key rotation happens. Check:

- `/health` endpoint for overall system status
- `/api-keys/status` for detailed key breakdown
- Backend console logs for rotation events

## Future Enhancements

- [ ] Persistent tracking of key quotas (database)
- [ ] Key priority/weighting
- [ ] Quota reset time tracking
- [ ] Alert notifications when keys fail
- [ ] Key rotation analytics dashboard
