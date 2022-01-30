import yahoo_fin.stock_info as si
import datetime

START_DATE = '1/1/2020'
PRICE_INTERVAL = '1mo'

fileOutput = open('reportList', 'w')

with open("tickerList", "r") as file:
    lines = file.read().splitlines()

print(lines)
for comp in lines:
    info = si.get_company_info(comp)
    country = info.loc["country"][0]
    sector = info.loc['sector'][0]
    bs = si.get_balance_sheet(comp)
    # print(comp, country)
    if (country.lower()) == "china":
        print(comp, "NO CHINA")
    # elif not ("retainedEarnings" in bs.index):
    #     print(comp, "has no retained earnings")
    else:
        # print(comp, country)
        # bs = si.get_balance_sheet(comp)

        #
        # if "retainedEarnings" in bs.index:
        #     retainedEarnings = bs.loc["retainedEarnings"][0]
        # else:
        #     print("retained earnings does not exist for ", comp)
        #     retainedEarnings = 0.0

        try:
            cf = si.get_cash_flow(comp)
            incomeStatement = si.get_income_statement(comp)

            equity = bs.loc["totalStockholderEquity"][0]
            totalCurrentAssets = bs.loc["totalCurrentAssets"][0]
            totalCurrentLiab = bs.loc["totalCurrentLiabilities"][0]
            totalAssets = bs.loc["totalAssets"][0]
            totalLiab = bs.loc["totalLiab"][0]
            retainedEarnings = bs.loc["retainedEarnings"][0]

            # IS
            # revenue = incomeStatement.loc["totalRevenue"][0]
            ebit = incomeStatement.loc["ebit"][0]

            # CF
            cfo = cf.loc["totalCashFromOperatingActivities"][0]
            # cfi = cf.loc["totalCashflowsFromInvestingActivities"][0]
            # cff = cf.loc["totalCashFromFinancingActivities"][0]
            marketPrice = si.get_live_price(comp)
            shares = si.get_quote_data(comp)['sharesOutstanding']
        except Exception as e:
            print("error when getting data ", comp, e)
        else:
            marketCap = marketPrice * shares
            currentRatio = totalCurrentAssets / totalCurrentLiab
            debtEquityRatio = totalLiab / (totalAssets - totalLiab)
            retainedEarningsAssetRatio = retainedEarnings / totalAssets
            cfoAssetRatio = cfo / totalAssets
            ebitAssetRatio = ebit / totalAssets

            try:
                assert currentRatio > 1, 'current ratio needs to be bigger than one'
            except AssertionError as ae:
                print(comp, "fails current ratio", currentRatio, ae)

            try:
                assert debtEquityRatio < 1, 'debt equity ratio needs to be less than one'
            except AssertionError as ae:
                print(comp, "fails DE ratio", debtEquityRatio, ae)

            try:
                assert retainedEarnings > 0, "retained earnings needs to be greater than 0"
            except AssertionError as ae:
                print(comp, "fails retained earnings", retainedEarnings, ae)

            try:
                assert cfo > 0, "cfo needs to be greater than 0"
            except AssertionError as ae:
                print(comp, "fails CFO", cfo, ae)

            try:
                assert ebit > 0, "ebit needs to be postive"
            except AssertionError as ae:
                print(datetime.datetime.now().time().strftime("%H:%M"), comp, "fails EBIT", ebit, ae)

            try:
                assert currentRatio > 1, 'current ratio needs to be bigger than one'
                assert debtEquityRatio < 1, 'debt equity ratio needs to be less than one'
                assert retainedEarnings > 0, "retained earnings needs to be greater than 0"
                assert cfo > 0, "cfo needs to be greater than 0"
                assert ebit > 0, "ebit needs to be postive"
            except AssertionError as ae:
                print(comp, "fails assertion", ae)
            else:
                if (currentRatio > 1 and debtEquityRatio < 1 and retainedEarnings > 0
                        and cfo > 0 and ebit > 0):
                    pb = marketCap / equity
                    data = si.get_data(comp, start_date=START_DATE, interval=PRICE_INTERVAL)
                    # print("data ", data)

                    try:
                        dataSize = data['adjclose'].size
                        # print("data size is ", data.size)
                        percentile = 100.0 * (data['adjclose'][-1] - data['adjclose'].min()) / (
                                data['adjclose'].max() - data['adjclose'].min())
                        # percentile = data['adjclose'].rank(method='max').apply(lambda x: 100 * (x - 1) / dataSize)[-1]
                    except Exception as e:
                        print(comp, "percentile issue ", e)
                    else:

                        outputString = " SUCCESS " + comp + " " + country + " " + sector \
                                       + " MV USD:" + str(round(marketCap / 1000000000.0, 2)) \
                                       + " CR:" + str(round(currentRatio, 2)) \
                                       + " D/E:" + str(round(debtEquityRatio, 2)) \
                                       + " RE/A:" + str(round(retainedEarningsAssetRatio, 2)) \
                                       + " cfo/A:" + str(round(cfoAssetRatio, 2)) \
                                       + " ebit/A:" + str(round(ebitAssetRatio, 2)) \
                                       + " p/b:" + str(round(pb, 2)) \
                                       + " 52wk p%: " + str(round(percentile))

                        print(outputString)
                        fileOutput.write(outputString + '\n')
                        fileOutput.flush()
