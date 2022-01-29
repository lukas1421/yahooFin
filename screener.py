import yahoo_fin.stock_info as si


def main():
    with open("tickerList", "r") as file:
        lines = file.read().splitlines()

    print(lines)
    for comp in lines:
        info = si.get_company_info(comp)
        country = info.loc["country"][0]
        sector = info.loc['sector'][0]
        # print(comp, country)
        if (country.lower()) == "china":
            print(comp, "NO CHINA")
        else:
            # print(comp, country)
            bs = si.get_balance_sheet(comp)
            cf = si.get_cash_flow(comp)
            incomeStatement = si.get_income_statement(comp)

            retainedEarnings = bs.loc["retainedEarnings"][0]
            equity = bs.loc["totalStockholderEquity"][0]
            totalCurrentAssets = bs.loc["totalCurrentAssets"][0]
            totalCurrentLiab = bs.loc["totalCurrentLiabilities"][0]
            totalAssets = bs.loc["totalAssets"][0]
            totalLiab = bs.loc["totalLiab"][0]

            # IS
            revenue = incomeStatement.loc["totalRevenue"][0]
            EBIT = incomeStatement.loc["ebit"][0]

            # CF
            cfo = cf.loc["totalCashFromOperatingActivities"][0]
            cfi = cf.loc["totalCashflowsFromInvestingActivities"][0]
            cff = cf.loc["totalCashFromFinancingActivities"][0]

            print(comp, country,
                  "CR", round(totalCurrentAssets / totalCurrentLiab, 2),
                  "D/E", round(totalLiab / (totalAssets - totalLiab), 2),
                  "RE/A", round(retainedEarnings / totalAssets, 2),
                  "cfo/A", round(cfo / totalAssets, 2),
                  "EBIT/A", round(EBIT / totalAssets, 2))


if __name__ == "__main__":
    main()
