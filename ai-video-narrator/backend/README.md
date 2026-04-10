# AI视频解说生成器后端

## 安装

```bash
pip install -r requirements.txt
```

## 运行

```bash
uvicorn app.main:app --reload
```

## 环境变量

创建 `.env` 文件：

```env
# OpenAI
OPENAI_API_KEY=sk-xxx

# Azure TTS
AZURE_TTS_KEY=xxx
AZURE_TTS_REGION=eastasia

# 阿里云OSS
OSS_ACCESS_KEY_ID=xxx
OSS_ACCESS_KEY_SECRET=xxx
OSS_BUCKET_NAME=xxx
OSS_ENDPOINT=xxx

# 数据库
DATABASE_URL=sqlite:///./data.db
```