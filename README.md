# 🦙 ollama-toolkit

> Ollama 工具集 — GGUF 模型转换 + 本地/云端混合 AI 调用脚本

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.8+-green.svg)](https://www.python.org/)
[![GitHub](https://img.shields.io/badge/GitHub-smiling66652-orange.svg)](https://github.com/smiling66652/ollama-toolkit)

---

## ✨ 功能一览

| 脚本 | 功能 | 适用场景 |
|------|------|----------|
| `gguf-to-ollama.py` | GGUF 模型文件转换为 Ollama 可识别格式 | 本地部署量化模型 |
| `gguf-to-ollama.bat` | 同上，Windows 批处理版 | 双击运行，无需 Python 环境 |
| `hybrid_ai.py` | 本地 Ollama + DeepSeek API 混合调用 | 日常轻量任务走本地，复杂推理走云端 |

---

## 🚀 快速开始

### 1. 环境准备

```bash
# 安装依赖
pip install openai requests
# 安装 Ollama（本地 AI 运行时）
# 访问 https://ollama.com/download 下载安装
```

### 2. 配置 API Key

```bash
# 设置 DeepSeek API Key（hybrid_ai.py 需要）
export DEEPSEEK_API_KEY="sk-你的Key"
# 或在脚本内直接填写（不推荐，Key 会暴露）
```

### 3. 运行

```bash
# GGUF 转 Ollama 格式
python gguf-to-ollama.py --input model.gguf --name my-model

# Windows 批处理版（双击运行）
gguf-to-ollama.bat

# 混合 AI 调用
python hybrid_ai.py
```

---

## 📖 详细使用

### `gguf-to-ollama.py` — GGUF → Ollama

**背景**：HuggingFace 下载的 GGUF 格式模型无法直接被 Ollama 使用，需要转换成 Modelfile 格式。

```bash
# 基本用法
python gguf-to-ollama.py \
  --input ./models/llama3-8b-q4.gguf \
  --name llama3-8b-q4 \
  --output ./Modelfiles/

# 转换后导入 Ollama
ollama create llama3-8b-q4 -f ./Modelfiles/llama3-8b-q4.Modelfile
ollama run llama3-8b-q4 "你好，介绍一下自己"
```

**参数说明**：

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--input` | 输入 GGUF 文件路径 | 必填 |
| `--name` | Ollama 模型名称 | 必填 |
| `--output` | 输出 Modelfile 目录 | `./` |
| `--system` | 系统提示词 | Ollama 默认 |
| `--temperature` | 温度参数 | `0.7` |

### `hybrid_ai.py` — 混合 AI 调用

**设计理念**：本地 Ollama 处理日常轻量任务（隐私保护 + 零成本），DeepSeek API 处理复杂推理任务（需要更强能力时自动切换）。

```python
from hybrid_ai import ask

# 自动选择：简单问题走本地，复杂问题走云端
response = ask("解释一下量子纠缠")
print(response)
```

**路由策略**：

| 条件 | 路由目标 | 说明 |
|------|-----------|------|
| 问题长度 < 100 字 | 本地 Ollama | 快速响应，零成本 |
| 问题包含"分析/推理/代码" | DeepSeek API | 复杂任务，精度优先 |
| 本地 Ollama 不可用 | DeepSeek API | 自动降级 |
| 云端 API 不可用 | 本地 Ollama | 自动降级 |

---

## 🔧 配置说明

### Ollama 配置

```bash
# 启动 Ollama 服务（默认端口 11434）
ollama serve

# 拉取模型
ollama pull llama3:8b
ollama pull qwen2:7b
ollama pull deepseek-r1:7b
```

### DeepSeek API 配置

1. 访问 https://platform.deepseek.com 注册
2. 获取 API Key（免费额度：2M tokens/天）
3. 设置环境变量：

```bash
export DEEPSEEK_API_KEY="sk-你的Key"
```

---

## 📂 项目结构

```
ollama-toolkit/
├── README.md              # 本文件
├── LICENSE               # MIT 许可证
├── gguf-to-ollama.py    # GGUF 转换脚本（Python）
├── gguf-to-ollama.bat   # GGUF 转换脚本（Windows 批处理）
└── hybrid_ai.py         # 混合 AI 调用脚本
```

---

## 💡 使用技巧

### 技巧 1：批量转换 GGUF 模型

```bash
# 遍历 models/ 目录下所有 .gguf 文件
for file in models/*.gguf; do
  name=$(basename "$file" .gguf)
  python gguf-to-ollama.py --input "$file" --name "$name"
  ollama create "$name" -f Modelfiles/"$name".Modelfile
done
```

### 技巧 2：混合 AI 的 system prompt 优化

```python
# 在 hybrid_ai.py 中修改 SYSTEM_PROMPT
SYSTEM_PROMPT = """你是一个专业的技术助手，
专注于编程、AI、自动化领域。
回答简洁，代码加注释。"""
```

### 技巧 3：本地模型量化选择

| 量化等级 | 文件大小 | 质量 | 内存占用 | 推荐场景 |
|----------|----------|------|----------|------------|
| Q4_0 | 最小 | 中等 | 低 | 日常使用 |
| Q5_K_M | 中等 | 较好 | 中 | 推荐 |
| Q8_0 | 最大 | 最佳 | 高 | 高质量需求 |
| FP16 | 极大 | 完美 | 极高 | 训练/微调 |

---

## 🐛 常见问题

### Q1: Ollama 服务连接失败？

```bash
# 检查 Ollama 是否运行
curl <ADDRESS_REMOVED>

# 如果没运行，启动它
ollama serve
```

### Q2: DeepSeek API 调用失败？

```bash
# 检查 API Key 是否设置
echo $DEEPSEEK_API_KEY

# 测试 API 连接
curl -H "<SECRET_REMOVED> $DEEPSEEK_API_KEY" \
  https://api.deepseek.com/user/balance
```

### Q3: GGUF 转换后模型无法加载？

检查 Modelfile 中的路径是否正确：

```bash
# 查看生成的 Modelfile
cat Modelfiles/your-model.Modelfile

# 确保 FROM 路径是绝对路径
FROM /absolute/path/to/your-model.gguf
```

---

## 🔗 相关资源

- [Ollama 官网](https://ollama.com)
- [Ollama 模型库](https://ollama.com/library)
- [DeepSeek API 文档](https://platform.deepseek.com/docs)
- [GGUF 格式说明](https://github.com/ggerganov/ggml/blob/master/docs/gguf.md)

---

## 📄 许可证

MIT License — 可自由使用、修改、分发。

---

## 🙏 致谢

- [Ollama](https://github.com/ollama/ollama) — 本地 LLM 运行时
- [DeepSeek](https://www.deepseek.com) — 国产优秀大模型
- [llama.cpp](https://github.com/ggerganov/llama.cpp) — GGUF 格式标准

---

## 📮 联系方式

- GitHub: [@smiling66652](https://github.com/smiling66652)
- Email: 2240678683@qq.com

---

<div align="center">

**⭐ 如果这个项目对你有帮助，请给我一个 Star！**

</div>
