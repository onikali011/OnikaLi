# ÖNIKA LI Bot - FastAPI版本

## 🎸 四层AI融合体 · Vercel部署

### 文件结构
```
OnikaLi/
├── api/
│   └── index.py          # FastAPI主程序
├── requirements.txt      # Python依赖
├── vercel.json          # Vercel配置
├── setup_webhook.py     # Webhook设置脚本
└── README.md
```

### 部署步骤

#### 1. 上传文件到GitHub
```bash
git add .
git commit -m "迁移到FastAPI + Vercel"
git push
```

#### 2. Vercel部署
- 访问 https://vercel.com
- 导入 `onikali011/OnikaLi`
- 添加环境变量：
  - `TELEGRAM_TOKEN` - Telegram Bot Token
  - `MOONSHOT_API_KEY` - Kimi API Key
  - `ANTHROPIC_API_KEY` - Claude API Key（可选）
- 点击 **Deploy**

#### 3. 设置Webhook
```bash
pip install requests
python setup_webhook.py
```

#### 4. 测试
Telegram发送 `/start`

### API端点
- `GET /` - 健康检查
- `POST /` - Telegram Webhook
- `GET /health` - 状态检查

### 特性
- ✅ FastAPI高性能
- ✅ 异步处理
- ✅ 自动故障转移
- ✅ Layer 1-4 AI融合
