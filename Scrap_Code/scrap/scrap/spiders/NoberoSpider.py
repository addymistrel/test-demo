import scrapy

class NoberoSpider(scrapy.Spider):
    name = "nobero_spider"

    initial_url = "https://nobero.com/pages/men"

    def start_requests(self):
        yield scrapy.Request(url=self.initial_url, callback=self.extract_all_start_urls)

    def extract_all_start_urls(self,response):

        baseURL = "https://nobero.com"

        categories_urls = response.css('div.custom-page-season-grid-item a::attr(href)').getall()
        categories_urls = list(map(lambda x:baseURL+x[1:],categories_urls))


        # Use the extracted URLs to continue the scraping process
        # for sub_url in categories_urls:
        yield scrapy.Request(url=categories_urls[0], callback=self.extract_item_urls)

    def extract_item_urls(self,response):
        item_urls = response.css('article').getall()

        print(item_urls)

