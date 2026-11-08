#!/usr/bin/env python3
"""
BenQ TK700 RS232 over TCP CLI controller (via UETEL UE-E5410 Serial Server).

Environment variables:
  BENQ_HOST  Serial server IP address (default: 192.168.5.40)
  BENQ_PORT  Serial server TCP port (default: 8010)
"""

import argparse
import os
import re
import socket
import sys
import time

DEFAULT_HOST = os.environ.get("BENQ_HOST", "192.168.5.40")
DEFAULT_PORT = int(os.environ.get("BENQ_PORT", "8010"))

ALIASES = {
    "on": "pow=on",
    "off": "pow=off",
    "power": "pow=?",
    "source": "sour=?",
    "hdmi1": "sour=hdmi",
    "hdmi2": "sour=hdmi2",
    "hdmi3": "sour=hdmi3",
    "blank-on": "blank=on",
    "blank-off": "blank=off",
    "lamp": "ltim=?",
    "lamp-mode": "lampm=?",
    "lamp-normal": "lampm=lnor",
    "lamp-eco": "lampm=eco",
    "lamp-seco": "lampm=seco",
    "lamp-save": "lampm=lampsave",
    "mode": "appmod=?",
    "mode-hdr": "appmod=hdr",
    "mode-game": "appmod=game",
    "mode-cinema": "appmod=cine",
    "mode-bright": "appmod=bright",
    "mode-living": "appmod=living",
    "mode-sport": "appmod=sport",
    "model": "modelname=?",
}

STATUS_QUERIES = [
    ("Model", "modelname=?"),
    ("Power", "pow=?"),
    ("Source", "sour=?"),
    ("Picture Mode", "appmod=?"),
    ("Lamp Mode", "lampm=?"),
    ("Lamp Hours", "ltim=?"),
    ("Blank", "blank=?"),
    ("Aspect Ratio", "asp=?"),
    ("Position", "pp=?"),
]


def send_cmd(cmd: str, host: str = DEFAULT_HOST, port: int = DEFAULT_PORT, wait: float = 0.6) -> str:
    clean = cmd.strip().lstrip("*").rstrip("#")
    payload = f"\r*{clean}#\r".encode("ascii")
    with socket.create_connection((host, port), timeout=3.0) as sock:
        sock.sendall(payload)
        time.sleep(wait)
        sock.setblocking(False)
        chunks = []
        while True:
            try:
                data = sock.recv(1024)
                if not data:
                    break
                chunks.append(data)
            except BlockingIOError:
                break
        raw = b"".join(chunks).decode("ascii", errors="ignore")
        matches = re.findall(r"\*([^#\r\n]+)#", raw)
        if matches:
            return f"*{matches[-1]}#"
        return raw.strip()


def main() -> int:
    parser = argparse.ArgumentParser(description="Control BenQ TK700 projector via RS232-over-TCP.")
    parser.add_argument(
        "command",
        help="Command alias (on, off, status, hdmi1, hdmi2, lamp, etc.) or raw RS232 command (e.g. 'pow=?')",
    )
    parser.add_argument("--host", default=DEFAULT_HOST, help=f"Serial server host (default: {DEFAULT_HOST})")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help=f"Serial server port (default: {DEFAULT_PORT})")
    args = parser.parse_args()

    if args.command == "status":
        for label, q in STATUS_QUERIES:
            resp = send_cmd(q, host=args.host, port=args.port, wait=0.35)
            print(f"{label:<15}: {resp}")
        return 0

    raw_cmd = ALIASES.get(args.command.lower(), args.command)
    resp = send_cmd(raw_cmd, host=args.host, port=args.port)
    print(resp)
    return 0


if __name__ == "__main__":
    sys.exit(main())
