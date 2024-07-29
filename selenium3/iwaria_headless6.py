from selenium import webdriver
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException
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
import glob
from urllib.request import urlopen, Request
from selenium.webdriver.support import expected_conditions as EC

DIR = os.path.dirname(os.path.abspath(__file__))
print(DIR)
DRIVER_PATH = os.path.join(DIR, "chromedriver.exe")
FOLDER = 'iwaria'

""" KEYWORD = str(sys.argv[1]) if len(sys.argv) > 1 else 'nigeria'
KEYWORD = KEYWORD.replace(' ', '%20')
print('Keyword')
print(KEYWORD) """
africa_list = ['Nigeria','Ethiopia','Egypt','Democratic Republic of the Congo','Tanzania','South Africa','Kenya','Uganda','Algeria','Sudan','Morocco','Mozambique','Ghana','Angola','Somalia','Ivory Coast','Madagascar','Cameroon','Burkina Faso','Niger','Malawi','Zambia','Mali','Senegal','Zimbabwe','Chad','Tunisia','Guinea','Rwanda','Benin','Burundi','South Sudan','Eritrea','Sierra Leone','Togo','Libya','Central African Republic','Mauritania','Republic of the Congo','Liberia','Namibia','Botswana','Lesotho','Gambia','Gabon','Guinea-Bissau','Mauritius','Equatorial Guinea','Eswatini','Djibouti','Reunion','Comoros','Western Sahara','Cape Verde','Mayotte','São Tomé','Seychelles','Saint Helena']

# list page
AELEMENTS_SELECTOR = "//div[@id='pinterestGridList']//a[@class='image-overlay']"
#LAST_AELEMENT_SELECTOR = "//div[@class='img-grid animated-grid']/div[contains(@class,'reveal') and not(contains(@class,'pubspace'))][30]/a"
#PD_SELECTOR = "//dl[@class='vh-Filters-license']//a[text()='Public Domain']"

# detail page
#THUMBNAIL_SELECTOR = "//a[@class='lightbox']/img"
#ID_SELECTOR = "//header/dl/dd"
#TITLE_SELECTOR = "//h1"
#CATEGORY_SELECTOR = "//a[@rel='category tag']"
#CC_SELECTOR = "//h5[text()='Check license']/following-sibling::a[1]"
AUTHOR_SELECTOR = "//span[@class='author']/a"
TAG_SELECTOR = "//div[@id='tagsList']//a"
#SOURCE_SELECTOR = "//div[contains(text(),'Source')]"
DATE_PUBLISHED_SELECTOR = "//span[text()='Published:']/parent::div"
#SIZE_SELECTOR = "//div[@id='detail_content']/div[1]"
# FILE_TYPE_SELECTOR = "//div[@style=\"margin-top:5px; background-image:url('http://res.publicdomainfiles.com/i/dloption.png'); background-repeat:no-repeat;\"]/div[@style='border:1px solid #c9c9c9; float:right; margin-left:5px; width:318px; background-color:#FFFFFF;'][1]//div[@style='font-family:Arial; font-size:11px; padding-left:5px;'][last()]"
#DOWNLOAD_OPTION_SELECTOR = "//span[text()='download for free']"
#DOWNLOAD_OPTION2_SELECTOR = "//div[@class='download-options']/label[@for='download-option'][last()]"
PHOTO_INFO_BTN_SELECTOR = "//span[@class='icon-info-block']"
PHOTO_INFO_CLOSE_BTN_SELECTOR = "//span[@id='close']"
DOWNLOAD_SELECTOR = "//span[text()='Download']/parent::a"

chrome_options = webdriver.ChromeOptions()
chrome_options.headless = True
# chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=1320,1080")
chrome_options.add_argument('--ignore-certificate-errors')
chrome_options.add_argument('--ignore-ssl-errors')
chrome_options.add_argument('log-level=2')


def selectCatch(driver, selector, type='text', multiple=False):
    staleElement = True; 
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


def makeScreenshot(driver, height, width=1092):
    driver.set_window_size(width, height)
    print('making screenshot...')
    dt = getDateString()
    saveScreenshotPath = os.path.join(dirname, f"screenshot/{dt}.png")
    if not os.path.exists(os.path.dirname(saveScreenshotPath)):
        os.makedirs(os.path.dirname(saveScreenshotPath))
    driver.save_screenshot(saveScreenshotPath)


