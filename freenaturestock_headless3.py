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

DIR = os.path.dirname(os.path.abspath(__file__))
print(DIR)
DRIVER_PATH = os.path.join(DIR, "chromedriver.exe")

FOLDER = 'freenaturestock'

FIRST_PAGE = int(sys.argv[1]) if len(sys.argv) > 1 else 1
LAST_PAGE = int(sys.argv[2]) if len(sys.argv) > 2 else 168

# list page
AELEMENTS_SELECTOR = "//div[@class='pxu-photo']/a[2]"
#LAST_AELEMENT_SELECTOR = "//div[@class='img-grid animated-grid']/div[contains(@class,'reveal') and not(contains(@class,'pubspace'))][30]/a"

# detail page
#THUMBNAIL_SELECTOR = "//figure[@class='media-preview']/img"
#TITLE_SELECTOR = "//h1"
# CC_SELECTOR = "//div[@class='desktopstuff']//a[@rel='license']"
#AUTHOR_SELECTOR = "//ul[@class='media-details']//a"
#CATEGORY_SELECTOR = "//ul[@class='media-details']//li/em[text()='Category']/following-sibling::strong"
# SOURCE_SELECTOR = "//div[@style='border:1px solid #c3c3c3; background-color:#fbfbfb; padding:10px; font-size:12px; margin-top:5px;']/div[@class='infleft'][text()='Source:']/following-sibling::div[1]/a"
#SIZE_SELECTOR = "//ul[@class='media-details']//li/em[text()='Dimensions']/following-sibling::strong"
# FILE_TYPE_SELECTOR = "//div[@style=\"margin-top:5px; background-image:url('http://res.publicdomainfiles.com/i/dloption.png'); background-repeat:no-repeat;\"]/div[@style='border:1px solid #c9c9c9; float:right; margin-left:5px; width:318px; background-color:#FFFFFF;'][1]//div[@style='font-family:Arial; font-size:11px; padding-left:5px;'][last()]"

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


def checkPageFine(selector, restartDriver=False, sec=3, sleep=0):
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
    global x, y, detailUrls, row, dirname
    try:
        # Open the url image, set stream to True, this will return the stream content.
        r = requests.get(URL, stream=True)
        if (URL != r.url):
            print('real url after redirection')
            print(r.url)
            URL = r.url
            r = requests.get(URL, stream=True)

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
            row.append(URL)
            row.append(fileName)
            row.append(getDateString())
        else:
            print('Image Couldn\'t be retreived')
            row.append('')
            row.append('')
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
previous_file = 'abc'
latest_file = 'abc'

driver = webdriver.Chrome(options=chrome_options, executable_path=DRIVER_PATH)
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

    listingPage = f'https://freenaturestock.com/page/{x}'
    driver.get(listingPage)

    print('listingPage:')
    print(listingPage)

    AElements = driver.find_elements_by_xpath(AELEMENTS_SELECTOR)
    detailUrls = [el.get_attribute("href") for el in AElements]

    print('len of imageURLs')
    print(len(detailUrls))

    with open(filename, 'w', encoding="utf-8", newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['tags', 'date_published', 'imageURL',
                         'fileName', 'date_downloaded'])
        y = 0
        isTimeout = False
        #shutil.rmtree(f"{FOLDER}/{x}/", ignore_errors=True)
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
            row = []

            print('page ' + str(x))

            TAG_SELECTOR = f"//article[@class='post type-photo'][{y+1}]//div[@class='tags']/a"
            tags = selectCatch(driver, TAG_SELECTOR, 'text', True)
            print('tags')
            print(tags)
            row.append(tags)

            DATE_PUBLISHED_SELECTOR = f"//article[@class='post type-photo'][{y+1}]//a[@class='timestamp']"
            date_published = selectCatch(
                driver, DATE_PUBLISHED_SELECTOR, 'text')
            print('date_published')
            print(date_published)
            row.append(date_published)

            print('imageURL')
            print(detailUrls[y])

            downloadFromURL(detailUrls[y])

            print(row)
            writer.writerow(row)
            y += 1
    x += 1
