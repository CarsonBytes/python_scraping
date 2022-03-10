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

DIR = os.path.dirname(os.path.abspath(__file__))
print(DIR)
DRIVER_PATH = os.path.join(DIR, "chromedriver.exe")

FOLDER = 'lifeofpix'

FIRST_PAGE = int(sys.argv[1]) if len(sys.argv) > 1 else 1
LAST_PAGE = int(sys.argv[2]) if len(sys.argv) > 2 else 146

# list page
AELEMENTS_SELECTOR = "//div[@class='img-grid animated-grid']/div[contains(@class,'reveal') and not(contains(@class,'pubspace'))]/a"
LAST_AELEMENT_SELECTOR = "//div[@class='img-grid animated-grid']/div[contains(@class,'reveal') and not(contains(@class,'pubspace'))][30]/a"

# detail page
THUMBNAIL_SELECTOR = "//img[@id='pic']"

TITLE_SELECTOR = "//h1[@class='pic-name']"
TAG_SELECTOR = "//div[@class='tags-group']/a"
# CC_SELECTOR = "//div[@class='desktopstuff']//a[@rel='license']"
AUTHOR_SELECTOR = "//div[@class='node large show reveal']//a[@class='info']"
# SOURCE_SELECTOR = "//div[@style='border:1px solid #c3c3c3; background-color:#fbfbfb; padding:10px; font-size:12px; margin-top:5px;']/div[@class='infleft'][text()='Source:']/following-sibling::div[1]/a"
DATE_PUBLISHED_SELECTOR = "//div[@class='location']/div"
# SIZE_SELECTOR = "//div[@style=\"margin-top:5px; background-image:url('http://res.publicdomainfiles.com/i/dloption.png'); background-repeat:no-repeat;\"]/div[@style='border:1px solid #c9c9c9; float:right; margin-left:5px; width:318px; background-color:#FFFFFF;'][1]//div[@style='font-family:Arial; font-size:11px; padding-left:5px;'][last()]"
# FILE_TYPE_SELECTOR = "//div[@style=\"margin-top:5px; background-image:url('http://res.publicdomainfiles.com/i/dloption.png'); background-repeat:no-repeat;\"]/div[@style='border:1px solid #c9c9c9; float:right; margin-left:5px; width:318px; background-color:#FFFFFF;'][1]//div[@style='font-family:Arial; font-size:11px; padding-left:5px;'][last()]"
DOWNLOAD_SELECTOR = "//div[@class='actions']/a[@class='download']"

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


def makeScreenshot():
    global driver
    driver.set_window_size(1092, 2500)
    dt = getDateString()
    saveScreenshotPath = os.path.join(dirname, f"screenshot/{dt}.png")
    if not os.path.exists(os.path.dirname(saveScreenshotPath)):
        os.makedirs(os.path.dirname(saveScreenshotPath))
    driver.save_screenshot(saveScreenshotPath)


def checkPageFine(selector, restartDriver=True, sec=3, sleep=0):
    global driver, temp_chrome_options, DRIVER_PATH
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
                options=temp_chrome_options, executable_path=DRIVER_PATH)
        return False


def downloadFromURL(URL):
    global x, y, detailUrls, row, dirname, fileName
    try:
        # Open the url image, set stream to True, this will return the stream content.
        r = requests.get(URL, stream=True)

        # Check if the image was retrieved successfully
        if r.status_code == 200:
            # Set decode_content value to True, otherwise the downloaded image file's size will be zero.
            r.raw.decode_content = True

            # Open a local file with wb ( write binary ) permission.
            with open(os.path.join(dirname, fileName), 'wb') as f:
                shutil.copyfileobj(r.raw, f)

            print('Image sucessfully Downloaded: ',
                  os.path.join(dirname, fileName))
        else:
            print('Image Couldn\'t be retreived')
            row.append('')
    except OSError as e:
        saveErrorDownloadLog(x, y, detailUrls[y])
        y += 1


