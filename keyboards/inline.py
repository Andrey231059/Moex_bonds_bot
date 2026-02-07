from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from typing import List
import pandas as pd


class InlineKeyboards:
    """Генераторы инлайн-клавиатур"""

    @staticmethod
    def bonds_list(df: pd.DataFrame) -> InlineKeyboardMarkup:
        """Клавиатура со списком облигаций"""
        buttons = []

        for idx, row in df.iterrows():
            ticker = row['SECID']
            coupon = row['COUPONPERCENT']
            years = row['YEARS_TO_MATURITY']

            # Эмодзи для визуального выделения рейтинга
            rating_emoji = "⭐" if "ААА" in str(row['RATING']) else "💎" if "АА" in str(row['RATING']) else "🔷"

            btn_text = f"{rating_emoji} {idx + 1}. {ticker} | {coupon:.1f}% | {years}г"
            buttons.append([InlineKeyboardButton(
                text=btn_text,
                callback_data=f"bond:{ticker}"
            )])

        # Добавляем кнопку обновления
        buttons.append([InlineKeyboardButton(
            text="🔄 Обновить данные",
            callback_data="refresh_bonds"
        )])

        return InlineKeyboardMarkup(inline_keyboard=buttons)

    @staticmethod
    def bond_details(ticker: str) -> InlineKeyboardMarkup:
        """Клавиатура для детальной информации"""
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text="🔙 Назад к списку",
                callback_data="back_to_list"
            )],
            [InlineKeyboardButton(
                text="🔄 Обновить",
                callback_data="refresh_bonds"
            )],
            [InlineKeyboardButton(
                text="ℹ️ Как выбрать облигацию?",
                callback_data="help_bonds"
            )]
        ])

    @staticmethod
    def help_keyboard() -> InlineKeyboardMarkup:
        """Клавиатура для справки"""
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text="🔙 Назад к списку",
                callback_data="back_to_list"
            )]
        ])