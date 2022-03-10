from selenium import webdriver
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException, ElementClickInterceptedException
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.common.action_chains import ActionChains
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
FOLDER = 'snappygoat'

KEYWORD_CSV = os.path.join(DIR, f"snappygoat_keywords.txt")
KEYWORDFile = pathlib.Path(KEYWORD_CSV)
if KEYWORDFile.exists():
    keywords = open(KEYWORDFile).read().splitlines()
else:
    print('I cannot find snappygoat_keywords.txt')
    sys.exit()

# list page
AELEMENTS_SELECTOR = "//div[@id='ph']/div[contains(@class,'f')]"
AELEMENTS_A_SELECTOR = f"{AELEMENTS_SELECTOR}/a"
DOWNLOAD_SELECTOR = "//div[@class='bpic']//td[text()='View Original:']//following-sibling::td[1]/a[@class='llink']"
CC_SELECTOR = "//div[@class='bpic']//td[text()='Courtesy of:']//following-sibling::td[1]/a[@class='llink']"

hasLogin = False


def restartDriver(driverTemp, timeoutTemp=40):
    global hasLogin

    DRIVER_PATH = os.path.join(DIR, "chromedriver.exe")

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
    chrome_options.add_argument(
        "--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.86 Safari/537.36")

    d = DesiredCapabilities.CHROME
    d['loggingPrefs'] = {'browser': 'ALL'}

    driverTemp = webdriver.Chrome(
        options=chrome_options, executable_path=DRIVER_PATH, desired_capabilities=d)
    driverTemp.set_page_load_timeout(timeoutTemp)
    driverTemp.delete_all_cookies()

    if hasLogin:
        driverTemp = login(driverTemp)

    return driverTemp


def selectCatch(driver, selector, type='text', multiple=False):
    staleElement = True
    while(staleElement):
        try:
            if multiple:
                elements = driver.find_elements_by_xpath(selector)
                elementList = []
                for element in elements:
                    elementList.append(getSelect(element, type))

                return elementList
            else:
                element = driver.find_element_by_xpath(selector)

            staleElement = False
            return getSelect(element, type)

        except NoSuchElementException:
            print('no such element:')
            print(selector)
            staleElement = False
            return ''

        except StaleElementReferenceException:
            print('selected element seems changed, retrying to select the element:')
            print(selector)
            staleElement = True


def getSelect(element, type='text'):
    if type == 'text':
        return element.text
    return element.get_attribute(type)


def getDateString():
    now = datetime.now()
    print("now =", now)
    # dd/mm/YY H:M:S
    return now.strftime("%Y.%m.%d_%H.%M.%S")


def makeScreenshot(driverTemp, screenShotPath, height=1500, width=1092):
    driverTemp.set_window_size(width, height)
    dt = getDateString()
    saveScreenshotPath = os.path.join(screenShotPath, f"screenshot/{dt}.png")
    if not os.path.exists(os.path.dirname(saveScreenshotPath)):
        os.makedirs(os.path.dirname(saveScreenshotPath))
    driverTemp.save_screenshot(saveScreenshotPath)


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


def isURLValid(URL):
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

    if (isURLValid(URL) is not True):
        return ''

    if isVirtual:
        # Open the url image, set stream to True, this will return the stream content.

        r = requests.get(URL, stream=isStream, headers={
                         'User-agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 11_0 like Mac OS X) AppleWebKit/604.1.38 (KHTML, like Gecko) Version/11.0 Mobile/15A5370a Safari/604.1'})
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
    if (isURLValid(URL) is not True):
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
            saveErrorDownloadLog(f"Image Couldn\'t be retrieved: {URL}")
            row.append('')
            row.append('')
            row.append('')
    except OSError as e:
        saveErrorDownloadLog(f"OSError on file download: {URL}")
        print(e)


def clickCatch(driverTemp, selector, mouse_simulation=False, wait_time=5):
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
                # element.click()
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


def saveErrorDownloadLog(content):
    logPath = os.path.join(DIR, f"{FOLDER}/error.log")
    logFile = pathlib.Path(logPath)
    if logFile.exists():
        with open(logPath, 'a') as file:
            file.write(f'{content}\n')


