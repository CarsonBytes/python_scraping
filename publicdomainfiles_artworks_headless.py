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

FOLDER = 'publicdomainfiles/artworks'

FIRST_PAGE = int(sys.argv[1]) if len(sys.argv) > 1 else 1
LAST_PAGE = int(sys.argv[2]) if len(sys.argv) > 2 else 56

# list page
AELEMENTS_SELECTOR = "//div[contains(@class,'bb')]/div/div/a"

# detail page
TITLE_SELECTOR = "//div[@style='border:1px solid #c3c3c3; background-color:#fbfbfb; padding:10px; font-size:12px; margin-top:5px;']/div[@class='infleft'][text()='Title:']/following-sibling::div[1]/span"
TAG_SELECTOR = "//div[@style='border:1px solid #c3c3c3; background-color:#fbfbfb; padding:10px; font-size:12px; margin-top:5px;']/div[@class='infleft'][text()='Keywords:']/following-sibling::div[1]/a"
# CC_SELECTOR = "//div[@class='desktopstuff']//a[@rel='license']"
AUTHOR_SELECTOR = "//div[@style='border:1px solid #c3c3c3; background-color:#fbfbfb; padding:10px; font-size:12px; margin-top:5px;']/div[@class='infleft'][text()='Creator:']/following-sibling::div[1]"
SOURCE_SELECTOR = "//div[@style='border:1px solid #c3c3c3; background-color:#fbfbfb; padding:10px; font-size:12px; margin-top:5px;']/div[@class='infleft'][text()='Source:']/following-sibling::div[1]/a"
DATE_PUBLISHED_SELECTOR = "//div[@style='border:1px solid #c3c3c3; background-color:#fbfbfb; padding:10px; font-size:12px; margin-top:5px;']/div[@class='infleft'][text()='Date Added:']/following-sibling::div[1]"
SIZE_SELECTOR = "//div[@style=\"margin-top:5px; background-image:url('http://res.publicdomainfiles.com/i/dloption.png'); background-repeat:no-repeat;\"]/div[@style='border:1px solid #c9c9c9; float:right; margin-left:5px; width:318px; background-color:#FFFFFF;'][1]//div[@style='font-family:Arial; font-size:11px; padding-left:5px;'][last()]"
FILE_TYPE_SELECTOR = "//div[@style=\"margin-top:5px; background-image:url('http://res.publicdomainfiles.com/i/dloption.png'); background-repeat:no-repeat;\"]/div[@style='border:1px solid #c9c9c9; float:right; margin-left:5px; width:318px; background-color:#FFFFFF;'][1]//div[@style='font-family:Arial; font-size:11px; padding-left:5px;'][last()]"
DOWNLOAD_SELECTOR = "//div[@style=\"margin-top:5px; background-image:url('http://res.publicdomainfiles.com/i/dloption.png'); background-repeat:no-repeat;\"]//div[@style='float:right; background-color:#DEDEDE; width:130px; margin:5px;']//input[@type='submit']"

chrome_options = webdriver.ChromeOptions()
chrome_options.headless = True
# chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=1320,1080")
chrome_options.add_argument('--ignore-certificate-errors')
chrome_options.add_argument('--ignore-ssl-errors')


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


def checkPageFine(selector, restartDriver=True, sec=3):
    global driver, temp_chrome_options, DRIVER_PATH
    try:
        element = WebDriverWait(driver, sec).until(
            EC.presence_of_element_located(
                (By.XPATH, selector))
        )
        return True
    except TimeoutException:
        print(
            f"TimeoutException on selecting {selector}! resetting session and retry the page...")
        driver.quit()
        print('sleeping.....')
        time.sleep(60)
        print('waking up.....')
        if restartDriver:
            driver = webdriver.Chrome(
                options=temp_chrome_options, executable_path=DRIVER_PATH)
        return False


