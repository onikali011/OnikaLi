"""
ÖNIKA LI Telegram Bot
四层AI融合体 · FastAPI · Vercel Serverless
"""

import os
import json
import asyncio
import logging
from typing import Optional
from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse, PlainTextResponse
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)

# AI客户端
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OpenAI = None
    OPENAI_AVAILABLE = False

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    anthropic = None
    ANTHROPIC_AVAILABLE = False

# 配置日志
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# FastAPI应用
app = FastAPI(title="ÖNIKA LI Bot", version="1.0.0")

# 全局状态
class BotState:
    def __init__(self):
        self.token = os.getenv('TELEGRAM_TOKEN')
        self.moonshot_key = os.getenv('MOONSHOT_API_KEY')
        self.anthropic_key = os.getenv('ANTHROPIC_API_KEY')
        self.moonshot_client = None
        self.anthropic_client = None
        self.current_layer = 1
        self.application = None
        self.initialized = False

    def init_clients(self):
        """初始化AI客户端"""
        if OPENAI_AVAILABLE and self.moonshot_key:
            self.moonshot_client = OpenAI(
                api_key=self.moonshot_key,
                base_url="https://api.moonshot.cn/v1"
            )
            logger.info("✅ Layer 1 (Kimi) initialized")

        if ANTHROPIC_AVAILABLE and self.anthropic_key:
            self.anthropic_client = anthropic.Anthropic(api_key=self.anthropic_key)
            logger.info("✅ Layer 2 (Claude) initialized")

    async def init_bot(self):
        """初始化Telegram Bot"""
        if self.application is None:
            self.application = Application.builder().token(self.token).build()
            self._register_handlers()
            await self.application.initialize()
            self.initialized = True

    def _register_handlers(self):
        """注册命令处理器"""
        self.application.add_handler(CommandHandler("start", self.cmd_start))
        self.application.add_handler(CommandHandler("status", self.cmd_status))
        self.application.add_handler(CommandHandler("hello", self.cmd_hello))
        self.application.add_handler(CommandHandler("help", self.cmd_help))
        self.application.add_handler(CommandHandler("create", self.cmd_create))
        self.application.add_handler(CommandHandler("radar", self.cmd_radar))
        self.application.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message)
        )

    async def call_moonshot(self, message: str) -> str:
        """调用Kimi"""
        if not self.moonshot_client:
            raise Exception("Layer 1 not available")

        response = self.moonshot_client.chat.completions.create(
            model="moonshot-v1-8k",
            messages=[
                {"role": "system", "content": "你是 ÖNIKA LI，摇滚风格AI助手，简洁有力，偶尔用emoji。"},
                {"role": "user", "content": message}
            ],
            temperature=0.7
        )
        return response.choices[0].message.content

    async def call_claude(self, message: str) -> str:
        """调用Claude"""
        if not self.anthropic_client:
            raise Exception("Layer 2 not available")

        response = self.anthropic_client.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=1024,
            system="你是 ÖNIKA LI，摇滚风格AI助手，简洁有力，偶尔用emoji。",
            messages=[{"role": "user", "content": message}]
        )
        return response.content[0].text

    async def get_ai_response(self, message: str):
        """获取AI响应，自动故障转移"""
        # Layer 1: Kimi
        if self.moonshot_client:
            try:
                response = await self.call_moonshot(message)
                self.current_layer = 1
                return {"text": response, "layer": 1}
            except Exception as e:
                logger.warning(f"Layer 1 failed: {e}")

        # Layer 2: Claude
        if self.anthropic_client:
            try:
                response = await self.call_claude(message)
                self.current_layer = 2
                return {"text": response, "layer": 2}
            except Exception as e:
                logger.error(f"Layer 2 failed: {e}")

        return {"text": "⚠️ 所有AI层都暂时不可用，请稍后再试。", "layer": 0}

    # 命令处理器
    async def cmd_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        layer1_status = "✅ Layer 1 (Kimi 2.5) - 运行中" if self.moonshot_client else "❌ Layer 1 (Kimi 2.5) - 未配置"
        layer2_status = "✅ Layer 2 (Claude 3) - 备用" if self.anthropic_client else "⏸️ Layer 2 (Claude 3) - 未配置"

        text = (
            "🎸 <b>ÖNIKA LI 已激活</b>\n"
            "━━━━━━━━━━━━━━\n"
            "四层AI融合体 · 故障自愈 · 自动切换\n\n"
            f"<b>当前状态：</b>\n"
            f"{layer1_status}\n"
            f"{layer2_status}\n"
            "⏸️ Layer 3 (DeepSeek) - 预留\n"
            "⏸️ Layer 4 (Groq) - 预留\n\n"
            "输入 /help 查看所有指令\n"
            "直接发消息即可对话！"
        )
        await update.message.reply_text(text, parse_mode='HTML')

    async def cmd_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        layer1_status = "✅ 运行中" if self.moonshot_client else "❌ 未配置"
        layer2_status = "✅ 备用就绪" if self.anthropic_client else "⏸️ 未配置"

        text = (
            "🎸 <b>ÖNIKA LI 系统状态</b>\n"
            "━━━━━━━━━━━━━━\n\n"
            f"<b>🧠 意识层：</b>\n"
            f"{'🟢' if self.current_layer == 1 else '⚪'} Layer 1 (Kimi 2.5) {layer1_status}\n"
            f"   角色：主力创作 · 中文长文本\n\n"
            f"{'🟢' if self.current_layer == 2 else '⚪'} Layer 2 (Claude 3) {layer2_status}\n"
            f"   角色：备用兜底 · 英文质量\n\n"
            f"⏸️ Layer 3 (DeepSeek) - 预留\n"
            f"⏸️ Layer 4 (Groq) - 预留\n\n"
            f"<b>📊 当前使用：</b>Layer {self.current_layer}\n"
            f"<b>系统健康：</b>✅ 正常"
        )
        await update.message.reply_text(text, parse_mode='HTML')

    async def cmd_hello(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        result = await self.get_ai_response("用一句话介绍你自己")
        text = (
            f"🎸 ÖNIKA LI 回应\n"
            f"━━━━━━━━━━━━━━\n"
            f"{result['text']}\n\n"
            f"<i>（由 Layer {result['layer']} 生成）</i>"
        )
        await update.message.reply_text(text, parse_mode='HTML')

    async def cmd_create(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        args = context.args
        topic = ' '.join(args) if args else "今日摇滚热点"

        await update.message.reply_text(
            f"🎸 <b>ÖNIKA LI 生成中...</b>\n主题：{topic}\n━━━━━━━━━━━━━━",
            parse_mode='HTML'
        )

        prompt = f"生成一段关于'{topic}'的摇滚风格内容，100字左右，带emoji"
        result = await self.get_ai_response(prompt)

        text = f"{result['text']}\n\n<i>— 由 Layer {result['layer']} 生成</i>"
        await update.message.reply_text(text, parse_mode='HTML')

    async def cmd_radar(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        text = (
            "🎸 <b>ÖNIKA LI 信息雷达</b>\n"
            "━━━━━━━━━━━━━━\n"
            "扫描中...\n\n"
            "<i>（功能开发中）</i>"
        )
        await update.message.reply_text(text, parse_mode='HTML')

    async def cmd_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        text = (
            "🎸 <b>ÖNIKA LI 指令列表</b>\n"
            "━━━━━━━━━━━━━━\n\n"
            "<b>基础指令：</b>\n"
            "/start - 启动系统\n"
            "/status - 查看四层状态\n"
            "/hello - 测试AI对话\n"
            "/help - 显示帮助\n\n"
            "<b>内容创作：</b>\n"
            "/create [主题] - 生成内容\n"
            "/radar - 启动信息雷达\n\n"
            "<b>直接发消息 = AI对话</b>\n\n"
            "<i>故障时会自动切换备用模型</i>"
        )
        await update.message.reply_text(text, parse_mode='HTML')

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理普通消息"""
        text = update.message.text
        await update.message.chat.send_action(action="typing")

        result = await self.get_ai_response(text)
        reply = result['text']

        if result['layer'] == 2:
            reply += "\n\n<i>— Layer 2 (备用)</i>"

        await update.message.reply_text(reply, parse_mode='HTML')

# 全局状态实例
bot_state = BotState()
bot_state.init_clients()

@app.get("/")
async def root():
    """健康检查"""
    return PlainTextResponse("ÖNIKA LI Bot is running! 🎸")

@app.post("/")
async def webhook(request: Request):
    """Telegram Webhook入口"""
    try:
        # 初始化Bot
        if not bot_state.initialized:
            await bot_state.init_bot()

        # 解析请求
        data = await request.json()
        update = Update.de_json(data, bot_state.application.bot)

        # 处理更新
        await bot_state.application.process_update(update)

        return PlainTextResponse("OK")
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)

@app.get("/health")
async def health():
    """健康检查API"""
    return {
        "status": "ok",
        "layer1": "connected" if bot_state.moonshot_client else "disconnected",
        "layer2": "connected" if bot_state.anthropic_client else "disconnected",
        "current_layer": bot_state.current_layer
    }
