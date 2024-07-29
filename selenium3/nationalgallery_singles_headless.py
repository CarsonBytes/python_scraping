from selenium import webdriver
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException, ElementClickInterceptedException
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.common.action_chains import ActionChains
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
from multiprocessing import Pool

DIR = os.path.dirname(os.path.abspath(__file__))
print(DIR)

txtFile = {}
filename = dirname = ''
hasLogin = False

FOLDER = 'nationalgallery_single_headless'

DRIVER_PATH = os.path.join(DIR, "chromedriver.exe")

breakTime = 3600  # 1hour
FIRST_PAGE = int(sys.argv[1]) if len(sys.argv) > 1 else 1
LAST_PAGE = int(sys.argv[2]) if len(sys.argv) > 2 else 800
# login page
""" USERNAME_SELECTOR = "//input[@id='edit-name']"
PASSWORD_SELECTOR = "//input[@id='edit-pass']"
SIGNIN_SELECTOR = "//button[@id='edit-submit']"
username = "Yankee"
password = "23579691" """

# list page
AELEMENTS_SELECTOR = "//div[@class='image-item']/a"
# LAST_AELEMENT_SELECTOR = "//div[@class='img-grid animated-grid']/div[contains(@class,'reveal') and not(contains(@class,'pubspace'))][30]/a"

# detail page


def getFilePath():
    return os.path.join(
        os.path.dirname(os.path.abspath(__file__)), 'nationalgallery_single_headless/list.csv')
        
def getErrorLogPath():
    return os.path.join(
        os.path.dirname(os.path.abspath(__file__)), 'nationalgallery_single_headless/error.log')
        
def getDateString():
    now=datetime.now()
    print("now =", now)
    # dd/mm/YY H:M:S
    return now.strftime("%Y.%m.%d_%H.%M.%S")


def initListCSV():
    global filename, dirname, DIR, FOLDER
    listFile=f"list.csv"
    print('creating '+f'{listFile}...')
    filename=os.path.join(
        DIR, f"{FOLDER}/{listFile}")
    # print(filename)
    dirname=os.path.dirname(filename)
    print('dirname:')
    print(dirname)
    if not os.path.exists(dirname):
        os.makedirs(dirname)

def selectCatch(driver, selector, type='text', multiple=False):
    # fix for special situations like lightbox
    driver.set_window_size(1500, 1500)
    
    try:
        if multiple:
            elements=driver.find_elements_by_xpath(selector)
            elementList=[]
            for element in elements:
                elementList.append(getSelect(element, type))

            return elementList
        else:
            element=driver.find_element_by_xpath(selector)

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
    dt=getDateString()
    saveScreenshotPath=os.path.join(DIR, f"{FOLDER}/screenshot/{dt}.png")
    if not os.path.exists(os.path.dirname(saveScreenshotPath)):
        os.makedirs(os.path.dirname(saveScreenshotPath))
    driverTemp.save_screenshot(saveScreenshotPath)


