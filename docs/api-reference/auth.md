# Authentication Endpoints

## Issue an API key

```
POST /api/v1/auth/keys
```

No authentication required.

**Request:**
```json
{ "name": "my-production-app" }
```

**Response:**
```json
{
  "api_key": "fsri_a1b2c3d4...",
  "name": "my-production-app",
  "expires_at": "2027-04-23T00:00:00Z",
  "note": "Store this key securely. It will NOT be shown again."
}
```

!!! danger
    The key is only shown once. Store it immediately.

## Inspect current key

```
GET /api/v1/auth/keys/me
```

Requires authentication.

**Response:**
```json
{
  "name": "my-production-app",
  "created_at": "2025-04-23T10:00:00Z",
  "expires_at": "2027-04-23T10:00:00Z",
  "requests_total": 1432
}
```
