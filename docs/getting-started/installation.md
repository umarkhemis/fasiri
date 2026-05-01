# Installation

## Python SDK

```bash
pip install fasiri
```

Requires Python 3.9 or higher.

## Self-hosted API Server

```bash
git clone https://github.com/umarkhemis/fasiri
cd fasiri
pip install -r requirements.txt
cp .env.example .env
```

Then fill in your provider API keys in `.env` — see [Environment Variables](../self-hosting/env.md).

Start the server:

```bash
uvicorn app.main:app --reload
```

Open [http://localhost:8000/docs](http://localhost:8000/docs) for interactive API docs.
