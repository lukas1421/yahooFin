import os
import statistics
import sys
from datetime import datetime, timedelta
import yahoo_fin.stock_info as si
import pandas as pd
from Market import Market
from currency_scrapeYahoo import getBalanceSheetCurrency
from currency_scrapeYahoo import getListingCurrency
import currency_getExchangeRate
from helperMethods import getFromDF, getFromDFYearly, roundB, boolToString, getInsiderOwnership

MARKET = Market.US
yearlyFlag = False
INSIDER_OWN_MIN = 10
ONE_YEAR_AGO = datetime.today() - timedelta(weeks=53)

COUNT = 0


def increment():
    global COUNT
    COUNT = COUNT + 1
    return COUNT


# yearAgo = datetime.today() - timedelta(weeks=53)
# START_DATE = (datetime.today() - timedelta(weeks=52 * 10)).strftime('%-m/%-d/%Y')
# PRICE_START_DATE = (datetime.today() - timedelta(weeks=52 * 2)).strftime('%-m/%-d/%Y')
# PRICE_START_DATE = (datetime.today() - timedelta(weeks=52 * 2)).strftime('%-m/%-d/%Y')
# DIVIDEND_START_DATE = (datetime.today() - timedelta(weeks=52 * 10)).strftime('%-m/%-d/%Y')
PRICE_INTERVAL = '1wk'

exchange_rate_dict = currency_getExchangeRate.getExchangeRateDict()

fileOutput = open('list_results_US', 'w')

stock_df = pd.read_csv('list_US_Tickers', sep=" ", index_col=False,
                       names=['ticker', 'name', 'sector', 'industry', 'country', 'mv', 'price'])
print(stock_df)

listStocks = stock_df[~stock_df['sector'].str.contains('financial', regex=True, case=False)
                      & (stock_df['industry'].str.contains('reit', regex=True, case=False) == False)
                      & (stock_df['country'].str.lower() != 'china')]['ticker'].tolist()

# listStocks = stock_df[(stock_df['price'] > 1)
#                       & (stock_df['sector'].str
#                          .contains('financial|healthcare', regex=True, case=False) == False)
#                       & (stock_df['industry'].str.contains('reit', regex=True, case=False) == False)
#                       & (stock_df['country'].str.lower() != 'china')]['ticker'].tolist()
# listStocks = stock_df['ticker'].tolist()
# listStocks = ['CENT']

print(len(listStocks), listStocks)

