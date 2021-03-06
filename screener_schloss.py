# schloss method
# no financials,
# PB < 1
# no long term debt
# price < 1.1 * 52 week low
# insider  ownership > median
import math

import yahoo_fin.stock_info as si
import pandas as pd

from Market import Market
from currency_scrapeYahoo import getBalanceSheetCurrency
from currency_scrapeYahoo import getListingCurrency
import currency_getExchangeRate
from helperMethods import getFromDF, convertHK, roundB, getFromDFYearly
from helperMethods import getInsiderOwnership
from datetime import datetime, timedelta

COUNT = 0
MARKET = Market.US
yearlyFlag = False
INSIDER_OWN_MIN = 10


def increment():
    global COUNT
    COUNT = COUNT + 1
    return COUNT


# START_DATE = '3/1/2020'
START_DATE = (datetime.today() - timedelta(weeks=52)).strftime('%-m/%-d/%Y')
print("data start date:", START_DATE)
DIVIDEND_START_DATE = '1/1/2010'
PRICE_INTERVAL = '1mo'

exchange_rate_dict = currency_getExchangeRate.getExchangeRateDict()

fileOutput = open('list_schlossOutput', 'w')

# ownershipDic = getInsiderOwnership()

if MARKET == Market.US:
    stock_df = pd.read_csv('list_US_companyInfo', sep="\t", index_col=False,
                           names=['ticker', 'name', 'sector', 'industry', 'country', 'mv', 'price'])
    print(stock_df)

    listStocks = stock_df[(stock_df['price'] > 1)
                          & (stock_df['sector'].str
                             .contains('financial|healthcare', regex=True, case=False) == False)
                          & (stock_df['industry'].str.contains('reit', regex=True, case=False) == False)
                          & (stock_df['country'].str.lower() != 'china')]['ticker'].tolist()

elif MARKET == Market.HK:
    stock_df = pd.read_csv('list_HK_Tickers', dtype=object, sep=" ", index_col=False, names=['ticker', 'name'])
    stock_df['ticker'] = stock_df['ticker'].astype(str)
    hk_shares = pd.read_csv('list_HK_totalShares', sep="\t", index_col=False, names=['ticker', 'shares'])
    stock_df['ticker'] = stock_df['ticker'].map(lambda x: convertHK(x))
    listStocks = stock_df['ticker'].tolist()
    # listStocks = ['0030.HK']
else:
    raise Exception("market not found")

print(len(listStocks), listStocks)

for comp in listStocks:
    print(increment(), comp)

    try:
        cf = si.get_cash_flow(comp, yearly=yearlyFlag)
        cfo = getFromDFYearly(cf, "totalCashFromOperatingActivities", yearlyFlag)

        if cfo < 0:
            print(comp, " cfo < 0 ")
            continue

        info = si.get_company_info(comp)

        country = getFromDF(info, 'country')
        sector = getFromDF(info, 'sector')

        if 'real estate' in sector.lower() or 'financial' in sector.lower():
            print(comp, " no real estate or financial ")
            continue

        marketPrice = si.get_live_price(comp)
        if marketPrice < 1:
            print(comp, 'market price < 1: ', marketPrice)
            continue

        # if MARKET == Market.US:
        #     insiderPerc = ownershipDic[comp]
        #     if insiderPerc < INSIDER_OWN_MIN:
        #         print(comp, "insider ownership < " + str(INSIDER_OWN_MIN), insiderPerc)
        #         continue
        # else:
        insiderPerc = float(si.get_holders(comp).get('Major Holders')[0][0].rstrip("%"))
        print(comp, MARKET, "insider percent", insiderPerc)

        if insiderPerc < INSIDER_OWN_MIN:
            print(comp, "insider percentage < " + str(INSIDER_OWN_MIN), insiderPerc)
            continue

        bs = si.get_balance_sheet(comp, yearly=yearlyFlag)
        retainedEarnings = getFromDF(bs, 'retainedEarnings')

        # RE>0 ensures that the stock is not a chronic cash burner
        if retainedEarnings <= 0:
            print(comp, " retained earnings <= 0 ", retainedEarnings)
            continue

        totalAssets = getFromDF(bs, "totalAssets")
        totalLiab = getFromDF(bs, "totalLiab")
        currentLiab = getFromDF(bs, 'totalCurrentLiabilities')

        goodWill = getFromDF(bs, 'goodWill')
        intangibles = getFromDF(bs, 'intangibleAssets')
        tangible_equity = totalAssets - totalLiab - goodWill - intangibles

        debtEquityRatio = totalLiab / tangible_equity

        longTermDebtRatio = (totalLiab - currentLiab) / totalAssets

        if debtEquityRatio > 0.5 or totalAssets < totalLiab:
            print(comp, "DE Ratio > 0.5 OR  A<L. ", debtEquityRatio)
            continue

        if MARKET == Market.US:
            shares = si.get_quote_data(comp)['sharesOutstanding']
        elif MARKET == Market.HK:
            shares = hk_shares[hk_shares['ticker'] == comp]['shares'].values[0]
        else:
            raise Exception(str(comp + " no shares found for market non US non HK"))

        # shares = si.get_quote_data(comp)['sharesOutstanding']

        listingCurrency = getListingCurrency(comp)
        bsCurrency = getBalanceSheetCurrency(comp, listingCurrency)
        exRate = currency_getExchangeRate.getExchangeRate(exchange_rate_dict, listingCurrency, bsCurrency)

        marketCap = marketPrice * shares

        if MARKET == Market.HK:
            if marketCap < 1000000000:
                print(comp, "market cap < 1B TOO SMALL", roundB(marketCap, 2))
                continue

        pb = marketCap / (tangible_equity / exRate)

        # requirement on book value
        if pb < 0 or pb > 0.6:
            print(comp, ' pb < 0 or pb > 0.6. PB mv equity exrate', pb, roundB(marketCap, 2),
                  roundB(tangible_equity, 2), exRate)
            continue

        data = si.get_data(comp, start_date=START_DATE, interval=PRICE_INTERVAL)
        divs = si.get_dividends(comp, start_date=DIVIDEND_START_DATE)
        low_52wk = data['low'].min()

        # requirement on low price
        if marketPrice > low_52wk * 1.1:
            print(comp, "exceeding 52wk low * 1.1, P/Low ratio:", marketPrice, low_52wk,
                  round(marketPrice / low_52wk, 2))
            continue

        # insiderPercOutput = str(round(insiderPerc, 1)) if MARKET == Market.US else "non data"

        outputString = comp + " " + stock_df[stock_df['ticker'] == comp]['name'] \
            .to_string(index=False, header=False) + " " \
                       + country.replace(" ", "_") + " " \
                       + sector.replace(" ", "_") + " " \
                       + listingCurrency + bsCurrency \
                       + " MV:" + str(roundB(marketCap, 1)) + 'B' \
                       + " Eq:" + str(roundB((totalAssets - totalLiab) / exRate, 1)) + 'B' \
                       + " pb:" + str(round(pb, 1)) \
                       + " D/E:" + str(round(debtEquityRatio, 1)) \
                       + " LT_debt_ratio:" + str(round(longTermDebtRatio, 1)) \
                       + " insider%:" + str(round(insiderPerc)) \
                       + " p/52Low:" + str(round(100 * (marketPrice / low_52wk - 1))) + "%"

        print(outputString)
        fileOutput.write(outputString + '\n')
        fileOutput.flush()

    except Exception as e:
        print(comp, "exception", e)
