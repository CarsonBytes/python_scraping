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

DIR = os.path.dirname(os.path.abspath(__file__))
print(DIR)
DRIVER_PATH = os.path.join(DIR, "chromedriver.exe")

FOLDER = os.path.splitext(os.path.basename(__file__))[0]

FIRST_PAGE = int(sys.argv[1]) if len(sys.argv) > 1 else 1
LAST_PAGE = int(sys.argv[2]) if len(sys.argv) > 2 else 908

# login
OPENSIGNIN_SELECTOR = "//a[@class='button pink']"
USERNAME_SELECTOR = "//input[@name='uname']"
PASSWORD_SELECTOR = "//input[@name='pass']"
SIGNIN_SELECTOR = "//a[@class='button signin pink']"

# list page
AELEMENTS_SELECTOR = "//li[contains(@class,'thcell')]/a"

# detail page
TITLE_SELECTOR = "//h1"
TAG_SELECTOR = "//ul[@class='item-keywords-container']/li/a"
# CC_SELECTOR = "//div[@class='desktopstuff']//a[@rel='license']"
AUTHOR_SELECTOR = "//div[@class='author-name']/a"
#SIZE_SELECTOR = "//tr[@class='tr_cart'][last()]/td[last()-1]"
#DATE_PUBLISHED_SELECTOR = "//div[@class='item-actions gradient']/a"
DOWNLOAD_SELECTOR = "//div[@class='item-actions gradient']/a"
#PREVIEW_SELECTOR = "//div[@class='col-lg-6 col-md-6']/img"

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
            "TimeoutException! resetting session and retry the page...")
        driver.quit()
        print('sleeping.....')
        time.sleep(60)
        print('waking up.....')
        if restartDriver:
            driver = webdriver.Chrome(
                options=temp_chrome_options, executable_path=DRIVER_PATH)
            login()
        return False


def login():
    global driver, OPENSIGNIN_SELECTOR, USERNAME_SELECTOR, PASSWORD_SELECTOR, SIGNIN_SELECTOR
    driver.get(f'https://www.dreamstime.com')
    driver.find_element_by_xpath(OPENSIGNIN_SELECTOR).click()

    email = driver.find_element_by_xpath(USERNAME_SELECTOR)
    password = driver.find_element_by_xpath(PASSWORD_SELECTOR)

    email.send_keys("cindylw1225@gmail.com")
    password.send_keys("V3Ym3mUMlug7")

    driver.find_element_by_xpath(SIGNIN_SELECTOR).click()

    print('clicked login')


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

    login()

    listingPage = f'https://www.dreamstime.com/free-public-domain-images?pg={x}'
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
        writer.writerow(['detailUrl', 'title', 'tags', 'author', 'size',
                         'fileName', 'date_downloaded'])
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

            row.append(str(driver.execute_script('return thumbWidth')) +
                       ' x '+str(driver.execute_script('return thumbHeight')))

            fileName = 'dreamstime_xxl_' + \
                str(driver.execute_script('return imageid')) + '.jpg'
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

            downloadBtn = driver.find_element_by_xpath(DOWNLOAD_SELECTOR)
            downloadBtn.click()
            print("waiting file to be downloaded")

            try:
                WebDriverWait(driver, 1).until(EC.alert_is_present(),
                                               'Timed out waiting for PA creation ' +
                                               'confirmation popup to appear.')

                alert = driver.switch_to.alert
                alert.accept()
                print("alert accepted")
            except TimeoutException:
                print("no alert")

            dt = getDateString()
            saveScreenshotPath = os.path.join(dirname, f"screenshot/{dt}.png")
            if not os.path.exists(os.path.dirname(saveScreenshotPath)):
                os.makedirs(os.path.dirname(saveScreenshotPath))
            driver.save_screenshot(saveScreenshotPath)

            if checkPageFine(DOWNLOAD_SELECTOR) == False:
                continue

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
                        driver.quit()
                        driver = webdriver.Chrome(
                            options=temp_chrome_options, executable_path=DRIVER_PATH)
                        login()
                    continue

            print(row)
            writer.writerow(row)
            y += 1
    driver.quit()
    x += 1
