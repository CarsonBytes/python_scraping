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
import sys
import urllib.parse as urlparse
from urllib.parse import parse_qs
import glob
from urllib.request import urlopen, Request
from selenium.webdriver.support import expected_conditions as EC
import json
from bs4 import BeautifulSoup

DIR = os.path.dirname(os.path.abspath(__file__))
print(DIR)
DRIVER_PATH = os.path.join(DIR, "chromedriver.exe")

FOLDER = 'realisticshots'
#KEYWORD = 'city'

# list page
AELEMENTS_SELECTOR = "//div[@class='photo']/a"
#LAST_AELEMENT_SELECTOR = "//div[@class='img-grid animated-grid']/div[contains(@class,'reveal') and not(contains(@class,'pubspace'))][30]/a"

# detail page
THUMBNAIL_SELECTOR = "//div[@class='photo']/a/img"
#ID_SELECTOR = "//header/dl/dd"
#TITLE_SELECTOR = "//h1"
TAG_SELECTOR = "//div[@class='tags']/a"
#CATEGORY_SELECTOR = "//a[@rel='category tag']"
#CC_SELECTOR = "//h5[text()='Check license']/following-sibling::a[1]"
AUTHOR_SELECTOR = "//div[@class='captions']/p/a[1]"
#SOURCE_SELECTOR = "//div[contains(text(),'Source')]"
#DATE_CREATED_SELECTOR = "//td[text()='Created']//following-sibling::td[1]"
#SIZE_SELECTOR = "//div[@id='detail_content']/div[1]"
# FILE_TYPE_SELECTOR = "//div[@style=\"margin-top:5px; background-image:url('http://res.publicdomainfiles.com/i/dloption.png'); background-repeat:no-repeat;\"]/div[@style='border:1px solid #c9c9c9; float:right; margin-left:5px; width:318px; background-color:#FFFFFF;'][1]//div[@style='font-family:Arial; font-size:11px; padding-left:5px;'][last()]"
# DOWNLOAD_OPTION_SELECTOR = "//span[text()='download for free']"
# DOWNLOAD_OPTION2_SELECTOR = "//div[@class='download-options']/label[@for='download-option'][last()]"
DOWNLOAD_SELECTOR = "//div[@class='photo']/a"

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


def makeScreenshot(driver, height, width=1092):
    driver.set_window_size(width, height)
    dt = getDateString()
    saveScreenshotPath = os.path.join(dirname, f"screenshot/{dt}.png")
    if not os.path.exists(os.path.dirname(saveScreenshotPath)):
        os.makedirs(os.path.dirname(saveScreenshotPath))
    driver.save_screenshot(saveScreenshotPath)


def checkPageFine(driver, selector, restartDriver=False, sec=3, sleep=0):
    global chrome_options, DRIVER_PATH
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
    global x, y, detailUrls, row, dirname

    if (isURLvalid(URL) is not True):
        print('URL is not valid')
        row.append('')
        row.append('')
        row.append('')
        saveErrorDownloadLog(y, detailUrls[y])
        return False

    print('downloading image...')
    try:
        if isVirtual == False:
            print('old url before redirection')
            oldURL = copy.copy(URL)
            print(oldURL)
            print('real url after redirection')
            URL = getRealRequest(URL, False)
            print(URL)

        r = getRealRequest(URL, True, True)
        # Check if the image was retrieved successfully
        if r.status_code == 200:
            # Set decode_content value to True, otherwise the downloaded image file's size will be zero.
            r.raw.decode_content = True

            a = urlparse.urlparse(URL)
            fileName = os.path.basename(a.path)

            # Open a local file with wb ( write binary ) permission.
            with open(os.path.join(dirname, fileName), 'wb') as f:
                shutil.copyfileobj(r.raw, f)

            print('Image sucessfully Downloaded: ',
                  os.path.join(dirname, fileName))
            row.append(imageURL)
            row.append(fileName)
            row.append(getDateString())
        else:
            print('Image Couldn\'t be retreived')
            row.append('')
            row.append('')
            row.append('')
    except OSError as e:
        saveErrorDownloadLog(y, detailUrls[y])
        y += 1


def saveErrorDownloadLog(order, detailUrl):
    logPath = os.path.join(DIR, f"{FOLDER}/error.log")
    logFile = pathlib.Path(logPath)
    if logFile.exists():
        with open(logPath, 'a') as file:
            file.write(f'{order};{detailUrl}\n')
    else:
        with open(logPath, 'w') as file:
            file.write(f'{order};{detailUrl}\n')

def getMetaTags(url):
    out = {}
    r = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    html = urlopen(r).read().decode('utf-8')
    m = re.findall("property=\"([^\"]*)\" content=\"([^\"]*)\"", html)
    for i in m:
        out[i[0]] = i[1]
    return out


def getValueFromArray(array, key):
    try:
        result = array[key]
    except KeyError as e:
        print('KeyError')
        print(e)
        result = ''
    return result

