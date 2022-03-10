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
from selenium.webdriver.common.action_chains import ActionChains
from urllib.request import urlopen, Request
import json


DIR = os.path.dirname(os.path.abspath(__file__))
print(DIR)
DRIVER_PATH = os.path.join(DIR, "chromedriver.exe")

FOLDER = 'photostockeditor'
ITEM_PER_FOLDER = 500

FIRST_ITEM = int(sys.argv[1]) if len(sys.argv) > 1 else 32
LAST_ITEM = int(sys.argv[2]) if len(sys.argv) > 2 else 94187

# detail page
THUMBNAIL_SELECTOR = "//img[@id='download2']"
TITLE_SELECTOR = "//h1[1]"
TAG_SELECTOR = "//div[@class='row mobile_fix']//div[@class='col-md-12']/a[@style='font-size:12px; color:#ccc']"
# CC_SELECTOR = "//div[@class='desktopstuff']//a[@rel='license']"
#AUTHOR_SELECTOR = "//span[@itemprop='author']"
# SOURCE_SELECTOR = "//div[@style='border:1px solid #c3c3c3; background-color:#fbfbfb; padding:10px; font-size:12px; margin-top:5px;']/div[@class='infleft'][text()='Source:']/following-sibling::div[1]/a"
# DATE_PUBLISHED_SELECTOR = "//article[@class='has-sidebar']/div[@class='' and not(@style)][1]/p[contains(text(),'Online') or contains(text(),'Taken')]"
#SIZE_SELECTOR = "//div[@class='stats clearfix']//li/i[@class='icon-frame']"
# FILE_TYPE_SELECTOR = "//div[@style=\"margin-top:5px; background-image:url('http://res.publicdomainfiles.com/i/dloption.png'); background-repeat:no-repeat;\"]/div[@style='border:1px solid #c9c9c9; float:right; margin-left:5px; width:318px; background-color:#FFFFFF;'][1]//div[@style='font-family:Arial; font-size:11px; padding-left:5px;'][last()]"
DOWNLOAD_SELECTOR = "//a[@id='download']"
#IMG_ID_SELECTOR = "//button[@class='btn fav-btn ']"

chrome_options = webdriver.ChromeOptions()
chrome_options.headless = True
# chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=1500,1080")
chrome_options.add_argument('--ignore-certificate-errors')
chrome_options.add_argument('--ignore-ssl-errors')
chrome_options.add_argument('log-level=2')
chrome_options.add_argument('--no-proxy-server')
chrome_options.add_argument("--proxy-server='direct://'")
chrome_options.add_argument("--proxy-bypass-list=*")


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
    saveScreenshotPath = os.path.join(
        dirname, f"screenshot/{getDateString()}.png")
    if not os.path.exists(os.path.dirname(saveScreenshotPath)):
        os.makedirs(os.path.dirname(saveScreenshotPath))
    driver.save_screenshot(saveScreenshotPath)


