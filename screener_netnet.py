# screens for netnets
# both HK and US

import yahoo_fin.stock_info as si
import pandas as pd
from currency_scrapeYahoo import getBalanceSheetCurrency
from currency_scrapeYahoo import getListingCurrency
import currency_getExchangeRate
from helperMethods import getFromDF, convertHK

COUNT = 0


def increment():
    global COUNT
    COUNT = COUNT + 1
    return COUNT


START_DATE = '3/1/2020'
DIVIDEND_START_DATE = '1/1/2010'
PRICE_INTERVAL = '1mo'

exchange_rate_dict = currency_getExchangeRate.getExchangeRateDict()

fileOutput = open('list_results_netnet', 'w')

# US Version Starts
# stock_df = pd.read_csv('list_UScompanyInfo', sep=" ", index_col=False,
#                        names=['ticker', 'name', 'sector', 'industry', 'country', 'mv', 'price', 'listingDate'])
#
# stock_df['listingDate'] = pd.to_datetime(stock_df['listingDate'])
#
# listStocks = stock_df[(stock_df['price'] > 1)
#                       & (stock_df['sector'].str
#                          .contains('financial|healthcare', regex=True, case=False) == False)
#                       & (stock_df['listingDate'] < pd.to_datetime('2010-1-1'))
#                       & (stock_df['industry'].str.contains('reit', regex=True, case=False) == False)
#                       & (stock_df['country'].str.lower() != 'china')]['ticker'].tolist()
# US version ends

# HK version STARTS
stock_df = pd.read_csv('list_hkstocks', dtype=object, sep=" ", index_col=False, names=['ticker', 'name'])
stock_df['ticker'] = stock_df['ticker'].astype(str)
# HK Version ENDS

listStocks = stock_df['ticker'].map(lambda x: convertHK(x)).tolist()

print(len(listStocks), listStocks)

for comp in listStocks:
    print(increment())
    try:

        marketPrice = si.get_live_price(comp)

        if marketPrice < 1:
            print(comp, " cent stock ", marketPrice)
            continue

        bs = si.get_balance_sheet(comp, yearly=False)

        retainedEarnings = getFromDF(bs.loc["retainedEarnings"]) if 'retainedEarnings' in bs.index else 0

        # RE>0 ensures that the stock is not a chronic cash burner
        if retainedEarnings < 0:
            print(comp, " retained earnings < 0 ", retainedEarnings)
            continue

        currentAssets = getFromDF(bs.loc["totalCurrentAssets"]) if 'totalCurrentAssets' in bs.index else 0.0

        totalLiab = getFromDF(bs.loc["totalLiab"]) if 'totalLiab' in bs.index else 0.0

        if currentAssets < totalLiab:
            print(comp, " current assets < total liab", round(currentAssets / 1000000000, 2),
                  round(totalLiab / 1000000000, 2))
            continue

        cash = getFromDF(bs.loc['cash']) if 'cash' in bs.index else 0.0
        receivables = getFromDF(bs.loc['netReceivables']) if 'netReceivables' in bs.index else 0.0
        inventory = getFromDF(bs.loc['inventory']) if 'inventory' in bs.index else 0.0

        shares = si.get_quote_data(comp)['sharesOutstanding']
        marketCap = marketPrice * shares

        listingCurr = getListingCurrency(comp)
        bsCurr = getBalanceSheetCurrency(comp, listingCurr)
        exRate = currency_getExchangeRate.getExchangeRate(exchange_rate_dict, listingCurr, bsCurr)

        if (currentAssets - totalLiab) / exRate < marketCap:
            print(comp, listingCurr, bsCurr,
                  'current assets - total liab < mv. CurrAssets Liab MV:',
                  round(currentAssets / 1000000000, 2),
                  round(totalLiab / 1000000000, 2),
                  round(marketCap / 1000000000, 2))
            continue

        outputString = ""

        if (cash - totalLiab) / exRate > marketCap:
            outputString = "cash netnet:" + comp + " " \
                           + listingCurr + bsCurr \
                           + " cash:" + str(round(cash / 1000000000, 2)) \
                           + " L:" + str(round(totalLiab / 1000000000, 2))

        elif (cash + receivables * 0.5 - totalLiab) / exRate > marketCap:
            outputString = "cash receivable netnet:" + comp + " "

        elif (cash + receivables * 0.5 + inventory * 0.3 - totalLiab) / exRate > marketCap:
            outputString = "cash rec inv netnet " + comp

        elif (currentAssets - totalLiab) / exRate > marketCap:
            outputString = 'currentAsset netnet ' + comp
        else:
            outputString = 'undefined net net,check:' + comp

        additionalComment = ""
        if (cash - totalLiab) / exRate - marketCap > 0:
            profit = (cash - totalLiab) / exRate - marketCap
            additionalComment = "clean cash netnet, profit:" + str(round(profit, 2))
        elif (cash + receivables - totalLiab) / exRate - marketCap > 0:
            additionalComment = "receivable conversion rate required: " \
                                + str(round((totalLiab + marketCap * exRate - cash) / receivables, 2))
        elif (cash + 0.5* receivables + inventory - totalLiab) / exRate - marketCap > 0:
            additionalComment = "inventory conversion rate required: " \
                                + str(round((totalLiab + marketCap * exRate - cash - 0.5 * receivables)
                                            / inventory, 2))

        outputString = outputString + " " + listingCurr + bsCurr \
                       + " cash:" + str(round(cash / 1000000000, 2)) \
                       + " rec:" + str(round(receivables / 1000000000, 2)) \
                       + " inv:" + str(round(inventory / 1000000000, 2)) \
                       + " CA:" + str(round(currentAssets / 1000000000, 2)) \
                       + " L:" + str(round(totalLiab / 1000000000, 2)) \
                       + " mv:" + str(round(marketCap / 1000000000, 2)) \
                       + " comment" + additionalComment

        # + ' profit:' + str(round(((cash + 0.5 * receivables
        #                            + 0.3 * inventory - totalLiab) / exRate - marketCap)
        #                          / 1000000000, 2))

        print(outputString)

        fileOutput.write(outputString + '\n')
        fileOutput.flush()


    except Exception as e:
        print(comp, "exception", e)
