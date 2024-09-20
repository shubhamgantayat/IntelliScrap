from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time
from selenium.webdriver.common.by import By
from urllib.parse import quote


class SeleniumHandler:

    def __init__(self) -> None:
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument(
            'user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36')
        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    def open_a_new_window(self, url: str = "", status='open'):

        # track main_window
        if status == 'open':
            self.driver.execute_script("window.open('" + url + "', 'new_window')")
            self.driver.switch_to.window(self.driver.window_handles[-1])

        elif status == 'close':
            self.driver.switch_to.window(self.driver.window_handles[-2])


class GoogleNewsScrapper(SeleniumHandler):

    def __init__(self):
        self.class_name = "XlKvRb"
        self.get_news_url = lambda keyword: f"https://news.google.com/search?q={quote(keyword + ' when:1d')}"
        super().__init__()

    def scrap(self, keyword):
        self.driver.get(self.get_news_url(keyword))
        elements = self.driver.find_elements(By.CLASS_NAME, self.class_name)
        links = [element.find_elements(By.TAG_NAME, "a")[0].get_attribute("href") for element in elements]
        self.driver.quit()
        return links


class DuckDuckGoNewsScrapper(SeleniumHandler):

    def __init__(self):
        self.class_name = "result__body"
        self.get_news_url = lambda keyword:f"https://duckduckgo.com/?q={quote(keyword)}&iar=news&df=d&ia=news"
        super().__init__()

    def scrap(self, keyword):
        self.driver.get(self.get_news_url(keyword))
        time.sleep(1)
        elements = self.driver.find_elements(By.CLASS_NAME, self.class_name)
        links = [element.find_elements(By.TAG_NAME, "a")[0].get_attribute("href") for element in elements]
        self.driver.quit()
        return links
