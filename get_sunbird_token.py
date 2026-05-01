#!/usr/bin/env python3
"""
Fasiri – Sunbird Token Helper
================================
Gets a fresh JWT from Sunbird and writes it to your .env automatically.

Usage:
    python get_sunbird_token.py
    python get_sunbird_token.py --email you@example.com --password yourpassword
    python get_sunbird_token.py --env-file /path/to/.env
"""
from __future__ import annotations

import argparse
import getpass
import json
import os
import re
import sys
from pathlib import Path

import httpx

SUNBIRD_TOKEN_URL = "https://api.sunbird.ai/auth/token"
SUNBIRD_REGISTER_URL = "https://api.sunbird.ai/auth/register"


def get_token(email: str, password: str) -> str:
    """Login and return the JWT access_token."""
    print(f"\n→ Logging in to Sunbird as {email}...")
    try:
        resp = httpx.post(
            SUNBIRD_TOKEN_URL,
            data={"username": email, "password": password},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=15,
        )
    except httpx.ConnectError:
        print("❌ Cannot reach api.sunbird.ai — check your internet connection.")
        sys.exit(1)

    if resp.status_code == 200:
        data = resp.json()
        token = data.get("access_token")
        if token:
            print(f"✅ Got JWT token: {token[:20]}...")
            return token
        else:
            print(f"❌ Response missing access_token: {data}")
            sys.exit(1)

    elif resp.status_code in (401, 400):
        print(f"❌ Login failed (HTTP {resp.status_code}) — wrong email or password.")
        print(f"   Response: {resp.text[:200]}")
        print(f"\n   To register a new account:")
        print(f"   python get_sunbird_token.py --register")
        sys.exit(1)

    else:
        print(f"❌ Unexpected HTTP {resp.status_code}: {resp.text[:200]}")
        sys.exit(1)


def register(email: str, password: str) -> bool:
    """Register a new Sunbird account."""
    print(f"\n→ Registering {email} with Sunbird...")
    resp = httpx.post(
        SUNBIRD_REGISTER_URL,
        json={"email": email, "password": password},
        headers={"Content-Type": "application/json"},
        timeout=15,
    )
    if resp.status_code in (200, 201):
        print(f"✅ Registered successfully. Now logging in...")
        return True
    elif resp.status_code == 409:
        print(f"ℹ️  Account already exists — proceeding to login.")
        return True
    else:
        print(f"❌ Registration failed (HTTP {resp.status_code}): {resp.text[:200]}")
        return False


def write_to_env(token: str, env_path: Path) -> None:
    """Write or update SUNBIRD_API_KEY in the .env file."""
    if not env_path.exists():
        # Create from .env.example if it exists
        example = env_path.parent / "env.example"
        if example.exists():
            env_path.write_text(example.read_text())
            print(f"ℹ️  Created {env_path} from env.example")
        else:
            env_path.write_text(f"SUNBIRD_API_KEY={token}\n")
            print(f"✅ Created {env_path} with SUNBIRD_API_KEY")
            return

    content = env_path.read_text()

    if "SUNBIRD_API_KEY=" in content:
        # Replace existing value
        new_content = re.sub(
            r"^SUNBIRD_API_KEY=.*$",
            f"SUNBIRD_API_KEY={token}",
            content,
            flags=re.MULTILINE,
        )
        env_path.write_text(new_content)
        print(f"✅ Updated SUNBIRD_API_KEY in {env_path}")
    else:
        # Append
        with open(env_path, "a") as f:
            f.write(f"\nSUNBIRD_API_KEY={token}\n")
        print(f"✅ Appended SUNBIRD_API_KEY to {env_path}")


def verify_token(token: str) -> None:
    """Quick sanity check — call nllb_translate with the token."""
    print("\n→ Verifying token with a test translation (en→lug)...")
    try:
        resp = httpx.post(
            "https://api.sunbird.ai/tasks/nllb_translate",
            json={"source_language": "eng", "target_language": "lug", "text": "Hello"},
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
            timeout=20,
        )
    except httpx.ConnectError:
        print("⚠️  Could not reach Sunbird for verification (no internet?)")
        return

    if resp.status_code == 200:
        output = resp.json().get("output", {})
        translated = output.get("translated_text", "")
        print(f"✅ Token works!  'Hello' → '{translated}' (Luganda)")
    elif resp.status_code == 405:
        print(f"❌ Token verification failed with 405 — token may be invalid or expired.")
        print(f"   Try running this script again to get a fresh token.")
    else:
        print(f"⚠️  Unexpected HTTP {resp.status_code}: {resp.text[:200]}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Get a fresh Sunbird JWT token")
    parser.add_argument("--email",    default=None, help="Sunbird account email")
    parser.add_argument("--password", default=None, help="Sunbird account password")
    parser.add_argument("--env-file", default=".env", help="Path to .env file (default: .env)")
    parser.add_argument("--register", action="store_true", help="Register a new account first")
    parser.add_argument("--no-write", action="store_true", help="Print token only, don't write .env")
    parser.add_argument("--verify",   action="store_true", default=True,
                        help="Verify token with a test call (default: True)")
    args = parser.parse_args()

    print("=" * 55)
    print("  Fasiri – Sunbird Token Helper")
    print("=" * 55)

    # Get credentials
    email    = args.email    or input("\n  Sunbird email: ").strip()
    password = args.password or getpass.getpass("  Sunbird password: ")

    # Optional registration
    if args.register:
        if not register(email, password):
            sys.exit(1)

    # Get token
    token = get_token(email, password)

    # Verify
    if args.verify:
        verify_token(token)

    # Write to .env
    env_path = Path(args.env_file)
    if args.no_write:
        print(f"\n  Token (copy this into your .env as SUNBIRD_API_KEY):")
        print(f"  {token}")
    else:
        write_to_env(token, env_path)
        print(f"\n  ✅ Done. Restart your server:")
        print(f"     uvicorn app.main:app --reload")
        print(f"\n  Then run the test suite:")
        print(f"     python test_live.py")
