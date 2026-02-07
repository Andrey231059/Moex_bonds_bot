import pandas as pd


def format_bonds_table(df: pd.DataFrame) -> str:
    """Форматирование таблицы облигаций"""
    if df.empty:
        return "❌ Нет данных"

    message = "🔝 <b>Топ-10 надёжных облигаций</b>\n<i>✅ Без оферты | ✅ Без амортизации</i>\n\n"

    for idx, row in df.iterrows():
        ticker = row['SECID']
        name = row['SHORTNAME'][:25] + "..." if len(str(row['SHORTNAME'])) > 25 else row['SHORTNAME']
        rating = row['RATING'].split()[0]
        coupon = row['COUPONPERCENT']
        years = row['YEARS']

        message += f"{idx + 1}. <b>{ticker}</b>\n   {name}\n   {rating} | {coupon:.2f}% | {years}г\n\n"

    return message + "👉 Выберите облигацию:"


def format_bond_details(row: pd.Series) -> str:
    """Форматирование деталей облигации"""
    # Расчёт размера купона
    face_value = row.get('FACEVALUE', 0)
    coupon_percent = row.get('COUPONPERCENT', 0)
    coupon_period = row.get('COUPONPERIOD', 0)

    if face_value and coupon_percent and coupon_period:
        coupon_value = face_value * (coupon_percent / 100) * (coupon_period / 365)
        coupon_value = round(coupon_value, 2)
    else:
        coupon_value = 0.0

    message = f"📜 <b>{row['SECID']}</b>\n\n"
    message += f"📌 {row['SHORTNAME']}\n"
    message += f"🏢 {row['SECNAME'][:50]}{'...' if len(row['SECNAME']) > 50 else ''}\n\n"
    message += f"⭐ {row['RATING']}\n"
    message += f"💵 Купон: {row['COUPONPERCENT']:.2f}% годовых\n"
    message += f"💰 Размер: {coupon_value:.2f} ₽\n"
    message += f"📅 Выплат: {int(row['COUPON_FREQ'])} раз/год\n"
    message += f"⏳ Погашение: {row['MATDATE'].strftime('%d.%m.%Y')} ({row['YEARS']:.1f} лет)\n"
    message += f"💼 Объём: {row['ISSUESIZE']:,.0f} ₽\n\n"
    message += "<i>ℹ️ Данные: Мосбиржа</i>"

    return message