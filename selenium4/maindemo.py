import os
from botdemo import DemoBot
from urllib.parse import urljoin

# Get user input for the URL and code
url = input("Enter the list URL: ")
if not url:
    url="???"
    print(f"You entered an empty value. Using the default value:  {url}")
else:
    # If the input is not empty, use the user's input
    print(f"You entered: {url}")

code = input("Enter the code: ")
if not url:
    code="???"
    print(f"You entered an empty value. Using the default value:  {code}")
else:
    # If the input is not empty, use the user's input
    print(f"You entered: {code}")
    
DIR = os.path.dirname(os.path.abspath(__file__))

bot = DemoBot()

x = 1

# Get the total number of pages
LAST_PAGE = bot.get_total_pages(urljoin(url, str(x)))
print(f"Total number of pages: {LAST_PAGE}")

# LAST_PAGE = 29

# Looping through pagination
while x < LAST_PAGE + 1:
    print("Page ", x)
    all_records = bot.find_all_records(urljoin(url, str(x)), code)
    for record in all_records:
        print(record)
        bot.process_page(record, code)
    x += 1

bot.close()
