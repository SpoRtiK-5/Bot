from aiogram import Bot, Dispatcher, types
from aiogram.types import Message, CallbackQuery
from aiogram.utils import executor
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters import Text
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

API_TOKEN = '7763998160:AAHCHxNBE7PHKi2dJsMZzUZlsaaJcT9BCV4'
ADMIN_GROUP_ID = -4827726129  # Замените на ID вашей группы
ADMIN_IDS = [737905673]  # ID админов, кто может использовать обратную связь

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())

users_data = {}  # временное хранилище анкет
contact_context = {}  # временное хранилище для обратной связи

class Form(StatesGroup):
    name = State()
    age = State()
    hours = State()
    steam_nick = State()
    steam_link = State()
    faceit_link = State()

class ContactForm(StatesGroup):
    message = State()

@dp.message_handler(commands=['start'])
async def start_command(message: Message):
    await message.answer("👋 Привет! Давай заполним анкету для вступления в команду.\n\nВведите своё имя:")
    await Form.name.set()

@dp.message_handler(state=Form.name)
async def process_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("Укажите ваш возраст:")
    await Form.age.set()

@dp.message_handler(state=Form.age)
async def process_age(message: Message, state: FSMContext):
    await state.update_data(age=message.text)
    await message.answer("Сколько часов у вас в игре?")
    await Form.hours.set()

@dp.message_handler(state=Form.hours)
async def process_hours(message: Message, state: FSMContext):
    await state.update_data(hours=message.text)
    await message.answer("Укажите ваш ник в Steam:")
    await Form.steam_nick.set()

@dp.message_handler(state=Form.steam_nick)
async def process_steam_nick(message: Message, state: FSMContext):
    await state.update_data(steam_nick=message.text)
    await message.answer("Вставьте ссылку на ваш Steam профиль:")
    await Form.steam_link.set()

@dp.message_handler(state=Form.steam_link)
async def process_steam_link(message: Message, state: FSMContext):
    await state.update_data(steam_link=message.text)
    await message.answer("И наконец, вставьте ссылку на ваш Faceit профиль:")
    await Form.faceit_link.set()

@dp.message_handler(state=Form.faceit_link)
async def process_faceit_link(message: Message, state: FSMContext):
    data = await state.get_data()
    telegram_username = message.from_user.username or "не указан"
    user_id = message.from_user.id

    users_data[user_id] = {
        'name': data['name'],
        'age': data['age'],
        'hours': data['hours'],
        'steam_nick': data['steam_nick'],
        'steam_link': data['steam_link'],
        'faceit_link': data['faceit_link'],
        'telegram': telegram_username,
        'id': user_id
    }

    text = (
        "📥 Новая анкета:\n\n"
        f"👤 Имя: {data['name']}\n"
        f"🎂 Возраст: {data['age']}\n"
        f"⏱ Часов в игре: {data['hours']}\n"
        f"🎮 Ник в Steam: {data['steam_nick']}\n"
        f"🔗 Steam: {data['steam_link']}\n"
        f"🔗 Faceit: {data['faceit_link']}\n"
        f"📱 Telegram: @{telegram_username}"
    )

    await bot.send_message(chat_id=ADMIN_GROUP_ID, text=text)
    await message.answer("✅ Спасибо за регистрацию! С вами скоро свяжутся.")
    await state.finish()

# Команда /list для админов
@dp.message_handler(commands=['list'])
async def show_users(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        return await message.reply("❌ У вас нет доступа к этой команде.")
    if not users_data:
        return await message.answer("Пока нет зарегистрированных анкет.")

    for uid, user in users_data.items():
        kb = InlineKeyboardMarkup().add(
            InlineKeyboardButton(text="✉️ Связаться", callback_data=f"contact_{uid}")
        )
        user_info = (
            f"👤 Имя: {user['name']}\n"
            f"📱 Telegram: @{user['telegram']}\n"
            f"🎂 Возраст: {user['age']}\n"
            f"🕹 Часы: {user['hours']}"
        )
        await message.answer(user_info, reply_markup=kb)

# Обработка кнопки "Связаться"
@dp.callback_query_handler(Text(startswith="contact_"))
async def contact_start(call: CallbackQuery, state: FSMContext):
    if call.from_user.id not in ADMIN_IDS:
        return await call.answer("Нет доступа.", show_alert=True)
    user_id = int(call.data.split("_")[1])
    contact_context[call.from_user.id] = user_id
    await call.message.answer("Введите сообщение, которое хотите отправить игроку:")
    await ContactForm.message.set()

@dp.message_handler(state=ContactForm.message)
async def send_contact_message(message: Message, state: FSMContext):
    admin_id = message.from_user.id
    if admin_id not in contact_context:
        return await message.reply("⚠️ Не найден пользователь для отправки.")
    
    target_user_id = contact_context[admin_id]
    text = f"📩 Сообщение от администратора:\n\n{message.text}"
    try:
        await bot.send_message(chat_id=target_user_id, text=text)
        await message.answer("✅ Сообщение успешно отправлено.")
    except Exception as e:
        await message.answer("❌ Не удалось отправить сообщение. Возможно, пользователь не начал диалог с ботом.")
    await state.finish()
