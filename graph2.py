from math import pi
from bokeh.io import curdoc
from bokeh.layouts import column, row
from bokeh.models import TextInput, Button, RadioGroup, Paragraph, Label, Range1d, LinearAxis, DataRange1d, FactorRange

from helperMethods import fill0Get, getBarWidth, indicatorFunction, roundB
from scrape_sharesOutstanding import scrapeTotalSharesXueqiu

ANNUALLY = False
FIRST_TIME_GRAPHING = True

from bokeh.layouts import gridplot
from bokeh.models import ColumnDataSource, HoverTool
from bokeh.plotting import figure, show
import yahoo_fin.stock_info as si
import currency_getExchangeRate
from currency_scrapeYahoo import getListingCurrency, getBalanceSheetCurrency
import pandas as pd

pd.set_option('display.expand_frame_repr', False)

HALF_YEAR_WIDE = 15552000000

TICKER = '0001.HK'

global_source = ColumnDataSource(pd.DataFrame())
stockData = ColumnDataSource(pd.DataFrame())
divPriceData = ColumnDataSource(pd.DataFrame())


def getWidthDivGraph():
    if 'year' not in divPriceData.data:
        # print('getwidthdiv year not in data yet')
        return 0

    return 0.8


def my_text_input_handler(attr, old, new):
    global TICKER
    TICKER = new.upper()
    print('new ticker is ', TICKER)


infoParagraph = Paragraph(width=1000, height=500, text='Blank')

# price chart
gPrice = figure(title='prices chart', width=1000, x_axis_type="datetime")
gPrice.xaxis.major_label_orientation = pi / 4
gPrice.grid.grid_line_alpha = 0.3
gPrice.add_tools(HoverTool(tooltips=[('date', '@date{%Y-%m-%d}'), ('close', '@close')],
                           formatters={'@date': 'datetime'}, mode='vline'))

# priceChart.background_fill_color = "#f5f5f5"
gDiv = figure(title="divYld", width=1000)
gDiv.add_tools(HoverTool(tooltips=[('year', '@year'), ("yield", "@yield")], mode='vline'))

gCash = figure(title='cash', x_range=FactorRange(factors=list()))
gCash.title.text = 'cash '
gCash.add_tools(HoverTool(tooltips=[('dateStr', '@dateStr'), ("cash", "@cash")], mode='vline'))

gBook = figure(title='book', x_range=FactorRange(factors=list()))
gBook.title.text = 'Book'
gBook.add_tools(HoverTool(tooltips=[('dateStr', '@dateStr'), ("book", "@netBook")], mode='vline'))

gCurrentRatio = figure(title='currentRatio', x_range=FactorRange(factors=list()))
gRetainedEarnings = figure(title='RetEarnings/A', x_range=FactorRange(factors=list()))
gDE = figure(title='D/E Ratio', x_range=FactorRange(factors=list()))
gPB = figure(title='MV/B Ratio', x_range=FactorRange(factors=list()))
gCFO = figure(title='CFO', x_range=FactorRange(factors=list()))
gCFORatio = figure(title='MV/CFO', x_range=FactorRange(factors=list()))
gSA = figure(title='Sales/Assets Ratio', x_range=FactorRange(factors=list()))
gNetnet = figure(title='netnet Ratio', x_range=FactorRange(factors=list()))
gCFOA = figure(title='CFO/A Ratio', x_range=FactorRange(factors=list()))

gCurrentRatio.add_tools(HoverTool(tooltips=[('date', '@dateStr'), ("cr", "@currentRatio")], mode='vline'))
gRetainedEarnings.add_tools(HoverTool(tooltips=[('date', '@dateStr'), ("Re/A", "@REAssetsRatio")], mode='vline'))

gDE.add_tools(HoverTool(tooltips=[('date', '@dateStr'), ("DERatio", "@DERatio")], mode='vline'))
gPB.add_tools(HoverTool(tooltips=[('date', '@dateStr'), ("PB", "@PB")], mode='vline'))
gCFO.add_tools(HoverTool(tooltips=[('date', '@dateStr'), ("CFO", "@CFO")], mode='vline'))
gCFORatio.add_tools(HoverTool(tooltips=[('date', '@dateStr'), ("PCFO", "@PCFO")], mode='vline'))
gSA.add_tools(HoverTool(tooltips=[('date', '@dateStr'), ("S/A Ratio", "@SalesAssetsRatio")], mode='vline'))
gNetnet.add_tools(HoverTool(tooltips=[('date', '@dateStr'), ("netnet", "@netnetRatio")], mode='vline'))
gCFOA.add_tools(HoverTool(tooltips=[('date', '@dateStr'), ("CFO/A", "@CFOAssetRatio")], mode='vline'))

