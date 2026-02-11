"""
ÖNIKA LI Telegram Bot
四层AI融合体 · 统一入口
适配 python-telegram-bot 20.7
"""

import os
import logging
import asyncio
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)

# AI 客户端
try:
    from openai import OpenAI  # Moonshot 兼容 OpenAI 格式
    ANTHROPIC_AVAILABLE = True
    try:
        import anthropic
    except ImportError:
        ANTHROPIC_AVAILABLE = False
        logging.warning("Anthropic not installed, Claude layer disabled")
except ImportError:
    OpenAI = None
    ANTHROPIC_AVAILABLE = False
    logging.warning("OpenAI not installed, AI layers disabled")

# 配置日志
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


class OnikaliBot:
    """
    ÖNIKA LI Bot 核心
    Layer 1: Kimi (主模型)
    Layer 2: Claude (备用)
    Layer 3-4: 预留
    """

    def __init__(self):
        self.token = os.getenv('TELEGRAM_TOKEN')
        self.chat_id = os.getenv('TELEGRAM_CHAT_ID')
        
        # API Keys
        self.moonshot_key = os.getenv('MOONSHOT_API_KEY')
        self.anthropic_key = os.getenv('ANTHROPIC_API_KEY')
        
        # 初始化 AI 客户端
        self.moonshot_client = None
        self.anthropic_client = None
        self.current_layer = 1
        
        if OpenAI and self.moonshot_key:
            self.moonshot_client = OpenAI(
                api_key=self.moonshot_key,
                base_url="https://api.moonshot.cn/v1"
            )
            logger.info("✅ Layer 1 (Kimi) initialized")
        
        if ANTHROPIC_AVAILABLE and self.anthropic_key:
            self.anthropic_client = anthropic.Anthropic(api_key=self.anthropic_key)
            logger.info("✅ Layer 2 (Claude) initialized")

        # v20: 使用 Application
        self.application = Application.builder().token(self.token).build()

        # 注册命令
        self._register_handlers()

    def _register_handlers(self):
        """注册所有处理器"""
        self.application.add_handler(CommandHandler("start", self.cmd_start))
        self.application.add_handler(CommandHandler("status", self.cmd_status))
        self.application.add_handler(CommandHandler("hello", self.cmd_hello))
        self.application.add_handler(CommandHandler("help", self.cmd_help))
        self.application.add_handler(CommandHandler("create", self.cmd_create))
        self.application.add_handler(CommandHandler("radar", self.cmd_radar))

        # 普通消息
        self.application.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_ai_message)
        )

        # 错误处理
        self.application.add_error_handler(self.error_handler)

    async def _call_moonshot(self, message: str) -> str:
        """调用 Kimi/Moonshot"""
        if not self.moonshot_client:
            raise Exception("Layer 1 not available")
        
        try:
            response = self.moonshot_client.chat.completions.create(
                model="moonshot-v1-8k",
                messages=[
                    {"role": "system", "content": "你是 ÖNIKA LI，一个摇滚风格的AI助手，说话简洁有力，偶尔用emoji。"},
                    {"role": "user", "content": message}
                ],
                temperature=0.7
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Layer 1 error: {e}")
            raise

    async def _call_claude(self, message: str) -> str:
        """调用 Claude"""
        if not self.anthropic_client:
            raise Exception("Layer 2 not available")
        
        try:
            response = self.anthropic_client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=1024,
                system="你是 ÖNIKA LI，一个摇滚风格的AI助手，说话简洁有力，偶尔用emoji。",
                messages=[{"role": "user", "content": message}]
            )
            return response.content[0].text
        except Exception as e:
            logger.error(f"Layer 2 error: {e}")
            raise

    async def _get_ai_response(self, message: str) -> tuple[str, int]:
        """
        获取 AI 响应，自动故障转移
        返回: (响应文本, 使用的层数)
        """
        # Layer 1: Kimi (主模型)
        if self.moonshot_client:
            try:
                response = await self._call_moonshot(message)
                self.current_layer = 1
                return response, 1
            except Exception as e:
                error_str = str(e).lower()
                # 检查是否是限额错误
                if "429" in error_str or "rate limit" in error_str or "insufficient_quota" in error_str:
                    logger.warning("Layer 1 rate limited, switching to Layer 2")
                else:
                    logger.error(f"Layer 1 failed: {e}")
        
        # Layer 2: Claude (备用)
        if self.anthropic_client:
            try:
                response = await self._call_claude(message)
                self.current_layer = 2
                return response, 2
            except Exception as e:
                error_str = str(e).lower()
                if "429" in error_str or "rate limit" in error_str:
                    logger.error("Layer 2 also rate limited")
                else:
                    logger.error(f"Layer 2 failed: {e}")
        
        # 都失败了
        return "⚠️ 所有AI层都暂时不可用，请稍后再试。", 0

    async def cmd_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """启动命令"""
        layer_status = []
        if self.moonshot_client:
            layer_status.append("✅ Layer 1 (Kimi 2.5) - 运行中")
        else:
            layer_status.append("❌ Layer 1 (Kimi 2.5) - 未配置")
            
        if self.anthropic_client:
            layer_status.append("✅ Layer 2 (Claude 3) - 备用")
        else:
            layer_status.append("⏸️ Layer 2 (Claude 3) - 未配置")
        
        welcome_text = (
            "🎸 <b>ÖNIKA LI 已激活</b>\n"
            "━━━━━━━━━━━━━━\n"
            "四层AI融合体 · 故障自愈 · 自动切换\n\n"
            "<b>当前状态：</b>\n" +
            "\n".join(layer_status) +
            "\n⏸️ Layer 3 (DeepSeek) - 预留\n"
            "⏸️ Layer 4 (Groq) - 预留\n\n"
            "输入 /help 查看所有指令\n"
            "直接发消息即可对话！"
        )
        await update.message.reply_text(welcome_text, parse_mode='HTML')

    async def cmd_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """查看四层状态"""
        layer1_status = "✅ 运行中" if self.moonshot_client else "❌ 未配置"
        layer2_status = "✅ 备用就绪" if self.anthropic_client else "⏸️ 未配置"
        
        status_text = (
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
        await update.message.reply_text(status_text, parse_mode='HTML')

    async def cmd_hello(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """测试对话"""
        # 测试 AI 是否工作
        test_response, layer = await self._get_ai_response("用一句话介绍你自己")
        
        await update.message.reply_text(
            f"🎸 ÖNIKA LI 回应\n"
            f"━━━━━━━━━━━━━━\n"
            f"{test_response}\n\n"
            f"<i>（由 Layer {layer} 生成）</i>",
            parse_mode='HTML'
        )

    async def cmd_create(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """创建内容"""
        args = context.args
        topic = ' '.join(args) if args else "今日摇滚热点"
        
        await update.message.reply_text(
            f"🎸 <b>ÖNIKA LI 生成中...</b>\n"
            f"主题：{topic}\n"
            f"━━━━━━━━━━━━━━",
            parse_mode='HTML'
        )
        
        prompt = f"生成一段关于'{topic}'的摇滚风格内容，100字左右，带emoji"
        response, layer = await self._get_ai_response(prompt)
        
        await update.message.reply_text(
            f"{response}\n\n"
            f"<i>— 由 Layer {layer} 生成</i>",
            parse_mode='HTML'
        )

    async def cmd_radar(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """启动信息雷达"""
        await update.message.reply_text(
            "🎸 <b>ÖNIKA LI 信息雷达</b>\n"
            "━━━━━━━━━━━━━━\n"
            "扫描中...\n\n"
            "<i>（功能开发中，明天接入实时数据源）</i>",
            parse_mode='HTML'
        )

    async def cmd_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """帮助信息"""
        help_text = (
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
        await update.message.reply_text(help_text, parse_mode='HTML')

    async def handle_ai_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理普通消息 - 调用AI"""
        text = update.message.text
        
        # 显示"输入中..."
        await update.message.chat.send_action(action="typing")
        
        # 获取AI响应
        response, layer = await self._get_ai_response(text)
        
        # 添加层标识（如果是备用模型）
        if layer == 2:
            response += "\n\n<i>— Layer 2 (备用)</i>"
        
        await update.message.reply_text(response, parse_mode='HTML')

    async def error_handler(self, update: object, context: ContextTypes.DEFAULT_TYPE):
        """错误处理"""
        logger.error(f"Update {update} caused error {context.error}")
        
        if update and hasattr(update, 'effective_message'):
            await update.effective_message.reply_text(
                "⚠️ ÖNIKA LI 遇到错误\n"
                "━━━━━━━━━━━━━━\n"
                "正在尝试切换至备用层..."
            )

    def run(self):
        """启动 Bot"""
        logger.info("🎸 ÖNIKA LI Bot 启动...")
        logger.info(f"Token: {self.token[:10]}..." if self.token else "No token!")
        
        self.application.run_polling()


if __name__ == "__main__":
    bot = OnikaliBot()
    bot.run()
