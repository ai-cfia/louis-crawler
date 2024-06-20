"""Test the Russell spider"""
import datetime
import os
import unittest
from uuid import UUID

from louis.crawler.spiders.russell import RussellSpider

from louis.crawler.responses import response_from_crawl

CWD = os.path.dirname(os.path.abspath(__file__))

def get_html(filename):
    with open(f"{CWD}/responses/{filename}.html", encoding="UTF-8") as f:
        return f.read()

class TestRussell(unittest.TestCase):
    """Test the Kurt spider"""

    def setUp(self):
        self.spider = RussellSpider()

    def test_start_requests(self):
        """Test that the spider returns a request for each chunk_id"""
        requests = self.spider.start_requests()
        # print(requests)
        generator_type = type(1 for i in "")
        self.assertIsInstance(requests, generator_type)

    def test_parse(self):
        """Test that the spider returns a request for each chunk_id"""
        row = {"html_content": "<html><body><p>hello</p></body></html>"}
        response = response_from_crawl(row, "https://example.com/path")
        item = yield from self.spider.parse(response)
        self.assertEqual(item["url"], "https://example.com/path")

    def test_parse_example1(self):
        row = {
            "id": UUID("00009c98-e335-4ed1-aeff-b9de05c1f022"),
            "url": 'https://inspection.canada.ca/about-cfia/find-a-form/privacy-notice/eng/1445601295813/1445601296610',
            "title": "Énoncé de confidentialité applicable au formulaire CFIA/ACIA 3369"
                " - Demande d'inspection des exportations et de certification phytosanitaire"  # noqa: E501
                " - Agence canadienne d'inspection des aliments",
            "lang": "fr",
            "html_content": get_html("1445601296610"),
            "last_crawled": "1685416791",
            "last_updated": "2022-07-05",
            "last_updated_date": datetime.date(2022, 7, 5),
        }

        response = response_from_crawl(row, row['url'])
        items = list(self.spider.parse(response))
        self.assertEqual(items[0]["url"], row['url'])
        self.assertEqual(len(items), 8)
        self.assertTrue(items[0]["text_content"].startswith(
            'Comment ouvrir un formulaire'))
