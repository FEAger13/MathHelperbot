import os
import re
from PIL import Image
import pytesseract
from sympy import sympify, simplify, symbols
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)

x = symbols('x')

# --- Форматирование степеней ---
def format_exponent(expr_str):
    superscript_map = {"0":"⁰","1":"¹","2":"²","3":"³","4":"⁴","5":"⁵",
                       "6":"⁶","7":"⁷","8":"⁸","9":"⁹"}
    result = ""
    i = 0
    while i < len(expr_str):
        if expr_str[i] == "^" and i+1 < len(expr_str):
            exp = expr_str[i+1]
            result += superscript_map.get(exp, exp)
            i += 2
        else:
            result += expr_str[i]
            i += 1
    return result

# --- Форматирование дробей ---
def format_fraction(frac_str):
    if "/" in frac_str:
        num, den = frac_str.split("/")
        return f"{num}⁄{den}"
    return frac_str

# --- Разделение текста на примеры ---
def split_examples(text):
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    examples = []
    for line in lines:
        parts = re.split(r'[;,]', line)
        for p in parts:
            if p.strip():
                examples.append(p.strip())
    return examples

# --- Решение и форматирование примера ---
def solve_example(expr_text):
    try:
        expr = sympify(expr_text)
        result = simplify(expr)
        if expr.is_number or len(expr.free_symbols) <= 1:
            explanation = "Привели к общему знаменателю, посчитали результат"
        else:
            explanation = None
        expr_fmt = format_fraction(format_exponent(str(expr_text)))
        result_fmt = format_fraction(format_exponent(str(result)))
        return expr_fmt, result_fmt, explanation
    except:
        return expr_text, None, None

# --- Команда /start ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! Отправь мне фото с примерами, и я решу их с пошаговым объяснением."
    )

# --- Обработка фото ---
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    photo_file = await update.message.photo[-1].get_file()
    await photo_file.download_to_drive("example.jpg")

    text = pytesseract.image_to_string(Image.open("example.jpg"))
    examples = split_examples(text)

    response = ""
    for i, ex in enumerate(examples, start=1):
        expr_fmt, result_fmt, explanation = solve_example(ex)
        response += f"{i} пример:\nПример: {expr_fmt}\n"
        if result_fmt:
            response += f"Решение: {result_fmt}\n"
        if explanation:
            response += f"Пошаговое объяснение: {explanation}\n"
        response += f"Ответ: {result_fmt if result_fmt else 'Не удалось решить'}\n\n"

    await update.message.reply_text(response)

# --- Основной запуск бота ---
if __name__ == "__main__":
    TOKEN = os.environ.get("TOKEN")
    PORT = int(os.environ.get("PORT", 10000))
    WEBHOOK_URL = os.environ.get("WEBHOOK_URL")

    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))

    print("Бот запущен...")

    if WEBHOOK_URL:
        print(f"Запуск через Webhook на {WEBHOOK_URL}")
        app.run_webhook(
            listen="0.0.0.0",
            port=PORT,
            webhook_url=WEBHOOK_URL
        )
    else:
        print("WEBHOOK_URL не задан, запускаем через polling")
        app.run_polling()
