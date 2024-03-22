import logging
import sys
from os import getenv

from aiohttp import web

from aiogram import Bot, Dispatcher, Router, types, F
from aiogram.filters import CommandStart
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiogram.filters.callback_data import CallbackData
from aiogram.utils.markdown import hbold, hlink
from aiogram.types import CallbackQuery
import json
import time
from async_main import get_data


TOKEN = getenv('MIZUNO_BOT')

# Webserver settings
# bind localhost only to prevent any external access
WEB_SERVER_HOST = "::"
# Port for incoming request from reverse proxy. Should be any available port
WEB_SERVER_PORT = 8350

# Path to webhook route, on which Telegram will send requests
WEBHOOK_PATH = "/bot/"
# Secret key to validate requests from Telegram (optional)
# WEBHOOK_SECRET = "my-secret"
# Base URL for webhook will be used to generate webhook URL for Telegram,
# in this example it is used public DNS with HTTPS support
BASE_WEBHOOK_URL = "https://iolar.alwaysdata.net"

# All handlers should be attached to the Router (or Dispatcher)
router = Router()


class MyCallback(CallbackData, prefix="my"):
    action: str
    items_type: str


@router.message(CommandStart())
async def cmd_start(message: types.Message):
    kb = [
        [types.KeyboardButton(text="Мужские кроссовки")],
        [types.KeyboardButton(text="Женские кроссовки")],
        [types.KeyboardButton(text="Мужская одежда")],
        [types.KeyboardButton(text="Женская одежда")]
    ]
    keyboard = types.ReplyKeyboardMarkup(
        keyboard=kb,
        resize_keyboard=True,
        input_field_placeholder='Какие товары вас интересуют?'
    )
    await message.answer("Выберите интересующую вас категорию товаров", reply_markup=keyboard)


@router.message(F.text.lower() == 'мужские кроссовки')
async def male_sneakers(message: types.Message):
    await message.answer('Пожалуйста, подождите... ')
    url = 'https://mizuno.com.ru/shop/muzhskaya_obuv2/'
    try:
        await get_data(url)
    except Exception:
        print(f"[!] URL {url} is unavailable!\n{'-' * 30} ")

    await show_data(message, message.text)


@router.message(F.text.lower() == 'женские кроссовки')
async def male_sneakers(message: types.Message):
    await message.answer('Пожалуйста, подождите... ')
    url = 'https://mizuno.com.ru/shop/zhenskaya_obuv1/'
    try:
        await get_data(url)
    except Exception:
        print(f"[!] URL {url} is unavailable!\n{'-' * 30} ")

    await show_data(message, message.text)


@router.message(F.text.lower() == 'мужская одежда')
async def male_sneakers(message: types.Message):
    await message.answer('Пожалуйста, подождите... ')
    url = 'https://mizuno.com.ru/shop/muzhskaya_odezhda/'
    try:
        await get_data(url)
    except Exception:
        print(f"[!] URL {url} is unavailable!\n{'-' * 30} ")

    await show_data(message, message.text)


@router.message(F.text.lower() == 'женская одежда')
async def male_sneakers(message: types.Message):
    await message.answer('Пожалуйста, подождите... ')
    url = 'https://mizuno.com.ru/shop/zhenskaya_odezhda/'
    try:
        await get_data(url)
    except Exception:
        print(f"[!] URL {url} is unavailable!\n{'-' * 30} ")

    await show_data(message, message.text)


async def show_data(message: types.Message, items_type):
    with open(f'data/{items_type}.json', encoding='utf-8') as file:
        data = json.load(file)

    discount_items = [x for x in data if x.get("Старая цена") != '']

    if len(discount_items) != 0:
        for index, item in enumerate(discount_items):
            card = f"{hlink(item.get('Название'), item.get('Ссылка'))}\n" \
                   f"{'Старая цена : '} {hbold(item.get('Старая цена'))} ₽\n" \
                   f"{'Цена со скидкой '}{hbold(item.get('Скидка'))}{hbold('% ')}:  " \
                   f"{hbold(item.get('Цена'))} ₽  🔥\n"

            await message.answer(card, parse_mode='html')

            if index % 20 == 0:
                time.sleep(3)

    else:
        await message.answer('В данной категории отсутствуют товары со скидкой 😕')

    kb = [
        [types.InlineKeyboardButton(text="Да, конечно!", callback_data=MyCallback(
            action='yes', items_type=items_type).pack())]
    ]
    keyboard = types.InlineKeyboardMarkup(
        inline_keyboard=kb,
        resize_keyboard=True,
    )
    await message.answer('Хотите увидеть товары в этой категории без скидки?', reply_markup=keyboard)


@router.callback_query(MyCallback.filter(F.action == 'yes'))
async def without_discount(callback: CallbackQuery, callback_data: MyCallback):
    await callback.message.edit_text(
        text='Собираю информацию...',
        reply_markup=callback.message.reply_markup
    )
    await callback.answer()
    await show_data_without_discount(callback.message, callback_data.items_type)


async def show_data_without_discount(message: types.Message, items_type):

    with open(f'data/{items_type}.json', encoding='utf-8') as file:
        data = json.load(file)

    non_discount_items = [x for x in data if x.get("Старая цена") == '']

    if len(non_discount_items) != 0:
        for index, item in enumerate(non_discount_items):
            card = f"{hlink(item.get('Название'), item.get('Ссылка'))}\n" \
                   f"{'Цена: '}:  {hbold(item.get('Цена'))} ₽  \n"

            await message.answer(card, parse_mode='html')

            if index % 20 == 0:
                time.sleep(3)

    else:
        await message.answer('В данной категории отсутствуют товары без скидки! 😲')


@router.message()
async def any_other_message(message: types.Message):
    await message.answer("Не надо мне ничего писать, я - обычный бот 🤖 и умею только показывать скидки на обувь и "
                         "одежду. \n"
                         "Лучше просто нажмите сюда --> /start <-- а потом на кнопочку с интересующей вас категорией "
                         "товаров 😉")


async def on_startup(bot: Bot) -> None:
    # If you have a self-signed SSL certificate, then you will need to send a public
    # certificate to Telegram
    await bot.set_webhook(f"{BASE_WEBHOOK_URL}{WEBHOOK_PATH}")


def main() -> None:
    # Dispatcher is a root router
    dp = Dispatcher()
    # ... and all other routers should be attached to Dispatcher
    dp.include_router(router)

    # Register startup hook to initialize webhook
    dp.startup.register(on_startup)

    # Initialize Bot instance with a default parse mode which will be passed to all API calls
    bot = Bot(TOKEN)

    # Create aiohttp.web.Application instance
    app = web.Application()

    # Create an instance of request handler,
    # aiogram has few implementations for different cases of usage
    # In this example we use SimpleRequestHandler which is designed to handle simple cases
    webhook_requests_handler = SimpleRequestHandler(
        dispatcher=dp,
        bot=bot
    )
    # Register webhook handler on application
    webhook_requests_handler.register(app, path=WEBHOOK_PATH)

    # Mount dispatcher startup and shutdown hooks to aiohttp application
    setup_application(app, dp, bot=bot)

    # And finally start webserver
    web.run_app(app, host=WEB_SERVER_HOST, port=WEB_SERVER_PORT)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    main()
