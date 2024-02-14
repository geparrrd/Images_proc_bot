import os
import telebot
from telebot import types
from random import choice
from PIL import Image
import re


class User:
    users = dict()
    def __init__(self, chat_id, first_name):
        self.chat_id = chat_id
        self.first_name = first_name
        self.actions = {}


with open('token.txt', encoding='utf-8') as f:
    token = f.read().rstrip()  # Токен

bot = telebot.TeleBot(token)


def jpg2webp(jpg_file, path):
    '''Конвертирует изображение формата jpg в формат webp'''
    new_file = jpg_file.replace('jpg', 'webp')
    with Image.open(path + jpg_file) as f:
        f = f.convert('RGB')
        f.save(path + new_file, 'webp')
    return new_file

def get_webp_images(path):
    '''Возвращает список WEBP-изображений'''
    list_webp = [file for file in os.listdir(path) if file.endswith('.webp')]

    for jpg_file in os.listdir(path):
        if jpg_file.endswith('.jpg'):
            webp_file = jpg2webp(jpg_file, path)
            list_webp.append(webp_file)
            if os.path.exists(path + jpg_file):
                os.remove(path + jpg_file)
    return list_webp

def getsticker(path):
    '''Возвращает рандомный стикер из списка'''
    cash = get_webp_images(path)
    return path + choice(cash)


def download_file(bot, file_id, orig_name=None, folder=''):
    '''Скачивание файла, который прислал пользователь'''
    file_info = bot.get_file(file_id)
    downloaded_file = bot.download_file(file_info.file_path)
    if orig_name is not None:
        point_i = orig_name.rfind('.')
        filename = f'{folder}/{orig_name[:point_i]}_edited{orig_name[point_i:]}'
    else:
        filename = file_id + file_info.file_path
        filename = filename.replace('/', '_')
        filename = f'{folder}/{filename}'

    with open(filename, 'wb') as f:
        f.write(downloaded_file)
    print(os.path.getsize(filename))
    return filename


@bot.message_handler(commands=['start'])
def start(message):
    '''Задаёт действия при нажатии на start'''

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton('Получить стикер')
    btn2 = types.KeyboardButton('Задать вопрос')
    markup_inline = types.InlineKeyboardMarkup()
    btn3 = types.InlineKeyboardButton(text='Обработка изображений', callback_data='process_photo')
    markup.add(btn1, btn2)
    markup_inline.add(btn3)
    if message.text == '/start':
        send_text = f'Привет, {message.chat.first_name}!'
    else:
        width, height = User.users[message.chat.id].actions.get('size', (None, None))
        send_text = f'Держи документы.\nРазмер: {width}x{height} px. DPI: 300'
    User.users[message.chat.id] = User(message.chat.id, message.chat.first_name)
    bot.send_message(message.chat.id, send_text, reply_markup=markup)
    bot.send_message(message.chat.id, text='Выбери действие:', reply_markup=markup_inline)


@bot.callback_query_handler(func=lambda call: True)
def inline_keyboard(call):
    '''Функционал inline-клавиатуры'''
    if call.data in ('back_1', 'process_photo'):
        markup1 = types.InlineKeyboardMarkup(row_width=2)
        crop_btn = types.InlineKeyboardButton('Обрезать фото', callback_data='crop')
        add_field_btn = types.InlineKeyboardButton('Добавить поля', callback_data='field_add')
        markup1.add(crop_btn, add_field_btn)
        print('test')
        folder_name = f'images_of_{call.message.chat.id}'
        if call.data != 'back_1' and not os.path.exists(folder_name):
            os.mkdir(folder_name)
        bot.edit_message_text(chat_id=User.users[call.message.chat.id].chat_id, message_id=call.message.message_id,
                              text='Выбери действие:', reply_markup=markup1)
    if call.data in ('crop', 'field_add', 'back_2'):
        markup2 = types.InlineKeyboardMarkup(row_width=2)
        size_btn1 = types.InlineKeyboardButton('1205х1795', callback_data='size_1')
        size_btn2 = types.InlineKeyboardButton('1795х2398', callback_data='size_2')
        size_btn3 = types.InlineKeyboardButton('Свой размер', callback_data='custom_size')
        back_btn = types.InlineKeyboardButton('Назад', callback_data='back_1')
        markup2.add(size_btn1, size_btn2, size_btn3, back_btn)
        if call.data != 'back_2':
            User.users[call.message.chat.id].actions['action'] = call.data
            print(User.users[call.message.chat.id].actions)

        bot.edit_message_text(chat_id=User.users[call.message.chat.id].chat_id, message_id=call.message.message_id,
                              text='Выбери размер:', reply_markup=markup2)

    markup3 = types.InlineKeyboardMarkup()
    btn = types.InlineKeyboardButton('Назад', callback_data='back_2')
    markup3.add(btn)

    if call.data in ('size_1', 'size_2'):
        User.users[call.message.chat.id].actions['size'] = (1205, 1795) if call.data == 'size_1' else (1795, 2398)
        print(User.users[call.message.chat.id].actions)
        bot.edit_message_text(chat_id=User.users[call.message.chat.id].chat_id, message_id=call.message.message_id,
                              text='Загрузи изображения как <b>документы</b>', reply_markup=markup3, parse_mode='HTML')
        send_done_mes(call.message)
    elif call.data == 'custom_size':
        bot.edit_message_text(chat_id=User.users[call.message.chat.id].chat_id, message_id=call.message.message_id,
                              text='Введи размеры изображения через пробел', reply_markup=markup3)