def checkPageFine(driver, selector, restartDriver=False, sec=3, sleep=0):
    global chrome_options, DRIVER_PATH
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
    global y, detailUrls, row, dirname, driver2

    if (isURLvalid(URL) is not True):
        print('URL is not valid')
        row.append('')
        row.append('')
        row.append('')
        saveErrorDownloadLog(y, detailUrls[y])
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
        saveErrorDownloadLog(y, detailUrls[y])
        y += 1


def saveErrorDownloadLog(order, detailUrl):
    logPath = os.path.join(DIR, f"{FOLDER}/error.log")
    logFile = pathlib.Path(logPath)
    if logFile.exists():
        with open(logPath, 'a') as file:
            file.write(f'{order};{detailUrl}\n')
    else:
        with open(logPath, 'w') as file:
            file.write(f'{order};{detailUrl}\n')


def getMetaTags(url):
    out = {}
    r = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    html = urlopen(r).read().decode('utf-8')
    m = re.findall("property=\"([^\"]*)\" content=\"([^\"]*)\"", html)
    for i in m:
        out[i[0]] = i[1]
    return out


def getValueFromArray(array, key):
    try:
        result = array[key]
    except KeyError as e:
        print('KeyError')
        print(e)
        result = ''
    return result

    global driver, USERNAME_SELECTOR, PASSWORD_SELECTOR, SIGNIN_SELECTOR
    driver.get(f'https://www.rawpixel.com/user/login')
    """ driver.find_element_by_xpath(OPENSIGNIN_SELECTOR).click() """

    email = driver.find_element_by_xpath(USERNAME_SELECTOR)
    password = driver.find_element_by_xpath(PASSWORD_SELECTOR)

    email.send_keys("jnontoquine")
    password.send_keys("123456789")

    driver.find_element_by_xpath(SIGNIN_SELECTOR).click()

    print('clicked login')


previous_file = 'abc'
latest_file = 'abc'

# driver is for loading listing page
driver = webdriver.Chrome(options=chrome_options, executable_path=DRIVER_PATH)
driver.set_page_load_timeout(10)

