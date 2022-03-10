from selenium import webdriver
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException, ElementClickInterceptedException
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.common.action_chains import ActionChains
import errno
from urllib.parse import parse_qs
import urllib.parse as urlparse
from urllib.request import urlopen, Request, urlretrieve
from datetime import datetime
import csv
import os
import re
import copy
import time
import sys
import requests
import shutil
import pathlib
import cgi
import glob

DIR = os.path.dirname(os.path.abspath(__file__))
print(DIR)

yPath = yFile = ''
filename = dirname = ''
hasLogin = False

FOLDER = 'pexels'

DRIVER_PATH = os.path.join(DIR, "chromedriver.exe")

FIRST_PAGE = int(sys.argv[1]) if len(sys.argv) > 1 else 1
LAST_PAGE = int(sys.argv[2]) if len(sys.argv) > 2 else 9999999

# list page
#AELEMENTS_SELECTOR = "//div[@class='item']/a"
#LAST_AELEMENT_SELECTOR = "//div[@class='img-grid animated-grid']/div[contains(@class,'reveal') and not(contains(@class,'pubspace'))][30]/a"

# detail page
THUMBNAIL_SELECTOR = "//div[@id='photo-page-body']//div[@class='photo-page__photo']//img"
#ID_SELECTOR = "//header/dl/dd"
#TITLE_SELECTOR = "//h1"
TAG_SELECTOR = "//ul[@class='photo-page__related-tags__container']//a"
#CATEGORY_SELECTOR = "//th[text()='Category']/following-sibling::td/a"
#CC_SELECTOR = "//h5[text()='Check license']/following-sibling::a[1]"
AUTHOR_SELECTOR = "//div[@id='photo-page-body']//h3[@class='js-photo-page-mini-profile-full-name photo-page__mini-profile__text__title']"
AUTHOR_URL_SELECTOR = "//div[@id='photo-page-body']//a[@class='js-photo-page-mini-profile-link photo-page__mini-profile']"
#SOURCE_SELECTOR = "//div[contains(text(),'Source')]"
DATE_CREATED_SELECTOR = "//td[text()='Taken at']/following-sibling::td"
#DATE_PUBLISHED_SELECTOR = "//th[text()='Uploaded']/following-sibling::td"
#SIZE_SELECTOR = "//label[contains(text(),'Resolution')]/following-sibling::p"
# FILE_TYPE_SELECTOR = "//div[@style=\"margin-top:5px; background-image:url('http://res.publicdomainfiles.com/i/dloption.png'); background-repeat:no-repeat;\"]/div[@style='border:1px solid #c9c9c9; float:right; margin-left:5px; width:318px; background-color:#FFFFFF;'][1]//div[@style='font-family:Arial; font-size:11px; padding-left:5px;'][last()]"
# DOWNLOAD_OPTION_SELECTOR = "//span[text()='download for free']"
# DOWNLOAD_OPTION2_SELECTOR = "//div[@class='download-options']/label[@for='download-option'][last()]"
#DOWNLOAD_SELECTOR = "//div[@class='tab-pane fade show active']//a[text()='Original Size']"
INFO_BTN_SELECTOR ="//button[@data-track-action='info-button']"

hasLogin = False


def waitForCloudflareCheck(driverTemp):
    CLOUDFLARETEXT_SELECTOR = "//h1/span[contains(text(),'Checking your')]"
    cloudflareText = selectCatch(driverTemp, CLOUDFLARETEXT_SELECTOR)
    while cloudflareText == 'Checking your browser before accessing':
        time.sleep(1)
        cloudflareText = selectCatch(driverTemp, CLOUDFLARETEXT_SELECTOR)
        makeScreenshot(driverTemp)
        print('waiting for cloudflare check...')

    print('cloudflare check page is done!')
    return True


def login(driverTemp):
    global loginURL
    global USERNAME_SELECTOR, PASSWORD_SELECTOR, SIGNIN_SELECTOR
    global usernameText, passwordText
    #global OPENSIGNIN_SELECTOR

    getPage(driverTemp, loginURL)

    # driver.find_element_by_xpath(OPENSIGNIN_SELECTOR).click()

    email = driverTemp.find_element_by_xpath(USERNAME_SELECTOR)
    password = driverTemp.find_element_by_xpath(PASSWORD_SELECTOR)

    email.send_keys(usernameText)
    password.send_keys(passwordText)

    clickCatch(driverTemp, SIGNIN_SELECTOR)

    print('clicked login')


def getDateString():
    now = datetime.now()
    print("now =", now)
    # dd/mm/YY H:M:S
    return now.strftime("%Y.%m.%d_%H.%M.%S")