for figu in [gPrice, gCash, gBook, gDiv, gCurrentRatio, gRetainedEarnings, gDE, gPB, gCFO, gCFORatio, gSA, gNetnet,
             gCFOA]:
    figu.title.text_font_size = '18pt'
    figu.title.align = 'center'

grid = gridplot(
    [[gCash, gBook], [gCurrentRatio, gRetainedEarnings], [gDE, gPB], [gCFO, gCFORatio], [gSA, gNetnet], [gCFOA, None]]
    , width=500, height=500)

exchange_rate_dict = currency_getExchangeRate.getExchangeRateDict()


def resetCallback():
    print('resetting')
    global_source.data = ColumnDataSource.from_df(pd.DataFrame())
    stockData.data = ColumnDataSource.from_df(pd.DataFrame())
    divPriceData.data = ColumnDataSource.from_df(pd.DataFrame())
    infoParagraph.text = ""
    text_input.title = ''
    gPrice.title.text = ''
    print(' cleared source ')


def buttonCallback():
    print(' new ticker is ', TICKER)
    print('annual is ', ANNUALLY)

    try:
        listingCurrency = getListingCurrency(TICKER)
        bsCurrency = getBalanceSheetCurrency(TICKER, listingCurrency)
        print("ticker, listing currency, bs currency, ", TICKER, listingCurrency, bsCurrency)
        exRate = currency_getExchangeRate.getExchangeRate(exchange_rate_dict, listingCurrency, bsCurrency)

    except Exception as e:
        print(e)

    info = si.get_company_info(TICKER)
    infoText = info.loc['country'].item() + "______________" + info.loc['industry'].item() + \
               '______________' + info.loc['sector'].item() + "______________" + info.loc['longBusinessSummary'].item()

    print('info text is ', infoText)
    infoParagraph.text = str(infoText)

    priceData = si.get_data(TICKER)
    priceData.index.name = 'date'
    divData = si.get_dividends(TICKER)
    divPrice = pd.DataFrame()
    if not divData.empty:
        divData.groupby(by=lambda a: a.year)['dividend'].sum()
        divPrice = pd.merge(divData.groupby(by=lambda d: d.year)['dividend'].sum(),
                            priceData.groupby(by=lambda d: d.year)['close'].mean(),
                            left_index=True, right_index=True)
        divPrice.index.name = 'year'
        divPrice['yield'] = divPrice['dividend'] / divPrice['close'] * 100
        divPriceData.data = ColumnDataSource.from_df(divPrice)

    latestPrice = si.get_live_price(TICKER)
    bs = si.get_balance_sheet(TICKER, yearly=ANNUALLY)
    bsT = bs.T
    bsT['REAssetsRatio'] = bsT['retainedEarnings'] / bsT['totalAssets']
    bsT['currentRatio'] = (bsT['cash'] + 0.5 * fill0Get(bsT, 'netReceivables') +
                           0.2 * fill0Get(bsT, 'inventory')) / bsT['totalCurrentLiabilities']
    bsT['netBook'] = bsT['totalAssets'] - bsT['totalLiab'] - fill0Get(bsT, 'goodWill') \
                     - fill0Get(bsT, 'intangibleAssets')
    bsT['DERatio'] = bsT['totalLiab'] / bsT['netBook']
    bsT['priceOnOrAfter'] = bsT.index.map(lambda d: priceData[priceData.index >= d].iloc[0]['adjclose'])
    bsT['priceOnOrAfter'][0] = latestPrice

    shares = si.get_quote_data(TICKER)['sharesOutstanding']

    if TICKER.upper().endswith("HK") and bsCurrency == 'CNY':
        shares = scrapeTotalSharesXueqiu(TICKER)
        print('using xueqiu total shares for china', TICKER, shares)

    bsT['marketCap'] = bsT['priceOnOrAfter'] * shares
    bsT['PB'] = bsT['marketCap'] * exRate / bsT['netBook']
    income = si.get_income_statement(TICKER, yearly=ANNUALLY)
    incomeT = income.T
    bsT['revenue'] = bsT.index.map(
        lambda d: incomeT[incomeT.index == d]['totalRevenue'].item() * indicatorFunction(ANNUALLY))
    bsT['SalesAssetsRatio'] = bsT['revenue'] / bsT['totalAssets']
    cf = si.get_cash_flow(TICKER, yearly=ANNUALLY)
    cfT = cf.T
    bsT['CFO'] = bsT.index.map(
        lambda d: cfT[cfT.index == d]['totalCashFromOperatingActivities'].item() * indicatorFunction(ANNUALLY))
    bsT['PCFO'] = bsT['marketCap'] * exRate / bsT['CFO']
    bsT['netnetRatio'] = ((bsT['cash'] + fill0Get(bsT, 'netReceivables') * 0.8 +
                           fill0Get(bsT, 'inventory') * 0.5) / (bsT['totalLiab'] + exRate * bsT['marketCap']))
    bsT['CFOAssetRatio'] = bsT['CFO'] / bsT['totalAssets']

    bsT['dateStr'] = pd.to_datetime(bsT.index)
    bsT['dateStr'] = bsT['dateStr'].transform(lambda x: x.strftime('%Y-%m-%d'))

    global_source.data = ColumnDataSource.from_df(bsT)
    stockData.data = ColumnDataSource.from_df(priceData)

    print("=============graph now===============")

    updateGraphs()

    compName1 = info.loc['longBusinessSummary'].item().split(' ')[0] if 'longBusinessSummary' in info.index else ""
    compName2 = info.loc['longBusinessSummary'].item().split(' ')[1] if 'longBusinessSummary' in info.index else ""
    # print(' comp name ', compName1, compName2, 'summary', info.loc['longBusinessSummary'].item().split(' '))
    text_input.title = compName1 + ' ' + compName2 + ' ' \
                       + 'shares:' + str(roundB(shares, 0)) + 'B' \
                       + listingCurrency + bsCurrency + '______MV:' + str(roundB(bsT['marketCap'][0], 1)) + 'B' \
                       + "____NetB:" + str(roundB(bsT['netBook'][0] / exRate, 1)) + 'B' \
                       + '____PB:' + str(round(bsT['PB'][0], 2)) \
                       + '____CR:' + str(round(bsT['currentRatio'][0], 1)) \
                       + '____DE:' + str(round(bsT['DERatio'][0], 1)) \
                       + '____RE/A:' + str(round(bsT['REAssetsRatio'][0], 1)) \
                       + '____P/CFO:' + str(round(bsT['PCFO'][0], 1)) \
                       + '____DivYld:' + (str(round(divPrice['yield'].mean(), 1)) if 'yield' in divPrice else '') + '%' \
                       + '____lastDivYld:' \
                       + (str(round(divPrice['yield'].iloc[-1], 1)) if 'yield' in divPrice else '') + '%'

    print("=============graph finished===============")


