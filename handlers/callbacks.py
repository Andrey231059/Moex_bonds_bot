from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.exceptions import TelegramBadRequest
from services.moex_api import MoexAPI
from services.bond_analyzer import BondAnalyzer
from keyboards.inline import InlineKeyboards
from utils.formatters import MessageFormatters
import pandas as pd


router = Router()


@router.callback_query(F.data == "refresh_bonds")
async def refresh_bonds(callback: CallbackQuery):
    """Обновление списка облигаций"""
    await callback.answer("🔄 Обновляю данные...")
    await callback.message.edit_text("⏳ Обновляю данные с Московской биржи...")

    # Получаем свежие данные
    moex_api = MoexAPI()
    df = await moex_api.get_all_bonds()

    if df.empty:
        await callback.message.edit_text("❌ Ошибка обновления данных. Попробуйте позже.")
        return

    # Фильтруем
    analyzer = BondAnalyzer()
    df_filtered = analyzer.filter_reliable_bonds(df, limit=Config.BONDS_LIMIT)

    if df_filtered.empty:
        await callback.message.edit_text("❌ Не найдено подходящих облигаций.")
        return

    # Сохраняем
    await callback.bot["data_storage"].set_user_data(
        callback.from_user.id,
        "bonds_data",
        df_filtered.to_dict()
    )

    # Формируем ответ
    formatter = MessageFormatters()
    table_message = formatter.format_bonds_table(df_filtered)
    keyboard = InlineKeyboards.bonds_list(df_filtered)

    try:
        await callback.message.edit_text(
            table_message,
            parse_mode="HTML",
            reply_markup=keyboard
        )
    except TelegramBadRequest:
        await callback.message.answer(
            table_message,
            parse_mode="HTML",
            reply_markup=keyboard
        )


@router.callback_query(F.data.startswith("bond:"))
async def show_bond_details(callback: CallbackQuery):
    """Показ детальной информации об облигации"""
    ticker = callback.data.split(":")[1]
    await callback.answer(f"ℹ️ Загружаю данные по {ticker}...")

    # Получаем сохранённые данные
    bonds_data = await callback.bot["data_storage"].get_user_data(
        callback.from_user.id,
        "bonds_data"
    )

    if not bonds_data:
        await callback.message.edit_text(
            "❌ Данные устарели. Используйте /bonds для обновления."
        )
        return

    # Восстанавливаем DataFrame
    df = pd.DataFrame(bonds_data)
    bond_row = df[df['SECID'] == ticker]

    if bond_row.empty:
        await callback.message.edit_text("❌ Облигация не найдена в списке.")
        return

    # Получаем информацию о купонах
    moex_api = MoexAPI()
    coupons = await moex_api.get_bond_coupons(ticker)

    # Формируем детали
    analyzer = BondAnalyzer()
    details = analyzer.get_bond_details(bond_row.iloc[0], coupons)

    # Форматируем сообщение
    formatter = MessageFormatters()
    details_message = formatter.format_bond_details(details)

    keyboard = InlineKeyboards.bond_details(ticker)

    await callback.message.edit_text(
        details_message,
        parse_mode="HTML",
        reply_markup=keyboard
    )


@router.callback_query(F.data == "back_to_list")
async def back_to_list(callback: CallbackQuery):
    """Возврат к списку облигаций"""
    await callback.answer()

    # Получаем сохранённые данные
    bonds_data = await callback.bot["data_storage"].get_user_data(
        callback.from_user.id,
        "bonds_data"
    )

    if not bonds_data:
        await callback.message.edit_text(
            "❌ Данные устарели. Используйте /bonds для обновления."
        )
        return

    # Восстанавливаем DataFrame
    df = pd.DataFrame(bonds_data)

    # Формируем сообщение
    formatter = MessageFormatters()
    table_message = formatter.format_bonds_table(df)
    keyboard = InlineKeyboards.bonds_list(df)

    await callback.message.edit_text(
        table_message,
        parse_mode="HTML",
        reply_markup=keyboard
    )


@router.callback_query(F.data == "help_bonds")
async def show_help(callback: CallbackQuery):
    """Показ справки"""
    await callback.answer()

    formatter = MessageFormatters()
    help_message = formatter.format_help()

    keyboard = InlineKeyboards.help_keyboard()

    await callback.message.edit_text(
        help_message,
        parse_mode="HTML",
        reply_markup=keyboard
    )