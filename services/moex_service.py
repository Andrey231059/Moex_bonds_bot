import aiohttp
import pandas as pd
from datetime import datetime, timedelta
from config import Config


class MoexService:
    """Сервис для работы с API Московской биржи"""

    def __init__(self):
        self.base_url = Config.MOEX_API_URL

    async def _fetch_json(self, endpoint: str, params: dict = None) -> dict:
        """Выполнение асинхронного запроса к API"""
        url = f"{self.base_url}{endpoint}"

        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(
                        url,
                        params=params,
                        timeout=Config.REQUEST_TIMEOUT
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        print(f"API error: {response.status}")
                        return {}
            except Exception as e:
                print(f"Ошибка запроса к MOEX API: {e}")
                return {}

    async def get_all_bonds(self) -> pd.DataFrame:
        """Получение списка всех облигаций"""
        endpoint = "/engines/stock/markets/bonds/boards/TQOB/securities.json"

        params = {
            "securities.columns": (
                "SECID,SHORTNAME,SECNAME,ISSUESIZE,COUPONPERCENT,"
                "COUPONPERIOD,MATDATE,LISTLEVEL,FACEVALUE,CURRENCY"
            ),
            "marketdata.columns": "YIELDCLOSE"
        }

        data = await self._fetch_json(endpoint, params)

        if not data or 'securities' not in data:
            return pd.DataFrame()

        sec_cols = data['securities']['columns']
        sec_data = data['securities']['data']
        df = pd.DataFrame(sec_data, columns=sec_cols)

        # Преобразуем типы данных
        df['MATDATE'] = pd.to_datetime(df['MATDATE'], errors='coerce')
        df['COUPONPERCENT'] = pd.to_numeric(df['COUPONPERCENT'], errors='coerce')
        df['COUPONPERIOD'] = pd.to_numeric(df['COUPONPERIOD'], errors='coerce')
        df['ISSUESIZE'] = pd.to_numeric(df['ISSUESIZE'], errors='coerce')
        df['FACEVALUE'] = pd.to_numeric(df['FACEVALUE'], errors='coerce')

        return df


    def filter_reliable_bonds(self, df: pd.DataFrame, limit: int = 10) -> pd.DataFrame:
        """Фильтрация надёжных облигаций с проверкой наличия колонок"""
        if df.empty:
            return df

        filtered = df.copy()

        # Фильтр 1: Только 1-й уровень листинга (если колонка существует)
        if 'LISTLEVEL' in filtered.columns:
            filtered = filtered[filtered['LISTLEVEL'] == 1]

        # Фильтр 2: Только рублёвые облигации (если колонка существует)
        if 'CURRENCY' in filtered.columns:
            filtered = filtered[filtered['CURRENCY'] == 'RUB']
        else:
            # Если нет колонки CURRENCY, предполагаем, что все облигации рублёвые
            # или пропускаем этот фильтр
            pass

        # Фильтр 3: Только с купонной доходностью
        if 'COUPONPERCENT' in filtered.columns:
            filtered = filtered[
                filtered['COUPONPERCENT'].notna() &
                (filtered['COUPONPERCENT'] > 0)
                ]

        # Фильтр 4: Срок погашения в будущем
        if 'MATDATE' in filtered.columns:
            today = datetime.now().date()
            filtered = filtered[
                pd.to_datetime(filtered['MATDATE'], errors='coerce').dt.date > today + timedelta(days=30)
                ]

        # Фильтр 5: Минимальный объём выпуска
        if 'ISSUESIZE' in filtered.columns:
            filtered = filtered[filtered['ISSUESIZE'] >= 100_000_000]

        # Проверка на оферту и амортизацию
        def has_offer(name):
            keywords = ['оферта', 'досрочн', 'погашен', 'call', 'put']
            return any(kw in str(name).lower() for kw in keywords)

        def has_amort(name):
            return 'аморт' in str(name).lower()

        if 'SECNAME' in filtered.columns:
            filtered = filtered[~filtered['SECNAME'].apply(has_offer)]
            filtered = filtered[~filtered['SECNAME'].apply(has_amort)]

        # Добавляем недостающие колонки со значениями по умолчанию
        if 'CURRENCY' not in filtered.columns:
            filtered['CURRENCY'] = 'RUB'  # Предполагаем рубли по умолчанию

        if 'FACEVALUE' not in filtered.columns:
            filtered['FACEVALUE'] = 1000.0  # Стандартный номинал

        # Рейтинги
        def calculate_rating(row):
            if 'SHORTNAME' not in row.index or 'SECNAME' not in row.index:
                return "📊 BBB (Иные)"

            shortname = str(row['SHORTNAME']).lower() if pd.notna(row['SHORTNAME']) else ''
            secname = str(row['SECNAME']).lower() if pd.notna(row['SECNAME']) else ''

            if 'офз' in shortname:
                return "🇷🇺 AAA (ОФЗ)"
            elif any(x in secname for x in ['сбербанк', 'втб']):
                return "🏦 AA (Банк)"
            elif any(x in secname for x in ['газпром', 'роснефть', 'лукойл']):
                return "🏭 A (Корпорация)"
            else:
                return "📊 BBB (Иные)"

        filtered['RATING'] = filtered.apply(calculate_rating, axis=1)

        # Купонная частота
        if 'COUPONPERIOD' in filtered.columns:
            filtered['COUPON_FREQ'] = (365 / filtered['COUPONPERIOD']).round().fillna(0).astype(int)
        else:
            filtered['COUPON_FREQ'] = 2  # По умолчанию 2 раза в год

        # Срок до погашения
        if 'MATDATE' in filtered.columns:
            filtered['YEARS'] = ((pd.to_datetime(filtered['MATDATE']) - pd.Timestamp.now()).dt.days / 365).round(1)
        else:
            filtered['YEARS'] = 1.0

        # Сортировка
        rating_order = {'🇷🇺 AAA (ОФЗ)': 1, '🏦 AA (Банк)': 2, '🏭 A (Корпорация)': 3, '📊 BBB (Иные)': 4}
        filtered['R_ORDER'] = filtered['RATING'].map(lambda x: rating_order.get(x, 5))
        filtered = filtered.sort_values(['R_ORDER', 'COUPONPERCENT'], ascending=[True, False])

        return filtered.head(limit).reset_index(drop=True).drop(columns=['R_ORDER'])