def downloadFromURL(URL):
    global x, y, detailUrls
    try:
        # Open the url image, set stream to True, this will return the stream content.
        r = requests.get(URL, stream=True)

        # Check if the image was retrieved successfully
        if r.status_code == 200:
            # Set decode_content value to True, otherwise the downloaded image file's size will be zero.
            r.raw.decode_content = True

            # Open a local file with wb ( write binary ) permission.
            with open(savePath, 'wb') as f:
                shutil.copyfileobj(r.raw, f)

            print('Image sucessfully Downloaded: ', savePath)
            row.append(fileName)
            row.append(getDateString())
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
            file.write(page+':'+order+':'+detailUrl+'\n')
    else:
        with open(logPath, 'w') as file:
            file.write(page+':'+order+':'+detailUrl+'\n')


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
        

    listingPage = f'http://www.publicdomainfiles.com/browse.php?q=all&s={30*(x-1)}&o=newest&a=all&m=3'
    driver.get(listingPage)

    print('listingPage:')
    print(listingPage)

    if checkPageFine(AELEMENTS_SELECTOR, False) == False:
        continue

    AElements = driver.find_elements_by_xpath(AELEMENTS_SELECTOR)
    detailUrls = [el.get_attribute("href") for el in AElements]

    print('len of detailUrls')
    print(len(detailUrls))

    with open(filename, 'w', encoding="utf-8", newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['detailUrl', 'title', 'tags', 'author', 'source',
                         'source_URL', 'date_published', 'size', 'fileURL', 'fileName', 'date_downloaded'])
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

            if checkPageFine(DOWNLOAD_SELECTOR) == False:
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

            source = selectCatch(driver, SOURCE_SELECTOR)
            print('source')
            print(source)
            row.append(source)

            sourceURL = selectCatch(driver, SOURCE_SELECTOR, 'href')
            print('sourceURL')
            print(sourceURL)
            row.append(sourceURL)

            date_published = selectCatch(driver, DATE_PUBLISHED_SELECTOR)
            print('date_published')
            print(date_published)
            row.append(date_published)

            size = selectCatch(driver, SIZE_SELECTOR)
            print('size')
            size = size.replace('\r', '').replace('\n', '')
            result = re.search('Size: (.+?)File size', size)
            print(result)
            print(result.group(1))
            row.append(result.group(1))

            filetype = selectCatch(driver, FILE_TYPE_SELECTOR)
            print('file type')
            result = re.search('File type: (.*)', filetype)
            filetype = result.group(1)
            row.append(filetype)

            parsed = urlparse.urlparse(detailUrls[y])
            # print(parse_qs(parsed.query)['id'])
            fileName = parse_qs(parsed.query)['id'][0] + '.' + filetype
            savePath = os.path.join(DIR, f"{FOLDER}/{x}/{fileName}")
            print('drafted fileName')
            print(fileName)
            print('drafted savePath')
            print(savePath)

            file = pathlib.Path(savePath)
            if file.exists():
                print("File exist! skipped download")
                row.append(fileName)
                row.append('')
                print(row)
                writer.writerow(row)
                y += 1
                continue

            makeScreenshot()

            downloadBtn = driver.find_element_by_xpath(DOWNLOAD_SELECTOR)
            downloadBtn.click()
            print("waiting file to be downloaded")

            if filetype != 'tif':
                print('the image will be loaded on page..')
                downloadFromURL(driver.current_url)
            else:
                print('the image will be downloaded directly on page..')

                i = 0
                print('downloading...')
                while True:
                    if file.exists():
                        print("File exist!")
                        row.append(fileName)
                        row.append(getDateString())

                        i = 0
                        break
                    else:
                        i += 1
                        time.sleep(1)
                        print(str(i)+'s')
                        if i > 300:
                            saveErrorDownloadLog(x, y, detailUrls[y])
                            y += 1
                        continue

            print(row)
            writer.writerow(row)
            y += 1
    driver.quit()
    x += 1
