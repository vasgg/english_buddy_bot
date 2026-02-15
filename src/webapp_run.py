from __future__ import annotations

import argparse
import os
from pathlib import Path

import uvicorn


def _env_bool(key: str) -> bool | None:
    raw = os.getenv(key)
    if raw is None:
        return None
    raw = raw.strip().lower()
    if raw in {"1", "true", "yes", "y", "on"}:
        return True
    if raw in {"0", "false", "no", "n", "off"}:
        return False
    raise SystemExit(f"Invalid boolean value for {key}={raw!r}")


def _env_int(key: str) -> int | None:
    raw = os.getenv(key)
    if raw is None:
        return None
    try:
        return int(raw.strip())
    except ValueError as exc:
        raise SystemExit(f"Invalid integer value for {key}={raw!r}") from exc


def run_main(argv: list[str] | None = None) -> None:
    try:
        from dotenv import load_dotenv
    except ImportError:
        load_dotenv = None

    if load_dotenv is not None:
        load_dotenv(override=False)

    parser = argparse.ArgumentParser(description="Run the admin webapp (FastAPI) via uvicorn.")
    parser.add_argument("--host", default=None, help="Bind host. Use 0.0.0.0 on VPS.")
    parser.add_argument("--port", type=int, default=None, help="Bind port.")
    parser.add_argument(
        "--reload",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Auto-reload on code changes.",
    )
    parser.add_argument(
        "--log-level",
        default=None,
        choices=["critical", "error", "warning", "info", "debug", "trace"],
        help="Uvicorn log level.",
    )
    parser.add_argument("--workers", type=int, default=None, help="Number of worker processes.")
    parser.add_argument(
        "--proxy-headers",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Trust X-Forwarded-* headers (use behind ngrok/reverse proxy).",
    )
    parser.add_argument(
        "--forwarded-allow-ips",
        default=None,
        help="Comma-separated IPs to trust for forwarded headers. Use '*' to trust all.",
    )
    args = parser.parse_args(argv)

    stage = os.getenv("STAGE", "").strip().upper()
    default_reload = stage == "DEV"

    host = args.host or os.getenv("WEBAPP_HOST") or "127.0.0.1"
    port = args.port if args.port is not None else (_env_int("WEBAPP_PORT") or 8000)
    log_level = args.log_level or os.getenv("WEBAPP_LOG_LEVEL") or "info"
    workers = args.workers if args.workers is not None else (_env_int("WEBAPP_WORKERS") or 1)

    reload = args.reload
    if reload is None:
        reload = _env_bool("WEBAPP_RELOAD")
    if reload is None:
        reload = default_reload

    proxy_headers = args.proxy_headers
    if proxy_headers is None:
        proxy_headers = _env_bool("WEBAPP_PROXY_HEADERS")
    if proxy_headers is None:
        proxy_headers = True

    forwarded_allow_ips = args.forwarded_allow_ips or os.getenv("WEBAPP_FORWARDED_ALLOW_IPS")

    if reload and workers != 1:
        raise SystemExit("--reload cannot be used with --workers != 1")

    Path("logs").mkdir(parents=True, exist_ok=True)

    uvicorn.run(
        "app:app",
        host=host,
        port=port,
        reload=reload,
        log_level=log_level,
        workers=workers,
        proxy_headers=proxy_headers,
        forwarded_allow_ips=forwarded_allow_ips,
    )