def send_done_mes(message):
    '''Отправляет сообщение и выдаёт кнопку "Готово"'''
    markup4 = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup4.row('Готово')
    arrow = u"\u21D3"
    bot.send_message(message.chat.id, f'Затем нажми "Готово"\n{" " * 7}{arrow * 10}{" " * 7}',
                     reply_markup=markup4)


def send_load_mes(message):
    '''Отправляет сообщение о загрузке изображений'''
    bot.send_message(message.chat.id, 'Загрузи изображения как <b>документы</b>', parse_mode='HTML')
    send_done_mes(message)

def any_answer(message):
    '''Отправляет рандомный ответ'''
    answers = ['Бесспорно', 'Мне кажется - да', 'Пока не ясно, попробуй снова', 'Даже не думай',
               'Предрешено', 'Вероятнее всего', 'Спроси позже', 'Мой ответ - нет', 'Никаких сомнений',
               'Хорошие перспективы', 'Лучше не рассказывать', 'По моим данным - нет', 'Определённо да',
               'Знаки говорят - да', 'Сейчас нельзя предсказать', 'Перспективы не очень хорошие',
               'Можешь быть уверен в этом', 'Да', 'Сконцентрируйся и спроси опять', 'Весьма сомнительно']
    bot.send_message(message.chat.id, choice(answers))

def crop_fill(imagefile, params):
    '''Обрезает изображение и возвращает его'''
    image = Image.open(imagefile)

    width, height = image.size[0], image.size[1]
    width_user, height_user = params['size']

    if (width > height) ^ (width_user > height_user):
        width_user, height_user = height_user, width_user

    w_scale, h_scale = width_user / width, height_user / height
    if params['action'] == 'crop':
        scale = max(w_scale, h_scale)
    elif params['action'] == 'field_add':
        scale = min(w_scale, h_scale)
    new_width, new_height = int(width * scale), int(height * scale)
    image_res = image.resize((new_width, new_height))

    if scale == h_scale:
        new_image = image_res.crop(((new_width - width_user) // 2, 0, (new_width + width_user) // 2, height_user))
    else:
        new_image = image_res.crop((0, (new_height - height_user) // 2, width_user, (new_height + height_user) // 2))

    new_image = new_image.convert('RGB')
    new_image.save(imagefile, quality=95, dpi=(300, 300))
    print(os.path.getsize(imagefile))
    return imagefile

def make_mediadocument(message):
    '''Отправляет обработанные изображения как группу и удаляет файлы'''
    media_group = []
    if User.users[message.chat.id].actions.get('mediaphoto', False):
        for file in User.users[message.chat.id].actions['mediaphoto']:
            media_group.append(types.InputMediaDocument(media=open(file, 'rb')))
        bot.send_media_group(chat_id=message.chat.id, media=media_group)

        for input_media in media_group:
            input_media.media.close()
        for file in User.users[message.chat.id].actions['mediaphoto']:
            if os.path.exists(file):
                os.remove(file)

        User.users[message.chat.id].actions['mediaphoto'].clear()
        start(message)
    else:
        bot.send_message(message.chat.id, 'Загрузи изображения')


@bot.message_handler(content_types=['photo', 'document'])
def send_image(message):
    '''Загружает фото или документ, обрабатывает его'''
    user_folder = f'images_of_{message.chat.id}'
    if message.photo:
        file_id = message.photo[-1].file_id
        original_filename = None
    else:
        original_filename = message.document.file_name
        file_id = message.document.file_id

    filename = download_file(bot, file_id, original_filename, user_folder)
    filename = crop_fill(filename, User.users[message.chat.id].actions)
    User.users[message.chat.id].actions.setdefault('mediaphoto', []).append(filename)


@bot.message_handler(content_types=['text'])
def smth_doing(message):
    '''Обработчик текстовых сообщений'''
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    if message.text == 'Задать вопрос':
        bot.send_message(message.chat.id, 'Задай мне вопрос (ответы типа Да/Нет)')
        bot.register_next_step_handler(message, any_answer)
    elif message.text == 'Получить стикер':
        path = 'images/'
        stick = open(getsticker(path), 'rb')
        bot.send_sticker(message.chat.id, stick)
        stick.close()
    elif message.text == 'Готово':
        make_mediadocument(message)
    elif re.fullmatch(r'\d+ \d+', message.text):
        input_size(message)


def input_size(message):
    '''Принимает пользовательские размеры изображения'''
    try:
        temp1, temp2 = map(int, message.text.split())
        print(temp1, temp2)
        if not 480 < temp1 < 8000 or not 480 < temp2 < 8000:
            raise ValueError
        User.users[message.chat.id].actions['size'] = temp1, temp2
        send_load_mes(message)
    except ValueError:
        bot.send_message(message.chat.id, 'Числа должны быть из диапазона 480-8000')
        bot.register_next_step_handler(message, input_size)
    except Exception as e:
        print(e)
        bot.send_message(message.chat.id, 'Неверный формат')
        bot.register_next_step_handler(message, input_size)


bot.polling()
