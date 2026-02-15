from __future__ import annotations

import argparse

import uvicorn


def run_main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Run the admin webapp (FastAPI) via uvicorn.")
    parser.add_argument("--host", default="127.0.0.1", help="Bind host. Use 0.0.0.0 on VPS.")
    parser.add_argument("--port", type=int, default=8000, help="Bind port.")
    parser.add_argument("--reload", action="store_true", help="Auto-reload on code changes.")
    parser.add_argument(
        "--log-level",
        default="info",
        choices=["critical", "error", "warning", "info", "debug", "trace"],
        help="Uvicorn log level.",
    )
    parser.add_argument("--workers", type=int, default=1, help="Number of worker processes.")
    parser.add_argument(
        "--proxy-headers",
        action="store_true",
        help="Trust X-Forwarded-* headers (use behind ngrok/reverse proxy).",
    )
    parser.add_argument(
        "--forwarded-allow-ips",
        default=None,
        help="Comma-separated IPs to trust for forwarded headers. Use '*' to trust all.",
    )
    args = parser.parse_args(argv)

    if args.reload and args.workers != 1:
        raise SystemExit("--reload cannot be used with --workers != 1")

    uvicorn.run(
        "app:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level=args.log_level,
        workers=args.workers,
        proxy_headers=args.proxy_headers,
        forwarded_allow_ips=args.forwarded_allow_ips,
    )

