fileOutput = open('list_US_companyInfo', 'w')

from bs4 import BeautifulSoup
from urllib.request import Request, urlopen

numStocks = 8700

for i in range(1, numStocks, 20):
    urlToScrape = 'https://finviz.com/screener.ashx?v=111&r=' + str(i)

    req = Request(urlToScrape, headers={'User-Agent': 'Mozilla/5.0'})
    webpage = urlopen(req).read()
    soup = BeautifulSoup(webpage, "html.parser")
    tBody = soup.find('div', {"id": "screener-content"})

    for tr in tBody.find_all('tr', {'valign': 'top'}):
        index = tr.find_all('a')[0].get_text(strip=True)
        ticker = tr.find_all('a')[1].get_text(strip=True)
        name = tr.find_all('a')[2].get_text(strip=True)
        sector = tr.find_all('a')[3].get_text(strip=True)
        industry = tr.find_all('a')[4].get_text(strip=True)
        country = tr.find_all('a')[5].get_text(strip=True)
        cap = tr.find_all('a')[6].get_text(strip=True)
        pe = tr.find_all('a')[7].get_text(strip=True)
        price = tr.find_all('a')[8].get_text(strip=True)

        print(index, ticker, name.replace(" ", "_"), sector.replace(" ", "_")
              , industry.replace(" ", "_"), country.replace(" ", "_"), cap, pe, price)

        fileOutput.write(ticker + "\t" + name.replace(" ", "_") + "\t"
                         + sector.replace(" ", "_") + "\t"
                         + industry.replace(" ", "_") + "\t"
                         + country.replace(" ", "_") + "\t"
                         + cap + "\t" + price + '\n')
        fileOutput.flush()