for comp in listStocks:
    try:
        companyName = stock_df.loc[stock_df['ticker'] == comp]['name'].item()

        print(increment())
        print(comp, companyName)

        try:
            info = si.get_company_info(comp)
        except Exception as e:
            print(e)
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(exc_type, fname, exc_tb.tb_lineno)
            info = ""

        country = getFromDF(info, "country")
        sector = getFromDF(info, 'sector')

        if 'real estate' in sector.lower() or 'financial' in sector.lower():
            print(comp, " no real estate or financial ", sector)
            continue

        # if marketPrice <= 1:
        #     print(comp, 'market price < 1: ', marketPrice)
        #     continue

        bs = si.get_balance_sheet(comp, yearly=yearlyFlag)

        if bs.empty:
            print(comp, "balance sheet is empty")
            continue

        retainedEarnings = getFromDF(bs, "retainedEarnings")

        if retainedEarnings <= 0:
            print(comp, " retained earnings < 0 ", retainedEarnings)
            continue

        currL = getFromDF(bs, "totalCurrentLiabilities")

        cash = getFromDF(bs, "cash")
        receivables = getFromDF(bs, 'netReceivables')
        inventory = getFromDF(bs, 'inventory')

        currRatio = (cash + 0.8 * receivables + 0.5 * inventory) / currL

        if currRatio <= 0.5:
            print(comp, "current ratio < 0.5", currRatio)
            continue

        totalAssets = getFromDF(bs, "totalAssets")
        totalL = getFromDF(bs, "totalLiab")
        goodWill = getFromDF(bs, 'goodWill')
        intangibles = getFromDF(bs, 'intangibleAssets')
        tangible_Equity = totalAssets - totalL - goodWill - intangibles

        if tangible_Equity < 0:
            print(comp, "de ratio> 1. or tangible equity < 0 ", tangible_Equity)
            continue

        debtEquityRatio = totalL / tangible_Equity

        # if debtEquityRatio > 1:
        #     print(comp, "de ratio > 1 ", debtEquityRatio)
        #     continue

        incomeStatement = si.get_income_statement(comp, yearly=yearlyFlag)

        cf = si.get_cash_flow(comp, yearly=yearlyFlag)
        cfo = getFromDFYearly(cf, "totalCashFromOperatingActivities", yearlyFlag)
        dep = getFromDFYearly(cf, "depreciation", yearlyFlag)
        capex = getFromDFYearly(cf, "capitalExpenditures", yearlyFlag)

        if cfo <= 0 or cfo < dep:
            print(comp, "cfo <= 0 or cfo < dep", cfo, dep)
            continue

        shares = si.get_quote_data(comp)['sharesOutstanding']

        listingCurrency = getListingCurrency(comp)
        bsCurrency = getBalanceSheetCurrency(comp, listingCurrency)
        # print("listing currency, bs currency, ", listingCurrency, bsCurrency)
        exRate = currency_getExchangeRate.getExchangeRate(exchange_rate_dict, listingCurrency, bsCurrency)

        marketPrice = si.get_live_price(comp)
        marketCap = marketPrice * shares

        fcf = cfo - dep
        pb = marketCap * exRate / tangible_Equity
        pFCF = marketCap * exRate / fcf
        print("MV, cfo", roundB(marketCap, 2), roundB(cfo, 2))

        # if pb >= 0.6 or pb <= 0:
        #     print(comp, 'pb > 0.6 or pb <= 0', pb)
        #     continue
        #
        if pFCF > 6:
            print(comp, 'pFCF > 6', pFCF)
            continue

        revenue = getFromDFYearly(incomeStatement, "totalRevenue", yearlyFlag)

        retainedEarningsAssetRatio = retainedEarnings / totalAssets
        fcfAssetRatio = fcf / totalAssets
        # ebitAssetRatio = ebit / totalAssets

        priceData = si.get_data(comp, interval=PRICE_INTERVAL)
        print("start date ", priceData.index[0].strftime('%-m/%-d/%Y'))
        data52wk = priceData.loc[priceData.index > ONE_YEAR_AGO]
        percentile = 100.0 * (marketPrice - data52wk['low'].min()) / (data52wk['high'].max() - data52wk['low'].min())
        low_52wk = data52wk['low'].min()
        # avgDollarVol = (data[-10:]['close'] * data[-10:]['volume']).sum() / 10
        medianDollarVol = statistics.median(priceData[-10:]['close'] * priceData[-10:]['volume']) / 5

        # insiderPerc = ownershipDic[comp]
        insiderPerc = float(si.get_holders(comp).get('Major Holders')[0][0].rstrip("%"))
        print(comp, "insider percent", insiderPerc)

        divs = si.get_dividends(comp)

        yearSpan = 2021 - priceData[:1].index.item().year + 1
        divPrice = pd.merge(divs.groupby(by=lambda d: d.year)['dividend'].sum(),
                            priceData.groupby(by=lambda d: d.year)['close'].mean(), left_index=True, right_index=True)
        divPrice['yield'] = divPrice['dividend'] / divPrice['close']
        print('divprice', divPrice)

        divYieldAll = divPrice[divPrice.index != 2022]['yield'].sum() / yearSpan \
            if not divPrice[divPrice.index != 2022].empty else 0

        divLastYearYield = divPrice.loc[2021]['yield'] if 2021 in divPrice.index else 0
        print('div yield all', divYieldAll, 'lastyear', divLastYearYield)

        schloss = pb < 1 and marketPrice < low_52wk * 1.1 and insiderPerc > INSIDER_OWN_MIN
        netnet = (cash + receivables * 0.8 + inventory * 0.5 - totalL) / exRate - marketCap > 0
        magic6 = pFCF < 6 and (divYieldAll >= 0.06 or divLastYearYield >= 0.06)
        pureHighYield = (divYieldAll >= 0.06 or divLastYearYield >= 0.06)

        if schloss or netnet or magic6 or pureHighYield:
            outputString = comp + " " + " " + companyName + ' ' \
                           + " dai$Vol:" + str(round(medianDollarVol / 1000000)) + "M " \
                           + country.replace(" ", "_") + " " \
                           + sector.replace(" ", "_") + " " + listingCurrency + bsCurrency \
                           + boolToString(schloss, "schloss") + boolToString(netnet, "netnet") \
                           + boolToString(magic6, "magic6") + boolToString(pureHighYield, 'highYield') \
                           + " MV:" + str(roundB(marketCap, 1)) + 'B' \
                           + " B:" + str(roundB(tangible_Equity / exRate, 1)) + 'B' \
                           + " P/FCF:" + str(round(pFCF, 2)) \
                           + " DEP/CFO:" + str(round(dep / cfo, 2)) \
                           + " CAPEX/CFO:" + str(round(capex / cfo, 2)) \
                           + " P/B:" + str(round(pb, 1)) \
                           + " C/R:" + str(round(currRatio, 2)) \
                           + " D/E:" + str(round(debtEquityRatio, 2)) \
                           + " RetEarning/A:" + str(round(retainedEarningsAssetRatio, 2)) \
                           + " S/A:" + str(round(revenue / totalAssets, 2)) \
                           + " fcf/A:" + str(round(fcfAssetRatio, 2)) \
                           + " 52w_p%:" + str(round(percentile)) \
                           + " divYldAll:" + str(round(divYieldAll * 100)) + "%" \
                           + " divYldLastYear:" + str(round(divLastYearYield * 100)) + "%" \
                           + " insider%: " + str(round(insiderPerc)) + "%"

            print(outputString)
            fileOutput.write(outputString + '\n')
            fileOutput.flush()

    except Exception as e:
        print(comp, "exception", e)
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print(exc_type, fname, exc_tb.tb_lineno)
        fileOutput.flush()