def saveErrorDownloadLog(page, order, detailUrl):
    logPath = os.path.join(DIR, f"{FOLDER}/error.log")
    logFile = pathlib.Path(logPath)
    if logFile.exists():
        with open(logPath, 'a') as file:
            file.write(f'{page};{order};{detailUrl}\n')
    else:
        with open(logPath, 'w') as file:
            file.write(f'{page};{order};{detailUrl}\n')


x = FIRST_PAGE
while x < LAST_PAGE+1:
    dt_string = getDateString()
    listFile = f'list_{dt_string}.csv'
    print('creating '+f'{listFile}...')
    filename = os.path.join(DIR, f"{FOLDER}/{x}/{listFile}")
    # print(filename)
    dirname = os.path.dirname(filename)
    print('dirname:')
    print(dirname)
    if not os.path.exists(dirname):
        os.makedirs(dirname)

    # format download directory of chrome driver to be valid
    dirname = dirname.replace('/', '\\')

    preference = {'download.default_directory': dirname,
                  "safebrowsing.enabled": "false"}
    temp_chrome_options = copy.deepcopy(chrome_options)
    temp_chrome_options.add_experimental_option('prefs', preference)

    driver = webdriver.Chrome(
        options=temp_chrome_options, executable_path=DRIVER_PATH)

    listingPage = f'https://www.lifeofpix.com/search/all/{x}/?category=&orientation=&color='
    driver.get(listingPage)

    print('listingPage:')
    print(listingPage)

    if checkPageFine(AELEMENTS_SELECTOR) == False:
        continue

    driver.execute_script("window.scrollTo(0, document.body.scrollHeight)")

    if checkPageFine(LAST_AELEMENT_SELECTOR, True, 10) == False:
        continue
    
    AElements = driver.find_elements_by_xpath(AELEMENTS_SELECTOR)
    detailUrls = [el.get_attribute("href") for el in AElements]

    print('len of detailUrls')
    print(len(detailUrls))

    with open(filename, 'w', encoding="utf-8", newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['detailUrl', 'title', 'tags', 'author',
                         'date_published', 'fileURL', 'fileName', 'date_downloaded'])
        y = 0
        isTimeout = False
        while y < len(detailUrls):
            yPath = os.path.join(DIR, f"{FOLDER}/{x}/y.txt")
            yFile = pathlib.Path(yPath)

            if y == 0 and yFile.exists():
                fileContent = open(yPath, 'r')
                y = int(fileContent.readline())
            else:
                fileContent = open(yPath, 'w')
                fileContent.write(str(y))

            print('y')
            print(y)
            isFileExisted = False
            row = [detailUrls[y]]

            print('page ' + str(x))
            print(detailUrls[y])
            driver.get(detailUrls[y])

            if checkPageFine(TITLE_SELECTOR) == False:
                continue

            thumbnailUrl = selectCatch(driver, THUMBNAIL_SELECTOR,'src')
            print('thumbnailUrl')
            print(thumbnailUrl)
            if thumbnailUrl == '':
                print('thumbnailUrl is empty, logged and skip to next one')
                saveErrorDownloadLog(x,y,detailUrls[y])
                y+=1
                continue

            title = selectCatch(driver, TITLE_SELECTOR)
            print('title')
            print(title)
            row.append(title)

            tags = selectCatch(driver, TAG_SELECTOR, 'text', True)
            print('tags')
            print(tags)
            row.append(tags)

            author = selectCatch(driver, AUTHOR_SELECTOR)
            print('author')
            print(author)
            row.append(author)

            date_published = selectCatch(driver, DATE_PUBLISHED_SELECTOR)
            result = date_published.splitlines()
            print('date_published')
            print(result[1])
            row.append(result[1])

            makeScreenshot()

            if checkPageFine(DOWNLOAD_SELECTOR) == False:
                continue
            downloadLink = selectCatch(driver, DOWNLOAD_SELECTOR, 'href')
            fileName = os.path.basename(downloadLink)

            print("waiting file to be downloaded")
            downloadFromURL(downloadLink)

            row.append(downloadLink)
            row.append(fileName)
            row.append(getDateString())

            print(row)
            writer.writerow(row)
            y += 1
    driver.quit()
    x += 1