def checkPageFine(selector, tempdriver='', restartDriver=False, sec=3, sleep=0):
    global temp_chrome_options, DRIVER_PATH, driver
    if tempdriver == '':
        tempdriver = driver
    try:
        element = WebDriverWait(tempdriver, sec).until(
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
            tempdriver.quit()
            tempdriver = webdriver.Chrome(
                options=temp_chrome_options, executable_path=DRIVER_PATH)
        return False


def downloadFromURL(URL, path):
    global x, row, dirname
    try:
        # Open the url image, set stream to True, this will return the stream content.
        r = requests.get(URL, stream=True)

        # Check if the image was retrieved successfully
        if r.status_code == 200:
            # Set decode_content value to True, otherwise the downloaded image file's size will be zero.
            r.raw.decode_content = True

            a = urlparse.urlparse(imageURL)
            fileName = os.path.basename(a.path)

            # Open a local file with wb ( write binary ) permission.
            with open(f'{path}/{fileName}', 'wb') as f:
                shutil.copyfileobj(r.raw, f)

            print('Image sucessfully Downloaded: ',f'{path}/{fileName}')
            
            row.append(imageURL)
            row.append(fileName)
            row.append(getDateString())

        else:
            print('Image Couldn\'t be retreived')
            row.append('')
            row.append('')
            row.append('')
    except OSError as e:
        saveErrorDownloadLog(itemOrdering, URL)
        x += 1


def saveErrorDownloadLog(page, detailUrl):
    logPath = os.path.join(DIR, f"{FOLDER}/error.log")
    logFile = pathlib.Path(logPath)
    if logFile.exists():
        with open(logPath, 'a') as file:
            file.write(f'{page};{detailUrl}\n')
    else:
        with open(logPath, 'w') as file:
            file.write(f'{page};{detailUrl}\n')


latest_file = ''
previous_file = ''

driver = webdriver.Chrome(options=chrome_options, executable_path=DRIVER_PATH)

x = FIRST_ITEM

xPath = os.path.join(DIR, f"{FOLDER}/x.txt")
xFile = pathlib.Path(xPath)
if xFile.exists():
    fileContent = open(xPath, 'r')
    x = int(fileContent.readline())
    print('x:')
    print(x)

print('x')
print(x)
while x <= LAST_ITEM:

    subfolder = (x // ITEM_PER_FOLDER + 1) * ITEM_PER_FOLDER

    listFile = f'list_{getDateString()}.csv'
    print(f'creating {listFile}...')
    filename = os.path.join(DIR, f"{FOLDER}/{subfolder}/{listFile}")
    dirname = os.path.dirname(filename)
    print('dirname:')
    print(dirname)
    if not os.path.exists(dirname):
        os.makedirs(dirname)

    remainder = x % ITEM_PER_FOLDER
    
    with open(filename, 'w', encoding="utf-8", newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['id', 'title', 'tags', 'image_URL', 'fileName', 'date_downloaded'])
        while remainder <= ITEM_PER_FOLDER:
            remainder = x % ITEM_PER_FOLDER
            
            print('subfolder')
            print(subfolder)
            print('remainder')
            print(remainder)
            print('detail URL')
            print(f'https://photostockeditor.com/{x}')
            itemOrdering = (subfolder-ITEM_PER_FOLDER) + remainder
            fileContent = open(xPath, 'w')
            fileContent.write(str(itemOrdering))

            driver.get(f'https://photostockeditor.com/{x}')
            row = [x]

            thumbnailUrl = selectCatch(driver, THUMBNAIL_SELECTOR, 'src')
            print('thumbnailUrl')
            print(thumbnailUrl)
            if thumbnailUrl == '':
                print('thumbnailUrl is empty, logged and skip to next one')
                saveErrorDownloadLog(itemOrdering, f'https://photostockeditor.com/{x}')
                x += 1
                continue

            title = selectCatch(driver, TITLE_SELECTOR)
            print('title')
            print(title)
            row.append(title)

            tags = selectCatch(driver, TAG_SELECTOR, 'text', True)
            print('tags')
            print(tags)
            row.append(tags)

            """ author = selectCatch(driver, AUTHOR_SELECTOR)
            print('author')
            print(author)
            row.append(author)

            size = selectCatch(driver, SIZE_SELECTOR)
            size = size.replace(' px', '')
            print('size')
            print(size)
            row.append(size) """

            makeScreenshot(1000)

            if checkPageFine(DOWNLOAD_SELECTOR) == False:
                continue

            """ downloadPath = os.path.join(DIR, f"{FOLDER}/{subfolder}")
            downloadPath2 = downloadPath.replace('/', '\\')
            params = {'behavior': 'allow',
                      'downloadPath': downloadPath2}
            driver.execute_cdp_cmd('Page.setDownloadBehavior', params)

            downloadBtn = driver.find_element_by_xpath(DOWNLOAD_SELECTOR)
            driver.implicitly_wait(5)
            ActionChains(driver).move_to_element(
                downloadBtn).click(downloadBtn).perform()

            print('checking if specific file is downloaded')
            imgFileName = f'StockSnap_{imgID}.jpg'
            imgPath = os.path.join(DIR, f"{FOLDER}/{subfolder}/{imgFileName}")
            imgFile = pathlib.Path(imgPath)
            i = 0
            while True:
                print(f'{i}s...')
                if imgFile.exists():
                    print('download completed!')
                    break
                if i > 60:
                    print('download speed too slow, restart session')
                    driver.quit()
                    list_of_files = glob.glob(f'{downloadPath}/*.crdownload')
                    for crdownload in list_of_files:
                        os.remove(crdownload)
                    driver = webdriver.Chrome(
                        options=chrome_options, executable_path=DRIVER_PATH)
                    break
                time.sleep(1)
                i += 1

            if i > 60:
                print('retrying....')
                continue
            """
            imageURL = selectCatch(driver, DOWNLOAD_SELECTOR, 'href')
            print('imageURL')
            print(imageURL)

            savePath = os.path.join(DIR, f"{FOLDER}/{subfolder}")

            downloadFromURL(imageURL, savePath)

            print(row)
            writer.writerow(row)
            x += 1
    