def checkPageFine(driverTemp, selector, isRestartDriver=False, sec=3, sleep=0):
    # fix for special situations like lightbox
    driverTemp.set_window_size(1500, 1500)
    try:
        element=WebDriverWait(driverTemp, sec).until(
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
            driverTemp=restartDriver(driverTemp)
        return False


def saveErrorDownloadLog(page, detailUrl):
    logPath=getErrorLogPath()
    logFile=pathlib.Path(logPath)
    if logFile.exists():
        with open(logPath, 'a') as file:
            file.write(f'{page};{detailUrl}\n')
    else:
        with open(logPath, 'w') as file:
            file.write(f'{page};{detailUrl}\n')


def getPage(driverTemp, url):
    print('calling:')
    print(url)
    while True:
        try:
            driverTemp.get(url)
            break
        except TimeoutException as e:
            saveErrorDownloadLog(0, url)
            driverTemp.delete_all_cookies()
            print("Page load Timeout. Deleting cookies and retrying...")


def clickCatch(driverTemp, selector, wait_time=5, mouse_simulation=False):
    staleElement=True
    while staleElement:
        try:
            wait=WebDriverWait(driverTemp, wait_time)
            element=wait.until(
                EC.element_to_be_clickable((By.XPATH, selector)))

            if mouse_simulation:
                ActionChains(driverTemp).move_to_element(
                    element).click(element).perform()
            else:
                driverTemp.execute_script("arguments[0].click();", element)

            staleElement=False
            return True
        except StaleElementReferenceException:
            print('StaleElementReferenceException, retrying...')
            staleElement=True
        except TimeoutException:
            print('TimeoutException... element not found')
            return False
        except ElementClickInterceptedException as e:
            print(
                'ElementClickInterceptedException... element was overlayed by another element..')
            print(e)
            return False


def restartDriver(driverTemp, timeoutTemp=40):
    global hasLogin

    if driverTemp is not None:
        driverTemp.delete_all_cookies()
        driverTemp.quit()

    chrome_options=webdriver.ChromeOptions()
    chrome_options.headless=True
    # chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1320,1080")
    chrome_options.add_argument('--ignore-certificate-errors')
    chrome_options.add_argument('--ignore-ssl-errors')
    chrome_options.add_argument('log-level=2')

    d=DesiredCapabilities.CHROME
    d['loggingPrefs']={'browser': 'ALL'}

    driverTemp=webdriver.Chrome(
        options=chrome_options, executable_path=DRIVER_PATH, desired_capabilities=d)
    driverTemp.set_page_load_timeout(timeoutTemp)
    driverTemp.delete_all_cookies()

    if hasLogin:
        driverTemp=login(driverTemp)

    return driverTemp


def login(driverTemp):
    global USERNAME_SELECTOR, PASSWORD_SELECTOR, SIGNIN_SELECTOR, username, password
    getPage(driverTemp, 'https://www.rawpixel.com/user/login')

    emailElement=driverTemp.find_element_by_xpath(USERNAME_SELECTOR)
    passwordElement=driverTemp.find_element_by_xpath(PASSWORD_SELECTOR)

    emailElement.send_keys(username)
    passwordElement.send_keys(password)

    clickCatch(driverTemp, SIGNIN_SELECTOR)

    print('clicked login')

    return driverTemp


def isURLValid(URL):
    regex=re.compile(
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

        r=requests.get(URL, stream=isStream, headers={
                         'User-agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 11_0 like Mac OS X) AppleWebKit/604.1.38 (KHTML, like Gecko) Version/11.0 Mobile/15A5370a Safari/604.1'})
        if (URL != r.url):
            print('real url after redirection')
            print(r.url)
        return r
    else:
        driver.get(URL)
        return driver.current_url

ToDLFileName=None
# dependent: getRealRequest,isURLvalid
# y is the counter, default is nothing
# row is to append current row
def downloadFromURL(URL, dirname, row=[], ToDLFileName=None, y=-1, isServerDecidesFilename=False):
    if (isURLValid(URL) is not True):
        print('URL is not valid')
        """ row.append('')
        row.append('')
        row.append('') """
        saveErrorDownloadLog('downloadFromURL isURLValid', URL)
        return False
    try:
        r=getRealRequest(URL, True, True)
        print('downloading image...')
        print(URL)

        # Check if the image was retrieved successfully
        if r.status_code == 200:
            # Set decode_content value to True, otherwise the downloaded image file's size will be zero.
            r.raw.decode_content=True
            if ToDLFileName is not None:
                fileName=ToDLFileName
            else:
                a=urlparse.urlparse(r.url)
                fileName=os.path.basename(a.path)
            print('filename')
            print(fileName)

            # Open a local file with wb ( write binary ) permission.
            with open(os.path.join(dirname, fileName), 'wb') as f:
                shutil.copyfileobj(r.raw, f)

            print('Image sucessfully Downloaded: ',
                  os.path.join(dirname, fileName))
            return True

        else:
            print('Image Couldn\'t be retreived')
            saveErrorDownloadLog('downloadFromURL r.status_code != 200', URL)
            return False
    except OSError as e:
        saveErrorDownloadLog(f"downloadFromURL OSError", URL)
        print(e)
        return False


def getSubstringBetween(text, left, right):
    try:
        return re.search(f'{left}(.+?){right}', text).group(1)
    except AttributeError:
        return ''


def clickCatch(driverTemp, selector, wait_time=5, mouse_simulation=False):
    staleElement=True
    while staleElement:
        try:
            wait=WebDriverWait(driverTemp, wait_time)
            element=wait.until(
                EC.element_to_be_clickable((By.XPATH, selector)))

            if mouse_simulation:
                ActionChains(driverTemp).move_to_element(
                    element).click(element).perform()
            else:
                # element.click()
                driverTemp.execute_script("arguments[0].click();", element)

            staleElement=False
            return True
        except StaleElementReferenceException:
            print('StaleElementReferenceException, retrying...')
            staleElement=True
        except TimeoutException:
            print('TimeoutException... element not found')
            return False
        except ElementClickInterceptedException as e:
            print(
                'ElementClickInterceptedException... element was overlayed by another element..')
            print(e)
            return False


def getSingle(name):
    # THUMBNAIL_SELECTOR = "//div[@id='photo-pins']/img"
    # ID_SELECTOR = "//figure[contains(@class,'wp-block-image')]/img"
    MENU_SELECTOR="//button[text()='Key facts']"
    MENU2_SELECTOR="//button[text()='Description']"
    MENU2a_SELECTOR="//button[text()='In-depth']"

    TITLE_SELECTOR="//div[@class='painting-overlay-content']//th[text()='Full title']/following-sibling::td"
    # TAG_SELECTOR = "//div[@class='inside']/p[text()[contains(.,'tag')]]"
    # CATEGORY_SELECTOR = "//table[@id='details']//th[text()='Category']/following-sibling::td"
    # CC_SELECTOR = "//div[@style='margin:20px 0 10px;padding:15px 20px;background:#f7f8fa;line-height:1.5']"
    ARTIST_SELECTOR="//div[@class='painting-overlay-content']//th[text()='Artist']/following-sibling::td/a"
    ARTISTDATES_SELECTOR="//div[@class='painting-overlay-content']//th[text()='Artist dates']/following-sibling::td"
    DATEMADE_SELECTOR="//div[@class='painting-overlay-content']//th[text()='Date made']/following-sibling::td"
    MEDIUMANDSUPPORT_SELECTOR="//div[@class='painting-overlay-content']//th[text()='Medium and support']/following-sibling::td"
    DIMENSIONS_SELECTOR="//div[@class='painting-overlay-content']//th[text()='Dimensions']/following-sibling::td"
    CREDIT_SELECTOR="//div[@class='painting-overlay-content']//th[text()='Acquisition credit']/following-sibling::td"
    INVENTORYNUM_SELECTOR="//div[@class='painting-overlay-content']//th[text()='Inventory number']/following-sibling::td"
    LOCATION_SELECTOR="//div[@class='painting-overlay-content']//th[text()='Location']/following-sibling::td"
    COPYRIGHT_SELECTOR="//div[@class='painting-overlay-content']//th[text()='Image copyright']/following-sibling::td"
    COLLECTION_SELECTOR="//div[@class='painting-overlay-content']//th[text()='Collection']/following-sibling::td"
    # SOURCE_SELECTOR = "//div[contains(text(),'Source')]"
    # DATE_PUBLISHED_SELECTOR = "//strong[text()='UPLOADED: ']//parent::p"
    # SIZE_SELECTOR = "//div[@id='detail_content']/div[1]"
    # FILE_TYPE_SELECTOR = "//div[@style=\"margin-top:5px; background-image:url('http://res.publicdomainfiles.com/i/dloption.png'); background-repeat:no-repeat;\"]/div[@style='border:1px solid #c9c9c9; float:right; margin-left:5px; width:318px; background-color:#FFFFFF;'][1]//div[@style='font-family:Arial; font-size:11px; padding-left:5px;'][last()]"
    SHORTDESC_SELECTOR="//div[@class='painting-overlay-content']//div[@class='rte short-text']"
    DESC_SELECTOR="//div[@class='painting-overlay-content']//div[@class='rte long-text']"
    DOWNLOAD_SELECTOR="//div[@class='view']//img"
    DOWNLOAD2_SELECTOR="//div[@class='expand-image']//img"

    t0=time.time()

    driver=None
    driver=restartDriver(driver)

    url=f"https://www.nationalgallery.org.uk/paintings/{name}"

    row=[url]

    getPage(driver, url)

    clickCatch(driver, MENU_SELECTOR)

    time.sleep(1)

    title=selectCatch(driver, TITLE_SELECTOR)
    print('title')
    print(title)
    row.append(title)

    artist=selectCatch(driver, ARTIST_SELECTOR)
    # artistName = selectCatch(driver, ARTIST_SELECTOR, 'href')
    # artistName = artistName.replace('https://www.nationalgallery.org.uk/artists/','')
    print('artist')
    print(artist)
    row.append(artist)

    artistDates=selectCatch(driver, ARTISTDATES_SELECTOR)
    print('artistDates')
    print(artistDates)
    row.append(artistDates)

    dateMade=selectCatch(driver, DATEMADE_SELECTOR)
    print('dateMade')
    print(dateMade)
    row.append(dateMade)

    mediumAndSupport=selectCatch(
        driver, MEDIUMANDSUPPORT_SELECTOR)
    print('mediumAndSupport')
    print(mediumAndSupport)
    row.append(mediumAndSupport)

    dimensions=selectCatch(driver, DIMENSIONS_SELECTOR)
    print('dimensions')
    print(dimensions)
    row.append(dimensions)

    credit=selectCatch(driver, CREDIT_SELECTOR)
    print('credit')
    print(credit)
    row.append(credit)

    inventorynum=selectCatch(driver, INVENTORYNUM_SELECTOR)
    print('inventorynum')
    print(inventorynum)
    row.append(inventorynum)

    location=selectCatch(driver, LOCATION_SELECTOR)
    print('location')
    print(location)
    row.append(location)

    imageCopyright=selectCatch(driver, COPYRIGHT_SELECTOR)
    print('imageCopyright')
    print(imageCopyright)
    row.append(imageCopyright)

    collection=selectCatch(driver, COLLECTION_SELECTOR)
    print('collection')
    print(collection)
    row.append(collection)

    clickCatch(driver, MENU2_SELECTOR)
    shortdesc=selectCatch(
        driver, SHORTDESC_SELECTOR, 'innerHTML')
    shortdesc=shortdesc.strip()
    print('shortdesc')
    print(shortdesc)
    row.append(shortdesc)

    clickCatch(driver, MENU2a_SELECTOR)
    desc=selectCatch(driver, DESC_SELECTOR, 'innerHTML')
    desc=desc.strip()
    print('desc')
    print(desc)
    row.append(desc)

    row.append(getDateString())
    
    with open(getFilePath(), 'a', encoding="utf-8", newline='') as csvfile:
        writer=csv.writer(csvfile)
        writer.writerow(row)

    ToDLFileName=None

    titleName=url.replace(
        'https://www.nationalgallery.org.uk/paintings/', '')
    tempFilePath=os.path.join(
        DIR, f"{FOLDER}/{titleName}/try.txt")
    tempFolderPath=os.path.dirname(tempFilePath)

    if not os.path.exists(tempFolderPath):
        os.makedirs(tempFolderPath)

    downloadURL=selectCatch(driver, DOWNLOAD2_SELECTOR, 'src')

    if downloadURL != '':
        print('downloadURL')
        downloadURL=selectCatch(
            driver, DOWNLOAD2_SELECTOR, 'src')
        print(downloadURL)
        isDownloaded=downloadFromURL(
            f'{downloadURL}', tempFolderPath, row)
    else:
        print('downloadURL')
        downloadURL=selectCatch(driver, DOWNLOAD_SELECTOR, 'src')
        print(downloadURL)
        downloadURL=downloadURL.split('JTL=')[0]
        print(downloadURL)

        i=0
        while True:
            ToDLFileName=f'{i}.jpg'

            isDownloaded=downloadFromURL(
                f'{downloadURL}JTL=5,{i}', tempFolderPath, row, ToDLFileName)

            if isDownloaded == False:
                break

            i += 1

    elapsed=time.time() - t0
    print('elapsed:' + str(elapsed))
    if elapsed > breakTime:
        print(f'it has been > {breakTime}s... take a 5-min break!')
        driver=restartDriver(driver)
        time.sleep(300)
        t0=time.time()

def close_pool():
    global pool
    pool.close()
    pool.terminate()
    pool.join()

if __name__ == "__main__":

    path=os.path.join(os.path.dirname(os.path.abspath(__file__)),
                      'temp nationalgallery missing files1.csv')
    names=[]
    with open(path, newline='') as csvfile:
        rows=csv.reader(csvfile)
        for row in rows:
            names.append(row[1])

    initListCSV()

    with open(getFilePath(), 'w', encoding="utf-8", newline='') as csvfile:
        writer=csv.writer(csvfile)
        writer.writerow(['detailUrl', 'title', 'artist', 'artistDates', 'dateMade', 'MediumAndSupport', 'dimensions',
                'acquisitionCredit', 'inventoryNumber', 'location', 'imageCopyright', 'collection', 'shortDesc', 'desc', 'date_accessed'])

    test=names
    #test=[names[1]]
    pool=Pool()  # Pool() 不放參數則默認使用電腦核的數量
    pool.map(getSingle, test)
    pool.close()
    pool.join()