def updateGraphs():
    global FIRST_TIME_GRAPHING

    print(' updating graphs. FIrst time graphing', FIRST_TIME_GRAPHING)
    print('update price graph')
    lastPrice = round(stockData.data['close'][-1], 2) if 'close' in stockData.data else ''
    gPrice.title.text = ' prices ' + TICKER + '____' + str(lastPrice)

    for figu in [gCash, gBook, gCurrentRatio, gRetainedEarnings, gDE, gPB, gCFO, gCFORatio, gSA, gNetnet, gCFOA]:
        figu.x_range.factors = list(global_source.data['dateStr'][::-1])

    if FIRST_TIME_GRAPHING:
        gPrice.line(x='date', y='close', source=stockData, color='#D06C8A')
        gDiv.vbar(x='year', top='yield', source=divPriceData, width=getWidthDivGraph())

        # cash
        gCash.vbar(x='dateStr', top='cash', source=global_source, width=0.5)

        # book
        gBook.vbar(x='dateStr', top='netBook', source=global_source, width=0.5)

        # current ratio
        gCurrentRatio.vbar(x='dateStr', top='currentRatio', source=global_source, width=0.5)

        # retained earnings/Asset
        gRetainedEarnings.vbar(x='dateStr', top='REAssetsRatio', source=global_source, width=0.5)

        # Debt/Equity
        gDE.vbar(x='dateStr', top='DERatio', source=global_source, width=0.5)

        # P/B
        gPB.vbar(x='dateStr', top='PB', source=global_source, width=0.5)

        # CFO
        gCFO.vbar(x='dateStr', top='CFO', source=global_source, width=0.5)

        # P/CFO
        gCFORatio.vbar(x='dateStr', top='PCFO', source=global_source, width=0.5)

        # Sales/Assets
        gSA.vbar(x='dateStr', top='SalesAssetsRatio', source=global_source, width=0.5)

        # netnet ratio
        gNetnet.vbar(x='dateStr', top='netnetRatio', source=global_source, width=0.5)

        # CFO/A ratio
        gCFOA.vbar(x='dateStr', top='CFOAssetRatio', source=global_source, width=0.5)
        FIRST_TIME_GRAPHING = False


text_input = TextInput(value="0001.HK", title="Label:")
text_input.on_change("value", my_text_input_handler)

button = Button(label="Get Data")
button.on_click(buttonCallback)

button2 = Button(label='Reset')
button2.on_click(resetCallback)


# prelimLabel = Label(width=500, text='abc')


def my_radio_handler(new):
    global ANNUALLY
    ANNUALLY = True if new == 0 else False
    print('ANNUAL IS', ANNUALLY)
    resetCallback()


rg = RadioGroup(labels=['Annual', 'Quarterly'], active=1)
rg.on_click(my_radio_handler)

curdoc().add_root(column(row(button, button2), rg, text_input, gPrice, gDiv, grid, infoParagraph))
