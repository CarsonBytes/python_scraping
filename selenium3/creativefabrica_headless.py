#listing_URL = 'https://www.creativefabrica.com/subscriptions/fonts'
listing_URL = 'https://www.creativefabrica.com/search/?query=antique'

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

saveScreenshot = False
DIR = os.path.dirname(os.path.abspath(__file__))
print(DIR)

yPath = yFile = ''
filename = dirname = ''
hasLogin = True

FOLDER = 'creativefabrica'

DRIVER_PATH = os.path.join(DIR, "chromedriver.exe")

FIRST_PAGE = int(sys.argv[1]) if len(sys.argv) > 1 else 1
LAST_PAGE = int(sys.argv[2]) if len(sys.argv) > 2 else 9999999

# login page
loginURL = 'https://www.creativefabrica.com/login/'
USERNAME_SELECTOR = "//input[@name='username']"
PASSWORD_SELECTOR = "//input[@id='password-input-login']"
SIGNIN_SELECTOR = "//button[@name='login']"
LOGINBTN_SELECTOR = "//div[@class='menu-icons']/a[text()='Login']"
usernameText = "jnontoquine@gmail.com"
passwordText = "2n*QLfs^aM3E"
#passwordText = "12345"

# list page
AELEMENTS_SELECTOR = "//div[contains(@class,'col-card')]/div/a"
SEARCH_AELEMENTS_SELECTOR = "//li[contains(@class,'ais-Hits-item')]/div/a"
#LAST_AELEMENT_SELECTOR = "//div[@class='img-grid animated-grid']/div[contains(@class,'reveal') and not(contains(@class,'pubspace'))][30]/a"

# detail page
THUMBNAIL_SELECTOR = "//div[@class='fotorama__stage__shaft']/div[1]/img[@class='fotorama__img']"
#ID_SELECTOR = "//header/dl/dd"
TITLE_SELECTOR = "//h1"
DESC_SELECTOR = "//div[@id='single-product-description']/p"
TAG_SELECTOR = "//div[@class='c-product-box--product-detail-box u-mt-20']//a"
CATEGORY_SELECTOR = "//ul[@class='c-breadcrumb__list']/li"
#CC_SELECTOR = "//h5[text()='Check license']/following-sibling::a[1]"
AUTHOR_SELECTOR = "//div[@class='pull-left foreground']/h4/a"
#AUTHOR_URL_SELECTOR = "//div[@id='photo-page-body']//a[@class='js-photo-page-mini-profile-link photo-page__mini-profile']"
#SOURCE_SELECTOR = "//div[contains(text(),'Source')]"
DATE_CREATED_SELECTOR = "//span[contains(text(),'Listed on')]"
#DATE_PUBLISHED_SELECTOR = "//th[text()='Uploaded']/following-sibling::td"
#SIZE_SELECTOR = "//label[contains(text(),'Resolution')]/following-sibling::p"
# FILE_TYPE_SELECTOR = "//div[@style=\"margin-top:5px; background-image:url('http://res.publicdomainfiles.com/i/dloption.png'); background-repeat:no-repeat;\"]/div[@style='border:1px solid #c9c9c9; float:right; margin-left:5px; width:318px; background-color:#FFFFFF;'][1]//div[@style='font-family:Arial; font-size:11px; padding-left:5px;'][last()]"
# DOWNLOAD_OPTION_SELECTOR = "//span[text()='download for free']"
# DOWNLOAD_OPTION2_SELECTOR = "//div[@class='download-options']/label[@for='download-option'][last()]"
DOWNLOAD_SELECTOR = "//a[contains(@class,'product-download-button')]"
#INFO_BTN_SELECTOR = "//button[@data-track-action='info-button']"


