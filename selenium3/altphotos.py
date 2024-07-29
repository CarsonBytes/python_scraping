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
import pickle
import socket


DIR = os.path.dirname(os.path.abspath(__file__))
print(DIR)
DRIVER_PATH = os.path.join(DIR, "chromedriver.exe")

FOLDER = os.path.splitext(os.path.basename(__file__))[0]


# list page
AELEMENTS_SELECTOR = "//div[@class='item fleximages__item']/a"

# detail page
TITLE_SELECTOR = "//h1"
TAG_SELECTOR = "//div[@class='u-flex u-flex-wrap u-margin-bottom']/a"
#CC_SELECTOR = "//div[@class='fw-col-sm-8']//div[@class='section_head']//h5"
#AUTHOR_SELECTOR = "//div[@style='font-size:12px;line-height:18px;']"
SIZE_SELECTOR = "//ul[@class='o-list-bare u-margin-bottom-small']/li[1]//span[@class='radio-list__label__span'][1]/span[@class='label__text']"
DATE_CREATED_SELECTOR = "//table[@class='details__table u-margin-bottom-none']/tbody/tr[3]/td"
DATE_PUBLISHED_SELECTOR = "//table[@class='details__table u-margin-bottom-none']/tbody/tr[4]/td"
FILENAME_SELECTOR = "//img[@class='u-margin-bottom o-img--fill']"
#FILEURL_SELECTOR = "//div[@class='fw-col-sm-41']//tr[position() = (last() - 1)]/td[position() =5]/a"
DOWNLOAD_SELECTOR = "//button[@class='c-btn u-1/1 c-btn--primary']"

MORE_SELECCTOR = "//a[text()='Show me more...']"

chrome_options = webdriver.ChromeOptions()
chrome_options.headless = False
#chrome_options.add_argument("--disable-gpu")

lastFileName = ''
countSec = 0


def download_starts(driver):
    global lastFileName, row, countSec
    if not driver.current_url.startswith("chrome://downloads"):
        print('switching to download history page to check if there is any new downloads starting..')
        driver.switch_to.window(driver.window_handles[2])

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
                #row.append(fileName)

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


def selectCatch(driver, selector, multiple=True, type='text'):
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
    if type in ['href', 'src', 'onclick']:
        return element.get_attribute(type)
    return element.text


now = datetime.now()
print("now =", now)
# dd/mm/YY H:M:S
dt_string = now.strftime("%Y.%m.%d_%H.%M.%S")
listFile = f'list_{dt_string}.csv'
print('creating '+f'{listFile}...')
filename = os.path.join(DIR, f"{FOLDER}/{listFile}")
dirname = os.path.join(DIR, f"{FOLDER}")
if not os.path.exists(dirname):
    os.makedirs(dirname)

preference = {'download.default_directory': dirname,
              "safebrowsing.enabled": "false"}
temp_chrome_options = copy.deepcopy(chrome_options)
temp_chrome_options.add_experimental_option('prefs', preference)
driver = webdriver.Chrome(
    options=temp_chrome_options, executable_path=DRIVER_PATH)
driver.get('https://altphotos.com/gallery/')