def getPage(driverTemp, url):
    print('calling:')
    print(url)
    while True:
        try:
            driverTemp.get(url)
            break
        except TimeoutException as e:
            saveErrorDownloadLog(f"Timeout on page call: {url}")
            driverTemp.delete_all_cookies()
            print("Page load Timeout. Deleting cookies and retrying...")


driver = None
driver = restartDriver(driver)

for keyword in keywords:
    getPage(driver, f'https://snappygoat.com/s/?q={keyword}')

    lastLenDetailURLs = 0
    y = 0
    while True:

        print('subfolder')
        print(keyword)

        if checkPageFine(driver, AELEMENTS_A_SELECTOR, True) == False:
            driver = restartDriver(driver)
            getPage(driver, f'https://snappygoat.com/s/?q={keyword}')
            continue

        detailUrls = selectCatch(driver, AELEMENTS_A_SELECTOR, 'href', True)

        yPath = os.path.join(DIR, f"{FOLDER}/{keyword}/y.txt")
        yFile = pathlib.Path(yPath)
        if yFile.exists():
            fileContent = open(yPath, 'r')
            string = fileContent.readline()
            if string.isdigit():
                y = int(float(string))

        retrialTimes = 0
        maxRetrialTimes = 10
        isReachMaxRetrialTimes = False
        while len(detailUrls) <= lastLenDetailURLs:
            driver.execute_script("window.scrollTo(0, 0)")
            driver.execute_script(
                "window.scrollTo(0, document.body.scrollHeight)")

            makeScreenshot(driver, os.path.dirname(yFile))
            detailUrls = selectCatch(
                driver, AELEMENTS_A_SELECTOR, 'href', True)
            print('checking for more detail URLs total:')
            print(len(detailUrls))
            retrialTimes += 1
            print('retrial times: #')
            print(retrialTimes)
            if retrialTimes >= maxRetrialTimes:
                print(
                    'reached max retrial times, no new detail URLs, jump to next keyword...')
                isReachMaxRetrialTimes = True
                break
            time.sleep(1)

        if isReachMaxRetrialTimes:
            break

        print('len(detailUrls)')
        print(len(detailUrls))
        # print(detailUrls)
        if y < len(detailUrls):
            dt_string = getDateString()
            listFile = f'list.csv'
            print('creating '+f'{listFile}...')
            filename = os.path.join(
                DIR, f"{FOLDER}/{keyword}/{lastLenDetailURLs}/{listFile}")
            # print(filename)
            dirname = os.path.dirname(filename)
            print('dirname:')
            print(dirname)
            if not os.path.exists(dirname):
                os.makedirs(dirname)
            isCSVExists = os.path.exists(filename)
            with open(filename, 'a', encoding="utf-8", newline='') as csvfile:
                writer = csv.writer(csvfile)
                if not isCSVExists:
                    writer.writerow(['y', 'detailUrl', 'cc', 'ccURL', 'fileURL',
                                     'fileName', 'date_downloaded'])
                while y < len(detailUrls):
                    print('folder:')
                    print(dirname)
                    print('y')
                    print(y)
                    print('detailUrl')
                    print(detailUrls[y])

                    row = [y, detailUrls[y]]

                    print(f"{AELEMENTS_SELECTOR}[{y+1}]")
                    clickCatch(
                        driver, f"{AELEMENTS_SELECTOR}[{y+1}]", True, 10)

                    makeScreenshot(driver, dirname)

                    cc = selectCatch(driver, CC_SELECTOR)
                    print('cc')
                    print(cc)
                    row.append(cc)

                    cc_url = selectCatch(driver, CC_SELECTOR, 'href')
                    print('cc_url')
                    print(cc_url)
                    row.append(cc_url)

                    imageURL = selectCatch(driver, DOWNLOAD_SELECTOR, 'href')
                    print('imageURL')
                    print(imageURL)

                    downloadFromURL(imageURL, dirname, row)

                    print(row)
                    writer.writerow(row)
                    y += 1
                    fileContent = open(yPath, 'w')
                    fileContent.write(str(y))
        lastLenDetailURLs = len(detailUrls)
