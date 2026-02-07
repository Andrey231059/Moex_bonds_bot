from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from services.moex_service import MoexService
from keyboards.inline_kb import bonds_list_keyboard, bond_details_keyboard
from utils.formatters import format_bonds_table, format_bond_details
import pandas as pd

router = Router()

# Хранилище данных пользователей (в реальном проекте использовать Redis)
user_data_storage = {}


@router.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer(
        "🤖 <b>Бот надёжных облигаций</b>\n\n"
        "Показывает топ-10 облигаций Мосбиржи:\n"
        "✅ Без оферты и амортизации\n"
        "✅ Высокая ликвидность\n\n"
        "👉 Команда: /bonds",
        parse_mode="HTML"
    )


@router.message(Command("bonds"))
async def cmd_bonds(message: Message):
    await message.answer("⏳ Загружаю данные с Мосбиржи...")

    moex = MoexService()
    df = await moex.get_all_bonds()

    if df.empty:
        await message.answer("❌ Ошибка загрузки данных")
        return

    df_filtered = moex.filter_reliable_bonds(df, limit=10)

    if df_filtered.empty:
        await message.answer("❌ Не найдено подходящих облигаций")
        return

    # Сохраняем данные пользователя
    user_data_storage[message.from_user.id] = df_filtered

    table = format_bonds_table(df_filtered)
    keyboard = bonds_list_keyboard(df_filtered)

    await message.answer(table, parse_mode="HTML", reply_markup=keyboard)


@router.callback_query(F.data == "refresh")
async def refresh_bonds(callback: CallbackQuery):
    await callback.answer("🔄 Обновляю...")
    await callback.message.edit_text("⏳ Обновляю данные...")

    moex = MoexService()
    df = await moex.get_all_bonds()

    if df.empty:
        await callback.message.edit_text("❌ Ошибка обновления")
        return

    df_filtered = moex.filter_reliable_bonds(df, limit=10)

    if df_filtered.empty:
        await callback.message.edit_text("❌ Нет подходящих облигаций")
        return

    user_data_storage[callback.from_user.id] = df_filtered

    table = format_bonds_table(df_filtered)
    keyboard = bonds_list_keyboard(df_filtered)

    await callback.message.edit_text(table, parse_mode="HTML", reply_markup=keyboard)


@router.callback_query(F.data.startswith("bond:"))
async def show_bond_details(callback: CallbackQuery):
    ticker = callback.data.split(":")[1]
    await callback.answer(f"ℹ️ {ticker}")

    df_filtered = user_data_storage.get(callback.from_user.id)

    if df_filtered is None or df_filtered.empty:
        await callback.message.edit_text("❌ Данные устарели. Используйте /bonds")
        return

    bond_row = df_filtered[df_filtered['SECID'] == ticker]

    if bond_row.empty:
        await callback.message.edit_text("❌ Облигация не найдена")
        return

    details = format_bond_details(bond_row.iloc[0])
    keyboard = bond_details_keyboard(ticker)

    await callback.message.edit_text(details, parse_mode="HTML", reply_markup=keyboard)


@router.callback_query(F.data == "back_to_list")
async def back_to_list(callback: CallbackQuery):
    await callback.answer()

    df_filtered = user_data_storage.get(callback.from_user.id)

    if df_filtered is None or df_filtered.empty:
        await callback.message.edit_text("❌ Данные устарели. Используйте /bonds")
        return

    table = format_bonds_table(df_filtered)
    keyboard = bonds_list_keyboard(df_filtered)

    await callback.message.edit_text(table, parse_mode="HTML", reply_markup=keyboard)