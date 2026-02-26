import shutil
import subprocess
import sys
from pathlib import Path

from .extractors import extract_json_payload


class BridgeError(RuntimeError):
    pass


def _resolve_executable(name):
    local_bin = Path(sys.executable).parent / name
    if local_bin.exists() and local_bin.is_file():
        return str(local_bin)

    resolved_bin = Path(sys.executable).resolve().parent / name
    if resolved_bin.exists() and resolved_bin.is_file():
        return str(resolved_bin)

    found = shutil.which(name)
    if found:
        return found

    return None


def run_cmd(cmd, timeout=60):
    proc = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    if proc.returncode != 0:
        raise BridgeError(proc.stderr.strip() or proc.stdout.strip() or "command failed")
    return proc.stdout.strip()


def check_agent_reach_ready():
    agent_reach_bin = _resolve_executable("agent-reach")
    if not agent_reach_bin:
        raise BridgeError("agent-reach 未安装，请先安装 Agent-Reach")

    try:
        run_cmd([agent_reach_bin, "doctor"], timeout=30)
    except BridgeError as exc:
        raise BridgeError("agent-reach doctor 执行失败: %s" % exc)


def call_mcporter(expr, timeout=120):
    mcporter_bin = _resolve_executable("mcporter")
    if not mcporter_bin:
        raise BridgeError("mcporter 未安装，请先执行 agent-reach install")

    try:
        output = run_cmd([mcporter_bin, "call", expr], timeout=timeout)
    except FileNotFoundError:
        raise BridgeError("mcporter 未安装，请先执行 agent-reach install")

    try:
        return extract_json_payload(output)
    except Exception:
        return {"raw_output": output}


def search_feeds(keyword):
    expr = "xiaohongshu.search_feeds(keyword: %s)" % _quote(keyword)
    return call_mcporter(expr, timeout=180)


def get_feed_detail(feed_id, xsec_token):
    expr = "xiaohongshu.get_feed_detail(feed_id: %s, xsec_token: %s)" % (_quote(feed_id), _quote(xsec_token))
    return call_mcporter(expr, timeout=120)


def _quote(value):
    text = str(value).replace('\\', '\\\\').replace('"', '\\"')
    return '"%s"' % text
