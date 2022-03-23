from math import pi
from bokeh.io import curdoc
from bokeh.layouts import column, row
from bokeh.models import TextInput, Button, RadioGroup

from helperMethods import fill0Get, getBarWidth, indicatorFunction

ANNUALLY = False

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


def my_text_input_handler(attr, old, new):
    global TICKER
    TICKER = new
    print('new ticker is ', TICKER)


priceChart = figure(title='prices chart', width=1000, x_axis_type="datetime")
priceChart.xaxis.major_label_orientation = pi / 4
priceChart.grid.grid_line_alpha = 0.3
# priceChart.background_fill_color = "#f5f5f5"
pDiv = figure(title="divYld", width=1000)

pCash = figure(title='cash', x_axis_type="datetime")
p1 = figure(title='currentRatio', x_axis_type="datetime")
p2 = figure(title='RetEarnings/A', x_axis_type="datetime")
p3 = figure(title='D/E Ratio', x_axis_type="datetime")
p4 = figure(title='P/B Ratio', x_axis_type="datetime")
p5 = figure(title='P/CFO Ratio', x_axis_type="datetime")
p6 = figure(title='Sales/Assets Ratio', x_axis_type="datetime")
p7 = figure(title='netnet Ratio', x_axis_type="datetime")
p8 = figure(title='CFO/A Ratio', x_axis_type="datetime")
for figu in [priceChart, pCash, pDiv, p1, p2, p3, p4, p5, p6, p7, p8]:
    figu.title.text_font_size = '18pt'
    figu.title.align = 'center'

grid = gridplot([[pCash, None], [p1, p2], [p3, p4], [p5, p6], [p7, p8]], width=500, height=500)

exchange_rate_dict = currency_getExchangeRate.getExchangeRateDict()
global_source = ColumnDataSource(pd.DataFrame())
stockData = ColumnDataSource(pd.DataFrame())
divPriceData = ColumnDataSource(pd.DataFrame())


def resetCallback():
    print('resetting')
    global_source.data = ColumnDataSource.from_df(pd.DataFrame())
    stockData.data = ColumnDataSource.from_df(pd.DataFrame())
    divPriceData.data = ColumnDataSource.from_df(pd.DataFrame())
    updateGraphs()
    print(' cleared source ')


def buttonCallback():
    global TICKER
    print(' new ticker is ', TICKER)
    print('annual is ', ANNUALLY)

    print('clearing graphs')
    global_source.data = ColumnDataSource.from_df(pd.DataFrame())
    stockData.data = ColumnDataSource.from_df(pd.DataFrame())
    divPriceData.data = ColumnDataSource.from_df(pd.DataFrame())

    updateGraphs()
    print('clearing graphs done')

    try:
        listingCurrency = getListingCurrency(TICKER)
        bsCurrency = getBalanceSheetCurrency(TICKER, listingCurrency)
        print("ticker, listing currency, bs currency, ", TICKER, listingCurrency, bsCurrency)
        exRate = currency_getExchangeRate.getExchangeRate(exchange_rate_dict, listingCurrency, bsCurrency)

    except Exception as e:
        print(e)

    print('ticker exrate', TICKER, listingCurrency, bsCurrency, exRate)
    price = si.get_live_price(TICKER)
    print(' ticker price ', TICKER, price)
    priceData = si.get_data(TICKER)
    priceData.index.name = 'date'
    divData = si.get_dividends(TICKER)
    divData.groupby(by=lambda a: a.year)['dividend'].sum()
    divPrice = pd.merge(divData.groupby(by=lambda d: d.year)['dividend'].sum(),
                        priceData.groupby(by=lambda d: d.year)['close'].mean(),
                        left_index=True, right_index=True)
    divPrice.index.name = 'year'
    divPrice['yield'] = divPrice['dividend'] / divPrice['close']
    # print('div price ', divPrice)
    # updatePriceGraph(priceData[-300:])

    bs = si.get_balance_sheet(TICKER, yearly=ANNUALLY)
    bsT = bs.T
    bsT['REAssetsRatio'] = bsT['retainedEarnings'] / bsT['totalAssets']
    bsT['currentRatio'] = (bsT['cash'] + 0.5 * fill0Get(bsT, 'netReceivables') +
                           0.2 * fill0Get(bsT, 'inventory')) / bsT['totalCurrentLiabilities']
    bsT['netBook'] = bsT['totalAssets'] - bsT['totalLiab'] - fill0Get(bsT, 'goodWill') \
                     - fill0Get(bsT, 'intangibleAssets')
    bsT['DERatio'] = bsT['totalLiab'] / bsT['netBook']
    bsT['priceOnOrAfter'] = bsT.index.map(lambda d: priceData[priceData.index >= d].iloc[0]['adjclose'])
    shares = si.get_quote_data(TICKER)['sharesOutstanding']
    bsT['marketCap'] = bsT['priceOnOrAfter'] * shares * exRate
    bsT['PB'] = bsT['marketCap'] / bsT['netBook']
    income = si.get_income_statement(TICKER, yearly=ANNUALLY)
    incomeT = income.T
    bsT['revenue'] = bsT.index.map(lambda d: incomeT[incomeT.index == d]['totalRevenue'] * indicatorFunction(ANNUALLY))
    bsT['SalesAssetsRatio'] = bsT['revenue'] / bsT['totalAssets']
    cf = si.get_cash_flow(TICKER, yearly=ANNUALLY)
    cfT = cf.T
    bsT['CFO'] = bsT.index.map(
        lambda d: cfT[cfT.index == d]['totalCashFromOperatingActivities'] * indicatorFunction(ANNUALLY))
    bsT['PCFO'] = bsT['marketCap'] / bsT['CFO']
    bsT['netnetRatio'] = ((bsT['cash'] + fill0Get(bsT, 'netReceivables') * 0.5 +
                           fill0Get(bsT, 'inventory') * 0.2) - bsT['totalLiab']) / exRate / bsT['marketCap']
    bsT['CFOAssetRatio'] = bsT['CFO'] / bsT['totalAssets']
    global_source.data = ColumnDataSource.from_df(bsT)
    stockData.data = ColumnDataSource.from_df(priceData)
    divPriceData.data = ColumnDataSource.from_df(divPrice)

    print('divpricedata.data length', len(divPriceData.data['year']))

    print("=============graph now===============")
    updateGraphs()
    print("=============graph finished===============")


