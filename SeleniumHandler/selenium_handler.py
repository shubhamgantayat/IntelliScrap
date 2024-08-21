from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager


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