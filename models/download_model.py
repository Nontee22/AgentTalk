# -*- coding: utf-8 -*-
"""下载 embedding 模型到本地目录。

用法：
    set HF_ENDPOINT=https://hf-mirror.com
    python models/download_model.py
"""

import os

os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")

from sentence_transformers import SentenceTransformer

MODEL_NAME = "BAAI/bge-small-zh-v1.5"
SAVE_DIR = os.path.join(os.path.dirname(__file__), "bge-small-zh-v1.5")

print(f"正在下载模型: {MODEL_NAME}")
print(f"保存路径: {SAVE_DIR}")

model = SentenceTransformer(MODEL_NAME)
model.save(SAVE_DIR)

# 验证
vec = model.encode("测试文本", normalize_embeddings=True)
print(f"维度: {len(vec)}")
print("下载完成!")
