from selenium import webdriver
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.support.wait import WebDriverWait
import csv
import os
import re
import copy
from datetime import datetime
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import time
import sys
import requests
import shutil
import pathlib
import urllib.parse as urlparse
from urllib.parse import parse_qs
import glob

DIR = os.path.dirname(os.path.abspath(__file__))
print(DIR)
DRIVER_PATH = os.path.join(DIR, "chromedriver.exe")
FIRST_PAGE = int(sys.argv[1]) if len(sys.argv) > 1 else 1
LAST_PAGE = int(sys.argv[2]) if len(sys.argv) > 2 else 13284

FOLDER = 'moveast'

# list page
ARTICLE_SELECTOR = "//div[@id='posts']//article"
#LAST_AELEMENT_SELECTOR = "//div[@class='img-grid animated-grid']/div[contains(@class,'reveal') and not(contains(@class,'pubspace'))][30]/a"
#THUMBNAIL_SELECTOR = "//figure[@class='media-preview']/img"
#TITLE_SELECTOR = "//h1"
#CC_SELECTOR = "//i[@class='fa fa-certificate']/following-sibling::a[1]"
TAG_SELECTOR = "//div[@class='tags']//a"
#AUTHOR_SELECTOR = "//i[@class='fa fa-camera']/following-sibling::span[1]"
#CATEGORY_SELECTOR = "//ul[@class='media-details']//li/em[text()='Category']/following-sibling::strong"
# SOURCE_SELECTOR = "//div[@style='border:1px solid #c3c3c3; background-color:#fbfbfb; padding:10px; font-size:12px; margin-top:5px;']/div[@class='infleft'][text()='Source:']/following-sibling::div[1]/a"
#SIZE_SELECTOR = "//ul[@class='media-details']//li/em[text()='Dimensions']/following-sibling::strong"
# FILE_TYPE_SELECTOR = "//div[@style=\"margin-top:5px; background-image:url('http://res.publicdomainfiles.com/i/dloption.png'); background-repeat:no-repeat;\"]/div[@style='border:1px solid #c9c9c9; float:right; margin-left:5px; width:318px; background-color:#FFFFFF;'][1]//div[@style='font-family:Arial; font-size:11px; padding-left:5px;'][last()]"
#DATE_PUBLISHED_SELECTOR = "//span[@class='posted-on']//a"
DOWNLOAD_SELECTOR = "//div[contains(@class,'photo')]//img[1]"

chrome_options = webdriver.ChromeOptions()
chrome_options.headless = True
# chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=1320,1080")
chrome_options.add_argument('--ignore-certificate-errors')
chrome_options.add_argument('--ignore-ssl-errors')
chrome_options.add_argument('log-level=2')


def selectCatch(driver, selector, type='text', multiple=False):
    try:
        if multiple:
            elements = driver.find_elements_by_xpath(selector)
            elementList = []
            for element in elements:
                elementList.append(getSelect(element, type))

            return elementList
        else:
            element = driver.find_element_by_xpath(selector)

        return getSelect(element, type)

    except NoSuchElementException:
        print('no such element:')
        print(selector)
        return ''


def getSelect(element, type='text'):
    if type == 'text':
        return element.text
    return element.get_attribute(type)


def getDateString():
    now = datetime.now()
    print("now =", now)
    # dd/mm/YY H:M:S
    return now.strftime("%Y.%m.%d_%H.%M.%S")


def makeScreenshot(height, width=1092):
    global driver
    driver.set_window_size(width, height)
    dt = getDateString()
    saveScreenshotPath = os.path.join(dirname, f"screenshot/{dt}.png")
    if not os.path.exists(os.path.dirname(saveScreenshotPath)):
        os.makedirs(os.path.dirname(saveScreenshotPath))
    driver.save_screenshot(saveScreenshotPath)


def checkPageFine(driver, selector, restartDriver=False, sec=3, sleep=0):
    try:
        element = WebDriverWait(driver, sec).until(
            EC.presence_of_element_located(
                (By.XPATH, selector))
        )
        print(f"checked {selector} exists! Proceeding...")

        return True
    except TimeoutException:
        print(
            f"TimeoutException on selecting {selector}! resetting session and retry the page...")
        if (sleep > 0):
            print('sleeping.....')
            time.sleep(5)
            print('waking up.....')
        if restartDriver:
            driver.quit()
            driver = webdriver.Chrome(
                options=chrome_options, executable_path=DRIVER_PATH)
        return False


def isURLvalid(URL):
    regex = re.compile(
        r'^(?:http|ftp)s?://'  # http:// or https://
        # domain...
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)

    return (re.match(regex, URL) is not None)

# if is virtual, the requests object will be returned, else the actual url


