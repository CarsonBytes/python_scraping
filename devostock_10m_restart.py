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
import errno

DIR = os.path.dirname(os.path.abspath(__file__))
print(DIR)
DRIVER_PATH = os.path.join(DIR, "chromedriver.exe")

FOLDER = os.path.splitext(os.path.basename(__file__))[0]

FIRST_PAGE = int(sys.argv[1]) if len(sys.argv) > 1 else 1
LAST_PAGE = int(sys.argv[2]) if len(sys.argv) > 2 else 1734

# list page
AELEMENTS_SELECTOR = "//div[@class='item_list_page']/a"

# detail page
TITLE_SELECTOR = "//h1"
TAG_SELECTOR = "//div[@class='file_details']/span[3]/a"
#CC_SELECTOR = "//div[@class='desktopstuff']//a[@rel='license']"
AUTHOR_SELECTOR = "//div[@class='col-lg-4 col-md-4 col-sm-4']/a"
SIZE_SELECTOR = "//tr[@class='tr_cart'][last()]/td[last()-1]"
DATE_PUBLISHED_SELECTOR = "//div[@class='file_details']/span[1]"
DOWNLOAD_SELECTOR = "//input[@id='item_button_cart']"
PREVIEW_SELECTOR = "//div[@class='col-lg-6 col-md-6']/img"

chrome_options = webdriver.ChromeOptions()
chrome_options.headless = False
# chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=1320,1080")
chrome_options.add_argument('--ignore-certificate-errors')
chrome_options.add_argument('--ignore-ssl-errors')

countSec = 0
currentHandle = ''


def is_download_completed(driver):
    global countSec, currentHandle

    if not driver.current_url.startswith("chrome://downloads"):
        currentHandle = driver.current_window_handle

    #'switching to download history page to check if download is completed..'
    driver.switch_to.window(
        driver.window_handles[len(driver.window_handles)-1])
    if not driver.current_url.startswith("chrome://downloads"):
        driver.execute_script("window.open('');")
        driver.switch_to.window(
            driver.window_handles[len(driver.window_handles)-1])
        driver.get("chrome://downloads")

    has_downloads_manager = driver.execute_script(
        "return document.querySelector('downloads-manager').shadowRoot.querySelector('#downloadsList downloads-item') != null")
    """ print('has_downloads_manager')
    print(has_downloads_manager) """

    countSec += 1
    print(f'checking if any file is being downloaded... {countSec}s')
    if (has_downloads_manager == True):

        has_progress = driver.execute_script(
            "return document.querySelector('downloads-manager').shadowRoot.querySelector('#downloadsList downloads-item').shadowRoot.querySelector('#progress') != null")
        """ print('has_progress')
        print(has_progress) """

        if (has_progress == True):

            progress = driver.execute_script(
                "return document.querySelector('downloads-manager').shadowRoot.querySelector('#downloadsList downloads-item').shadowRoot.querySelector('#progress').value")
            """ print('progress')
            print(progress) """

            if (progress < 100):
                return False

            # get the latest downloaded file name
            fileName = driver.execute_script(
                "return document.querySelector('downloads-manager').shadowRoot.querySelector('#downloadsList downloads-item').shadowRoot.querySelector('div#content #file-link').text")

            lastFileName = fileName
            row.append(fileName)

            # get the latest downloaded file url
            sourceURL = driver.execute_script(
                "return document.querySelector('downloads-manager').shadowRoot.querySelector('#downloadsList downloads-item').shadowRoot.querySelector('div#content #file-link').href")
            print('sourceURL')
            print(sourceURL)
            row.append(sourceURL)

            # file downloaded location
            donwloadedAt = driver.execute_script(
                "return document.querySelector('downloads-manager').shadowRoot.querySelector('#downloadsList downloads-item').shadowRoot.querySelector('div.is-active.focus-row-active #file-icon-wrapper img').src")
            """ print('donwloadedAt')
            print(donwloadedAt) """

            now = datetime.now()
            print("now =", now)
            # dd/mm/YY H:M:S
            dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
            row.append(dt_string)
    driver.switch_to.window(currentHandle)
    countSec = 0
    return True


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

def clickDownload():
    global driver, SIZE_SELECTOR, DOWNLOAD_SELECTOR, isTimeout
    downloadOption = driver.find_element_by_xpath(
        SIZE_SELECTOR)
    downloadOption.click()
    print('selected original option')

    downloadBtn = driver.find_element_by_xpath(
        DOWNLOAD_SELECTOR)
    downloadBtn.click()

    print('downloading...')
    try:
        WebDriverWait(driver, 120, 1).until(
            is_download_completed)
    except TimeoutException:
        print('still downloading timeout, retrying.....')
        isTimeout = True
        driver.switch_to.window(currentHandle)

def restartSessionAndTimer():
    global driver, temp_chrome_options, DRIVER_PATH,t0
    driver.quit()
    time.sleep(420)
    driver = webdriver.Chrome(
        options=temp_chrome_options, executable_path=DRIVER_PATH)
    t0 = time.time()

