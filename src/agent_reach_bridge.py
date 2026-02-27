import shutil
import subprocess
import sys
import time
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
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        raise BridgeError("command timeout after %ss" % timeout)

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


def call_mcporter(expr, timeout=120, retries=2, retry_delay_seconds=1.0):
    mcporter_bin = _resolve_executable("mcporter")
    if not mcporter_bin:
        raise BridgeError("mcporter 未安装，请先执行 agent-reach install")

    attempts = max(1, int(retries) + 1)
    last_error = None

    for attempt in range(1, attempts + 1):
        try:
            output = run_cmd([mcporter_bin, "call", expr], timeout=timeout)
            try:
                return extract_json_payload(output)
            except Exception:
                return {"raw_output": output}
        except FileNotFoundError:
            raise BridgeError("mcporter 未安装，请先执行 agent-reach install")
        except BridgeError as exc:
            last_error = exc
            if attempt >= attempts:
                break

            sleep_seconds = max(0.0, float(retry_delay_seconds)) * attempt
            if sleep_seconds > 0:
                time.sleep(sleep_seconds)

    raise BridgeError("mcporter 调用失败（已重试 %s 次）: %s" % (attempts, last_error))


def search_feeds(keyword, timeout=180, retries=2, retry_delay_seconds=1.0):
    expr = "xiaohongshu.search_feeds(keyword: %s)" % _quote(keyword)
    return call_mcporter(expr, timeout=timeout, retries=retries, retry_delay_seconds=retry_delay_seconds)


def get_feed_detail(feed_id, xsec_token, timeout=120, retries=1, retry_delay_seconds=0.8):
    expr = "xiaohongshu.get_feed_detail(feed_id: %s, xsec_token: %s)" % (_quote(feed_id), _quote(xsec_token))
    return call_mcporter(expr, timeout=timeout, retries=retries, retry_delay_seconds=retry_delay_seconds)


def _quote(value):
    text = str(value).replace('\\', '\\\\').replace('"', '\\"')
    return '"%s"' % text
