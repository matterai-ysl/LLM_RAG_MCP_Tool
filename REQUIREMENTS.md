# Requirements

This project is a Python MCP server managed with `uv`. Use `pyproject.toml`
and `uv.lock` as the source of truth for installation.

## Verified Local Environment

The current repository environment was checked with:

```bash
uv --version
uv run python --version
uv pip list
```

Observed versions:

| Component | Version |
| --- | --- |
| uv | 0.7.20 |
| Python | 3.12.11 |
| Project package | materials-science-mcp 1.0.0 |

The project declares support for Python `>=3.10`.

## Runtime Dependencies

Declared direct dependencies from `pyproject.toml`:

| Package | Declared range | Installed version in current uv environment |
| --- | --- | --- |
| fastmcp | >=0.2.0 | 2.12.2 |
| playwright | >=1.40.0 | 1.55.0 |
| litellm | >=1.50.0 | 1.76.2 |
| openai | >=1.0.0 | 1.106.1 |
| python-dotenv | >=1.0.0 | 1.1.1 |
| aiofiles | >=0.8.0 | 24.1.0 |
| httpx | >=0.25.0 | 0.28.1 |
| structlog | >=23.0.0 | 25.4.0 |

`requirements.txt` is kept for compatibility with tooling that expects a
requirements file, but the recommended install path is `uv sync`.

## External Requirements

- Internet access for OpenScholar retrieval and LiteLLM/OpenAI-compatible API calls.
- Chromium browser runtime for Playwright.
- An OpenAI-compatible API key and base URL.

Install the Python environment and Chromium runtime with:

```bash
uv sync
uv run python -m playwright install chromium
```

## Environment Variables

Create a local `.env` file. It is intentionally ignored by Git.

```env
BASE_URL=https://vip.dmxapi.com/v1
OPENAI_API_KEY=your-api-key-here
```

## Startup Commands

Run the MCP server over streamable HTTP:

```bash
uv run python materials_science_qa_mcp.py streamable-http
```

The server listens on port `8110`.

Run the MCP server over STDIO for clients that launch the process directly:

```bash
uv run python materials_science_qa_mcp.py stdio
```

Run the MCP server over SSE:

```bash
uv run python materials_science_qa_mcp.py sse
```

## Runtime Configuration Defaults

These defaults are defined in `materials_science_qa_mcp.py`:

| Setting | Default |
| --- | --- |
| `MAX_RETRIES` | 1 |
| `TIMEOUT_SECONDS` | 60 |
| `CONCURRENT_LIMIT` | 10 |
| MCP port | 8110 |

