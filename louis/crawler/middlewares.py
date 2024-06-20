# Define here the models for your spider middleware
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/spider-middleware.html

from scrapy import signals

from urllib.parse import urlparse

from louis.crawler.responses import (
    fake_response_from_file, response_from_crawl, response_from_chunk_token)

import ailab.db as db
import ailab.db.crawler as crawler

class LouisSpiderMiddleware:
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the spider middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_spider_input(self, response, spider):
        # Called for each response that goes through the spider
        # middleware and into the spider.

        # Should return None or raise an exception.
        return None

    def process_spider_output(self, response, result, spider):
        # Called with the results returned from the Spider, after
        # it has processed the response.

        # Must return an iterable of Request, or item objects.
        for i in result:
            yield i

    def process_spider_exception(self, response, exception, spider):
        # Called when a spider or process_spider_input() method
        # (from other spider middleware) raises an exception.

        # Should return either None or an iterable of Request or item objects.
        pass

    def process_start_requests(self, start_requests, spider):
        # Called with the start requests of the spider, and works
        # similarly to the process_spider_output() method, except
        # that it doesn’t have a response associated.

        # Must return only requests (not items).
        for r in start_requests:
            yield r

    def spider_opened(self, spider):
        spider.logger.info("Spider opened: %s" % spider.name)


class LouisDownloaderMiddleware:
    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        crawler.signals.connect(s.spider_closed, signal=signals.spider_closed)

        return s

    def process_request(self, request, spider):
        if spider.name == 'goldie':
            parsed = urlparse(request.url)
            if 'Referer' in request.headers:
                with db.cursor(self.connection) as cursor:
                    source_url = request.headers['Referer'].decode('utf-8')
                    destination_url = request.url
                    crawler.link_pages(cursor, source_url, destination_url)
            return fake_response_from_file(
                '/workspaces/louis-crawler/Cache' + parsed.path,
                request.url)

        if spider.name == 'hawn':
            with db.cursor(self.connection) as cursor:
                row = crawler.fetch_crawl_row(cursor, request.url)
                return response_from_crawl(row, request.url)

        if spider.name == 'russell':
            with db.cursor(self.connection) as cursor:
                row = crawler.fetch_crawl_row(cursor, request.url)
                # we use the row url to replace the fake url
                return response_from_crawl(row, row['url'])

        if spider.name == 'kurt':
            with db.cursor(self.connection) as cursor:
                row = crawler.fetch_chunk_token_row(cursor, request.url)
                return response_from_chunk_token(row, request.url)

    def process_response(self, request, response, spider):
        # Called with the response returned from the downloader.

        # Must either;
        # - return a Response object
        # - return a Request object
        # - or raise IgnoreRequest
        return response

    def process_exception(self, request, exception, spider):
        # Called when a download handler or a process_request()
        # (from other downloader middleware) raises an exception.

        # Must either:
        # - return None: continue processing this exception
        # - return a Response object: stops process_exception() chain
        # - return a Request object: stops process_exception() chain
        pass

    def spider_opened(self, spider):
        self.connection = db.connect_db()
        spider.logger.info("Spider opened: %s" % spider.name)

    def spider_closed(self, spider):
        spider.logger.info("Spider closed: %s" % spider.name)
        self.connection.close()