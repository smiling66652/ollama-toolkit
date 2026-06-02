#!/usr/bin/env python3
"""
混合 AI 助手 v1.0 - 本地 + 云端智能路由
Ollama (本地) 处理日常轻量任务，DeepSeek API 处理复杂推理任务

使用方式:
  1. 先运行: pip install openai
  2. 配置下方 API_KEY，或设置环境变量 DEEPSEEK_API_KEY
  3. python hybrid_ai.py
"""

import json
import os
import sys
import time
from typing import Optional

# ═══════════════════ 配置区 ═══════════════════
# DeepSeek API Key (在 https://platform.deepseek.com 获取，免费注册送 2M tokens/天)
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")  # ← 填入你的 Key

# Ollama 本地服务
OLLAMA_BASE_URL = "http://localhost:11434/v1"
OLLAMA_MODEL = "hermes-3-llama-3.2-3b"  # ← 改为你注册的模型名

# DeepSeek 云端服务
DEEPSEEK_BASE_URL = "https://api.deepseek.com/v1"
DEEPSEEK_MODEL = "deepseek-chat"  # DeepSeek-V3，性价比之王

# 路由阈值: 消息长度超过此值走 DeepSeek (token 估算 ≈ 字符数/2)
ROUTING_TOKEN_THRESHOLD = 150

# 系统提示词
SYSTEM_PROMPT_LOCAL = "你是一个简洁高效的AI助手。用中文回答，保持简洁，直接给出答案。"
SYSTEM_PROMPT_CLOUD = "你是一个专业的AI助手。用中文回答，分析要深入，推理要严谨。"

# 是否打印路由决策
DEBUG_ROUTING = True
# ══════════════════════════════════════════════


def estimate_tokens(text: str) -> int:
    """粗略估算 token 数（中文约 1.5字/token，英文约 4字符/token）"""
    chinese_chars = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
    other_chars = len(text) - chinese_chars
    return int(chinese_chars / 1.5 + other_chars / 4)


def should_use_cloud(message: str, history: list) -> tuple[bool, str]:
    """
    智能路由决策: 判断该用本地还是云端
    返回 (use_cloud, reason)
    """
    msg_lower = message.lower()

    # ── 强制走云端的场景 ──
    cloud_keywords = [
        "写一个", "写一段", "写一篇", "帮我写",
        "分析一下", "详细分析", "深度分析",
        "翻译成", "翻译这段",
        "总结一下", "总结这篇",
        "生成代码", "写代码", "写函数",
        "帮我设计", "设计方案",
        "对比一下", "比较一下",
        "解释一下", "详细解释",
        "列出", "列举", "罗列",
        "写一个脚本", "写一个程序",
        "数学", "计算", "推导",
        "论文", "报告",
    ]
    for kw in cloud_keywords:
        if kw in msg_lower:
            return True, f"命中云端关键词: {kw}"

    # ── 消息长度判断 ──
    tokens = estimate_tokens(message)
    if tokens > ROUTING_TOKEN_THRESHOLD:
        return True, f"消息较长 (约{tokens} tokens)"

    # ── 多轮对话上下文较长 ──
    history_tokens = sum(estimate_tokens(str(m)) for m in history)
    if history_tokens > 500:
        return True, f"对话上下文较长 (约{history_tokens} tokens)"

    # ── 默认走本地 ──
    return False, "短对话/简单问题 → 走本地"


def call_local_ollama(messages: list) -> str:
    """调用本地 Ollama"""
    try:
        from openai import OpenAI
        client = OpenAI(base_url=OLLAMA_BASE_URL, api_key="ollama")
        response = client.chat.completions.create(
            model=OLLAMA_MODEL,
            messages=messages,
            max_tokens=1024,
            temperature=0.7,
        )
        return response.choices[0].message.content
    except ConnectionError:
        return "[错误] 无法连接本地 Ollama，请确保 Ollama 正在运行 (ollama serve)"
    except Exception as e:
        return f"[错误] Ollama 调用失败: {e}"


