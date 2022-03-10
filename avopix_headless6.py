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
from urllib.request import urlopen, Request
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities


DIR = os.path.dirname(os.path.abspath(__file__))
print(DIR)
DRIVER_PATH = os.path.join(DIR, "chromedriver.exe")
FIRST_PAGE = int(sys.argv[1]) if len(sys.argv) > 1 else 1
LAST_PAGE = int(sys.argv[2]) if len(sys.argv) > 2 else 13284

FOLDER = 'avopix'

# list page
AELEMENTS_SELECTOR = "//div[@class='listing listing-overflow']/div[@class='listing-item']/a"
#LAST_AELEMENT_SELECTOR = "//div[@class='img-grid animated-grid']/div[contains(@class,'reveal') and not(contains(@class,'pubspace'))][30]/a"

# detail page
#THUMBNAIL_SELECTOR = "//div[contains(@class,'image-main-view')]//img"
#ID_SELECTOR = "//header/dl/dd"
TITLE_SELECTOR = "//h1"
TAG_SELECTOR = "//p[@class='detail-tags']/a"
#CATEGORY_SELECTOR = "//a[@rel='category tag']"
# CC_SELECTOR = "//div[@class='desktopstuff']//a[@rel='license']"
AUTHOR_SELECTOR = "//div[@class='main-title']//a"
#SOURCE_SELECTOR = "//div[contains(text(),'Source')]"
DATE_CREATED_SELECTOR = "//table//th[text()='Photographed']/following-sibling::td"
#DATE_PUBLISHED_SELECTOR = "//span[@class='date']//a"
SIZE_SELECTOR = "//table//th[text()='Size']/following-sibling::td"
# FILE_TYPE_SELECTOR = "//div[@style=\"margin-top:5px; background-image:url('http://res.publicdomainfiles.com/i/dloption.png'); background-repeat:no-repeat;\"]/div[@style='border:1px solid #c9c9c9; float:right; margin-left:5px; width:318px; background-color:#FFFFFF;'][1]//div[@style='font-family:Arial; font-size:11px; padding-left:5px;'][last()]"
DOWNLOAD_SELECTOR = "//p[@class='nomt']//a"

# download page
CLICK_HERE_SELECTOR = "//a[contains(text(),'click here')]"

def restartDriver(driverTemp, timeoutTemp=40):

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
    d['loggingPrefs'] = { 'browser':'ALL' }

    driverTemp = webdriver.Chrome(options=chrome_options, executable_path=DRIVER_PATH, desired_capabilities=d)
    driverTemp.set_page_load_timeout(timeoutTemp)
    driverTemp.delete_all_cookies()

    return driverTemp


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


def checkPageFine(driverTemp, selector, isRestartDriver=False, sec=3, sleep=0):
    #fix for special situations like lightbox
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


def getPage(driver, url):
    print('calling:')
    print(url)
    while True:
        try:
            driver.get(url)
            break
        except TimeoutException as e:
            saveErrorDownloadLog(-1, -1, url)
            driver.delete_all_cookies()
            print("Page load Timeout. Deleting cookies and retrying...")

def waitForImageDownloaded(driverTemp, wait_for_dl_time=120, dl_time=300):
    global row
    print('checking if any new image file is being downloaded')
    downloadingExtension = 'crdownload'
    listOfDownloadingFile = []
    i = 0
    call = None
    while True:

        print(f'{i}s...')
        listOfDownloadingFile.extend(
            glob.glob(dirname + '/*.' + downloadingExtension))
        if listOfDownloadingFile != []:
            print('an image is being downloaded:')
            crdownload_path = listOfDownloadingFile[0]
            print(os.path.basename(crdownload_path))
            target_path = crdownload_path.replace('.crdownload', '')
            break
        if i > wait_for_dl_time:
            print('the download still has not begun, removing any .crdownload...')
            list_of_files2 = glob.glob(f'{dirname}/*.crdownload')
            for crdownload in list_of_files2:
                os.remove(crdownload)
            return False

        clickhere_text = selectCatch(driverTemp, CLICK_HERE_SELECTOR, 'href')
        if call == 0 and clickhere_text == 'javascript:void(0);' :
            print('download ajax erorr....')
            return False

        call = driverTemp.execute_script("return jQuery.active;")
        print(f'no. of running ajax call: {call}')
        i += 1
        time.sleep(1)

    print('Downloading that image... checking if download is complete... Please do not abort!')
    i = 0
    while True:
        print(f'{i}s... still downloading... Please do not abort!')
        if not os.path.exists(crdownload_path):
            print('download complete!')
            break
        if i > dl_time:
            print('download is too slow')
            return False
        i += 1
        time.sleep(1)

    if os.path.exists(target_path):
        print('target image is downloaded:')
        print(target_path)
        print(f'image name: {os.path.basename(target_path)}')
        row.append(os.path.basename(target_path))
        row.append(getDateString())
        return True

    return False