def updateURLParams(url, params):
    #params = {"lang":"en", "tag":"python"}
    url_parse = urlparse.urlparse(url)
    query = url_parse.query
    url_dict = dict(urlparse.parse_qsl(query))
    url_dict.update(params)
    url_new_query = urlparse.urlencode(url_dict)
    url_parse = url_parse._replace(query=url_new_query)
    return urlparse.urlunparse(url_parse)


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

    getPage(driverTemp, "https://www.creativefabrica.com/")

    waitForJQuery(driverTemp)

    driverTemp.maximize_window()

    clickCatch(driverTemp, LOGINBTN_SELECTOR)

    #getPage(driverTemp, loginURL)

    """ wait = WebDriverWait(driverTemp,10)

    wait.until(EC.element_to_be_clickable((By.XPATH,USERNAME_SELECTOR))).send_keys(usernameText)

    wait.until(EC.element_to_be_clickable((By.XPATH,PASSWORD_SELECTOR))).click()
    wait.until(EC.element_to_be_clickable((By.XPATH,PASSWORD_SELECTOR))).send_keys(passwordText)
    """

    email = driverTemp.find_element_by_xpath(USERNAME_SELECTOR)
    #password = driverTemp.find_element_by_xpath(PASSWORD_SELECTOR)

    email.send_keys(usernameText)
    """ password.click()
    password.send_keys(passwordText) """

    driverTemp.execute_script(
        "jQuery('#password-input-login').val('"+passwordText+"')")

    clickCatch(driverTemp, SIGNIN_SELECTOR)

    print('clicked login')


def getDateString():
    now = datetime.now()
    print("now =", now)
    # dd/mm/YY H:M:S
    return now.strftime("%Y.%m.%d_%H.%M.%S")


def writeListCSV(row, isInit=True):
    global filename, dirname, DIR, FOLDER, x, listing_URL

    if isInit:
        listFile = f'list.csv'
        print('creating '+f'{listFile}...')
        filename = os.path.join(
            DIR, f"{FOLDER}/{changedURL}/{x}/{listFile}")
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
    global DIR, FOLDER, changedURL, saveScreenshot

    if saveScreenshot:
        driverTemp.set_window_size(width, height)
        saveScreenshotPath = os.path.join(
            DIR, f"{FOLDER}/{changedURL}", f"screenshot/{getDateString()}.png")
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
            # waitForCloudflareCheck(driverTemp)
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
        makeScreenshot(driverTemp)
        time.sleep(5)
        makeScreenshot(driverTemp)

    return driverTemp


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


def getTxt(variable, default_value=0):
    global DIR, FOLDER, txtFile, changedURL
    tempPath = os.path.join(DIR, f"{FOLDER}/{changedURL}/{x}/{variable}.txt")
    tempFolderPath = os.path.dirname(tempPath)
    tempFile = pathlib.Path(tempPath)

    if not os.path.exists(tempFolderPath):
        os.makedirs(tempFolderPath)

    if tempFile.exists():
        fileContent = open(tempPath, 'r')
        string = fileContent.readline()
        if string.isdigit():
            txtFile[variable] = int(string)
            return txtFile[variable]

    return saveTxt(variable, default_value)


def saveTxt(variable, number):
    global DIR, FOLDER, txtFile
    tempPath = os.path.join(DIR, f"{FOLDER}/{changedURL}/{x}/{variable}.txt")
    tempFolderPath = os.path.dirname(tempPath)
    tempFile = pathlib.Path(tempPath)

    if not os.path.exists(tempFolderPath):
        os.makedirs(tempFolderPath)

    fileContent = open(tempPath, 'w')
    fileContent.write(str(number))

    txtFile[variable] = int(number)
    return txtFile[variable]


def getSubstringBetween(text, left, right):
    try:
        return re.search(f'{left}(.+?){right}', text).group(1)
    except AttributeError:
        return ''


def waitForSmallFileDownloaded(driverTemp, wait_for_dl_time=10, dl_time=300):
    global dirname, row
    target_path = ''
    try:
        print('checking if any new image file is being downloaded')
        downloadingExtension = 'crdownload'
        listOfDownloadingFile = []
        i = 0
        call = None
        while True:
            if i % 1 == 0:
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
            i += 0.1
            time.sleep(0.1)

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
    except (OSError, IOError) as e:
        saveErrorDownloadLog(getErrorMessage(
            e, f"on waiting for file to be downloaded: {dirname}"))
        print(e)
        return False
    except:
        saveErrorDownloadLog(
            f"Unexpected error on file download: {sys.exc_info()[0]}")
        return False
    return False


x = FIRST_PAGE
txtFile = {}
txtFile['y'] = 0

