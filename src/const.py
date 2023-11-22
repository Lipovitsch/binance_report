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

class Messages:
    REPORT_GENERATED = "Wygenerowano raport"
    REPORT_NOT_GENERATED = "Nie wygenerowano raportu"
    TRANSACTIONS_NOT_FOUND = "Nie znaleziono transakcji dla: %s"