x = FIRST_PAGE
# driver is for loading listing page
driver = driver2 = None

driver = restartDriver(driver)

while x < LAST_PAGE+1:
    y = 0
    
    print('subfolder')
    print(x)

    getPage(
        driver, f'https://avopix.com/search/photos/all/newest/{x}?fsort=newest')

    if checkPageFine(driver, AELEMENTS_SELECTOR) == False:
        continue

    detailUrls = selectCatch(driver, AELEMENTS_SELECTOR, 'href', True)

    yPath = os.path.join(DIR, f"{FOLDER}/{x}/y.txt")
    yFile = pathlib.Path(yPath)
    if yFile.exists():
        fileContent = open(yPath, 'r')
        string = fileContent.readline()
        if string.isdigit():
            y = int(float(string))

    if y < len(detailUrls):
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
            driver2 = restartDriver(driver2, 20)

            writer = csv.writer(csvfile)
            writer.writerow(['detailUrl', 'title', 'author',
                             'tags',  'size', 'date_created', 'fileName', 'date_downloaded'])
            while y < len(detailUrls):
                driver2.delete_all_cookies()

                print('y')
                print(y)
                row = [detailUrls[y]]
                print('detailUrl')
                print(detailUrls[y])

                getPage(driver2, detailUrls[y])

                title = selectCatch(driver2, TITLE_SELECTOR)
                print('title')
                print(title)
                row.append(title)

                author = selectCatch(driver2, AUTHOR_SELECTOR)
                print('author')
                print(author)
                row.append(author)

                tags = selectCatch(driver2, TAG_SELECTOR, 'text', True)
                print('tags')
                print(tags)
                row.append(tags)

                size = selectCatch(driver2, SIZE_SELECTOR)
                print('size')
                print(size)
                row.append(size)

                date_created = selectCatch(driver2, DATE_CREATED_SELECTOR)
                print('date_created')
                print(date_created)
                row.append(date_created)

                dirname2 = dirname.replace('/', '\\')
                params = {'behavior': 'allow',
                          'downloadPath': dirname2}
                driver2.execute_cdp_cmd('Page.setDownloadBehavior', params)

                # clear old .crdownloaded before downloading...
                list_of_old_crdownloaded = glob.glob(f'{dirname}/*.crdownload')
                for crdownload in list_of_old_crdownloaded:
                    os.remove(crdownload)

                downloadPageURL = selectCatch(
                    driver2, DOWNLOAD_SELECTOR, 'href')

                # triggering page for image download from browser
                getPage(driver2, downloadPageURL)

                isImageDownloaded = waitForImageDownloaded(driver2, 80)

                if isImageDownloaded:
                    print(row)
                    writer.writerow(row)
                    y += 1
                    fileContent = open(yPath, 'w')
                    fileContent.write(str(y))
                else:
                    print('clearning cookies, restarting session, save erorr log, and go to next 1...')
                    saveErrorDownloadLog(x,y,detailUrls[y])

                    y += 1
                    fileContent = open(yPath, 'w')
                    fileContent.write(str(y))

                    driver2 = restartDriver(driver2)
                    continue
    if len(detailUrls) > 0:
        x += 1