def getRealRequest(URL, isVirtual=True, isStream=False):
    global driver

    if (isURLvalid(URL) is not True):
        return ''

    if isVirtual:
        # Open the url image, set stream to True, this will return the stream content.
        r = requests.get(URL, stream=isStream)
        if (URL != r.url):
            print('real url after redirection')
            print(r.url)
        return r
    else:
        driver.get(URL)
        return driver.current_url


def downloadFromURL(URL, isVirtual=True, saveURLB4Redirection=False):
    global y, row, dirname

    if (isURLvalid(URL) is not True):
        print('URL is not valid')
        row.append('')
        row.append('')
        row.append('')
        return False

    print('downloading image...')
    try:
        print('scrapped url')
        oldURL = copy.copy(URL)
        print(oldURL)
        if isVirtual == False:
            print('real url after redirection')
            URL = getRealRequest(URL, False)
            print(URL)

        r = getRealRequest(URL, True, True)

        print('using url')
        print(r.url)
        # Check if the image was retrieved successfully
        if r.status_code == 200:
            # Set decode_content value to True, otherwise the downloaded image file's size will be zero.
            r.raw.decode_content = True

            a = urlparse.urlparse(r.url)
            fileName = os.path.basename(a.path)

            # Open a local file with wb ( write binary ) permission.
            with open(os.path.join(dirname, fileName), 'wb') as f:
                shutil.copyfileobj(r.raw, f)

            print('Image sucessfully Downloaded: ',
                  os.path.join(dirname, fileName))

            if saveURLB4Redirection:
                row.append(oldURL)

            if oldURL == r.url and saveURLB4Redirection:
                row.append('')
            else:
                row.append(r.url)
            row.append(fileName)
            row.append(getDateString())
        else:
            print('Image Couldn\'t be retreived')
            row.append('')
            row.append('')
            row.append('')
    except OSError as e:
        saveErrorDownloadLog(y, URL)


def saveErrorDownloadLog(page, detailUrl):
    logPath = os.path.join(DIR, f"{FOLDER}/error.log")
    logFile = pathlib.Path(logPath)
    if logFile.exists():
        with open(logPath, 'a') as file:
            file.write(f'{page};{detailUrl}\n')
    else:
        with open(logPath, 'w') as file:
            file.write(f'{page};{detailUrl}\n')


def getPage(driver, url):
    print('calling:')
    print(url)
    while True:
        try:
            driver.get(url)
            break
        except TimeoutException as e:
            saveErrorDownloadLog(-1, -1, url)
            print("Page load Timeout occured.")


x = FIRST_PAGE
# driver is for loading listing page
driver = webdriver.Chrome(options=chrome_options, executable_path=DRIVER_PATH)
driver.set_page_load_timeout(40)

while x < LAST_PAGE+1:
    y = 0
    print('subfolder')
    print(x)
    getPage(
        driver, f'https://moveast.me/page/{x}')

    if checkPageFine(driver, ARTICLE_SELECTOR) == False:
        continue

    articles = selectCatch(driver, ARTICLE_SELECTOR, 'href', True)

    yPath = os.path.join(DIR, f"{FOLDER}/{x}/y.txt")
    yFile = pathlib.Path(yPath)
    if yFile.exists():
        fileContent = open(yPath, 'r')
        string = fileContent.readline()
        if string.isdigit():
            y = int(float(string))

    print('len(articles)')
    print(len(articles))

    if y < len(articles):
        dt_string = getDateString()
        listFile = f'list_{dt_string}.csv'
        print('creating '+f'{listFile}...')
        filename = os.path.join(
            DIR, f"{FOLDER}/{x}/{listFile}")
        # print(filename)
        dirname = os.path.dirname(filename)
        print('dirname:')
        print(dirname)
        if not os.path.exists(dirname):
            os.makedirs(dirname)

        with open(filename, 'w', encoding="utf-8", newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['group', 'title', 'tags',
                             'fileName', 'date_downloaded'])
            while y < len(articles):
                print('y')
                print(y)

                imageURLs_in_the_article = selectCatch(
                    driver, f'{ARTICLE_SELECTOR}[{y+1}]{DOWNLOAD_SELECTOR}', 'src', True)

                imageAlts_in_the_article = selectCatch(
                    driver, f'{ARTICLE_SELECTOR}[{y+1}]{DOWNLOAD_SELECTOR}', 'alt', True)

                print(imageURLs_in_the_article)

                i = 0
                for imageURL in imageURLs_in_the_article:

                    title = imageAlts_in_the_article[i]

                    tags = selectCatch(
                        driver, f'{ARTICLE_SELECTOR}[{y+1}]{TAG_SELECTOR}', 'text', True)
                    print('tags')
                    print(tags)
                    row = [f'{y+1}', title, tags]

                    downloadFromURL(imageURL)

                    print(row)
                    writer.writerow(row)

                    i += 1

                y += 1
                fileContent = open(yPath, 'w')
                fileContent.write(str(y))

    if len(articles) > 0:
        x += 1
