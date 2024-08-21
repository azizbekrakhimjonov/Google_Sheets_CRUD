from aiogram import Bot, Dispatcher, types
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.utils import executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import logging
from datetime import datetime
from geopy.distance import geodesic
from config import API_TOKEN

ADMIN_ID = '1486580350'
WORK_LOCATION = (41.32346500754505, 69.28690575802068)  # Ishxona koordinatalari

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)
dp.middleware.setup(LoggingMiddleware())

# Ro'yxatdan o'tgan foydalanuvchilarni saqlash
registered_users = {}
user_locations = {}

# FSM uchun holatlar
class RegisterState(StatesGroup):
    waiting_for_name = State()
    waiting_for_approval = State()
    approved = State()

class LocationState(StatesGroup):
    waiting_for_category = State()
    waiting_for_location = State()

# 1. Start komandasi
@dp.message_handler(commands=['start'], state='*')
async def register(message: types.Message, state: FSMContext):
    user_id = message.from_user.id

    if user_id in registered_users:
        if registered_users[user_id]["approved"]:
            await state.set_state(RegisterState.approved)
            await message.reply("Siz allaqachon ro'yxatdan o'tgansiz va ruxsat olingan. Botdan foydalanishingiz mumkin!")
            await ask_category(message)  # Kategoriyani tanlash
        else:
            await state.set_state(RegisterState.waiting_for_approval)
            await message.reply("Siz ro'yxatdan o'tdingiz. Administratorning ruxsatini kuting.")
    else:
        await state.set_state(RegisterState.waiting_for_name)
        await message.reply("Iltimos, ismingiz va familiyangizni kiriting.")

# 1.1 Foydalanuvchidan ism va familiya olish
@dp.message_handler(state=RegisterState.waiting_for_name)
async def process_name(message: types.Message, state: FSMContext):
    full_name = message.text.strip()
    user_id = message.from_user.id
    registered_users[user_id] = {"name": full_name, "approved": False}

    await state.set_state(RegisterState.waiting_for_approval)
    await message.reply("Ro'yxatdan o'tdingiz. Administratorning ruxsatini kuting.")

    # Adminga foydalanuvchi haqida habar yuborish
    approve_button = InlineKeyboardButton(text="Ruxsat berish", callback_data=f"approve_{user_id}")
    deny_button = InlineKeyboardButton(text="Rad etish", callback_data=f"deny_{user_id}")
    keyboard = InlineKeyboardMarkup().add(approve_button, deny_button)

    await bot.send_message(
        ADMIN_ID,
        f"Foydalanuvchi {full_name} ({user_id}) botdan foydalanmoqchi. Ruxsat etilsinmi?",
        reply_markup=keyboard
    )

# 1.2 Adminning ruxsat berishi yoki rad etishi
@dp.callback_query_handler(lambda c: c.data and (c.data.startswith('approve_') or c.data.startswith('deny_')))
async def process_approval(callback_query: CallbackQuery):
    user_id = int(callback_query.data.split('_')[1])

    if callback_query.data.startswith('approve_'):
        registered_users[user_id]["approved"] = True
        await bot.send_message(user_id, "Sizga botdan foydalanishga ruxsat berildi.")
        await dp.current_state(user=user_id).set_state(RegisterState.approved)
        await callback_query.answer("Foydalanuvchiga ruxsat berildi.")
        await ask_category_scheduled(user_id)  # Ro'yxatdan o'tgach kategoriya so'rash
    elif callback_query.data.startswith('deny_'):
        registered_users[user_id]["approved"] = False
        await bot.send_message(user_id, "Sizga botdan foydalanishga ruxsat berilmadi.")
        await dp.current_state(user=user_id).reset_state()
        await callback_query.answer("Foydalanuvchiga ruxsat berilmadi.")

# 2. Kategoriya tanlash va lokatsiyani tasdiqlash
async def ask_category(message: types.Message):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    buttons = ["At Work", "Not at Work", "Reasons", "In the object"]
    keyboard.add(*buttons)
    await message.answer("Qaysi holatda ekanligingizni tanlang:", reply_markup=keyboard)
    await LocationState.waiting_for_category.set()

# 2.1 Belgilangan vaqtlarda kategoriya so'rash uchun yordamchi funksiya
async def ask_category_scheduled(user_id):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    buttons = ["At Work", "Not at Work", "Reasons", "In the object"]
    keyboard.add(*buttons)
    await bot.send_message(user_id, "Qaysi holatda ekanligingizni tanlang:", reply_markup=keyboard)
    await LocationState.waiting_for_category.set()

# 2.2 Foydalanuvchi kategoriyani tanlaganda
@dp.message_handler(state=LocationState.waiting_for_category, content_types=types.ContentTypes.TEXT)
async def handle_category(message: types.Message, state: FSMContext):
    category = message.text
    user_id = message.from_user.id

    if category not in ["At Work", "Not at Work", "Reasons", "In the object"]:
        await message.answer("Iltimos, tugmalardan birini tanlang.")
        return

    await state.update_data(selected_category=category)

    # Faqat kerakli kategoriyalar uchun lokatsiya so'rash
    if category in ["At Work", "Not at Work", "In the object"]:
        await message.answer("Iltimos, lokatsiyangizni yuboring:", reply_markup=types.ReplyKeyboardRemove())
        await LocationState.waiting_for_location.set()
    else:
        await state.finish()
        await ask_category(message)

# 2.3 Lokatsiyani qabul qilish va tekshirish
@dp.message_handler(state=LocationState.waiting_for_location, content_types=['location'])
async def handle_location(message: types.Message, state: FSMContext):
    user_location = (message.location.latitude, message.location.longitude)
    user_id = message.from_user.id
    data = await state.get_data()
    category = data.get('selected_category')

    # Agar kategoriya "At Work" yoki "Not at Work" bo'lsa, lokatsiya tekshiriladi
    if category in ["At Work", "Not at Work"]:
        distance = calculate_distance(user_location, WORK_LOCATION)
        if distance < 0.1:  # 100 metrdan yaqin bo'lsa
            await message.answer(f"Siz ishxonadasiz ({category}). Rahmat!")
        else:
            await message.answer(f"Siz ishxonada emassiz ({category})!")

    # Har qanday holatda, lokatsiya va vaqt saqlanadi
    user_locations[user_id] = {
        'category': category,
        'location': user_location,
        'time': datetime.now()
    }

    await state.finish()
    await ask_category(message)  # Kategoriya qayta chiqishi

# Masofa hisoblash funksiyasi
def calculate_distance(loc1, loc2):
    return geodesic(loc1, loc2).km

# Schedulerni boshlash
scheduler = AsyncIOScheduler()
scheduler.start()

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