def get_ld_json(url: str) -> dict:
    parser = "html.parser"
    req = requests.get(url)
    soup = BeautifulSoup(req.text, parser)
    return json.loads("".join(soup.find("script", {"type":"application/ld+json"}).contents))

previous_file = 'abc'
latest_file = 'abc'

# driver is for loading listing page
driver = webdriver.Chrome(options=chrome_options, executable_path=DRIVER_PATH)

# driver2 is for loading detail page and download
driver2 = webdriver.Chrome(options=chrome_options, executable_path=DRIVER_PATH)
listingPage = f'https://realisticshots.com/'
driver.get(listingPage)

print('listingPage:')
print(listingPage)

lastLenDetailURLs = 0
y = 0
while True:

    print('subfolder')
    print(lastLenDetailURLs)

    dt_string = getDateString()
    listFile = f'list_{dt_string}.csv'
    print('creating '+f'{listFile}...')
    filename = os.path.join(DIR, f"{FOLDER}/{lastLenDetailURLs}/{listFile}")
    # print(filename)
    dirname = os.path.dirname(filename)
    print('dirname:')
    print(dirname)
    if not os.path.exists(dirname):
        os.makedirs(dirname)

    if checkPageFine(driver, AELEMENTS_SELECTOR) == False:
        continue

    detailUrls = selectCatch(driver, AELEMENTS_SELECTOR, 'href', True)

    yPath = os.path.join(DIR, f"{FOLDER}/y.txt")
    yFile = pathlib.Path(yPath)
    if yFile.exists():
        fileContent = open(yPath, 'r')
        string = fileContent.readline()
        if string.isdigit():
            y = int(float(string))

    retrialTimes = 0
    maxRetrialTimes = 10
    isReachMaxRetrialTimes = False
    while len(detailUrls) <= lastLenDetailURLs:
        driver.execute_script("window.scrollTo(0, 0)")
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight)")
        detailUrls = selectCatch(driver, AELEMENTS_SELECTOR, 'href', True)
        print('checking for more detail URLs total:')
        print(len(detailUrls))
        retrialTimes += 1
        print('retrial times: #')
        print(retrialTimes)
        if retrialTimes >= maxRetrialTimes:
            isReachMaxRetrialTimes = True
            break
        time.sleep(1)

    if isReachMaxRetrialTimes:
        print('reached max retrial times')
        break

    print('len(detailUrls)')
    print(len(detailUrls))
    # print(detailUrls)
    with open(filename, 'w', encoding="utf-8", newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['detailUrl', 'tags', 'author', 'date_published', 'fileURL',
                         'fileName', 'date_downloaded'])
        while y < len(detailUrls):
            isTimeout = False

            print('y')
            print(y)
            print('folder:')
            print(dirname)

            row = [detailUrls[y]]
            print('detailUrl')
            print(detailUrls[y])

            driver2.get(detailUrls[y])

            thumbnailUrl = selectCatch(driver2, THUMBNAIL_SELECTOR, 'src')
            print('thumbnailUrl')
            print(thumbnailUrl)
            if thumbnailUrl == '':
                print('thumbnailUrl is empty, logged and skip to next one')
                saveErrorDownloadLog(y, detailUrls[y])
                y += 1
                continue

            tags = selectCatch(driver2, TAG_SELECTOR, 'text', True)
            print('tags')
            print(tags)
            row.append(tags)

            author = selectCatch(driver2, AUTHOR_SELECTOR)
            print('author')
            print(author)
            row.append(author)

            author = selectCatch(driver2, AUTHOR_SELECTOR)
            print('author')
            print(author)
            row.append(author)

            jsonData = get_ld_json(detailUrls[y])
            print('date_published')
            print(jsonData['datePublished'])
            row.append(jsonData['datePublished'])

            """ result = selectCatch(driver, AUTHOR_SELECTOR)
            result = result.splitlines()
            author = ''
            size = ''
            filesize = ''
            for line in result:
                if "Uploaded by" in line:
                    author = line.replace('Uploaded by: ', '')
                if "Resolution:" in line:
                    size = line.replace('Resolution: ', '')
                    size = size.split(" ", 1)
                    size = size[0]
                if "File size" in line:
                    filesize = line.replace('File size: ', '')
                    filesize = filesize.split(" ", 1)
                    filesize = filesize[0] 

            print('author')
            print(author)
            row.append(author)
            print('size')
            print(size)
            row.append(size)
            print('filesize')
            print(filesize)
            row.append(filesize)"""

            makeScreenshot(driver2, 1500)

            if checkPageFine(driver2, DOWNLOAD_SELECTOR) == False:
                continue

            imageURL = selectCatch(driver2, DOWNLOAD_SELECTOR, 'href')
            print('imageURL')
            print(imageURL)

            downloadFromURL(imageURL)

            print(row)
            writer.writerow(row)
            y += 1
            fileContent = open(yPath, 'w')
            fileContent.write(str(y))
        lastLenDetailURLs = len(detailUrls)