def writeListCSV(row, isInit=True):
    global filename, dirname, DIR, FOLDER, x

    if isInit:
        listFile = f'list.csv'
        print('creating '+f'{listFile}...')
        filename = os.path.join(
            DIR, f"{FOLDER}/{x}/{listFile}")
        # print(filename)
        dirname = os.path.dirname(filename)
        print('dirname:')
        print(dirname)
        if not os.path.exists(dirname):
            os.makedirs(dirname)

    with open(filename, 'a', encoding="utf-8", newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(row)


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


def makeScreenshot(driverTemp, height=1500, width=1092):
    driverTemp.set_window_size(width, height)
    dt = getDateString()
    saveScreenshotPath = os.path.join(dirname, f"screenshot/{dt}.png")
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
            waitForCloudflareCheck(driverTemp)
            break
        except TimeoutException as e:
            saveErrorDownloadLog(f"Timeout on page call: {url}")
            driverTemp.delete_all_cookies()
            print("Page load Timeout. Deleting cookies and retrying...")


def clickCatch(driverTemp, selector, wait_time=5, mouse_simulation=False):
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


def restartDriver(driverTemp, isHeadless=True, timeoutTemp=40):
    global hasLogin

    DRIVER_PATH = os.path.join(DIR, "chromedriver.exe")

    if driverTemp is not None:
        driverTemp.delete_all_cookies()
        driverTemp.quit()

    chrome_options = webdriver.ChromeOptions()
    chrome_options.headless = isHeadless
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
        login(driverTemp)

    return driverTemp


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
        r = requests.get(URL, stream=isStream, headers={
                         'User-agent': 'Mozilla/5.0'})
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
    global x
    if (isURLvalid(URL) is not True):
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

            return True
        else:
            print('Image Couldn\'t be retrieved')
            saveErrorDownloadLog(f"Image Couldn\'t be retrieved: {x}")
            return False
    except (OSError, IOError) as e:
        saveErrorDownloadLog(getErrorMessage(e, f"on file download: {x}"))
        print(e)
        return False
    except:
        saveErrorDownloadLog(
            f"Unexpected error on file download: {sys.exc_info()[0]}")
        return False
    return False


def getErrorMessage(e, content):
    # PermissionError
    if e.errno == EPERM or e.errno == EACCES:
        return f"PermissionError error({e.errno}): {e.strerror}: {content}"
    # FileNotFoundError
    elif e.errno == ENOENT:
        return f"FileNotFoundError error({e.errno}): {e.strerror}: {content}"
    elif IOError:
        return f"I/O error({e.errno}): {e.strerror}: {content}"
    elif OSError:
        return f"OS error({e.errno}): {e.strerror}: {content}"


def waitForJQuery(driverTemp, timeout=10):
    i = 0
    while i < timeout:
        print(f'{i}s.. checking jquery')
        isjQuerySet = driverTemp.execute_script(
            "return (typeof jQuery != 'undefined');")
        if isjQuerySet:
            return True
        time.sleep(1)
        i += 1
    return False


x = FIRST_PAGE
y = 0
try:
    driver = None
    driver = restartDriver(driver)
    while x < LAST_PAGE + 1:

        print('x')
        print(x)

        getPage(driver, f'https://www.pexels.com/photo/{x}')

        if checkPageFine(driver, THUMBNAIL_SELECTOR) == False:
            x += 1
            continue

        y += 1

        fields = ['id', 'detailURL', 'author', 'authorURL', 'tags', 'date_created', 
                'thumbnailURL', 'thumbnailName', 'date_downloaded']

        # if y > 500 then open a new folder and reset y
        if y == 1 or y > 500:
            writeListCSV(fields)

        if y > 500:
            driver = restartDriver(driver)
            y = 1

        print(f'# in folder {dirname}')
        print(y)

        row = [x, driver.current_url]

        makeScreenshot(driver)

        clickCatch(driver, INFO_BTN_SELECTOR)

        author = selectCatch(driver, AUTHOR_SELECTOR)
        print('author')
        print(author)
        row.append(author)

        authorURL = selectCatch(driver, AUTHOR_URL_SELECTOR, 'href')
        print('authorURL')
        print(authorURL)
        row.append(authorURL)

        tags = selectCatch(driver, TAG_SELECTOR, 'text', True)
        print('tags')
        print(tags)
        row.append(tags)

        date_created = selectCatch(driver, DATE_CREATED_SELECTOR)
        print('date_created')
        print(date_created)
        row.append(date_created)

        downloadURL = selectCatch(driver, THUMBNAIL_SELECTOR, 'src')

        isImageDownloaded = downloadFromURL(downloadURL, dirname, row)

        if isImageDownloaded:
            print(row)
            writeListCSV(row, False)
        else:
            print(
                'image not downloaded... clearing cookies, restarting session, save error log, and go to next id...')
            saveErrorDownloadLog(f"Image cannot be downloaded: {x}")
            driver = restartDriver(driver)

        x += 1
except:
    saveErrorDownloadLog(
        f"Unexpected error: {sys.exc_info()[0]}")
