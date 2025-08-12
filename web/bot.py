import os
import django
import logging
from datetime import timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes

# Inicializa Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'web.settings')  # Ajustá el nombre del proyecto si no es "core"
os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"
django.setup()

from accounts.models import CustomUser

from django.utils import timezone

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Verifica si el chat_id está autorizado
def get_user_from_chat(chat_id):
    try:
        return CustomUser.objects.get(telegram_chat_id=chat_id)
    except CustomUser.DoesNotExist:
        return None

# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user = get_user_from_chat(chat_id)

    if user:
        await update.message.reply_text(f"Hola {user.get_full_name()} 👷‍♂️\nUsá /tareas para ver tus tareas o /nueva_tarea para crear una.")
    else:
        await update.message.reply_text("🚫 No estás autorizado. Agregá tu chat ID en tu perfil desde la web.")

# /tareas - FUNCIÓN DESHABILITADA (app worklog eliminada)
async def tareas(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🚫 Función deshabilitada - app worklog eliminada")

# Muestra detalle al tocar una tarea - FUNCIÓN DESHABILITADA (app worklog eliminada)
async def callback_query_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("🚫 Función deshabilitada - app worklog eliminada")

# Main
def main():
    TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    if not TOKEN:
        raise Exception("TELEGRAM_BOT_TOKEN no definido en .env")

    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("tareas", tareas))
    application.add_handler(telegram.ext.CallbackQueryHandler(callback_query_handler))

    logger.info("Bot iniciado...")
    application.run_polling()

if __name__ == "__main__":
    main()