driver2 = None
for KEYWORD in africa_list:
    listingPage = f'https://iwaria.com/search/{KEYWORD}/?sorted_by=location'
    driver.get(listingPage)
    """ PDBtn = driver.find_element_by_xpath(PD_SELECTOR)
    driver.execute_script("arguments[0].click();", PDBtn) """

    print('listingPage:')
    print(listingPage)

    lastLenDetailURLs = 0
    y = 0
    while True:

        print('subfolder')
        print(lastLenDetailURLs)

        """ if checkPageFine(driver, AELEMENTS_SELECTOR, True) == False:
            continue """

        detailUrls = selectCatch(driver, AELEMENTS_SELECTOR, 'href', True)

        yPath = os.path.join(DIR, f"{FOLDER}/{KEYWORD}/y.txt")
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
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight)")
            detailUrls = selectCatch(driver, AELEMENTS_SELECTOR, 'href', True)
            print('checking for more detail URLs total:')
            print(len(detailUrls))
            retrialTimes += 1
            print('retrial times: #')
            print(retrialTimes)
            if retrialTimes >= maxRetrialTimes:
                print('reached max retrial times, no new detail URLs, jump to next country...')
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
            listFile = f'list_{dt_string}.csv'
            print('creating '+f'{listFile}...')
            filename = os.path.join(
                DIR, f"{FOLDER}/{KEYWORD}/{lastLenDetailURLs}/{listFile}")
            # print(filename)
            dirname = os.path.dirname(filename)
            print('dirname:')
            print(dirname)
            if not os.path.exists(dirname):
                os.makedirs(dirname)
            with open(filename, 'w', encoding="utf-8", newline='') as csvfile:
                # driver2 is for loading detail page and download
                if driver2 is not None:
                    driver2.quit()
                driver2 = webdriver.Chrome(
                    options=chrome_options, executable_path=DRIVER_PATH)
                driver2.set_page_load_timeout(10)
                writer = csv.writer(csvfile)
                writer.writerow(['detailUrl', 'author', 'tags', 'date_published','fileURL',
                                'fileName', 'date_downloaded'])
                while y < len(detailUrls):

                    isTimeout = False

                    print('y')
                    print(y)
                    print('folder:')
                    print(dirname)

                    row = [detailUrls[y]]
                    print('detailUrl')
                    print(detailUrls[y])

                    driver2.get(detailUrls[y])

                    """ thumbnailUrl = selectCatch(driver2, THUMBNAIL_SELECTOR, 'src')
                    print('thumbnailUrl')
                    print(thumbnailUrl)
                    if thumbnailUrl == '':
                        driver2.quit()
                        driver2 = webdriver.Chrome(
                            options=chrome_options, executable_path=DRIVER_PATH)
                        print('thumbnailUrl is empty, logged and skip to next one')
                        saveErrorDownloadLog(y, detailUrls[y])
                        y += 1
                        continue """

                    author = selectCatch(driver2, AUTHOR_SELECTOR)
                    print('author')
                    print(author)
                    row.append(author)

                    driver2.set_window_size(1000, 1500) #fix for reading overlay element
                    PHOTO_INFO_BTN = driver2.find_element_by_xpath(PHOTO_INFO_BTN_SELECTOR)
                    driver2.execute_script("arguments[0].click();", PHOTO_INFO_BTN)
                    
                    #time.sleep(1)

                    """ element = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.XPATH, TAG_SELECTOR))
                    ) """
                    
                    tags = selectCatch(driver2, TAG_SELECTOR, 'text', True)
                    print('tags')
                    print(tags)
                    row.append(tags) 

                    result = selectCatch(driver2, DATE_PUBLISHED_SELECTOR)
                    #print(result)
                    result = result.splitlines()
                    date_published = result[1]
                    print('date_published')
                    print(date_published)
                    row.append(date_published) 

                    PHOTO_INFO_CLOSE_BTN = driver2.find_element_by_xpath(PHOTO_INFO_CLOSE_BTN_SELECTOR)
                    driver2.execute_script("arguments[0].click();", PHOTO_INFO_CLOSE_BTN)

                    """ title = selectCatch(driver2, TITLE_SELECTOR)
                    print('title')
                    print(title)
                    row.append(title) 

                    cc = selectCatch(driver2, CC_SELECTOR)
                    print('cc')
                    print(cc)
                    row.append(cc)

                    date_created = selectCatch(driver2, DATE_CREATED_SELECTOR)
                    print('date_created')
                    print(date_created)
                    row.append(date_created)"""

                    """ 
                    result = selectCatch(driver, AUTHOR_SELECTOR)
                    result = result.splitlines()
                    author = ''
                    size = ''
                    filesize = ''
                    for line in result:
                        if "Uploaded by" in line:
                            author = line.replace('Uploaded by: ', '')
                        if "Resolution:" in line:
                            size = line.replace('Resolution: ', '')
                            size = size.split(" ", 1)
                            size = size[0]
                        if "File size" in line:
                            filesize = line.replace('File size: ', '')
                            filesize = filesize.split(" ", 1)
                            filesize = filesize[0] 

                    print('author')
                    print(author)
                    row.append(author)
                    print('size')
                    print(size)
                    row.append(size)
                    print('filesize')
                    print(filesize)
                    row.append(filesize)"""

                    if checkPageFine(driver2, DOWNLOAD_SELECTOR, True) == False:
                        continue

                    """ dirname2 = dirname.replace('/', '\\')
                    params = {'behavior': 'allow',
                            'downloadPath': dirname2}
                    driver2.execute_cdp_cmd('Page.setDownloadBehavior', params)

                    downloadOptionBtn = driver2.find_element_by_xpath(
                        DOWNLOAD_OPTION_SELECTOR)
                    driver2.execute_script(
                        "arguments[0].click();", downloadOptionBtn)
                    downloadOption2Btn = driver2.find_element_by_xpath(
                        DOWNLOAD_OPTION2_SELECTOR)
                    driver2.execute_script(
                        "arguments[0].click();", downloadOption2Btn) """

                    imageURL = selectCatch(driver2, DOWNLOAD_SELECTOR, 'href')
                    print('imageURL')
                    print(imageURL)

                    downloadFromURL(imageURL)

                    makeScreenshot(driver2, 1500)

                    print(row)
                    writer.writerow(row)
                    y += 1
                    fileContent = open(yPath, 'w')
                    fileContent.write(str(y))
        lastLenDetailURLs = len(detailUrls)
