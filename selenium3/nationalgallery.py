import shutil
import requests
import os
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium import webdriver

FOLDER = 'nationalgallery'
SUBFOLDER = 'hilaire1'
LAST_ITEM = 455
URL = 'https://www.nationalgallery.org.uk/server.iip?FIF=/fronts/N-6581-00-000015-WZ-PYR.tif&CNT=1&JTL=5,'


DIR = os.path.dirname(os.path.abspath(__file__))
filename = os.path.join(DIR, f"{FOLDER}/{SUBFOLDER}")
dirname = os.path.dirname(filename)
if not os.path.exists(dirname):
    os.makedirs(dirname)
DRIVER_PATH = os.path.join(DIR, "chromedriver.exe")


def restartDriver(driverTemp, hasLogin=False, timeoutTemp=40):

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

    d = DesiredCapabilities.CHROME
    d['loggingPrefs'] = {'browser': 'ALL'}

    driverTemp = webdriver.Chrome(
        options=chrome_options, executable_path=DRIVER_PATH, desired_capabilities=d)
    driverTemp.set_page_load_timeout(timeoutTemp)
    driverTemp.delete_all_cookies()

    if hasLogin:
        login()

    return driverTemp

def getRealRequest(URL, isVirtual=True, isStream=False):
    global driver

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


def downloadFromURL(URL, dirname, fileName):
    try:
        r = getRealRequest(URL, True, True)
        print('downloading image...')

        # Check if the image was retrieved successfully
        if r.status_code == 200:
            # Set decode_content value to True, otherwise the downloaded image file's size will be zero.
            r.raw.decode_content = True

            # Open a local file with wb ( write binary ) permission.
            with open(os.path.join(dirname, fileName), 'wb') as f:
                shutil.copyfileobj(r.raw, f)

            print('Image sucessfully Downloaded: ',
                  os.path.join(dirname, fileName))

        else:
            print('Image Couldn\'t be retreived')
    except OSError as e:
        print(e)


driver = None
driver = restartDriver(driver)

for x in range(LAST_ITEM+1):
    downloadFromURL(
        f'{URL}{x}',
        dirname,
        f'{x}.jpg'
    )
