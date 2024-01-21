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
    
    def __init__(self, api_key: str = None, secret_key: str = None, progress_callback = None):
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

                    start_timestamp = date_to_timestamp(start_period)
                    end_timestamp = date_to_timestamp(end_period)

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
            
        output_df = pd.DataFrame(output_list)

        if len(output_df) > 0:
            output_df["isBuyer"] = output_df["isBuyer"].apply(lambda x: "Kupujący" if x else "Sprzedający")
            output_df["isMaker"] = output_df["isMaker"].apply(lambda x: "MAKER" if x else "TAKER")

            output_df["time"] = output_df["time"].apply(timestamp_to_datetime)
            output_df = output_df[(output_df['time'] >= start_date) & (output_df['time'] <= end_date)]
            output_df.sort_values(by='time', inplace=True)

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
            output_df.sort_values(by='createTime', inplace=True)

            output_df['tradeType'] = output_df['tradeType'].apply(lambda x: "Wpłata" if x == "BUY" else "Wypłata")

            cols_to_float = ['totalPrice', 'amount', 'unitPrice', 'commission', 'takerCommission', 'takerCommissionRate', 'takerAmount']
            output_df[cols_to_float] = output_df[cols_to_float].apply(lambda x: x.astype(float))

            output_df = output_df[ColumnsMapper.P2P.keys()]
            output_df = output_df.rename(ColumnsMapper.P2P, axis=1)

        return output_df


    def get_fiat_transactions(self, start_date: datetime, end_date: datetime):
        msg = f"Pobieranie transakcji FIAT..."
        if self.progress_callback != None:
            self.progress_callback.emit(msg)

        start_timestamp = date_to_timestamp(start_date)
        end_timestamp = date_to_timestamp(end_date)

        try:
            output_deposit_list = self.get_fiat_deposit_withdraw_history(beginTime=start_timestamp, endTime=end_timestamp, transactionType=0)['data']
            output_withdraw_list = self.get_fiat_deposit_withdraw_history(beginTime=start_timestamp, endTime=end_timestamp, transactionType=1)['data']
        except BinanceExceptions.BinanceAPIException as e:
            raise APIError(e)

        output_deposit_list = [el for el in output_deposit_list if el['status'] == "Successful"]
        output_withdraw_list = [el for el in output_withdraw_list if el['status'] == "Successful"]
        
        deposit_df = pd.DataFrame(output_deposit_list)
        withdraw_df = pd.DataFrame(output_withdraw_list)
        deposit_df["Rodzaj handlu"] = "Wpłata"
        withdraw_df["Rodzaj handlu"] = "Wypłata"

        output_df = pd.concat([deposit_df, withdraw_df])

        if len(output_df) > 0:
            output_df['createTime'] = output_df['createTime'].apply(timestamp_to_datetime)
            output_df['updateTime'] = output_df['updateTime'].apply(timestamp_to_datetime)
            output_df.sort_values(by='createTime', inplace=True)

            cols_to_float = ['indicatedAmount', 'amount', 'totalFee']
            output_df[cols_to_float] = output_df[cols_to_float].apply(lambda x: x.astype(float))

            output_df = output_df[ColumnsMapper.FIAT.keys()]
            output_df = output_df.rename(ColumnsMapper.FIAT, axis=1)

        return output_df


    def get_fiat_crypto_transactions(self, start_date: datetime, end_date: datetime):
        msg = f"Pobieranie transakcji FIAT - krypto..."
        if self.progress_callback != None:
            self.progress_callback.emit(msg)

        start_timestamp = date_to_timestamp(start_date)
        end_timestamp = date_to_timestamp(end_date)

        try:
            buy_dict = self.get_fiat_payments_history(transactionType=0, beginTime=start_timestamp, endTime=end_timestamp)
            sell_dict = self.get_fiat_payments_history(transactionType=1, beginTime=start_timestamp, endTime=end_timestamp)
        except BinanceExceptions.BinanceAPIException as e:
            raise APIError(e)

        buy_list = [el for el in buy_dict['data'] if el['status'] == 'Completed'] if 'data' in buy_dict.keys() else []
        sell_list = [el for el in sell_dict['data'] if el['status'] == 'Completed'] if 'data' in sell_dict.keys() else []
        
        buy_df = pd.DataFrame(buy_list)
        sell_df = pd.DataFrame(sell_list)
        buy_df["Rodzaj handlu"] = "Wpłata"
        sell_df["Rodzaj handlu"] = "Wypłata"

        output_df = pd.concat([buy_df, sell_df])

        if len(output_df) > 0:
            output_df['createTime'] = output_df['createTime'].apply(timestamp_to_datetime)
            output_df['updateTime'] = output_df['updateTime'].apply(timestamp_to_datetime)
            output_df.sort_values(by='createTime', inplace=True)

            cols_to_float = ['obtainAmount', 'price', 'sourceAmount', 'totalFee']
            output_df[cols_to_float] = output_df[cols_to_float].apply(lambda x: x.astype(float))

            output_df = output_df[ColumnsMapper.FIAT_KRYPTO.keys()]
            output_df = output_df.rename(ColumnsMapper.FIAT_KRYPTO, axis=1)

        return  output_df


    def get_between_platforms_transactions(self, start_date: datetime, end_date: datetime):
        output_deposit = []
        output_withdraw = []
        date_inc = timedelta(days=90)
        periods = math.ceil((end_date - start_date) / date_inc)

        period = 1
        start_period = start_date
        end_period = start_date + date_inc

        while start_period < end_date:
            if end_period >= end_date:
                end_period = end_date
            
            start_timestamp = date_to_timestamp(start_period)
            end_timestamp = date_to_timestamp(end_period)
            
            msg = f"Pobieranie transakcji między platformami ({period}/{periods})..."
            if self.progress_callback != None:
                self.progress_callback.emit(msg)

            try:
                deposit = self.get_deposit_history(startTime=start_timestamp, endTime=end_timestamp, status=1)
                withdraw = self.get_withdraw_history(startTime=start_timestamp, endTime=end_timestamp, status=6)

            except BinanceExceptions.BinanceAPIException as e:
                raise APIError(e)

            output_deposit += deposit
            output_withdraw += withdraw
            
            start_period += date_inc
            end_period += date_inc
            period += 1
        
        deposit_df = pd.DataFrame(output_deposit)
        withdraw_df = pd.DataFrame(output_withdraw)
        output_df = pd.DataFrame()

        if len(deposit_df) > 0:
            deposit_df['insertTime'] = deposit_df['insertTime'].apply(timestamp_to_datetime)
            deposit_df.sort_values(by='insertTime', inplace=True)

            cols_to_float = ['amount']
            deposit_df[cols_to_float] = deposit_df[cols_to_float].apply(lambda x: x.astype(float))

            deposit_df = deposit_df[ColumnsMapper.BETWEEN_PLATFORM_DEPOSIT.keys()]
            deposit_df = deposit_df.rename(ColumnsMapper.BETWEEN_PLATFORM_DEPOSIT, axis=1)
            deposit_df['Typ transakcji'] = 'Wpłata na Binance'
            output_df = deposit_df
        
        if len(withdraw_df) > 0:
            withdraw_df['applyTime'] = pd.to_datetime(withdraw_df['applyTime'])
            withdraw_df.sort_values(by='applyTime', inplace=True)

            cols_to_float = ['amount', 'transactionFee']
            withdraw_df[cols_to_float] = withdraw_df[cols_to_float].apply(lambda x: x.astype(float))

            withdraw_df = withdraw_df[ColumnsMapper.BETWEEN_PLATFORM_WITHDRAW.keys()]
            withdraw_df = withdraw_df.rename(ColumnsMapper.BETWEEN_PLATFORM_WITHDRAW, axis=1)
            withdraw_df['Typ transakcji'] = 'Wypłata z Binance'
            output_df = withdraw_df
        
        if len(deposit_df) > 0 and len(withdraw_df) > 0:
            output_df = pd.concat([deposit_df, withdraw_df])
            output_df.sort_values(by='Data', inplace=True)
            output_df["Liczba potwierdzeń"] = output_df["Liczba potwierdzeń"].apply(lambda x: str(x))

            output_df = output_df[list(ColumnsMapper.BETWEEN_PLATFORM_WITHDRAW.values()) + ['Typ transakcji']]

        return output_df


def main():
    api_key, secret_key = get_api_keys(r"data/keys_r.json")
    client = BinanceReport(api_key, secret_key)
    # result = client.get_fiat_crypto_transactions(datetime(2023, 1, 1), datetime(2024, 1, 1))
    # result = client.get_fiat_transactions(datetime(2021, 1, 1), datetime(2022, 1, 1))

    start_date = datetime(2023, 12, 1)
    # end_date = datetime(2023, 12, 1)
    end_date = start_date + timedelta(days=90)
    start_timestamp = date_to_timestamp(start_date)
    end_timestamp = date_to_timestamp(end_date)
    # result = client.get_fiat_payments_history(transactionType=0, beginTime=start_timestamp, endTime=end_timestamp)
    # result = client.get_lending_purchase_history(startTime=start_timestamp, endTime=end_timestamp)
    # result = client.get_withdraw_history(startTime=start_timestamp, endTime=end_timestamp, status=6)
    result = client.get_pay_trade_history(orderType='C2C')
    
    # /sapi/v1/lending/auto-invest/history/list
    pprint(result)
    

if __name__ == "__main__":
    main()
