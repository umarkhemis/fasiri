# Environment Variables

Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

## Provider Credentials

| Variable                  | Required | Description                                       |
|---------------------------|----------|---------------------------------------------------|
| `SUNBIRD_API_KEY`         | Yes       | JWT from `POST https://api.sunbird.ai/auth/token` |
| `KHAYA_API_KEY`           | Yes       | Subscription key from translation.ghananlp.org    |
| `KHAYA_API_KEY_SECONDARY` | -        | Secondary Khaya key for rate-limit failover       |
| `HUGGINGFACE_API_KEY`     | Yes       | Free token from huggingface.co/settings/tokens    |

## Security

| Variable            | Default         | Description                                        |
|---------------------|-----------------|--------------------------------------------------|
| `FASIRI_SECRET_KEY` | `change-me-...` | Generate with: `openssl rand -hex 32`             |
| `API_KEY_TTL_SECONDS` | `31536000`    | Key lifetime in seconds (default: 1 year)         |

## Rate Limiting

| Variable               | Default | Description                             |
|------------------------|---------|-----------------------------------------|
| `RATE_LIMIT_RPM`       | `60`    | Requests per minute per API key         |
| `RATE_LIMIT_BATCH_RPM` | `10`    | Batch requests per minute per API key   |
| `REDIS_URL`            | -       | Redis for multi-worker rate limiting    |

## Server

| Variable           | Default                 | Description             |
|--------------------|-------------------------|-------------------------|
| `BASE_URL`         | `https://fasiri-bu9u.onrender.com` | Public base URL         |
| `DEBUG`            | `false`                 | Enable debug logging    |
| `HTTP_TIMEOUT`     | `30`                    | Provider timeout (secs) |
| `HTTP_TIMEOUT_STT` | `60`                    | STT timeout (secs)      |
