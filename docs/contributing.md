# Contributing to Fasiri

Thank you for your interest in contributing to Fasiri. This guide covers everything you need to get started.

## Ways to contribute

- **Report bugs** - [open an issue](https://github.com/umarkhemis/fasiri/issues/new?template=bug_report.md)
- **Request features** - [open a feature request](https://github.com/umarkhemis/fasiri/issues/new?template=feature_request.md)
- **Add a language** - see [Adding a new language](#adding-a-new-language) below
- **Improve documentation** - edit any `.md` file in `docs/` and open a PR
- **Fix a bug** - pick an issue labelled `good first issue`
- **Add tests** - improve coverage in `tests/`

## Development setup

```bash
# 1. Fork and clone
git clone https://github.com/YOUR_USERNAME/fasiri.git
cd fasiri

# 2. Create a virtual environment
python -m venv .venv
source .venv/bin/activate      # Linux/macOS
.venv\Scripts\activate         # Windows

# 3. Install dependencies
pip install -r requirements.txt
pip install -e sdk/
pip install python-multipart ruff

# 4. Copy .env and fill in keys (optional for unit tests)
cp env.example .env

# 5. Run the tests
pytest tests/ -v
```

## Running the server locally

```bash
uvicorn app.main:app --reload
# API at https://fasiri-bu9u.onrender.com
# Docs at https://fasiri-bu9u.onrender.com/docs
```

## Code style

Fasiri uses [Ruff](https://docs.astral.sh/ruff/) for linting.

```bash
# Check for issues
ruff check app/ sdk/ --select E,F,W

# Auto-fix safe issues
ruff check app/ sdk/ --fix
```

Rules:
- Use type hints on all function signatures
- Docstrings on all public methods (Google style)
- Maximum line length: 100 characters
- Imports: standard library, then third-party, then local

## Project structure

```
fasiri/
├── app/                    # FastAPI application
│   ├── api/                # Route handlers
│   ├── core/               # Config, registry, security
│   ├── middleware/         # Auth, rate limiting
│   ├── schemas/            # Pydantic models
│   ├── services/           # Providers and routing
│   └── utils/              # Helpers
├── sdk/                    # Python SDK
│   └── fasiri_sdk/
│       ├── __init__.py
│       └── client.py
├── tests/                  # Test suite
├── docs/                   # Documentation source (MkDocs)
├── nginx/                  # Nginx config
├── scripts/                # Deploy scripts
├── Dockerfile
├── docker-compose.yml
├── mkdocs.yml
└── pyproject.toml
```

## Adding a new language

Adding a language requires changes in two places:

### 1. Register the language in `app/core/registry.py`

```python
# In LANGUAGE_REGISTRY dict
"xx": LanguageInfo(
    "xx",              # Fasiri code (BCP-47 where possible)
    "Language Name",   # English name
    "Native Name",     # Name in the language itself
    "Region",          # e.g. "West Africa"
    "Family",          # e.g. "Niger-Congo"
    sunbird_code="xx", # Sunbird's code (if different)
    nllb_code="xx_Latn", # NLLB flores200 code
),
```

### 2. Add a model entry in `MODEL_REGISTRY`

```python
ModelEntry(
    model_id="Helsinki-NLP/opus-mt-en-xx",
    provider="huggingface",
    source_langs=["en"],
    target_langs=["xx"],
    quality_score=0.75,    # estimate from BLEU scores if available
    avg_latency_ms=1300,
),
```

### 3. Add tests

In `tests/test_translate.py`, add the language to:
- `test_core_languages_present()` if it should be a core language
- Any relevant translation test cases

### 4. Update the docs

- Add the language to `docs/getting-started/languages.md`
- Mention it in `docs/changelog.md`

## Submitting a pull request

1. Create a branch: `git checkout -b feature/your-feature-name`
2. Make your changes
3. Run tests: `pytest tests/ -v`
4. Run linter: `ruff check app/ sdk/`
5. Commit with a clear message:
   ```
   feat: add Tigrinya language support
   fix: correct Sunbird STT language code for Acholi
   docs: update rate limiting guide
   ```
6. Push and open a PR against `main`
7. Fill in the PR template

## Commit message format

We follow [Conventional Commits](https://www.conventionalcommits.org/):

```
feat:     new feature
fix:      bug fix
docs:     documentation only
test:     adding or fixing tests
refactor: code change that is not a feature or fix
chore:    build, CI, dependency updates
```

## Questions?

Open a [GitHub Discussion](https://github.com/umarkhemis/fasiri/discussions) or reach out to the Beta-Tech Labs team at [dev@betatechlabs.io](mailto:dev@betatechlabs.io).
