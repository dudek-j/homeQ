from operator import truediv
import re
import time
from statistics import mean
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.common import exceptions as exc

#################################################################################
baseUrl = 'https://www.homeq.se'
searchUrl = baseUrl + '/search?roomMin=2&areaMin=40&rentMax=10000&selectedShapes=metropolitan_area.8%3B8c2a29cf2222d13142db38ba811ab69d5d579f21ead150d5985f68070586548e%3BG%C3%B6teborg'

driver = None


def getAdUrls():
    urls = []
    navigationIndex = 1

    while(True):
        soup = BeautifulSoup(loadSearchPageHTML(), 'html.parser')
        currentUrls = getUrlsFrom(soup)

        urls = urls + currentUrls

        if currentUrls:
            navigationIndex = navigationIndex + 1
            if naviagetToNextPage(soup, navigationIndex):
                continue

        break

    return urls


def getUrlsFrom(soup):
    try:
        adList = soup.find('div', class_='homeq-search-results-list')
        ads = adList.findAll('a', class_='homeq-search-ad-card')

        urls = []
        for ad in ads:
            href = ad['href']
            if href and 'lagenhet' in href:
                urls.append(href)

        return urls
    except:
        return []


def naviagetToNextPage(soup, index):
    try:
        nextPageUrl = soup.find(
            'a', class_='search-page-number', string=[index])['href']
        driver.find_element(
            by=By.XPATH, value=f'//a[@href="{nextPageUrl}"]').click()
        return True
    except:
        return False


def printApartmentCount():
    driver.get(searchUrl)
    soup = BeautifulSoup(loadSearchPageHTML(), 'html.parser')
    print(soup.find('div', class_='homeq-search-page-input-wrapper__total-ads').getText())


def loadSearchPageHTML():
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located(
            (By.CLASS_NAME, "homeq-search-results-list"))
    )

    return driver.find_element(
        by=By.CLASS_NAME, value="homeq-search-page").get_attribute('outerHTML')


def loadADPageHTML():
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located(
            (By.CLASS_NAME, "img-fluid"))
    )

    return driver.find_element(
        by=By.CLASS_NAME, value="homeq-ad").get_attribute('innerHTML')


def extractQueueData(url):
    try:
        driver.get(url)
        soup = BeautifulSoup(loadADPageHTML(), 'html.parser')
        res = soup.find("div", class_="homeq-ad-transparency").getText()
        return parseQueueDataString(res)
    except:
        return None


def parseQueueDataString(string):
    try:
        res = re.search(r'^(\d+)\sköpoäng', string, re.IGNORECASE).group(1)
        return res
    except:
        return None


def acceptCookiePrompt():
    driver.get(searchUrl)
    WebDriverWait(driver, 60).until(
        EC.presence_of_element_located(
            (By.ID, "onetrust-accept-btn-handler"))
    )
    driver.find_element(
        by=By.ID, value='onetrust-accept-btn-handler').click()


def initDriver():
    global driver
    options = Options()
    options.headless = True
    driver = webdriver.Chrome(options=options)
    driver.set_window_position(0, 0)
    driver.set_window_size(1920, 1080)


def run():
    initDriver()
    acceptCookiePrompt()
    urls = getAdUrls()

    dataPoints = []

    for idx, url in enumerate(urls):
#        print(f'{idx + 1}/{len(urls)}')
        queueData = extractQueueData(url)
        if queueData:
            dataPoints.append((queueData, url))
        time.sleep(2)

    dataPoints.sort(key=lambda dp: int(dp[0]))

    for point in dataPoints:
        print(f'{point[0]}: {point[1]}')

    print(mean(map(lambda x: int(x[0]), dataPoints)))

    driver.close()


run()
