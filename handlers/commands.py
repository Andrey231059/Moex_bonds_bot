from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from services.moex_api import MoexAPI
from services.bond_analyzer import BondAnalyzer
from keyboards.inline import InlineKeyboards
from utils.formatters import MessageFormatters
import pandas as pd

router = Router()


@router.message(Command("start"))
async def cmd_start(message: Message):
    """Обработчик команды /start"""
    welcome_text = """
🤖 <b>Бот надёжных облигаций Мосбиржи</b>

Я помогу вам найти самые надёжные облигации без оферты и амортизации.

📊 <b>Возможности:</b>
• Топ-10 надёжных облигаций в реальном времени
• Детальная информация по каждой бумаге
• Анализ купонных выплат и сроков погашения

🔍 <b>Критерии отбора:</b>
✅ Без оферты и амортизации
✅ Высокая ликвидность (1-й уровень листинга)
✅ Объём выпуска от 1 млрд ₽
✅ Рублёвые облигации

👉 Используйте команду /bonds для начала анализа
    """

    await message.answer(welcome_text, parse_mode="HTML")


@router.message(Command("bonds"))
async def cmd_bonds(message: Message):
    """Обработчик команды /bonds — показ списка облигаций"""
    await message.answer("⏳ Загружаю данные с Московской биржи...")

    # Получаем данные
    moex_api = MoexAPI()
    df = await moex_api.get_all_bonds()

    if df.empty:
        await message.answer("❌ Не удалось загрузить данные с биржи. Попробуйте позже.")
        return

    # Анализируем и фильтруем
    analyzer = BondAnalyzer()
    df_filtered = analyzer.filter_reliable_bonds(df, limit=Config.BONDS_LIMIT)

    if df_filtered.empty:
        await message.answer("❌ Не найдено облигаций, соответствующих критериям.")
        return

    # Сохраняем данные в состоянии пользователя
    await message.bot["data_storage"].set_user_data(
        message.from_user.id,
        "bonds_data",
        df_filtered.to_dict()
    )

    # Формируем сообщение
    formatter = MessageFormatters()
    table_message = formatter.format_bonds_table(df_filtered)

    keyboard = InlineKeyboards.bonds_list(df_filtered)

    await message.answer(table_message, parse_mode="HTML", reply_markup=keyboard)