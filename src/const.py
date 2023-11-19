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
        "totalPrice": "Cena",
        "fiat": "Fiat",
        "amount": "Ilość",
        "asset": "Aktywo",
        "unitPrice": "Cena za jednostkę",
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
        "updateTime": "Data aktualizacji",
        "indicatedAmount": "Ilość przesyłana",
        "amount": "Ilość otrzymana",
        "totalFee": "Prowizja",
        "fiatCurrency": "Waluta FIAT",
        "method": "Metoda płatności",
        "status": "Status",
        "orderNo": "Numer zamówienia",
    }
