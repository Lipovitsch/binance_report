import math
import json
from pprint import pprint
import traceback
from datetime import datetime, timedelta

import pandas as pd
import binance.exceptions as BinanceExceptions
from binance.client import Client

from const import *
from exceptions import *


def get_api_keys(path):
    with open(path, "r") as f:
        json_data = json.load(f)
    return json_data['api_key'], json_data['secret_key']


def date_to_timestamp(date: datetime):
    return int(datetime.timestamp(date)*1000)


def timestamp_to_datetime(timestamp: int):
    return datetime.fromtimestamp(timestamp / 1000)


class BinanceReport(Client):
    
    def __init__(self, api_key, secret_key, progress_callback = None):
        super().__init__(api_key=api_key, api_secret=secret_key)
        self.progress_callback = progress_callback
    

    def get_symbols(self) -> list:
        exchange_info = self.get_exchange_info()
        symbols = [symbol_info['symbol'] for symbol_info in exchange_info['symbols']]
        return symbols
    

    def get_crypto_transactions(self, start_date: datetime = None, end_date: datetime = None, symbols: list | None = None):
        if symbols == None:
            symbols = self.get_symbols()

        output_list = []
        date_inc = timedelta(days=1)
        periods = math.ceil((end_date - start_date) / date_inc)

        for i, symbol in enumerate(symbols):

            msg = f"Pobieranie danych dla symbolu '{symbol}' ({i+1}/{len(symbols)})..."
            if self.progress_callback != None:
                self.progress_callback.emit(msg)

            try:
                trades = self.get_my_trades(symbol=symbol)
            except BinanceExceptions.BinanceAPIException as e:
                raise APIError(e)

            if len(trades) >= 500:

                start_period = start_date
                end_period = start_date + date_inc
                period = 1
                while start_period < end_date:
                    if end_period >= end_date:
                        end_period = end_date

                    msg = f"Wykryto ponad 500 transakcji dla symbolu '{symbol}' - pobieranie dzień po dniu ({period}/{periods})..."
                    if self.progress_callback != None:
                        self.progress_callback.emit(msg)

                    start_timestamp = date_to_timestamp(start_period) # if start_date != None else None
                    end_timestamp = date_to_timestamp(end_period) # if start_date != None else None

                    try:
                        trades = self.get_my_trades(
                            symbol    = symbol, 
                            startTime = start_timestamp,
                            endTime   = end_timestamp
                        )
                    except BinanceExceptions.BinanceAPIException as e:
                        raise APIError(e)
                    
                    output_list += trades

                    start_period += date_inc
                    end_period += date_inc
                    period += 1

            else:
                output_list += trades
            
            if i == 10:
                break
        
        output_df = pd.DataFrame(output_list)

        if len(output_df) > 0:
            output_df["isBuyer"] = output_df["isBuyer"].apply(lambda x: "Kupujący" if x else "Sprzedający")
            output_df["isMaker"] = output_df["isMaker"].apply(lambda x: "Twórca" if x else "Biorca")

            output_df["time"] = output_df["time"].apply(timestamp_to_datetime)
            output_df = output_df[(output_df['time'] >= start_date) & (output_df['time'] <= end_date)]

            cols_to_float = ['price', 'qty', 'quoteQty', 'commission']
            output_df[cols_to_float] = output_df[cols_to_float].apply(lambda x: x.astype(float))

            output_df = output_df[ColumnsMapper.KRYPTO.keys()]
            output_df = output_df.rename(ColumnsMapper.KRYPTO, axis=1)

        return output_df


    def get_p2p_transactions(self, start_date: datetime, end_date: datetime):
        output_list = []
        date_inc = timedelta(days=30)
        periods = math.ceil((end_date - start_date) / date_inc) * 2

        period = 1
        for trade_type in ['BUY', 'SELL']:
            start_period = start_date
            end_period = start_date + date_inc

            while start_period < end_date:
                if end_period >= end_date:
                    end_period = end_date
                
                start_timestamp = date_to_timestamp(start_period)
                end_timestamp = date_to_timestamp(end_period)

                msg = f"Pobieranie transakcji P2P typu '{trade_type}' ({period}/{periods})..."
                if self.progress_callback != None:
                    self.progress_callback.emit(msg)

                try:
                    deposits = self.get_c2c_trade_history(
                        startTimestamp = start_timestamp,
                        endTimestamp   = end_timestamp,
                        tradeType      = trade_type
                    )
                except BinanceExceptions.BinanceAPIException as e:
                    raise APIError(e)

                output_list += deposits["data"]
                
                start_period += date_inc
                end_period += date_inc
                period += 1
        
        output_list = [el for el in output_list if el['orderStatus'] == "COMPLETED"]
        output_df = pd.DataFrame(output_list)

        if len(output_df) > 0:
            output_df['createTime'] = output_df['createTime'].apply(timestamp_to_datetime)

            cols_to_float = ['totalPrice', 'amount', 'unitPrice', 'commission', 'takerCommission', 'takerCommissionRate', 'takerAmount']
            output_df[cols_to_float] = output_df[cols_to_float].apply(lambda x: x.astype(float))

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
        msg = f"Pobieranie transakcji FIAT..."
        if self.progress_callback != None:
            self.progress_callback.emit(msg)

        start_timestamp = date_to_timestamp(start_date)
        end_timestamp = date_to_timestamp(end_date)

        try:
            output_deposit_list = self.get_fiat_deposit_transactions(start_timestamp, end_timestamp)
            output_withdraw_list = self.get_fiat_withdraw_transactions(start_timestamp, end_timestamp)
        except BinanceExceptions.BinanceAPIException as e:
            raise APIError(f"{e}")

        output_deposit_list = [el for el in output_deposit_list if el['status'] == "Successful"]
        output_withdraw_list = [el for el in output_withdraw_list if el['status'] == "Successful"]
        output_list = output_deposit_list + output_withdraw_list

        output_df = pd.DataFrame(output_list)

        if len(output_df) > 0:
            output_df['createTime'] = output_df['createTime'].apply(timestamp_to_datetime)
            output_df['updateTime'] = output_df['updateTime'].apply(timestamp_to_datetime)

            cols_to_float = ['indicatedAmount', 'amount', 'totalFee']
            output_df[cols_to_float] = output_df[cols_to_float].apply(lambda x: x.astype(float))

            output_df = output_df[ColumnsMapper.FIAT.keys()]
            output_df = output_df.rename(ColumnsMapper.FIAT, axis=1)

        return output_df


def main():
    api_key, secret_key = get_api_keys(r"data/keys_n.json")
    client = BinanceReport(api_key, secret_key)
    result = client.get_crypto_transactions()
    print(result)
    

if __name__ == "__main__":
    main()
