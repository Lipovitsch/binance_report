import json
import requests
from pprint import pprint
from datetime import datetime, timedelta

import pandas as pd

from exceptions import *

class NBPAPI:

    def get_valid_date(self, symbol, date: datetime):

        start_date = date - timedelta(days=30)
        end_date = date

        url = f"http://api.nbp.pl/api/exchangerates/rates/A/{symbol}/{start_date.strftime('%Y-%m-%d')}/{end_date.strftime('%Y-%m-%d')}/"
        response = requests.get(url)

        if response.status_code == 200:
            data = response.json()
            df = pd.DataFrame(data['rates'])

            while not date.strftime('%Y-%m-%d') in df['effectiveDate'].tolist():
                date -= timedelta(days=1)
                if date < start_date:
                    raise NBPAPIError("Błąd podczas walidacji daty")
            return(date)
        else:
            raise NBPAPIError("Błąd w pobieraniu danych z NBP. Kod odpowiedzi:", response.status_code)


    def get_mid_price(self, symbol: str, date: datetime):

        if symbol == "PLN":
            return 1
        
        date = self.get_valid_date(symbol=symbol, date=date)

        url = f"https://api.nbp.pl/api/exchangerates/rates/A/{symbol}/{date.strftime('%Y-%m-%d')}/?format=json"
        response = requests.get(url)

        if response.status_code == 200:
            data = response.json()
            return data['rates'][0]['mid']
        else:
            raise NBPAPIError("Błąd w pobieraniu danych z NBP. Kod odpowiedzi:", response.status_code)


if __name__ == '__main__':
    print(NBPAPI().get_mid_price("EUR", datetime(2022, 1, 12)))
