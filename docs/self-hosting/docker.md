# Docker Deployment

## Quick Start

```bash
git clone https://github.com/umarkhemis/fasiri
cd fasiri
cp .env.example .env
# Fill in your API keys in .env

docker-compose up --build
```

The API will be available at `https://api.fasiri-ai.com`.

## Production

```bash
# Build
docker build -t fasiri:latest .

# Run with 4 workers
docker run -d \
  --name fasiri \
  -p 8000:8000 \
  --env-file .env \
  fasiri:latest
```

## docker-compose.yml

The included `docker-compose.yml` starts:
- **fasiri** - the API server (port 8000)
- **nginx** - reverse proxy (port 80/443)
- **redis** - rate limiting (optional)