def getWidthDivGraph():
    if 'year' not in divPriceData.data:
        print('getwidthdiv year not in data yet')
        return 0

    print("get width div graph", 20 / len(divPriceData.data['year']))
    return 20 / len(divPriceData.data['year'])


def updateGraphs():
    print('update price graph')
    priceChart.line(x='date', y='close', source=stockData, color='#D06C8A')
    priceChart.add_tools(HoverTool(tooltips=[('date', '@date{%Y-%m-%d}'), ('close', '@close')],
                                   formatters={'@date': 'datetime'}, mode='vline'))

    pDiv.vbar(x='year', top='yield', source=divPriceData, width=getWidthDivGraph())
    pDiv.add_tools(HoverTool(tooltips=[('year', '@year'), ("yield", "@yield")], mode='vline'))

    pCash.title.text = 'cash ' + TICKER
    pCash.vbar(x='endDate', top='cash', source=global_source, width=getBarWidth(ANNUALLY))
    pCash.add_tools(HoverTool(tooltips=[('date', '@endDate{%Y-%m-%d}'), ("cash", "@cash")],
                              formatters={'@endDate': 'datetime'}, mode='vline'))

    # current ratio
    p1.add_tools(HoverTool(tooltips=[('date', '@endDate{%Y-%m-%d}'), ("cr", "@currentRatio")],
                           formatters={'@endDate': 'datetime'}, mode='vline'))
    p1.vbar(x='endDate', top='currentRatio', source=global_source, width=getBarWidth(ANNUALLY))

    # retained earnings/Asset
    p2.vbar(x='endDate', top='REAssetsRatio', source=global_source, width=getBarWidth(ANNUALLY))
    p2.add_tools(HoverTool(tooltips=[('date', '@endDate{%Y-%m-%d}'), ("Re/A", "@REAssetsRatio")],
                           formatters={'@endDate': 'datetime'}, mode='vline'))

    # Debt/Equity
    p3.vbar(x='endDate', top='DERatio', source=global_source, width=getBarWidth(ANNUALLY))
    p3.add_tools(HoverTool(tooltips=[('date', '@endDate{%Y-%m-%d}'), ("DERatio", "@DERatio")],
                           formatters={'@endDate': 'datetime'}, mode='vline'))

    # P/B
    p4.vbar(x='endDate', top='PB', source=global_source, width=getBarWidth(ANNUALLY))
    p4.add_tools(HoverTool(tooltips=[('date', '@endDate{%Y-%m-%d}'), ("PB", "@PB")],
                           formatters={'@endDate': 'datetime'}, mode='vline'))
    # P/CFO
    p5.vbar(x='endDate', top='PCFO', source=global_source, width=getBarWidth(ANNUALLY))
    p5.add_tools(HoverTool(tooltips=[('date', '@endDate{%Y-%m-%d}'), ("PCFO", "@PCFO")],
                           formatters={'@endDate': 'datetime'}, mode='vline'))

    # Sales/Assets
    p6.vbar(x='endDate', top='SalesAssetsRatio', source=global_source, width=getBarWidth(ANNUALLY))
    p6.add_tools(HoverTool(tooltips=[('date', '@endDate{%Y-%m-%d}'), ("S/A Ratio", "@SalesAssetsRatio")],
                           formatters={'@endDate': 'datetime'}, mode='vline'))

    # netnet ratio
    p7.vbar(x='endDate', top='netnetRatio', source=global_source, width=getBarWidth(ANNUALLY))
    p7.add_tools(HoverTool(tooltips=[('date', '@endDate{%Y-%m-%d}'), ("netnet", "@netnetRatio")],
                           formatters={'@endDate': 'datetime'}, mode='vline'))

    # CFO/A ratio
    p8.vbar(x='endDate', top='CFOAssetRatio', source=global_source, width=getBarWidth(ANNUALLY))
    p8.add_tools(HoverTool(tooltips=[('date', '@endDate{%Y-%m-%d}'), ("CFO/A", "@CFOAssetRatio")],
                           formatters={'@endDate': 'datetime'}, mode='vline'))


text_input = TextInput(value="0001.HK", title="Label:")
text_input.on_change("value", my_text_input_handler)

button = Button(label="Get Data")
button.on_click(buttonCallback)

button2 = Button(label='Reset')
button2.on_click(resetCallback)


def my_radio_handler(new):
    global ANNUALLY
    ANNUALLY = True if new == 0 else False
    print('ANNUAL IS', ANNUALLY)


rg = RadioGroup(labels=['Annual', 'Quarterly'], active=1)
rg.on_click(my_radio_handler)

curdoc().add_root(column(row(button, button2), rg, text_input, priceChart, pDiv, grid))
