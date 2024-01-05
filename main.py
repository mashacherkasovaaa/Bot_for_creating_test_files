# pip install python-telegram-bot
# pip install Pillow
# pip install lorem-text

from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (CallbackContext, CommandHandler, ConversationHandler,
                          MessageHandler, Filters, Updater)
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

import logging
from PIL import Image, ImageDraw, ImageFont
from lorem_text import lorem

# Установка уровня логирования
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

logger = logging.getLogger(__name__)

CHOOSING, IMAGE, TEXT = range(3)

reply_keyboard = [['Изображение', 'Текстовый файл']]
markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True)

def start(update: Update, context: CallbackContext) -> int:
    update.message.reply_text(
        "Привет! Я бот для создания тестовых файлов. Что вы хотите создать?",
        reply_markup=markup,
    )

    return CHOOSING

def error(update: Update, context: CallbackContext) -> int:
    update.message.reply_text(
        "Неправильный ввод. Пожалуйста, выберите из предложенных вариантов."
    )
    return CHOOSING

def cm_to_pixel(cm, dpi=96):
    return int(cm * dpi / 2.54)

def image_choice(update: Update, context: CallbackContext) -> int:
    user = update.message.from_user
    context.user_data['choice'] = update.message.text
    logger.info("Выбран вариант: %s", context.user_data['choice'])

    update.message.reply_text(
        f"Отлично, вы выбрали {context.user_data['choice'].lower()}. Теперь введите ширину и длину изображения в сантиметрах, разделяя значения пробелом.",
        reply_markup=ReplyKeyboardRemove(),
    )

    return IMAGE

def text_choice(update: Update, context: CallbackContext) -> int:
    user = update.message.from_user
    context.user_data['choice'] = update.message.text
    logger.info("Выбран вариант: %s", context.user_data['choice'])

    update.message.reply_text(
        f"Отлично, вы выбрали {context.user_data['choice'].lower()}. Теперь введите вес текстового файла в килобайтах.",
        reply_markup=ReplyKeyboardRemove(),
    )

    return TEXT

def create_test_image(update: Update, file_path, width_cm, height_cm):
    # Стандартное значение DPI (точек на дюйм)
    dpi = 96

    # Преобразование сантиметров в пиксели
    width_px = cm_to_pixel(width_cm)
    height_px = cm_to_pixel(height_cm)

    # Создание изображения
    image = Image.new("RGB", (width_px, height_px), "white")

    # Рисование текста на изображении
    draw = ImageDraw.Draw(image)
    text = f"Width: {width_cm} cm, Height: {height_cm} cm"
    font = ImageFont.load_default()
    text_width, text_height = draw.textsize(text, font)
    draw.text(((width_px - text_width) / 2, (height_px - text_height) / 2), text, font=font, fill="black")

    # Сохранение изображения
    image.save(file_path, format="png")

    # Отправка изображения пользователю
    update.message.reply_photo(open(file_path, 'rb'))

def create_test_file(update: Update, file_path, file_size_kb):
    # Генерация текста lorem ipsum
    lorem_text = lorem.paragraphs(5)

    # Расчет количества символов, необходимого для указанного размера файла
    char_count = int(file_size_kb * 1024 / 2)  # Предполагаем, что в среднем один символ кодируется двумя байтами

    # Обрезка текста до нужного количества символов
    trimmed_text = lorem_text[:char_count]

    # Сохранение текста в файл
    with open(file_path, "w", encoding="utf-8") as file:
        file.write(trimmed_text)

    # Отправка текстового файла пользователю
    update.message.reply_document(open(file_path, 'rb'))

def done(update: Update, context: CallbackContext) -> int:
    user = update.message.from_user
    logger.info("Введены данные: %s", update.message.text)

    try:
        if context.user_data['choice'] == 'Изображение':
            width, height = map(float, update.message.text.split())
            file_path = f"test_image_{int(width)}x{int(height)}.png"
            create_test_image(update, file_path, width, height)
        elif context.user_data['choice'] == 'Текстовый файл':
            file_size_kb = float(update.message.text)
            file_path = f"test_file_{int(file_size_kb)}KB.txt"
            create_test_file(update, file_path, file_size_kb)
        else:
            update.message.reply_text("Ошибка. Пожалуйста, попробуйте еще раз.")
            return CHOOSING

        update.message.reply_text(f"Тестовый файл создан. Прикрепляю к сообщению.")
    except ValueError:
        update.message.reply_text("Ошибка. Пожалуйста, введите корректные значения.")
        return CHOOSING

    return ConversationHandler.END

def cancel(update: Update, context: CallbackContext) -> int:
    user = update.message.from_user
    update.message.reply_text(
        f"Отменено. Если вы хотите начать заново, воспользуйтесь командой /start.",
        reply_markup=markup,
    )

    return ConversationHandler.END

def main() -> None:
    # Создаем Updater и передаем ему токен вашего бота
    updater = Updater("6848394567:AAGegq3X34b50eA142Kz9lwBwCDxATfQVUM")

    # Получаем из него диспетчер
    dp = updater.dispatcher

    # Создаем ConversationHandler и регистрируем его в диспетчере
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            CHOOSING: [MessageHandler(Filters.regex('^(Изображение|Текстовый файл)$'), image_choice)],
            IMAGE: [MessageHandler(Filters.text & ~Filters.command, done)],
            TEXT: [MessageHandler(Filters.text & ~Filters.command, done)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    dp.add_handler(conv_handler)

    # Запускаем бота
    updater.start_polling()

    # Останавливаем бота при нажатии Ctrl+C
    updater.idle()

if __name__ == '__main__':
    main()