import os
import scrapy
import logging

from time import sleep

from scrapy.crawler import CrawlerProcess
from scrapy.http.response.html import HtmlResponse

from selenium import webdriver;
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait;
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.common.exceptions import TimeoutException

class Aseanstats(scrapy.Spider):

    def __init__(self) -> None:
        self.name: str = 'aseanstats-spdier'
        self.start_urls: str = ['https://data.aseanstats.org/']
    
    def __setting_options(self, output: str = None) -> Options:
        self.__output: str = os.getcwd() + output
        if(not os.path.exists(self.__output)):
            os.makedirs(self.__output)

        options: Options = Options()
        options.add_argument('--headless')
        options.add_argument("--kiosk-printing")
        options.add_argument("--disable-popup-blocking")
        options.add_argument("--disable-notifications")
        options.add_argument("--disable-web-security")
        options.add_argument("--allow-running-insecure-content")
        options.add_argument("--disable-save-password-bubble")
        options.add_argument("--disable-extensions")
        options.add_experimental_option("prefs", {
            "savefile.default_directory": self.__output,
            "download.default_directory": self.__output,
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": True,
            'profile.default_content_setting_values.automatic_downloads': 1
        })

        return options
    
    def __wait_element(self, selector: str, timeout: int = 1) -> WebElement:
        return WebDriverWait(self.__driver, timeout).until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
    
    def __wait_element_invisible(self, selector: str, timeout: int = 200) -> WebElement:
        return WebDriverWait(self.__driver, timeout).until(EC.invisibility_of_element_located((By.CSS_SELECTOR, selector)))

    def __wait_download(self):
        try:
            WebDriverWait(self.__driver, 300).until(
                lambda x: len(os.listdir(self.__output)) == 6
            )
            print("Download completed.")
        except TimeoutException:
            print("Timed out waiting for download to complete.")

        self.__driver.close()

    def __download(self) -> None:
        self.__wait_element('#fm-tab-export', timeout=60).click()
        # for type in ['print', 'html', 'csv', 'excel', 'image', 'pdf']:
        for type in ['html', 'csv', 'excel', 'image', 'pdf']:
            self.__wait_element(f'#fm-tab-export-{type} a').click()

            if(type == 'pdf'): self.__wait_element('#fm-btn-apply').click()
            
            self.__wait_element_invisible('#fm-preloader-view')

        for cart in ["bar-line"]:
            self.__wait_element('#fm-tab-charts', timeout=60).click()
            
            self.__wait_element(f'#fm-tab-charts-{cart} a').click()
            
            self.__wait_element('#fm-tab-export', timeout=60).click()
            self.__wait_element('#fm-tab-export-image a').click()

        sleep(3)
        
        self.__wait_download()


    def __start_browser(self, url: str, title: str = 'hooh'):
        self.__driver: WebDriver = webdriver.Chrome(options=self.__setting_options(f'/data/{title}'))
        self.__driver.set_window_size(1920, 1080)
        self.__driver.get(url)

        try:
            self.__wait_element('#fm-pivot-view')

        except Exception:
            self.__perform_additional_selections()
        
        self.__download()
    
    def __perform_additional_selections(self) -> None:
        all_selectors: list = (
            '.row .col-sm-6',
            '.row .col-lg-4',
            '.row .col-lg-6',
            '.row .col-sm-4:first-child', 
            '.row .col-sm-4:nth-child(2)',
            '.row .col-sm-4:last-child',
        )

        for selector in all_selectors:
            try:
                self.__wait_element(f'{selector} .btn.dropdown-toggle.btn-light').click()
                self.__wait_element(f'{selector} .actions-btn.bs-select-all.btn.btn-light').click()
                self.__wait_element(f'{selector} .btn.dropdown-toggle.btn-light').click()
            except Exception:
                continue

        self.__wait_element('#fdiSubmit').click()

    def parse(self, response: HtmlResponse):
        for i, data in enumerate(response.css('.col-lg-6.col-md-6.col-sm-12')):
            self.__start_browser(data.css('a::attr("href")').get(), data.css('a::text').get().replace('\n', '_').replace(' ', '_').strip('_'))
            if(i == 6): break
        # self.__start_browser('https://data.aseanstats.org/fdi-by-hosts-and-sources-stock-outward')
        # self.__start_browser('https://data.aseanstats.org/fdi-by-sources-and-sectors')

if(__name__ == '__main__'):
    prosses: CrawlerProcess = CrawlerProcess()
    prosses.crawl(Aseanstats)
    prosses.start()

