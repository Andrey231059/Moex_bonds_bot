import aiohttp
import pandas as pd
from datetime import datetime
from config import Config


class MoexAPI:
    """Клиент для работы с API Московской биржи"""

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
                    response.raise_for_status()
                    return await response.json()
            except Exception as e:
                print(f"Ошибка запроса к MOEX API: {e}")
                return {}

    async def get_all_bonds(self) -> pd.DataFrame:
        """Получение списка всех облигаций с рынка Т+2"""
        endpoint = "/engines/stock/markets/bonds/boards/TQOB/securities.json"

        params = {
            "securities.columns": (
                "SECID,SHORTNAME,SECNAME,ISSUESIZE,COUPONPERCENT,"
                "COUPONPERIOD,MATDATE,LISTLEVEL,FACEVALUE,CURRENCY"
            ),
            "marketdata.columns": "YIELDCLOSE,COUPONVALUE"
        }

        data = await self._fetch_json(endpoint, params)

        if not data or 'securities' not in data:
            return pd.DataFrame()

        # Парсим секьюрити данные
        sec_cols = data['securities']['columns']
        sec_data = data['securities']['data']
        df_securities = pd.DataFrame(sec_data, columns=sec_cols)

        # Парсим рыночные данные
        mkt_cols = data['marketdata']['columns']
        mkt_data = data['marketdata']['data']
        df_marketdata = pd.DataFrame(mkt_data, columns=mkt_cols)

        # Объединяем
        df = pd.concat([df_securities, df_marketdata], axis=1)

        # Преобразуем даты и числа
        df['MATDATE'] = pd.to_datetime(df['MATDATE'], errors='coerce')
        df['COUPONPERCENT'] = pd.to_numeric(df['COUPONPERCENT'], errors='coerce')
        df['COUPONVALUE'] = pd.to_numeric(df['COUPONVALUE'], errors='coerce')
        df['COUPONPERIOD'] = pd.to_numeric(df['COUPONPERIOD'], errors='coerce')
        df['ISSUESIZE'] = pd.to_numeric(df['ISSUESIZE'], errors='coerce')

        return df

    async def get_bond_coupons(self, secid: str) -> list:
        """Получение информации о купонах облигации"""
        endpoint = f"/statistics/engines/stock/markets/bonds/boards/TQOB/securities/{secid}.json"

        data = await self._fetch_json(endpoint)

        if not data or 'coupons' not in data:
            return []

        coupons = data['coupons']['data']
        coupon_cols = data['coupons']['columns']

        # Возвращаем только будущие купоны
        today = datetime.now().date()
        future_coupons = []

        for coupon in coupons:
            coupon_dict = dict(zip(coupon_cols, coupon))
            coupon_date = coupon_dict.get('coupondate')

            if coupon_date and datetime.strptime(coupon_date, '%Y-%m-%d').date() > today:
                future_coupons.append(coupon_dict)

        return future_coupons[:3]  # Только ближайшие 3 купона