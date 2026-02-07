import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict


class BondAnalyzer:
    """Анализатор и фильтр облигаций"""

    @staticmethod
    def has_offer(name: str) -> bool:
        """Проверка наличия оферты в названии"""
        offer_keywords = [
            'оферта', 'оферты', 'оферте', 'call', 'put',
            'досрочн', 'досроч', 'погашен', 'погашени'
        ]
        name_lower = str(name).lower()
        return any(keyword in name_lower for keyword in offer_keywords)

    @staticmethod
    def has_amortization(name: str) -> bool:
        """Проверка наличия амортизации"""
        amort_keywords = ['аморт', 'амортизац', 'погашен', 'погашени']
        name_lower = str(name).lower()
        return any(keyword in name_lower for keyword in amort_keywords)

    @staticmethod
    def calculate_rating(row: pd.Series) -> str:
        """Определение кредитного рейтинга (упрощённо)"""
        secname = str(row.get('SECNAME', '')).lower()
        shortname = str(row.get('SHORTNAME', '')).lower()

        # ОФЗ - наивысший рейтинг
        if 'офз' in shortname or 'федеральн' in secname:
            return "🇷🇺 ААА (ОФЗ)"

        # Госкорпорации
        state_corps = ['вэб', 'ржд', 'росатом', 'роснефт', 'газпром', 'транснефт']
        if any(corp in secname for corp in state_corps):
            return "🏛️ АА (Госкорп.)"

        # Системообразующие банки
        if 'сбербанк' in secname or 'втб' in secname:
            return "🏦 А+ (Системный банк)"

        # Крупные компании
        if 'газпром' in secname or 'лукойл' in secname or 'сургутнефтегаз' in secname:
            return "🏭 А (Крупная компания)"

        # Остальные
        return "📊 BBB (Иные эмитенты)"

    @staticmethod
    def calculate_coupon_frequency(coupon_period: float) -> int:
        """Расчёт количества купонных выплат в году"""
        if pd.isna(coupon_period) or coupon_period <= 0:
            return 0

        days_per_year = 365
        freq = days_per_year / coupon_period

        # Округляем до ближайшего стандартного значения
        if freq < 1.5:
            return 1
        elif freq < 2.5:
            return 2
        elif freq < 4:
            return 4
        else:
            return int(round(freq))

    def filter_reliable_bonds(self, df: pd.DataFrame, limit: int = 10) -> pd.DataFrame:
        """Фильтрация надёжных облигаций без оферты и амортизации"""
        if df.empty:
            return df

        # Копируем для безопасности
        filtered = df.copy()

        # Фильтр 1: Только 1-й уровень листинга (ликвидные)
        filtered = filtered[filtered['LISTLEVEL'] == 1]

        # Фильтр 2: Только рублёвые облигации
        filtered = filtered[filtered['CURRENCY'] == 'RUB']

        # Фильтр 3: Только с купонной доходностью
        filtered = filtered[filtered['COUPONPERCENT'].notna() & (filtered['COUPONPERCENT'] > 0)]

        # Фильтр 4: Срок погашения в будущем (минимум 30 дней)
        today = datetime.now().date()
        filtered = filtered[filtered['MATDATE'].dt.date > today + timedelta(days=30)]

        # Фильтр 5: Без оферты
        filtered = filtered[~filtered['SECNAME'].apply(self.has_offer)]

        # Фильтр 6: Без амортизации
        filtered = filtered[~filtered['SECNAME'].apply(self.has_amortization)]

        # Фильтр 7: Минимальный объём выпуска (1 млрд руб)
        filtered = filtered[filtered['ISSUESIZE'] >= 1_000_000_000]

        # Добавляем расчётные поля
        filtered['RATING'] = filtered.apply(self.calculate_rating, axis=1)
        filtered['COUPON_FREQ'] = filtered['COUPONPERIOD'].apply(self.calculate_coupon_frequency)
        filtered['YEARS_TO_MATURITY'] = (
                (filtered['MATDATE'] - pd.Timestamp.now()).dt.days / 365.25
        ).round(1)

        # Сортировка: сначала по надёжности (ОФЗ > госкорпы > банки > компании), затем по доходности
        def sort_key(row):
            rating_order = {
                '🇷🇺 ААА (ОФЗ)': 1,
                '🏛️ АА (Госкорп.)': 2,
                '🏦 А+ (Системный банк)': 3,
                '🏭 А (Крупная компания)': 4,
                '📊 BBB (Иные эмитенты)': 5
            }
            return (
                rating_order.get(row['RATING'], 6),
                -row['COUPONPERCENT']  # Чем выше доходность - тем выше в списке
            )

        filtered = filtered.sort_values(
            by=['RATING', 'COUPONPERCENT'],
            key=lambda x: x.map(lambda r: {
                '🇷🇺 ААА (ОФЗ)': 1,
                '🏛️ АА (Госкорп.)': 2,
                '🏦 А+ (Системный банк)': 3,
                '🏭 А (Крупная компания)': 4,
                '📊 BBB (Иные эмитенты)': 5
            }.get(r, 6) if x.name == 'RATING' else -x),
            ascending=[True, False]
        )

        return filtered.head(limit).reset_index(drop=True)

    def get_bond_details(self, row: pd.Series, coupons: list) -> Dict:
        """Формирование детальной информации об облигации"""
        maturity_date = row['MATDATE'].strftime('%d.%m.%Y')
        years_to_maturity = row['YEARS_TO_MATURITY']

        details = {
            'ticker': row['SECID'],
            'name': row['SHORTNAME'],
            'full_name': row['SECNAME'],
            'rating': row['RATING'],
            'maturity_date': maturity_date,
            'years_to_maturity': years_to_maturity,
            'coupon_percent': row['COUPONPERCENT'],
            'coupon_value': row['COUPONVALUE'],
            'coupon_freq': row['COUPON_FREQ'],
            'coupon_period': int(row['COUPONPERIOD']) if pd.notna(row['COUPONPERIOD']) else 0,
            'issue_size': f"{row['ISSUESIZE']:,.0f}".replace(",", " "),
            'face_value': row['FACEVALUE'],
            'currency': row['CURRENCY'],
            'yield_close': row.get('YIELDCLOSE', row['COUPONPERCENT']),
            'next_coupons': coupons
        }

        return details