def call_deepseek(messages: list) -> str:
    """调用 DeepSeek API"""
    if not DEEPSEEK_API_KEY:
        return "[错误] 未配置 DeepSeek API Key。请设置环境变量 DEEPSEEK_API_KEY 或在脚本中填写。"

    try:
        from openai import OpenAI
        client = OpenAI(base_url=DEEPSEEK_BASE_URL, api_key=DEEPSEEK_API_KEY)
        response = client.chat.completions.create(
            model=DEEPSEEK_MODEL,
            messages=messages,
            max_tokens=4096,
            temperature=0.7,
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"[错误] DeepSeek API 调用失败: {e}"


def chat():
    """交互式聊天循环"""
    print("╔════════════════════════════════════════════╗")
    print("║     混合 AI 助手 v1.0                      ║")
    print("║     本地 Ollama + 云端 DeepSeek             ║")
    print("╠════════════════════════════════════════════╣")
    print(f"║  本地模型: {OLLAMA_MODEL:<30s} ║")
    print(f"║  云端模型: {DEEPSEEK_MODEL:<30s} ║")
    api_status = "✓ 已配置" if DEEPSEEK_API_KEY else "✗ 未配置"
    print(f"║  API状态:  {api_status:<30s} ║")
    print("╠════════════════════════════════════════════╣")
    print("║  命令: /local 强制本地 | /cloud 强制云端    ║")
    print("║        /quit 退出     | /clear 清空对话     ║")
    print("║        /status 查看状态                     ║")
    print("╚════════════════════════════════════════════╝")
    print()

    history: list[dict] = []
    force_mode: Optional[str] = None  # "local" | "cloud" | None

    while True:
        try:
            user_input = input("你: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n再见!")
            break

        if not user_input:
            continue

        # ── 命令处理 ──
        if user_input == "/quit" or user_input == "/exit":
            print("再见!")
            break
        elif user_input == "/clear":
            history.clear()
            print("[系统] 对话已清空")
            continue
        elif user_input == "/local":
            force_mode = "local"
            print("[系统] 已切换为强制本地模式")
            continue
        elif user_input == "/cloud":
            force_mode = "cloud"
            print("[系统] 已切换为强制云端模式")
            continue
        elif user_input == "/auto":
            force_mode = None
            print("[系统] 已切换为自动路由模式")
            continue
        elif user_input == "/status":
            print(f"  对话轮数: {len(history) // 2}")
            print(f"  模式: {'本地' if force_mode == 'local' else '云端' if force_mode == 'cloud' else '自动路由'}")
            print(f"  本地模型: {OLLAMA_MODEL}")
            print(f"  云端模型: {DEEPSEEK_MODEL}")
            print(f"  API Key: {'已配置' if DEEPSEEK_API_KEY else '未配置'}")
            continue

        # ── 路由决策 ──
        use_cloud = False
        reason = ""

        if force_mode == "local":
            use_cloud = False
            reason = "强制本地模式"
        elif force_mode == "cloud":
            use_cloud = True
            reason = "强制云端模式"
        else:
            use_cloud, reason = should_use_cloud(user_input, history)

        if DEBUG_ROUTING:
            mode_tag = "☁ DeepSeek" if use_cloud else "💻 本地"
            print(f"  [{mode_tag}] {reason}")

        # ── 构建消息 ──
        system_prompt = SYSTEM_PROMPT_CLOUD if use_cloud else SYSTEM_PROMPT_LOCAL
        messages = [{"role": "system", "content": system_prompt}] + history + [
            {"role": "user", "content": user_input}
        ]

        # ── 调用模型 ──
        start = time.time()
        if use_cloud:
            reply = call_deepseek(messages)
        else:
            reply = call_local_ollama(messages)
        elapsed = time.time() - start

        # ── 显示回复 ──
        print(f"\nAI ({'DeepSeek' if use_cloud else '本地'}): {reply}")
        print(f"  [耗时 {elapsed:.1f}s]\n")

        # ── 更新历史 ──
        history.append({"role": "user", "content": user_input})
        history.append({"role": "assistant", "content": reply})

        # 保持历史不超过 20 轮
        if len(history) > 40:
            history = history[-40:]


def test_connection():
    """测试两个服务的连通性"""
    print("═" * 40)
    print("  连通性测试")
    print("═" * 40)

    # 测试 Ollama
    print("\n[1] 测试本地 Ollama...")
    try:
        import urllib.request
        req = urllib.request.Request(OLLAMA_BASE_URL.replace("/v1", "/api/tags"), method="GET")
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read())
            models = [m["name"] for m in data.get("models", [])]
            print(f"  ✓ Ollama 连接成功")
            print(f"  已注册模型: {', '.join(models) if models else '(无)'}")
    except Exception as e:
        print(f"  ✗ Ollama 连接失败: {e}")
        print("  请先运行 Ollama (ollama serve)")

    # 测试 DeepSeek
    print("\n[2] 测试 DeepSeek API...")
    if not DEEPSEEK_API_KEY:
        print("  ✗ 未配置 API Key，跳过测试")
        print("  获取地址: https://platform.deepseek.com")
    else:
        try:
            from openai import OpenAI
            client = OpenAI(base_url=DEEPSEEK_BASE_URL, api_key=DEEPSEEK_API_KEY)
            resp = client.chat.completions.create(
                model=DEEPSEEK_MODEL,
                messages=[{"role": "user", "content": "hi"}],
                max_tokens=5,
            )
            print(f"  ✓ DeepSeek API 连接成功")
        except Exception as e:
            print(f"  ✗ DeepSeek API 连接失败: {e}")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        test_connection()
    else:
        chat()
