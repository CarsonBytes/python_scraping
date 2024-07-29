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
from urllib.parse import unquote

DIR = os.path.dirname(os.path.abspath(__file__))
print(DIR)
DRIVER_PATH = os.path.join(DIR, "chromedriver.exe")

FOLDER = 'mystock'

FIRST_ITEM = int(sys.argv[1]) if len(sys.argv) > 1 else 0

ITEM_PER_FOLDER = 100

# detail page
THUMBNAIL_SELECTOR = "//article[@class='section section-text']/img"
TITLE_SELECTOR = "//div[@class='sidebar-image-title']/h2"
TAG_SELECTOR = "//div[@class='post-tags']//a"
# CC_SELECTOR = "//div[@class='desktopstuff']//a[@rel='license']"
#AUTHOR_SELECTOR = "//div[@class='author-name']//h4[@class='card-title']"
# SOURCE_SELECTOR = "//div[@style='border:1px solid #c3c3c3; background-color:#fbfbfb; padding:10px; font-size:12px; margin-top:5px;']/div[@class='infleft'][text()='Source:']/following-sibling::div[1]/a"
# DATE_PUBLISHED_SELECTOR = "//article[@class='has-sidebar']/div[@class='' and not(@style)][1]/p[contains(text(),'Online') or contains(text(),'Taken')]"
#SIZE_SELECTOR = "//div[@class='stats clearfix']//li/i[@class='icon-frame']"
# FILE_TYPE_SELECTOR = "//div[@style=\"margin-top:5px; background-image:url('http://res.publicdomainfiles.com/i/dloption.png'); background-repeat:no-repeat;\"]/div[@style='border:1px solid #c9c9c9; float:right; margin-left:5px; width:318px; background-color:#FFFFFF;'][1]//div[@style='font-family:Arial; font-size:11px; padding-left:5px;'][last()]"
DOWNLOAD_SELECTOR = "//div[@class='dropdown-button']/a"

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
    global chrome_options, DRIVER_PATH, driver
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
    global x, detailURL, row, dirname

    if (isURLvalid(URL) is not True):
        print('URL is not valid')
        row.append('')
        row.append('')
        row.append('')
        saveErrorDownloadLog(x, detailURL)
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
        saveErrorDownloadLog(x, detailURL)
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
while True:
    subfolder = ((x // ITEM_PER_FOLDER)) * ITEM_PER_FOLDER
    page = x // ITEM_PER_FOLDER + 1
    jsonURL = f'https://mystock.themeisle.com/wp-json/wp/v2/photo-api?per_page={ITEM_PER_FOLDER}&context=gallery&page={page}'
    print('jsonURL')
    print(jsonURL)
    r = Request(jsonURL, headers={'User-Agent': 'Mozilla/5.0'})
    response = urlopen(r).read()
    data = json.loads(response)
    jsonPath = os.path.join(DIR, f"{FOLDER}/json/{subfolder}.json")
    jsonPathDir = os.path.dirname(jsonPath)
    if not os.path.exists(jsonPathDir):
        os.makedirs(jsonPathDir)
    with open(jsonPath, 'w') as f:
        json.dump(data, f)

    listFile = f'list_{getDateString()}.csv'
    print(f'creating {listFile}...')
    filename = os.path.join(DIR, f"{FOLDER}/{subfolder}/{listFile}")
    dirname = os.path.dirname(filename)
    print('dirname:')
    print(dirname)
    if not os.path.exists(dirname):
        os.makedirs(dirname)

    if len(data) == 0:
        break

    y = 0  # counter for item in each folder
    with open(filename, 'w', encoding="utf-8", newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['id', 'detailURL', 'title', 'tags', 'author',
                         'fileURL', 'fileName', 'date_downloaded'])
        while x < (subfolder/ITEM_PER_FOLDER+1) * ITEM_PER_FOLDER:

            yPath = os.path.join(dirname, f"y.txt")
            yFile = pathlib.Path(yPath)
            
            if y == 0 and yFile.exists():
                fileContent = open(yPath, 'r')
                string = fileContent.readline()
                if string.isdigit() and string != '': 
                    y = int(fileContent.readline())
                x = subfolder + y
            else:
                fileContent = open(yPath, 'w')
                if subfolder == 0:
                    y = x
                else:
                    y = x % subfolder
                fileContent.write(str(y))

            print('x')
            print(x)
            print('subfolder')
            print(subfolder)
            print('y')
            print(y)

            item = data[y]

            itemid = item['id']
            print('itemid')
            print(itemid)
            row = [itemid]

            detailURL = unquote(item['post_data']['permalink'])
            print('detailURL')
            print(detailURL)
            row.append(detailURL)

            driver.get(detailURL)

            title = selectCatch(driver, TITLE_SELECTOR)
            print('title')
            print(title)
            row.append(title)

            tags = selectCatch(driver, TAG_SELECTOR, 'text', True)
            print('tags')
            print(tags)
            row.append(tags)

            author = item['author']['name']
            print('author')
            print(author)
            row.append(author)

            """ makeScreenshot(1000)

            if checkPageFine(DOWNLOAD_SELECTOR) == False:
                continue 

            downloadPath = os.path.join(DIR, f"{FOLDER}/{subfolder}")
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

            row.append(imgFileName)
            row.append(getDateString())"""

            imageURL = selectCatch(driver, DOWNLOAD_SELECTOR, 'href')
            print('imageURL')
            print(imageURL)

            downloadFromURL(imageURL)

            print(row)
            writer.writerow(row)
            y += 1
            x += 1
