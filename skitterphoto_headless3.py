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

FOLDER = 'skitterphoto'

FIRST_PAGE = int(sys.argv[1]) if len(sys.argv) > 1 else 1
LAST_PAGE = int(sys.argv[2]) if len(sys.argv) > 2 else 146

# list page
AELEMENTS_SELECTOR = "//div[@class='other other--has-3-columns']/a"
#LAST_AELEMENT_SELECTOR = "//div[@class='img-grid animated-grid']/div[contains(@class,'reveal') and not(contains(@class,'pubspace'))][30]/a"

# detail page
THUMBNAIL_SELECTOR = "//article[@class='has-sidebar']/figure[1]/img"
TITLE_SELECTOR = "//article[@class='has-sidebar']/div[@class='' and not(@style)][1]/p[1]/strong"
TAG_SELECTOR = "//div[@class='photo__tags']/a"
# CC_SELECTOR = "//div[@class='desktopstuff']//a[@rel='license']"
AUTHOR_SELECTOR = "//div[@class='photographer']/p[1]/a"
# SOURCE_SELECTOR = "//div[@style='border:1px solid #c3c3c3; background-color:#fbfbfb; padding:10px; font-size:12px; margin-top:5px;']/div[@class='infleft'][text()='Source:']/following-sibling::div[1]/a"
DATE_PUBLISHED_SELECTOR = "//article[@class='has-sidebar']/div[@class='' and not(@style)][1]/p[contains(text(),'Online') or contains(text(),'Taken')]"
SIZE_SELECTOR = "//article[@class='has-sidebar']/div[@class='' and not(@style)]/p[contains(text(),'pixels')]"
# FILE_TYPE_SELECTOR = "//div[@style=\"margin-top:5px; background-image:url('http://res.publicdomainfiles.com/i/dloption.png'); background-repeat:no-repeat;\"]/div[@style='border:1px solid #c9c9c9; float:right; margin-left:5px; width:318px; background-color:#FFFFFF;'][1]//div[@style='font-family:Arial; font-size:11px; padding-left:5px;'][last()]"
DOWNLOAD_SELECTOR = "//button[text()='Download']"

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


def makeScreenshot(height,width=1092):
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
latest_file = ''
previous_file = ''

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

    listingPage = f'https://skitterphoto.com/photos?page={x}'
    driver.get(listingPage)

    print('listingPage:')
    print(listingPage)

    if checkPageFine(AELEMENTS_SELECTOR) == False:
        continue

    driver.execute_script("window.scrollTo(0, document.body.scrollHeight)")

    AElements = driver.find_elements_by_xpath(AELEMENTS_SELECTOR)
    detailUrls = [el.get_attribute("href") for el in AElements]

    print('len of detailUrls')
    print(len(detailUrls))

    with open(filename, 'w', encoding="utf-8", newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['detailUrl', 'title', 'tags', 'author',
                         'date_published', 'date_taken', 'size', 'fileName', 'date_downloaded'])
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

            thumbnailUrl = selectCatch(driver, THUMBNAIL_SELECTOR, 'src')
            print('thumbnailUrl')
            print(thumbnailUrl)
            if thumbnailUrl == '':
                print('thumbnailUrl is empty, logged and skip to next one')
                saveErrorDownloadLog(x, y, detailUrls[y])
                y += 1
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

            result = selectCatch(driver, DATE_PUBLISHED_SELECTOR)
            result = result.splitlines()
            date_published = ''
            date_taken = ''
            for line in result:
                if "Online since" in line:
                    date_published = line.replace('Online since: ', '')
                if "Taken" in line:
                    date_taken = line.replace('Taken: ', '')

            print('date_published')
            print(date_published)
            print('date_taken')
            print(date_taken)

            row.append(date_published)
            row.append(date_taken)

            size = selectCatch(driver, SIZE_SELECTOR)
            size = size.splitlines()[0]
            size = size.replace(' pixels', '')
            size = size.replace(' ', '')
            size = size.replace('x', ' x ')
            print('size')
            print(size)
            row.append(size)

            makeScreenshot(1500)

            if checkPageFine(DOWNLOAD_SELECTOR) == False:
                continue

            downloadPath = os.path.join(DIR, f"{FOLDER}/{x}")
            downloadPath2 = downloadPath.replace('/', '\\')
            params = {'behavior': 'allow',
                      'downloadPath': downloadPath2}
            driver.execute_cdp_cmd('Page.setDownloadBehavior', params)

            downloadBtn = driver.find_element_by_xpath(DOWNLOAD_SELECTOR)
            downloadBtn.click()

            time.sleep(5)

            print('checking if new jpg file is downloaded')
            i = 0
            while True:
                print(f'{i}s...')
                list_of_files = glob.glob(f'{downloadPath}/*.jpg')
                latest_file = max(list_of_files, key=os.path.getctime)
                if (previous_file != latest_file):
                    previous_file = latest_file
                    break
                if i > 60:
                    print('download is too slow, remove crdownload, then restart session...')
                    list_of_files2 = glob.glob(f'{downloadPath}/*.crdownload')
                    for crdownload in list_of_files2:
                        os.remove(crdownload)
                    driver.quit()
                    driver = webdriver.Chrome(
                        options=chrome_options, executable_path=DRIVER_PATH)
                    break
                time.sleep(1)
                i += 1
            
            if i > 60 :
                print('restarting session....')
                continue

            print(f'latest jpg file downloaded: {os.path.basename(latest_file)}')
            row.append(os.path.basename(latest_file))
            row.append(getDateString())

            print(row)
            writer.writerow(row)
            y += 1
    x += 1
