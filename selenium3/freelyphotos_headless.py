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
from selenium.webdriver.common.action_chains import ActionChains
from urllib.request import urlopen, Request
import json
from urllib.parse import unquote

DIR = os.path.dirname(os.path.abspath(__file__))
print(DIR)
DRIVER_PATH = os.path.join(DIR, "chromedriver.exe")

FOLDER = 'freelyphotos'

FIRST_PAGE = int(sys.argv[1]) if len(sys.argv) > 1 else 1
LAST_PAGE = int(sys.argv[2]) if len(sys.argv) > 2 else 14

ITEM_PER_FOLDER = 50

# detail page
#THUMBNAIL_SELECTOR = "//article[@class='section section-text']/img"
#TITLE_SELECTOR = "//div[@class='sidebar-image-title']/h2"
#TAG_SELECTOR = "//div[@class='post-tags']//a"
# CC_SELECTOR = "//div[@class='desktopstuff']//a[@rel='license']"
AUTHOR_SELECTOR = "//div[@class='sm-swipeable']/div[@data-testid='lightbox_current_content']//p[@class='sm-text-ellipsis']"
# SOURCE_SELECTOR = "//div[@style='border:1px solid #c3c3c3; background-color:#fbfbfb; padding:10px; font-size:12px; margin-top:5px;']/div[@class='infleft'][text()='Source:']/following-sibling::div[1]/a"
# DATE_PUBLISHED_SELECTOR = "//article[@class='has-sidebar']/div[@class='' and not(@style)][1]/p[contains(text(),'Online') or contains(text(),'Taken')]"
#SIZE_SELECTOR = "//div[@class='stats clearfix']//li/i[@class='icon-frame']"
# FILE_TYPE_SELECTOR = "//div[@style=\"margin-top:5px; background-image:url('http://res.publicdomainfiles.com/i/dloption.png'); background-repeat:no-repeat;\"]/div[@style='border:1px solid #c9c9c9; float:right; margin-left:5px; width:318px; background-color:#FFFFFF;'][1]//div[@style='font-family:Arial; font-size:11px; padding-left:5px;'][last()]"
DOWNLOAD_SELECTOR = "//ul//button[@data-testid='lightbox_download_button']"

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
    #fix for special situations like lightbox
    driver.set_window_size(1500, 1500)
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


def checkPageFine(driver, selector, restartDriver=False, sec=3, sleep=0):
    #fix for special situations like lightbox
    driver.set_window_size(1500, 1500)
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


def waitForImageDownloaded(wait_for_dl_time=300, dl_time=300):
    global row
    print('checking if any new image file is being downloaded')
    downloadingExtension = 'crdownload'
    listOfDownloadingFile = []
    i = 0
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


def getPage(driver, url):
    print('calling:')
    print(url)
    while True:
        try:
            driver.get(url)
            break
        except TimeoutException as e:
            saveErrorDownloadLog(-1, -1, url)
            print("Page load Timeout occured.")


driver = webdriver.Chrome(options=chrome_options, executable_path=DRIVER_PATH)

x = FIRST_PAGE
while x < LAST_PAGE+1:
    subfolder = x
    jsonURL = f'https://beta.freelyphotos.com/services/api/json/1.4.0/?galleryType=album&albumId=152755796&albumKey=SgvdNL&nodeId=5phFdx&PageNumber={x}&imageId=0&imageKey=&returnModelList=true&PageSize={ITEM_PER_FOLDER}&method=rpc.gallery.getalbum'
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

    if len(data['Images']) == 0:
        break

    y = 0  # counter for item in each folder
    with open(filename, 'w', encoding="utf-8", newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['id', 'detailURL', 'author',
                         'fileName', 'date_downloaded'])
        while y < ITEM_PER_FOLDER:

            yPath = os.path.join(dirname, f"y.txt")
            yFile = pathlib.Path(yPath)

            if y == 0 and yFile.exists():
                fileContent = open(yPath, 'r')
                string = fileContent.readline()
                if string.isdigit():
                    y = int(string)
            else:
                fileContent = open(yPath, 'w')
                fileContent.write(str(y))

            print('subfolder')
            print(subfolder)
            print('y')
            print(y)

            item = data['Images'][y]

            itemid = item['ImageID']
            print('itemid')
            print(itemid)
            row = [itemid]

            """ detailURL = unquote(item['LightboxUrl']) """
            detailURL = item['LightboxUrl']
            print('detailURL')
            print(detailURL)
            row.append(detailURL)

            getPage(driver, detailURL)

            """ tags = selectCatch(driver, TAG_SELECTOR, 'text', True)
            print('tags')
            print(tags)
            row.append(tags) """

            if checkPageFine(driver, DOWNLOAD_SELECTOR) == False:
                continue

            author = selectCatch(driver, AUTHOR_SELECTOR)
            author = author.replace('📷: ', '')
            print('author')
            print(author)
            row.append(author)

            dirname2 = dirname.replace('/', '\\')
            params = {'behavior': 'allow',
                      'downloadPath': dirname2}
            driver.execute_cdp_cmd('Page.setDownloadBehavior', params)

            # clear old .crdownloaded before downloading...
            list_of_old_crdownloaded = glob.glob(f'{dirname}/*.crdownload')
            for crdownload in list_of_old_crdownloaded:
                os.remove(crdownload)

            # triggering page for image download from browser
            downloadBtn = driver.find_element_by_xpath(DOWNLOAD_SELECTOR)
            print(downloadBtn)
            if downloadBtn is None:
                continue
            driver.execute_script("arguments[0].click();", downloadBtn)

            isImageDownloaded = waitForImageDownloaded()

            if isImageDownloaded:
                print(row)
                writer.writerow(row)
                y += 1
                print(y)
                fileContent = open(yPath, 'w')
                fileContent.write(str(y))
                driver.quit()
                driver = webdriver.Chrome(
                    options=chrome_options, executable_path=DRIVER_PATH)

            else:
                print('restarting session...')
                driver.quit()
                driver = webdriver.Chrome(
                    options=chrome_options, executable_path=DRIVER_PATH)
                continue

    x += 1
