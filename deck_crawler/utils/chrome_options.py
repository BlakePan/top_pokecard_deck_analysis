from selenium.webdriver.chrome.options import Options

chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--start-maximized")

# https://blog.csdn.net/sxf1061700625/article/details/124263680
# disable images
chrome_options.add_argument("blink-settings=imagesEnabled=false")
chrome_options.add_argument("--disable-images")
# disable javascripts
chrome_options.add_argument("--disable-javascript")
chrome_options.add_argument("--disable-plugins")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-software-rasterizer")
chrome_options.add_argument("--disable-extensions")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--disable-java")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--mute-audio")
chrome_options.add_argument("--single-process")
chrome_options.add_argument("--disable-blink-features")
chrome_options.add_argument("--disable-blink-features=AutomationControlled")
chrome_options.add_argument("--incognito")