"""Arranque para Render: abre $PORT antes de importar igraph/hnswlib/numpy.

Uvicorn importa la app antes de bindear. Si esa importación cuelga o lanza SIGILL,
Render no ve el puerto (timeout ~15 min) o sale con status 132.
"""
from __future__ import annotations

import asyncio
import os
import socket
import sys


def _prepare_env() -> None:
    os.environ.setdefault("PYTHONUNBUFFERED", "1")
    os.environ.setdefault("OMP_NUM_THREADS", "1")
    os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
    os.environ.setdefault("MKL_NUM_THREADS", "1")
    os.environ.setdefault("NUMEXPR_NUM_THREADS", "1")
    os.environ.setdefault("HNSWLIB_NO_NATIVE", "1")
    os.environ.setdefault(
        "NPY_DISABLE_CPU_FEATURES",
        "AVX512F,AVX512_SKX,AVX512CD,AVX512BW,AVX512DQ,AVX512VL",
    )


def _bind_port() -> tuple[socket.socket, int]:
    port = int(os.environ.get("PORT") or "8080")
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(("0.0.0.0", port))
    sock.listen(2048)
    sock.set_inheritable(True)
    print(f"[run_server] puerto {port} abierto; cargando FastAPI...", flush=True)
    return sock, port


def main() -> None:
    _prepare_env()
    sock, port = _bind_port()

    from uvicorn import Config, Server
    from app.main import app

    config = Config(
        app=app,
        host="0.0.0.0",
        port=port,
        proxy_headers=True,
        forwarded_allow_ips="*",
        timeout_keep_alive=75,
        log_level="info",
    )
    server = Server(config)
    asyncio.run(server.serve(sockets=[sock]))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"[run_server] fallo de arranque: {exc}", file=sys.stderr, flush=True)
        raise
