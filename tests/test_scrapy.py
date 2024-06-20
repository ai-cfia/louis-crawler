"""test that scrapy is able to load the settings.py correctly"""

import unittest

from scrapy.utils.project import get_project_settings

class TestScrapy(unittest.TestCase):
    """test that scrapy is able to load the settings.py correctly"""

    def test_settings(self):
        """test that scrapy is able to load the settings.py correctly"""
        settings = get_project_settings()
        self.assertTrue(settings.get("DOWNLOADER_MIDDLEWARES"))
        self.assertTrue(settings.get("ITEM_PIPELINES"))
        self.assertTrue(settings.get("BOT_NAME"))
        self.assertTrue(settings.get("SPIDER_MODULES"))
        self.assertTrue(settings.get("USER_AGENT"))