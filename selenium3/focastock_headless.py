﻿from selenium import webdriver
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

DIR = os.path.dirname(os.path.abspath(__file__))
print(DIR)
DRIVER_PATH = os.path.join(DIR, "chromedriver.exe")

FOLDER = 'focastock'

# list page
AELEMENTS_SELECTOR = "//div[@id='macy-wp-loop-grid-container']/a"
#LAST_AELEMENT_SELECTOR = "//div[@class='img-grid animated-grid']/div[contains(@class,'reveal') and not(contains(@class,'pubspace'))][30]/a"
MORE_SELECTOR = "//button[text()='Load more']"

# detail page
THUMBNAIL_SELECTOR = "//div[@class='content-single__preview__image']/img"
#ID_SELECTOR = "//header/dl/dd"
TITLE_SELECTOR = "//h1[@class='content-single__details__title']"
TAG_SELECTOR = "//div[@class='content-single__details__categories']//a"
#CATEGORY_SELECTOR = "//a[@rel='category tag']"
#CC_SELECTOR = "//div[@class='desktopstuff']//a[@rel='license']"
#AUTHOR_SELECTOR = "//h1/a"
#SOURCE_SELECTOR = "//div[contains(text(),'Source')]"
#DATE_PUBLISHED_SELECTOR = "//span[@class='date']//a"
#SIZE_SELECTOR = "//div[@id='detail_content']/div[1]"
# FILE_TYPE_SELECTOR = "//div[@style=\"margin-top:5px; background-image:url('http://res.publicdomainfiles.com/i/dloption.png'); background-repeat:no-repeat;\"]/div[@style='border:1px solid #c9c9c9; float:right; margin-left:5px; width:318px; background-color:#FFFFFF;'][1]//div[@style='font-family:Arial; font-size:11px; padding-left:5px;'][last()]"
DOWNLOAD_SELECTOR = "//button[text()='Download photo']"

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


def login():
    global driver, USERNAME_SELECTOR, PASSWORD_SELECTOR, SIGNIN_SELECTOR
    driver.get(f'https://www.rawpixel.com/user/login')
    """ driver.find_element_by_xpath(OPENSIGNIN_SELECTOR).click() """

    email = driver.find_element_by_xpath(USERNAME_SELECTOR)
    password = driver.find_element_by_xpath(PASSWORD_SELECTOR)

    email.send_keys("jnontoquine")
    password.send_keys("123456789")

    driver.find_element_by_xpath(SIGNIN_SELECTOR).click()

    print('clicked login')


previous_file = 'abc'
latest_file = 'abc'

# driver is for loading listing page
driver = webdriver.Chrome(options=chrome_options, executable_path=DRIVER_PATH)

# driver2 is for loading detail page and download
driver2 = webdriver.Chrome(options=chrome_options, executable_path=DRIVER_PATH)
listingPage = 'https://focastock.com/browse/'
driver.get(listingPage)

print('listingPage:')
print(listingPage)

moreBtn = driver.find_element_by_xpath(MORE_SELECTOR)
lastLenDetailURLs = 0
y = 0
while moreBtn:

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

    """ driver.execute_script("window.scrollTo(0, document.body.scrollHeight)") """

    detailUrls = selectCatch(driver, AELEMENTS_SELECTOR, 'href', True)

    yPath = os.path.join(DIR, f"{FOLDER}/y.txt")
    yFile = pathlib.Path(yPath)
    if yFile.exists():
        fileContent = open(yPath, 'r')
        string = fileContent.readline()
        if string.isdigit():
            y = int(float(string))

    beforeLenDetailURLs = copy.copy(len(detailUrls))
    while len(detailUrls) <= lastLenDetailURLs:
        moreBtn = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located(
                (By.XPATH, MORE_SELECTOR))
        )
        print(moreBtn)
        driver.execute_script("arguments[0].click();", moreBtn)

        print(moreBtn)
        time.sleep(1)
        moreBtn = WebDriverWait(driver, 20).until(EC.text_to_be_present_in_element((By.XPATH, MORE_SELECTOR),'Load more'))

        detailUrls = selectCatch(driver, AELEMENTS_SELECTOR, 'href', True)
        print('len(detailUrls)')
        print(len(detailUrls))

    print('len(detailUrls)')
    print(len(detailUrls))
    print(detailUrls)
    with open(filename, 'w', encoding="utf-8", newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['detailUrl', 'title', 'tags',
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

            title = selectCatch(driver2, TITLE_SELECTOR)
            print('title')
            print(title)
            row.append(title)

            tags = selectCatch(driver2, TAG_SELECTOR, 'text', True)
            print('tags')
            print(tags)
            row.append(tags)

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

            dirname2 = dirname.replace('/', '\\')
            params = {'behavior': 'allow',
                      'downloadPath': dirname2}
            driver2.execute_cdp_cmd('Page.setDownloadBehavior', params)

            downloadBtn = driver2.find_element_by_xpath(DOWNLOAD_SELECTOR)
            downloadBtn.click()

            print('checking if new image file is downloaded')
            i = 0
            fileExtensions = ["jpg", "jpeg", "png", "bmp", "gif"]
            listOfFiles = []
            while True:
                print(f'{i}s...')
                for extension in fileExtensions:
                    listOfFiles.extend(
                        glob.glob(dirname + '/*.' + extension))
                    if listOfFiles:
                        latest_file = max(listOfFiles, key=os.path.getctime)

                if (previous_file != latest_file):
                    print('previous_file')
                    print(previous_file)
                    print('latest_file')
                    print(latest_file)
                    previous_file = latest_file
                    break
                if i > 120:
                    print(
                        'download is too slow, remove crdownload, then restart session...')
                    driver2.quit()
                    list_of_files2 = glob.glob(f'{dirname}/*.crdownload')
                    for crdownload in list_of_files2:
                        os.remove(crdownload)
                    driver2 = webdriver.Chrome(options=chrome_options, executable_path=DRIVER_PATH)
                    break
                time.sleep(1)
                i += 1

            if i > 120:
                print('restarting session....')
                continue

            print(
                f'latest jpg file downloaded: {os.path.basename(latest_file)}')
            row.append(os.path.basename(latest_file))
            row.append(getDateString())

            print(row)
            writer.writerow(row)
            y += 1
            fileContent = open(yPath, 'w')
            fileContent.write(str(y))
        lastLenDetailURLs = len(detailUrls)