lastLenDetailURLs = 0
with open(filename, 'w', encoding="utf-8", newline='') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(['detailUrl', 'title', 'tags', 'size', 'date_created',
                     'date_published', 'fileName', 'sourceUrl', 'date_downloaded'])

    while driver.find_element_by_xpath(MORE_SELECCTOR):

        moreBtn = driver.find_element_by_xpath(MORE_SELECCTOR)
        moreBtn.click()

        time.sleep(3)

        AElements = driver.find_elements_by_xpath(AELEMENTS_SELECTOR)
        detailUrls = [el.get_attribute("href") for el in AElements]

        print('detailUrls')
        #print(detailUrls)

        yPath = os.path.join(DIR, f"{FOLDER}/y.txt")
        yFile = pathlib.Path(yPath)
        if yFile.exists():
            fileContent = open(yPath, 'r')
            lastLenDetailURLs = int(fileContent.readline())
            print(lastLenDetailURLs)

        while len(detailUrls) < lastLenDetailURLs:
            moreBtn = WebDriverWait(driver, 20).until(
                EC.presence_of_element_located(
                    (By.XPATH, MORE_SELECCTOR))
            )
            driver.execute_script("arguments[0].click();", moreBtn)
            AElements = driver.find_elements_by_xpath(AELEMENTS_SELECTOR)
            detailUrls = [el.get_attribute("href") for el in AElements]
            print(len(detailUrls))

        y = lastLenDetailURLs
        while y < len(detailUrls):
            isTimeout = False
            print('y')
            print(y)
            print('len(detailUrls)')
            print(len(detailUrls))
            print('lastLenDetailURLs')
            print(lastLenDetailURLs)
            fileContent = open(yPath, 'w')
            fileContent.write( str(y) )

            row = [detailUrls[y]]

            print(detailUrls[y])

            if len(driver.window_handles) == 1:
                driver.execute_script("window.open('');")

            driver.switch_to.window(driver.window_handles[1])
            driver.get(detailUrls[y])

            try:
                element = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located(
                        (By.XPATH, TITLE_SELECTOR))
                )
            except TimeoutException:
                print(
                    "TimeoutException! ")
                continue

            title = selectCatch(driver, TITLE_SELECTOR, False)
            print('title')
            print(title)
            row.append(title)

            tags = selectCatch(driver, TAG_SELECTOR)
            print('tags')
            print(tags)
            row.append(tags)

            """ cc = selectCatch(driver, CC_SELECTOR, False)
            print('cc')
            print(cc)
            row.append(cc)

            author = selectCatch(driver, AUTHOR_SELECTOR, False)
            print('author')
            print(author)
            row.append(author) """

            size = selectCatch(driver, SIZE_SELECTOR, False)
            sizeString = size.replace('Original (', '').replace(')', '')
            print('SIZE_SELECTOR')
            print(size)
            print('sizeString')
            print(sizeString)
            row.append(sizeString)

            dateCreated = selectCatch(driver, DATE_CREATED_SELECTOR, False)
            print('dateCreated')
            print(dateCreated)
            row.append(dateCreated)

            datePublished = selectCatch(driver, DATE_PUBLISHED_SELECTOR, False)
            print('datePublished')
            print(datePublished)
            """ datePublished = datePublished.split('Published: ')[1]
            print('datePublished')
            print(datePublished) """
            row.append(datePublished)

            #fileName = fileURL.split("&filename=")[-1]
            #fileName = title.lower().replace(' ', '_')+'.jpg'

            fileName = selectCatch(driver, FILENAME_SELECTOR, False, 'src')

            print('fileName')
            print(fileName)
            fileName = fileName.split('/')[-1]

            print(fileName)
            row.append(fileName)

            """ fileURL = selectCatch(driver, FILEURL_SELECTOR, False, 'href')
            print('fileURL')
            print(fileURL)
            fileURL = fileURL

            print('fileURL')
            print(fileURL) """

            savePath = os.path.join(DIR, f"{FOLDER}/{fileName}")
            print('savePath')
            print(savePath)

            file = pathlib.Path(savePath)
            if file.exists():
                print("File exist")
                row.append('')
            else:
                print("File not exist")
                print('loading File:')

                downloadOption = driver.find_element_by_xpath(SIZE_SELECTOR)
                downloadOption.click()
                print('selected original option')

                downloadBtn = driver.find_element_by_xpath(DOWNLOAD_SELECTOR)
                downloadBtn.click()

                print('downloading...')
                if len(driver.window_handles) == 2:
                    driver.execute_script("window.open('');")
                    driver.switch_to.window(driver.window_handles[2])
                    driver.get("chrome://downloads")

                try:
                    countSec = 0
                    WebDriverWait(driver, 5, 1).until(download_starts)
                except TimeoutException:
                    print('download timeout, retrying.....')
                    isTimeout = True

            if isTimeout == False:
                print(row)
                writer.writerow(row)
                y += 1
        lastLenDetailURLs = len(detailUrls)
        driver.switch_to.window(driver.window_handles[0])