try:
    mapping = [ ('https://www.creativefabrica.com/', ''), ('/?', '_'), ('/', '_'), ('=', '_'), ('?', '_') ]
    changedURL = listing_URL
    for k, v in mapping:
        changedURL = changedURL.replace(k, v)

    driver = None
    driver = restartDriver(driver)
    while x < LAST_PAGE + 1:
        getTxt('y')

        print('x')
        print(x)

        if "/search/" in listing_URL:
            modified_listing_URL = updateURLParams(listing_URL, {'page': x})
            selected_AELEMENTS_SELECTOR = SEARCH_AELEMENTS_SELECTOR
        else:
            modified_listing_URL = listing_URL + f'/page/{x}/'
            selected_AELEMENTS_SELECTOR = AELEMENTS_SELECTOR

        print(modified_listing_URL)
        getPage(driver, modified_listing_URL)
        makeScreenshot(driver)

        element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, selected_AELEMENTS_SELECTOR))
        )

        detailUrls = selectCatch(
            driver, selected_AELEMENTS_SELECTOR, 'href', True)

        print('len of detailUrls')
        print(len(detailUrls))

        # print(detailUrls)

        if txtFile['y'] < len(detailUrls):

            fields = ['detailURL', 'title', 'desc', 'tags', 'category', 'author', 'authorURL',  'date_created',
                      'fileName', 'date_downloaded']
            writeListCSV(fields)

            while txtFile['y'] < len(detailUrls):

                row = [detailUrls[txtFile['y']]]

                getPage(driver, detailUrls[txtFile['y']])

                if checkPageFine(driver, THUMBNAIL_SELECTOR) == False:
                    print(
                        'THUMBNAIL_SELECTOR not there... clearing cookies, restarting session, save error log, and go to next id...')
                    saveErrorDownloadLog(
                        f"THUMBNAIL_SELECTOR not there: {detailUrls[txtFile['y']]}")
                    driver = restartDriver(driver)
                    saveTxt('y', txtFile['y']+1)
                    continue

                title = selectCatch(driver, TITLE_SELECTOR)
                print('title')
                print(title)
                row.append(title)

                desc = selectCatch(driver, DESC_SELECTOR)
                print('desc')
                print(desc)
                row.append(desc)

                tags = selectCatch(driver, TAG_SELECTOR, 'text', True)
                print('tags')
                print(tags)
                row.append(tags)

                cat = selectCatch(driver, CATEGORY_SELECTOR, 'text', True)
                print('cat')
                print(cat)
                row.append(cat)

                author = selectCatch(driver, AUTHOR_SELECTOR)
                print('author')
                print(author)
                row.append(author)

                authorURL = selectCatch(driver, AUTHOR_SELECTOR, 'href')
                print('authorURL')
                print(authorURL)
                row.append(authorURL)

                date_created = selectCatch(driver, DATE_CREATED_SELECTOR)
                date_created = getSubstringBetween(
                    date_created, 'Listed on ', ' - ID ')
                print('date_created')
                print(date_created)
                row.append(date_created)

                if checkPageFine(driver, DOWNLOAD_SELECTOR) == False:
                    continue

                dirname2 = dirname.replace('/', '\\')
                params = {'behavior': 'allow',
                          'downloadPath': dirname2}
                driver.execute_cdp_cmd('Page.setDownloadBehavior', params)

                # clear old .crdownloaded before downloading...
                list_of_old_crdownloaded = glob.glob(f'{dirname}/*.crdownload')
                for crdownload in list_of_old_crdownloaded:
                    os.remove(crdownload)

                # triggering page for image download from browser
                clickCatch(driver, DOWNLOAD_SELECTOR)

                isFileDownloaded = waitForSmallFileDownloaded(driver)

                if isFileDownloaded:
                    print(row)
                    writeListCSV(row, False)
                else:
                    print(
                        'file not downloaded... clearing cookies, restarting session, save error log, and go to next id...')
                    saveErrorDownloadLog(
                        f"File cannot be downloaded: {detailUrls[txtFile['y']]}")
                    driver = restartDriver(driver)

                saveTxt('y', txtFile['y']+1)

        x += 1
except:
    saveErrorDownloadLog(
        f"Unexpected error: {sys.exc_info()[0]}")
