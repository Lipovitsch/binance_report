class ColumnsMapper:
    KRYPTO = {
        "time": "Data",
        "symbol": "Symbol",
        "price": "Cena",
        "qty": "Wolumen",
        "quoteQty": "Wartość",
        "commission": "Prowizja",
        "commissionAsset": "Symbol prowizji",
        "isBuyer": "Rola",
        "isMaker": "Strona",
        "id": "Numer ogłoszenia",
        "orderId": "Numer zamówienia",
    }

    P2P = {
        "createTime": "Data utworzenia",
        "totalPrice": "Ilość FIAT",
        "fiat": "FIAT",
        "amount": "Ilość krypto",
        "asset": "Kryptowaluta",
        "unitPrice": "Cena",
        "commission": "Prowizja",
        "takerCommission": "Prowizja biorcy",
        "takerCommissionRate": "Stawka prowizji biorcy",
        "takerAmount": "Kwota biorcy",
        "tradeType": "Rodzaj handlu",
        "advertisementRole": "Rola",
        "counterPartNickName": "Pseudonim strony",
        "orderNumber": "Numer zamówienia",
        "advNo": "Numer ogłoszenia",
    }

    FIAT = {
        "createTime": "Data utworzenia",
        "indicatedAmount": "Ilość FIAT",
        "amount": "Ilość FIAT otrzymana",
        "totalFee": "Prowizja",
        "fiatCurrency": "FIAT",
        "Rodzaj handlu": "Rodzaj handlu",
        "method": "Metoda płatności",
        # "status": "Status",
        "orderNo": "Numer zamówienia",
        "updateTime": "Data aktualizacji",
    }

    FIAT_KRYPTO = {
        'createTime': "Data utworzenia",
        'sourceAmount': 'Ilość FIAT',
        'totalFee': 'Prowizja',
        'fiatCurrency': 'FIAT',
        'obtainAmount': 'Ilość krypto',
        'cryptoCurrency': 'Kryptowaluta',
        'price': 'Cena',
        "Rodzaj handlu": "Rodzaj handlu",
        'paymentMethod': 'Metoda płatności',
        # 'status': 'Status',
        'orderNo': 'Numer zamówienia',
        'updateTime': "Data aktualizacji"
    }

    BETWEEN_PLATFORM_WITHDRAW = {
        'applyTime': 'Data',
        'coin': 'Moneta',
        'amount': 'Ilość',
        'transactionFee': 'Prowizja',
        'network': 'Sieć',
        'confirmNo': 'Liczba potwierdzeń',
        'address': 'Adres',
        'id': 'ID',
        # 'completeTime': 'Data ukończenia',
        # 'info': '0xe2fc31f816a9b94326492132018c3aecc4a93ae1',
        # 'status': 6,
        # 'transferType': 0,
        # 'txId': '0x50743dcc84d4d783b56352a62eb4cd6e6402a6386fb62c24cfb84ce4662b3e24',
        # 'txKey': '',
        # 'walletType': 0
    }

    BETWEEN_PLATFORM_DEPOSIT = {
        'insertTime': 'Data',
        'coin': 'Moneta',
        'amount': 'Ilość',
        'network': 'Sieć',
        'confirmTimes': 'Liczba potwierdzeń',
        'address': 'Adres',
        'id': 'ID',
        # 'status': 1,
        # 'transferType': 0,
        # 'txId': '6322ecede5097e95d09837efdce6b41bcc1859d4aad27a876aedfdf38aedea68',
        # 'unlockConfirm': 2,
        # 'walletType': 0,
        # 'addressTag': '',
    }
    

class Messages:
    REPORT_GENERATED = "Wygenerowano raport"
    REPORT_NOT_GENERATED = "Nie wygenerowano raportu"
    TRANSACTIONS_NOT_FOUND = "Nie znaleziono transakcji dla: %s"