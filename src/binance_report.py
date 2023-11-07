import json
from datetime import datetime, timedelta
import pandas as pd
from binance.client import Client

from pprint import pprint

from const import *


def get_api_keys(path):
    with open(path, "r") as f:
        json_data = json.load(f)
    return json_data['api_key'], json_data['secret_key']


def date_to_timestamp(date: datetime):
    return int(datetime.timestamp(date)*1000)


def timestamp_to_datetime(timestamp: int):
    return datetime.fromtimestamp(timestamp / 1000)


class BinanceReport(Client):
    
    def __init__(self, api_key, secret_key):
        super().__init__(api_key=api_key, api_secret=secret_key)
    

    def get_symbols(self) -> list:
        exchange_info = self.get_exchange_info()
        symbols = [symbol_info['symbol'] for symbol_info in exchange_info['symbols']]
        return symbols
    

    def get_krypto_transactions(self, start_date: datetime = None, end_date: datetime = None):
        symbols = self.get_symbols()

        output_list = []
        for i, symbol in enumerate(symbols):
            msg = f"Pobieranie danych dla symbolu '{symbol}' ({i}/{len(symbols)})"
            print(msg)

            start_timestamp = date_to_timestamp(start_date) if start_date != None else None
            end_timestamp = date_to_timestamp(end_date) if start_date != None else None

            trades = self.get_my_trades(
                symbol    = symbol, 
                startTime = start_timestamp,
                endTime   = end_timestamp
            )
            
            output_list += trades

            # if trades:
            #     pprint(trades)
            #     print()

            if i == 10:
                break
        
        output_df = pd.DataFrame(output_list)
        output_df["isBuyer"] = output_df["isBuyer"].apply(lambda x: "Kupujący" if x else "Sprzedający")
        output_df["isMaker"] = output_df["isMaker"].apply(lambda x: "Twórca" if x else "Biorca")
        output_df["time"] = output_df["time"].apply(timestamp_to_datetime)
        output_df.drop(["orderListId", "isBestMatch"], axis=1, inplace=True)

        output_df = output_df[ColumnsMapper.KRYPTO.keys()]
        output_df = output_df.rename(ColumnsMapper.KRYPTO, axis=1)

        return output_df


    def get_p2p_transactions(self, start_date: datetime, end_date: datetime):
        output_list = []
        date_inc = timedelta(days=30)

        for trade_type in ['BUY', 'SELL']:
            start_period = start_date
            end_period = start_date + date_inc

            while start_period < end_date:
                if end_period >= end_date:
                    end_period = end_date
                
                start_timestamp = date_to_timestamp(start_period)
                end_timestamp = date_to_timestamp(end_period)

                msg = f"Pobieranie transakcji P2P typu '{trade_type}' {start_period.date()} - {end_period.date()}"
                print(msg)

                deposits = self.get_c2c_trade_history(
                    startTimestamp = start_timestamp,
                    endTimestamp   = end_timestamp,
                    tradeType      = trade_type
                )

                output_list += deposits["data"]
                
                start_period += date_inc
                end_period += date_inc
        
        output_list = [el for el in output_list if el['orderStatus'] == "COMPLETED"]
        output_df = pd.DataFrame(output_list)

        output_df['createTime'] = output_df['createTime'].apply(timestamp_to_datetime)

        output_df = output_df[ColumnsMapper.P2P.keys()]
        output_df = output_df.rename(ColumnsMapper.P2P, axis=1)

        return output_df


    def get_fiat_deposit_transactions(self, start_timestamp: int, end_timestamp: int):
        return self.get_fiat_deposit_withdraw_history(
            beginTime       = start_timestamp,
            endTime         = end_timestamp,
            transactionType = 0
        )['data']


    def get_fiat_withdraw_transactions(self, start_timestamp: int, end_timestamp: int):
        return self.get_fiat_deposit_withdraw_history(
            beginTime       = start_timestamp,
            endTime         = end_timestamp,
            transactionType = 1
        )['data']


    def get_fiat_transactions(self, start_date: datetime, end_date: datetime):
        msg = f"Checking FIAT transactions from {start_date} to {end_date}"
        print(msg)

        start_timestamp = date_to_timestamp(start_date)
        end_timestamp = date_to_timestamp(end_date)

        output_deposit_list = self.get_fiat_deposit_transactions(start_timestamp, end_timestamp)
        output_withdraw_list = self.get_fiat_withdraw_transactions(start_timestamp, end_timestamp)

        output_deposit_list = [el for el in output_deposit_list if el['status'] == "Successful"]
        output_withdraw_list = [el for el in output_withdraw_list if el['status'] == "Successful"]
        output_list = output_deposit_list + output_withdraw_list

        output_df = pd.DataFrame(output_list)
        return output_df


def main():
    api_key, secret_key = get_api_keys(r"data/keys_n.json")
    client = BinanceReport(api_key, secret_key)
    result = client.get_krypto_transactions()
    print(result)
    

if __name__ == "__main__":
    main()
