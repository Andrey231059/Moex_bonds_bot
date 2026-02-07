from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import pandas as pd


def bonds_list_keyboard(df: pd.DataFrame) -> InlineKeyboardMarkup:
    """Клавиатура со списком облигаций"""
    buttons = []

    for idx, row in df.iterrows():
        ticker = row['SECID']
        coupon = row['COUPONPERCENT']
        btn_text = f"{idx + 1}. {ticker} ({coupon:.1f}%)"
        buttons.append([InlineKeyboardButton(text=btn_text, callback_data=f"bond:{ticker}")])

    buttons.append([InlineKeyboardButton(text="🔄 Обновить", callback_data="refresh")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def bond_details_keyboard(ticker: str) -> InlineKeyboardMarkup:
    """Клавиатура для деталей облигации"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_list")],
        [InlineKeyboardButton(text="🔄 Обновить", callback_data="refresh")]
    ])