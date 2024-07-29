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
import pathlib

DIR = os.path.dirname(os.path.abspath(__file__))
print(DIR)

FOLDER = os.path.splitext(os.path.basename(__file__))[0]

DRIVER_PATH = os.path.join(DIR, "chromedriver.exe")
FIRST_PAGE = int(sys.argv[1]) if len(sys.argv) > 1 else 1
LAST_PAGE = int(sys.argv[2]) if len(sys.argv) > 2 else 13284

chrome_options = webdriver.ChromeOptions()
chrome_options.headless = False
chrome_options.add_argument("--disable-gpu")

lastFileName = ''
countSec = 0


def download_starts(driver):
    global lastFileName, row, countSec
    if not driver.current_url.startswith("chrome://downloads"):
        print('switching to download history page to check if there is any new downloads starting..')
        driver.switch_to.window(driver.window_handles[1])

    has_downloads_manager = driver.execute_script(
        "return document.querySelector('downloads-manager').shadowRoot.querySelector('#downloadsList downloads-item') != null")
    """ print('has_downloads_manager')
    print(has_downloads_manager) """

    countSec += 1
    print(f'checking if any new file is being downloaded... {countSec}s')
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

            # get the latest downloaded file name
            fileName = driver.execute_script(
                "return document.querySelector('downloads-manager').shadowRoot.querySelector('#downloadsList downloads-item').shadowRoot.querySelector('div#content #file-link').text")
            """ print('fileName')
            print(fileName) """
            if fileName == lastFileName:
                #print('return False: fileName == lastFileName')
                return False
            else:
                #print('lastFileName = fileName')
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
            countSec = 0
            return True
    return False


def is_download_completed(driver):
    global countSec
    if not driver.current_url.startswith("chrome://downloads"):
        print('switching to download history page to check if download is completed..')
        driver.switch_to.window(driver.window_handles[1])

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
    return True

def restartDriver():
    global driver, temp_chrome_options, DRIVER_PATH, i
    print('restarting...')
    driver.quit()
    driver = webdriver.Chrome(
        options=temp_chrome_options, executable_path=DRIVER_PATH)
    i = 0


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
    # print('dirname:')
    # print(dirname)
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

    driver.get(f'https://avopix.com/search/photos/all/newest/{x}?fsort=newest')

    try:
        element = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located(
                (By.XPATH, "//.//div[@class='listing listing-overflow']/div[@class='listing-item']"))
        )
    except TimeoutException:
        print(
            "TimeoutException! resetting session and retry the list page...")
        driver.quit()
        continue

    AElements = driver.find_elements_by_xpath(
        "//.//div[@class='listing listing-overflow']/div[@class='listing-item']/a")
    detailUrls = [el.get_attribute("href") for el in AElements]
    thumbnailsUrls = [el.find_element_by_tag_name(
        'img').get_attribute("src") for el in AElements]
    alts = [el.find_element_by_tag_name(
        'img').get_attribute("alt") for el in AElements]

    """ print('alts')
    print(alts)
    print('detailUrls')
    print(detailUrls)
    print('thumbnails')
    print(thumbnailsUrls) """

    with open(filename, 'w', encoding="utf-8", newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['id', 'alt', 'detailUrl', 'thumbnail', 'size', 'filesize',
                         'tags', 'fileName', 'sourceUrl', 'date_downloaded'])
        i = 0
        y = 0
        while y < len(alts):
            yPath = os.path.join(DIR, f"{FOLDER}/{x}/y.txt")
            yFile = pathlib.Path(yPath)

            if y == 0 and yFile.exists():
                fileContent = open(yPath, 'r')
                y = int(fileContent.readline())
            else:
                fileContent = open(yPath, 'w')
                fileContent.write(str(y))

            # for y in range(0, len(alts)):
            isFileExisted = False
            id_string = re.search('#(.*)', alts[y]).group(1)
            print(id_string)
            print(f'loading detailUrl of page {x}:')
            row = [id_string, alts[y], detailUrls[y], thumbnailsUrls[y]]

            print(detailUrls[y])
            driver.get(detailUrls[y])

            try:
                element = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located(
                        (By.XPATH, '//table[@class="detail-parameters"]//tr[2]/td'))
                )
            except TimeoutException:
                print(
                    "TimeoutException! resetting session and retry the detail page...")
                driver.quit()
                driver = webdriver.Chrome(
                    options=temp_chrome_options, executable_path=DRIVER_PATH)
                i = 0
                continue

            try:
                # collecting size and filesize
                size = driver.find_element_by_xpath(
                    '//table[@class="detail-parameters"]//tr[2]/td').text
                filesize = driver.find_element_by_xpath(
                    '//table[@class="detail-parameters"]//tr[3]/td').text
            except NoSuchElementException:
                # collecting size and filesize
                size = driver.find_element_by_xpath(
                    '//table[@class="detail-parameters"]//tr[1]/td').text
                filesize = driver.find_element_by_xpath(
                    '//table[@class="detail-parameters"]//tr[2]/td').text

            row.append(size)
            row.append(filesize)

            # collecting tags
            tags = driver.find_elements_by_css_selector(
                '.detail-tags a')

            tagsList = []
            for tag in tags:
                tagsList.append(tag.text)

            # print('tagsList:')
            # print(tagsList)

            row.append(tagsList)

            for fileName in os.listdir(dirname):
                if fileName.startswith(f'{id_string}_') and fileName.endswith('.jpg'):
                    print('File already exists! skipping the download page...:')
                    print(fileName)
                    row.append(fileName)
                    row.append('')
                    row.append('')
                    isFileExisted = True
                    break

            if isFileExisted == False:
                downloadPage = driver.find_element_by_css_selector('.nomt a')

                print('loading download page:')
                print(downloadPage.get_attribute('href'))

                downloadPage.click()

                if i == 0:
                    driver.execute_script("window.open('');")
                    driver.switch_to.window(driver.window_handles[1])
                    driver.get("chrome://downloads")

                i += 1
                try:
                    countSec = 0
                    WebDriverWait(driver, 600, 1).until(download_starts)
                except TimeoutException:
                    print("download cannot starts!")
                    restartDriver()
                    continue

                print("waiting for all the previous downloads to complete first...")
                countSec = 0
                try:
                    WebDriverWait(driver, 120, 1).until(is_download_completed)
                except TimeoutException:
                    print("download cannot ends!")
                    restartDriver()
                    continue

                writer.writerow(row)
                time.sleep(1)
                restartDriver()
            y += 1
    x += 1
    if x < LAST_PAGE:
        driver.quit()
