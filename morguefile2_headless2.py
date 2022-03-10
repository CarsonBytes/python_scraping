from selenium import webdriver
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException, ElementClickInterceptedException
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.common.action_chains import ActionChains
from urllib.parse import parse_qs
import urllib.parse as urlparse
from urllib.request import urlopen, Request, urlretrieve
from datetime import datetime
import csv
import os
import re
import copy
import time
import sys
import requests
import shutil
import pathlib
import cgi
import glob
import json


DIR = os.path.dirname(os.path.abspath(__file__))
print(DIR)

yPath = yFile = ''
filename = dirname = ''
hasLogin = False

FOLDER = 'morguefile2'

DRIVER_PATH = os.path.join(DIR, "chromedriver.exe")


def getJSONByURL(jsonURL):
    print('jsonURL')
    print(jsonURL)
    header = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11',
              'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
              'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
              'Accept-Encoding': 'none',
              'Accept-Language': 'en-US,en;q=0.8',
              'Connection': 'keep-alive'}
    r = Request(jsonURL, headers=header)
    response = urlopen(r).read()
    return json.loads(response)


def getLastID():
    jsonData = getJSONByURL(
        f'https://morguefile.com/image/json?page=1&terms=&sort=recent&af=morguefile&author=&typ=false')
    return int(jsonData['doc'][0]['unique_id'])


FIRST_PAGE = int(sys.argv[1]) if len(sys.argv) > 1 else 1
LAST_PAGE = int(sys.argv[2]) if len(sys.argv) > 2 else getLastID()

# list page
#AELEMENTS_SELECTOR = "//figure[contains(@class,'rowgrid-image')]//a[contains(@class,'img-link')]"
#LAST_AELEMENT_SELECTOR = "//div[@class='img-grid animated-grid']/div[contains(@class,'reveal') and not(contains(@class,'pubspace'))][30]/a"

# detail page
THUMBNAIL_SELECTOR = "//div[@class='img']/img"
#ID_SELECTOR = "//header/dl/dd"
#TITLE_SELECTOR = "//h1"
TAG_BTN_SELECTOR = "//ul[@class='keywords']/li"
TAG_SELECTOR = "//ul[@class='keywords']/li"
#CATEGORY_SELECTOR = "//a[@rel='category tag']"
# CC_SELECTOR = "//div[@class='desktopstuff']//a[@rel='license']"
AUTHOR_SELECTOR = "//div[@class='creative-name']/a"
#SOURCE_SELECTOR = "//div[contains(text(),'Source')]"
DATE_PUBLISHED_SELECTOR = "//div[@class='moreInfo']/div[1]"
SIZE_SELECTOR = "//div[@class='moreInfo']/div[2]"
# FILE_TYPE_SELECTOR = "//div[@style=\"margin-top:5px; background-image:url('http://res.publicdomainfiles.com/i/dloption.png'); background-repeat:no-repeat;\"]/div[@style='border:1px solid #c9c9c9; float:right; margin-left:5px; width:318px; background-color:#FFFFFF;'][1]//div[@style='font-family:Arial; font-size:11px; padding-left:5px;'][last()]"
#DOWNLOAD_SELECTOR = "//button[contains(@class,'download')]"


def getDateString():
    now = datetime.now()
    print("now =", now)
    # dd/mm/YY H:M:S
    return now.strftime("%Y.%m.%d_%H.%M.%S")


def initListCSV():
    global filename, dirname, DIR, FOLDER
    listFile = f'list.csv'
    print('creating '+f'{listFile}...')
    filename = os.path.join(
        DIR, f"{FOLDER}/{x}/{listFile}")
    # print(filename)
    dirname = os.path.dirname(filename)
    print('dirname:')
    print(dirname)
    if not os.path.exists(dirname):
        os.makedirs(dirname)


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


def makeScreenshot(height, width=1092):
    global driver
    driver.set_window_size(width, height)
    dt = getDateString()
    saveScreenshotPath = os.path.join(dirname, f"screenshot/{dt}.png")
    if not os.path.exists(os.path.dirname(saveScreenshotPath)):
        os.makedirs(os.path.dirname(saveScreenshotPath))
    driver.save_screenshot(saveScreenshotPath)


