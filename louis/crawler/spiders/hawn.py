import scrapy

from louis.crawler.requests import extract_urls
from louis.crawler.convert import convert_html_content_to_chunk_items

class HawnSpider(scrapy.Spider):
    name = "hawn"
    allowed_domains = ["inspection.gc.ca", "inspection.canada.ca"]
    start_urls = ["https://inspection.canada.ca/splash"]

    def parse(self, response):
        yield from convert_html_content_to_chunk_items(response.url, response.body)
        yield from extract_urls(response, self.parse)
