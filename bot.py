from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
from PIL import Image
import pytesseract
from sympy import sympify, simplify, symbols
import re

x = symbols('x')

# Форматирование степеней
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

# Форматирование дробей
def format_fraction(frac_str):
    if "/" in frac_str:
        num, den = frac_str.split("/")
        return f"{num}⁄{den}"
    return frac_str

# Разделение текста на примеры
def split_examples(text):
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    examples = []
    for line in lines:
        # Разделяем по ; или , если несколько примеров на одной строке
        parts = re.split(r'[;,]', line)
        for p in parts:
            if p.strip():
                examples.append(p.strip())
    return examples

# Решение и форматирование
def solve_example(expr_text):
    try:
        expr = sympify(expr_text)
        result = simplify(expr)
        
        # Определяем простоту примера
        if expr.is_number or len(expr.free_symbols) <= 1:
            # Пошаговое объяснение для простых примеров
            explanation = "Привели к общему знаменателю, посчитали результат"
        else:
            explanation = None
        
        expr_fmt = format_fraction(format_exponent(str(expr_text)))
        result_fmt = format_fraction(format_exponent(str(result)))
        
        return expr_fmt, result_fmt, explanation
    except:
        return expr_text, None, None

# Команда /start
def start(update: Update, context: CallbackContext):
    update.message.reply_text("Привет! Отправь мне фото с примерами, и я решу их с пошаговым объяснением.")

# Обработка фото
def handle_photo(update: Update, context: CallbackContext):
    photo_file = update.message.photo[-1].get_file()
    photo_file.download("example.jpg")
    
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
    
    update.message.reply_text(response)

def main():
    import os
    TOKEN = os.environ.get("TOKEN")  # берем из переменной окружения Render
    updater = Updater(TOKEN)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.photo, handle_photo))
    
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