t0 = time.time()
x = FIRST_PAGE
while x < LAST_PAGE+1:
    now = datetime.now()
    print("now =", now)
    # dd/mm/YY H:M:S
    dt_string = now.strftime("%Y.%m.%d_%H.%M.%S")
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
    driver.get(
        f'https://www.devostock.com/index.php?sphoto=1&items=96&str={x}&vd=date&c=all')

    try:
        element = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located(
                (By.XPATH, AELEMENTS_SELECTOR))
        )
    except TimeoutException:
        print(
            "TimeoutException! resetting session and retry the list page...")
        driver.quit()
        continue

    time.sleep(5)

    AElements = driver.find_elements_by_xpath(AELEMENTS_SELECTOR)
    detailUrls = [el.get_attribute("href") for el in AElements]

    print('len of detailUrls')
    print(len(detailUrls))

    """ 
    print(len(detailUrls))
    print(len(thumbnailsUrls))
    sys.exit() """

    with open(filename, 'w', encoding="utf-8", newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['detailUrl', 'title', 'tags', 'author', 'size', 'date_published'
                         'fileName', 'sourceUrl', 'date_downloaded'])
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

            row = [detailUrls[y]]

            print('page ' + str(x))
            print(detailUrls[y])
            driver.get(detailUrls[y])

            try:
                element = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located(
                        (By.XPATH, TITLE_SELECTOR))
                )
            except TimeoutException:
                print(
                    "TimeoutException! resetting session and retry the detail page...")
                driver.quit()
                driver = webdriver.Chrome(
                    options=temp_chrome_options, executable_path=DRIVER_PATH)
                continue

            title = selectCatch(driver, TITLE_SELECTOR)
            print('title')
            print(title)
            """ 
            title = title.replace(' free photo','')
            print('replaced title')
            print(title) """
            row.append(title)

            tags = selectCatch(driver, TAG_SELECTOR, 'text', True)
            print('tags')
            print(tags)
            row.append(tags)

            """ cc = selectCatch(driver, CC_SELECTOR)
             if cc != 'CC0 / Public Domain':
                y += 1
                continue 
            print('cc')
            print(cc)
            row.append(cc) """

            author = selectCatch(driver, AUTHOR_SELECTOR)
            print('author')
            print(author)
            row.append(author)

            size = selectCatch(driver, SIZE_SELECTOR)
            """ sizeString = re.search('\n(.*)', size).group(1) """
            sizeString = size.replace(' px', '')
            print('size')
            print(size)
            print('sizeString')
            print(sizeString)
            row.append(sizeString)

            datePublished = selectCatch(driver, DATE_PUBLISHED_SELECTOR)
            print('datePublished')
            print(datePublished)

            datePublished = datePublished.replace('Published: ', '')
            print(datePublished)
            row.append(datePublished)

            fileName = title.replace(' ', '+').replace('+(', '++(')+'.jpg'
            savePath = os.path.join(DIR, f"{FOLDER}/{x}/{fileName}")
            print('drafted fileName')
            print(fileName)
            print('drafted savePath')
            print(savePath)

            file = pathlib.Path(savePath)
            try:
                if file.exists():
                    print("File exist")
                    row.append('')
                else:
                    print("File not exist")
                    print('loading File:')

                    fileName2 = title
                    savePath2 = os.path.join(DIR, f"{FOLDER}/{x}/{fileName2}")
                    file2 = pathlib.Path(savePath2)
                    # sometimes devostocks have no size options to choose and download,
                    # in this case preview download will be used
                    # sometimes file is a title and not a jpg, it has to be used to download preview
                    if sizeString != '' or file2.exists() == False:
                        clickDownload()

                    else:
                        previewURL = selectCatch(driver, PREVIEW_SELECTOR, 'src')

                        # Open the url image, set stream to True, this will return the stream content.
                        r = requests.get(previewURL, stream=True)

                        # Check if the image was retrieved successfully
                        if r.status_code == 200:
                            # Set decode_content value to True, otherwise the downloaded image file's size will be zero.
                            r.raw.decode_content = True

                            # Open a local file with wb ( write binary ) permission.
                            with open(savePath, 'wb') as f:
                                shutil.copyfileobj(r.raw, f)

                            print('Image sucessfully Downloaded: ', savePath)
                            row.append(fileName)

                            now = datetime.now()
                            print("now =", now)
                            # dd/mm/YY H:M:S
                            dt_string = now.strftime("%Y/%m/%d %H:%M:%S")
                            row.append(dt_string)
                        else:
                            print('Image Couldn\'t be retreived')
                            row.append('')
            except OSError as e:
                clickDownload()

            if isTimeout == False:
                print(row)
                writer.writerow(row)
                y += 1
                if time.time() - t0 >= 14400:
                    restartSessionAndTimer()
    driver.quit()
    x += 1
