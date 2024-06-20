import unittest

from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

from louis.crawler.spiders.russell import RussellSpider

class SpidersTests(unittest.TestCase):
  def setUp(self) -> None:
    settings = get_project_settings()
    settings['TWISTED_REACTOR'] = 'twisted.internet.epollreactor.EPollReactor'
    # self.crawler = Crawler(RussellSpider, settings=settings, init_reactor=True)
    self.crawlerProcess = CrawlerProcess(settings)

  def tearDown(self) -> None:
    pass

  def test_spider1(self):
    self.crawlerProcess.crawl(RussellSpider)
    crawler = list(self.crawlerProcess.crawlers)[0]

    self.crawlerProcess.start(stop_after_crawl=True)
    self.crawlerProcess.join()

    self.assertEqual(crawler.crawling, False)
    self.assertTrue(isinstance(crawler.spider, RussellSpider))
    _requests = list(crawler.spider.start_requests())
    # self.assertEqual(len(requests), 1)

    from louis.crawler.middlewares import LouisDownloaderMiddleware
    _downloader = list(filter(
      lambda x: isinstance(x, LouisDownloaderMiddleware),
      crawler.engine.downloader.middleware.middlewares))[0]
    # self.assertEqual(
    #     downloader.connection.info.status, downloader.connection.info.status.OK)
    # self.crawler.stop()
