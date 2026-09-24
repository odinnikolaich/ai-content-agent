from __future__ import annotations

import asyncio
import os
from pathlib import Path

from dotenv import load_dotenv
from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

from pipeline.service import generate_video

ROOT=Path(__file__).resolve().parent
load_dotenv(ROOT/".env")
TOKEN=os.getenv("TELEGRAM_BOT_TOKEN","").strip()
DURATION=int(os.getenv("TELEGRAM_VIDEO_DURATION","50"))
MAX_PROMPT=int(os.getenv("TELEGRAM_MAX_PROMPT_LENGTH","1200"))
ALLOWED={x.strip() for x in os.getenv("TELEGRAM_ALLOWED_USER_IDS","").split(",") if x.strip()}
queue: asyncio.Queue[tuple[Update,str]] = asyncio.Queue()

def allowed(update: Update) -> bool:
    return not ALLOWED or str(update.effective_user.id) in ALLOWED

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if allowed(update):
        await update.message.reply_text("Готов. Отправьте тему или промпт — агент создаст вертикальное видео 43–60 секунд и пришлёт MP4 сюда.")

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if allowed(update):
        await update.message.reply_text(f"В очереди сейчас: {queue.qsize()}")

async def handle_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not allowed(update): return
    prompt=(update.message.text or "").strip()
    if not prompt: return
    if len(prompt)>MAX_PROMPT:
        await update.message.reply_text(f"Промпт слишком длинный. Максимум {MAX_PROMPT} символов.")
        return
    await queue.put((update,prompt))
    await update.message.reply_text(f"Принял. Позиция в очереди: {queue.qsize()}.")

async def worker(app: Application):
    while True:
        update,prompt=await queue.get()
        chat=update.effective_chat
        msg=await chat.send_message("⏳ Запускаю генерацию…")
        try:
            loop=asyncio.get_running_loop()
            def run():
                stages=[]
                def cb(s): stages.append(s)
                path=generate_video(prompt,DURATION,progress=cb)
                return path,stages
            path,stages=await asyncio.to_thread(run)
            for stage in stages:
                await msg.edit_text(stage)
            await msg.edit_text("📤 Отправляю готовый MP4…")
            await chat.send_action(ChatAction.UPLOAD_VIDEO)
            with path.open("rb") as f:
                await chat.send_video(video=f,caption=f"Готово: {prompt[:900]}",supports_streaming=True)
            await msg.delete()
        except Exception as exc:
            await msg.edit_text(f"❌ Ошибка генерации: {type(exc).__name__}: {exc}")
        finally:
            queue.task_done()

async def post_init(app: Application):
    app.create_task(worker(app))

def main():
    if not TOKEN:
        raise SystemExit("TELEGRAM_BOT_TOKEN is not set in .env")
    app=Application.builder().token(TOKEN).post_init(post_init).build()
    app.add_handler(CommandHandler("start",start))
    app.add_handler(CommandHandler("status",status))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND,handle_prompt))
    print("Telegram bot is running. Send a text prompt to the bot.")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__=="__main__":
    main()
