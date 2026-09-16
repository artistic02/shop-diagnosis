#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
外卖门店诊断 · 后端服务
纯标准库实现，无需 pip install。

运行：
    python main.py
然后浏览器打开 http://localhost:8000

职责：
  1. 提供前端页面 (index.html)
  2. POST /api/report —— 接收诊断结果，调用 DeepSeek / 通义千问，返回 AI 诊断报告

注意：API Key 由前端每次请求携带，服务端不落盘。上线（Vercel）时应改为读服务端环境变量。
"""
import json
import os
import sys
import urllib.request
import urllib.error
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

# 防止某些控制台编码不支持中文时，print 抛 UnicodeEncodeError 把服务搞崩
for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(errors="replace")
    except Exception:
        pass

HOST = "127.0.0.1"
PORT = int(os.environ.get("PORT", "8000"))
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 供应商配置（均为 OpenAI 兼容接口）
PROVIDERS = {
    "deepseek": {
        "label": "DeepSeek",
        "url": "https://api.deepseek.com/chat/completions",
        "model": "deepseek-chat",
    },
    "qwen": {
        "label": "通义千问",
        "url": "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions",
        "model": "qwen-plus",
    },
}

SYSTEM_PROMPT = (
    "你是外卖代运营的资深运营顾问，擅长把数据问题翻译成加盟商听得懂的诊断报告。"
    "输出使用 Markdown，语气专业但不吓人。"
)

CONTENT_TYPES = {
    ".html": "text/html; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".js": "application/javascript; charset=utf-8",
    ".json": "application/json; charset=utf-8",
    ".svg": "image/svg+xml",
    ".ico": "image/x-icon",
}


def call_llm(provider, api_key, model, messages, temperature=0.7):
    """调用 OpenAI 兼容接口，返回模型文本内容。"""
    cfg = PROVIDERS.get(provider)
    if cfg is None:
        raise ValueError("未知供应商: " + str(provider))

    payload = json.dumps({
        "model": model or cfg["model"],
        "messages": messages,
        "temperature": temperature,
        "stream": False,
    }).encode("utf-8")

    req = urllib.request.Request(cfg["url"], data=payload, method="POST")
    req.add_header("Content-Type", "application/json")
    req.add_header("Authorization", "Bearer " + api_key)

    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", "replace")
        raise RuntimeError("LLM 接口返回 %s：%s" % (e.code, detail[:300]))
    except Exception as e:
        raise RuntimeError("请求失败：%s" % e)

    try:
        return data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError):
        raise RuntimeError("响应格式异常：%s" % json.dumps(data, ensure_ascii=False)[:300])


class Handler(BaseHTTPRequestHandler):
    def _send_json(self, status, obj):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _serve_file(self, path):
        # 防止目录穿越
        filepath = os.path.normpath(os.path.join(BASE_DIR, path))
        if not filepath.startswith(BASE_DIR) or not os.path.isfile(filepath):
            self.send_error(404)
            return
        ext = os.path.splitext(filepath)[1].lower()
        with open(filepath, "rb") as f:
            content = f.read()
        self.send_response(200)
        self.send_header("Content-Type", CONTENT_TYPES.get(ext, "application/octet-stream"))
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def do_GET(self):
        path = self.path.split("?", 1)[0]
        if path == "/":
            path = "/index.html"
        if path == "/favicon.ico":
            self.send_response(204)
            self.end_headers()
            return
        self._serve_file(path.lstrip("/"))

    def do_POST(self):
        if self.path != "/api/report":
            self._send_json(404, {"ok": False, "error": "接口不存在"})
            return
        try:
            length = int(self.headers.get("Content-Length", 0))
            raw = self.rfile.read(length)
            body = json.loads(raw) if raw else {}
        except (ValueError, json.JSONDecodeError):
            self._send_json(400, {"ok": False, "error": "请求体不是合法 JSON（需 UTF-8 编码）"})
            return

        provider = body.get("provider") or os.environ.get("LLM_PROVIDER", "deepseek")
        api_key = (body.get("apiKey") or "").strip() or os.environ.get("LLM_API_KEY", "").strip()
        model = body.get("model") or os.environ.get("LLM_MODEL", "")
        prompt = body.get("prompt") or ""

        if not api_key:
            self._send_json(400, {"ok": False, "error": "请填写 API Key，或设置环境变量 LLM_API_KEY"})
            return
        if not prompt:
            self._send_json(400, {"ok": False, "error": "缺少诊断内容（请先点击「开始诊断」）"})
            return

        try:
            content = call_llm(provider, api_key, model, [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ])
            self._send_json(200, {"ok": True, "report": content})
        except Exception as e:
            self._send_json(500, {"ok": False, "error": str(e)})

    def log_message(self, fmt, *args):
        print("[%s] %s" % (self.log_date_time_string(), fmt % args))


def main():
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    print("外卖门店诊断服务已启动：http://localhost:%d" % PORT)
    print("按 Ctrl+C 停止")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n已停止")


if __name__ == "__main__":
    main()