def checkPageFine(driverTemp, selector, isRestartDriver=False, sec=3, sleep=0):
    # fix for special situations like lightbox
    driverTemp.set_window_size(1500, 1500)
    try:
        element = WebDriverWait(driverTemp, sec).until(
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
        if isRestartDriver:
            driverTemp = restartDriver(driverTemp)
        return False


def saveErrorDownloadLog(page, order, detailUrl):
    logPath = os.path.join(DIR, f"{FOLDER}/error.log")
    logFile = pathlib.Path(logPath)
    if logFile.exists():
        with open(logPath, 'a') as file:
            file.write(f'{page};{order};{detailUrl}\n')
    else:
        with open(logPath, 'w') as file:
            file.write(f'{page};{order};{detailUrl}\n')


def getPage(driverTemp, url):
    print('calling:')
    print(url)
    while True:
        try:
            driverTemp.get(url)
            break
        except TimeoutException as e:
            saveErrorDownloadLog(-1, -1, url)
            driverTemp.delete_all_cookies()
            print("Page load Timeout. Deleting cookies and retrying...")


def clickCatch(driverTemp, selector, wait_time=5, mouse_simulation=False):
    staleElement = True
    while staleElement:
        try:
            wait = WebDriverWait(driverTemp, wait_time)
            element = wait.until(
                EC.element_to_be_clickable((By.XPATH, selector)))

            if mouse_simulation:
                ActionChains(driverTemp).move_to_element(
                    element).click(element).perform()
            else:
                driverTemp.execute_script("arguments[0].click();", element)

            staleElement = False
            return True
        except StaleElementReferenceException:
            print('StaleElementReferenceException, retrying...')
            staleElement = True
        except TimeoutException:
            print('TimeoutException... element not found')
            return False
        except ElementClickInterceptedException as e:
            print(
                'ElementClickInterceptedException... element was overlayed by another element..')
            print(e)
            return False


def restartDriver(driverTemp, timeoutTemp=40):
    global hasLogin

    if driverTemp is not None:
        driverTemp.delete_all_cookies()
        driverTemp.quit()

    chrome_options = webdriver.ChromeOptions()
    chrome_options.headless = True
    # chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1320,1080")
    chrome_options.add_argument('--ignore-certificate-errors')
    chrome_options.add_argument('--ignore-ssl-errors')
    chrome_options.add_argument('log-level=2')

    d = DesiredCapabilities.CHROME
    d['loggingPrefs'] = {'browser': 'ALL'}

    driverTemp = webdriver.Chrome(
        options=chrome_options, executable_path=DRIVER_PATH, desired_capabilities=d)
    driverTemp.set_page_load_timeout(timeoutTemp)
    driverTemp.delete_all_cookies()

    if hasLogin:
        driverTemp = login(driverTemp)

    return driverTemp


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
        r = requests.get(URL, stream=isStream, headers={
                         'User-agent': 'Mozilla/5.0'})
        if (URL != r.url):
            print('real url after redirection')
            print(r.url)
        return r
    else:
        driver.get(URL)
        return driver.current_url


# dependent: getRealRequest,isURLvalid
# y is the counter, default is nothing
# row is to append current row
def downloadFromURL(URL, dirname, row=[], isServerDecidesFilename=False):
    global x
    if (isURLvalid(URL) is not True):
        print('URL is not valid')
        row.append('')
        row.append('')
        row.append('')
        return False
    try:
        r = getRealRequest(URL, True, True)
        print('downloading image...')

        # Check if the image was retrieved successfully
        if r.status_code == 200:
            # Set decode_content value to True, otherwise the downloaded image file's size will be zero.
            r.raw.decode_content = True

            if isServerDecidesFilename:
                # server decides filename again...
                remotefile = urlopen(r.url)
                blah = remotefile.info()['Content-Disposition']
                value, params = cgi.parse_header(blah)
                filename = params["filename"]
                urlretrieve(url, filename)
                print('server decided filename')
                print(filename)
            else:
                # filename is there
                a = urlparse.urlparse(r.url)
                fileName = os.path.basename(a.path)
                print('filename')
                print(fileName)

            # Open a local file with wb ( write binary ) permission.
            with open(os.path.join(dirname, fileName), 'wb') as f:
                shutil.copyfileobj(r.raw, f)

            print('Image successfully Downloaded: ',
                  os.path.join(dirname, fileName))

            row.append(r.url)
            row.append(fileName)
            row.append(getDateString())
        else:
            print('Image Couldn\'t be retrieved')
            row.append('')
            row.append('')
            row.append('')
    except OSError as e:
        saveErrorDownloadLog(x, -1, URL)
        print(e)


x = FIRST_PAGE
y = 0

driver = None
driver = restartDriver(driver)
while x < LAST_PAGE + 1:

    print('x')
    print(x)

    if y == 500:
        print('reaches 500, restarting...')
        driver = restartDriver(driver)


    getPage(
        driver, f'https://morguefile.com/p/{x}')

    if checkPageFine(driver, THUMBNAIL_SELECTOR) == False:
        x += 1
        continue

    y += 1

    # if y is > 500 then open a new folder and reset y
    if y == 1:
        initListCSV()
        with open(filename, 'w', encoding="utf-8", newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['id', 'tags', 'author', 'size',
                             'date_published', 'fileURL', 'fileName', 'date_downloaded'])

    if y > 500:
        initListCSV()
        with open(filename, 'w', encoding="utf-8", newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['id', 'tags', 'author', 'size',
                             'date_published', 'fileURL', 'fileName', 'date_downloaded'])
        y = 1

    print(f'# in folder {dirname}')
    print(y)

    row = [x]

    driver.execute_script("showTags()")

    tags = selectCatch(driver, TAG_SELECTOR, 'text', True)
    print('tags')
    print(tags)
    row.append(tags)

    author = selectCatch(driver, AUTHOR_SELECTOR)
    print('author')
    print(author)
    row.append(author)

    size = selectCatch(driver, SIZE_SELECTOR)
    size = size.split('px')[0] + size.split('px')[1]
    print('size')
    print(size)
    row.append(size)

    date_published = selectCatch(driver, DATE_PUBLISHED_SELECTOR)
    date_published = date_published.replace('Uploaded ','')
    print('date_published')
    print(date_published)
    row.append(date_published)

    thumbnailURL = selectCatch(driver, THUMBNAIL_SELECTOR, 'src')
    print('thumbnailURL')
    print(thumbnailURL)

    downloadFromURL(thumbnailURL, dirname, row)

    with open(filename, 'a', encoding="utf-8", newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(row)

    x += 1
