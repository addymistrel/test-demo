import scrapy
from selenium import webdriver
import time
from scrapy.http import HtmlResponse
import json

class NoberoSpider(scrapy.Spider):
    name = "nobero_spider"
    initial_url = "https://nobero.com/pages/men"

    def __init__(self, *args, **kwargs):
        super(NoberoSpider, self).__init__(*args, **kwargs)
        self.driver = webdriver.Chrome()  # Ensure you have ChromeDriver installed
        self.categories_data = {}

    def start_requests(self):
        # Start by making the initial request to the main page
        yield scrapy.Request(url=self.initial_url, callback=self.extract_all_start_urls)

    def extract_all_start_urls(self, response):
        # Now extract category URLs
        baseURL = "https://nobero.com"
        categories_urls = response.css('div.custom-page-season-grid-item a::attr(href)').getall()
        categories_urls = list(map(lambda x: baseURL + x[1:], categories_urls))
        
        for url in categories_urls:
            category_name = url.split('/')[-1]  # Extract category name from URL
            self.categories_data[category_name] = []  # Initialize list for this category
            yield scrapy.Request(url=url, callback=self.extract_item_urls, meta={'category': category_name})

    def extract_item_urls(self, response):
        baseURL = "https://nobero.com/"
        category_name = response.meta['category']

        # Use Selenium to load the page and scroll to the bottom
        self.driver.get(response.url)

        # Simulate scrolling to the bottom of the page
        last_height = self.driver.execute_script("return document.body.scrollHeight")
        while True:
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)  # Wait for new content to load
            new_height = self.driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height

        # Get the fully loaded page source after scrolling
        page_source = self.driver.page_source

        # Create a Scrapy response object from the Selenium page source
        response = HtmlResponse(url=self.driver.current_url, body=page_source, encoding='utf-8')

        # Extract product URLs from the category page
        item_urls = response.css('section.product-card-container div a::attr(href)').getall()
        item_urls = list(map(lambda x: baseURL + x[1:], item_urls))

        for url in item_urls:
            yield scrapy.Request(url=url, callback=self.extract_info, meta={'category': category_name})

    def extract_info(self, response):
        category_name = response.meta['category']

        def getAllSizes(response):
            tempSizes = response.css("input.size-select-input::attr(value)").getall()
            finalSizes = []
            for k in tempSizes:
                if k not in finalSizes:
                    finalSizes.append(k)
            return finalSizes
        
        img = "https:"+response.css("figure#image-container img::attr(src)").get()
        name = response.css('main div.flex:nth-child(2) div:nth-child(1) div div h1::text').get().strip()
        price = response.css('div#price-template--16047755657382__main div:nth-child(1) h2#variant-price spanclass::text').get().strip()[1:]
        mrp = response.css('div#price-template--16047755657382__main div:nth-child(2) h2 span#variant-compare-at-price spanclass::text').get().strip()[1:]
        visitors = response.css('div.product_bought_count span::text').get().split()[0]
        colors = response.css("label.color-select input::attr(value)").getall()
        sizes = getAllSizes(response=response)

        item_data = {
            "name": name,
            "price": price,
            "mrp": mrp,
            "visitors": visitors,
            "baseImg": img,
            "availableColors": colors,
            "availableSizes": sizes
        }

        self.categories_data[category_name].append(item_data)

    def closed(self, reason):
        # Write the collected data to a JSON file when the spider finishes
        with open('nobero_data.json', 'w') as f:
            json.dump(self.categories_data, f, indent=4)

        # Close the Selenium browser
        self.driver.quit()
