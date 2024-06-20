import unittest
import uuid

import louis.crawler.items as items

import time

import ailab.db as db
import ailab.db.crawler as crawler

import objects.chunk as testchunk

class TestDB(unittest.TestCase):
    def setUp(self):
        self.connection = db.connect_db()
        self.dbname = self.connection.info.dbname

    def tearDown(self):
        self.connection.rollback()
        self.connection.close()

    def test_store_crawl_chunk_embedding_item(self):
        """sample test to check if three steps storage works"""
        with db.cursor(self.connection) as cursor:
            crawl_item = crawler.store_crawl_item(cursor, {
                "url": "https://inspection.canada.ca/a-propos-de-l-acia/contactez-nous/fra/1546627816321/1546627838025",
                "title": "Test Title",
                "lang": "fr",
                "html_content": "Test HTML Content " + uuid.uuid4().hex,
                "last_crawled": time.time(),
                "last_updated": "2023-06-01"
            })
            chunk_item = crawler.store_chunk_item(cursor, {
                "url": crawl_item["url"],
                "title": "Test Sub-Title",
                "text_content": "Test Text Content " + uuid.uuid4().hex,
                "token_count": 3,
                "tokens": [1, 2, 3],
                "encoding": "cl100k_base"
            })
            embedding_item = crawler.store_embedding_item(cursor, items.EmbeddingItem({
                "token_id": chunk_item['token_id'],
                "embedding": list(range(0, 1536)),
                "embedding_model": "ada_002"
            }))
        self.assertEqual(crawl_item['url'], chunk_item['url'])
        self.assertEqual(chunk_item['token_id'], embedding_item['token_id'])

    def test_fetch_crawl_ids_without_chunk(self):
        """sample test to check if fetch_crawl_ids_without_chunk works"""
        with db.cursor(self.connection) as cursor:
            # in RussellSpider start_requests
            crawl_ids = crawler.fetch_crawl_ids_without_chunk(cursor)
            self.assertEqual(len(crawl_ids), 0)
        #     url = db.create_postgresql_url(self.dbname, 'crawl', crawl_ids[0])
        #     # in LouisDownloaderMiddleware process_request
        #     row =  crawler.fetch_crawl_row(cursor, url)
        # self.assertIn('html_content', row)

    def test_store_chunk_item2(self):
        """sample test to check if store_chunk_item works"""""
        with db.cursor(self.connection) as cursor:
            stored_chunk = crawler.store_chunk_item(
                cursor, items.ChunkItem(testchunk.example1))
        self.assertIn('token_id', stored_chunk)
        self.assertIn('chunk_id', stored_chunk)
        self.assertIn('md5hash', stored_chunk)

    def test_store_chunk_page1581548517693(self):
        """sample test to check if store_chunk_item works"""""
        with db.cursor(self.connection) as cursor:
            stored_chunk = crawler.store_chunk_item(
                cursor, items.ChunkItem(testchunk.page1581548517693))
        self.assertIn('token_id', stored_chunk)
        self.assertIn('chunk_id', stored_chunk)
        self.assertIn('md5hash', stored_chunk)

    def test_hash(self):
        """sample test to check if the md5 hash matches output of postgresql"""
        with db.cursor(self.connection) as cursor:
            python_hash = db.hash('hello world')
            db_hash = cursor.execute("SELECT md5('hello world')").fetchone()['md5']
        self.assertEqual(python_hash, db_hash)

    def test_fetch_crawl_row(self):
        """sample test to check if fetch_crawl_row works"""
        with db.cursor(self.connection) as cursor:
            url = 'https://inspection.canada.ca/a-propos-de-l-acia/contactez-nous/fra/1546627816321/1546627838025'
            row =  crawler.fetch_crawl_row(cursor, url)
        self.assertIn('url', row)
        self.assertIn('html_content', row)

    def test_storing_chunk_item_that_already_exists_has_no_effect(self):
        """sample test to check if store_chunk_item works"""
        with db.cursor(self.connection) as cursor:
            item = {
                "url": "https://inspection.canada.ca/a-propos-de-l-acia/contactez-nous/fra/1546627816321/1546627838025",
                "title": "Test Sub-Title",
                "text_content": "Test Text Content " + uuid.uuid4().hex,
                "token_count": 3,
                "tokens": [1, 2, 3],
                "encoding": "cl100k_base"
            }
            chunk_item_first_insert = crawler.store_chunk_item(cursor, item)

            # should work fine second time
            chunk_item_repeated = crawler.store_chunk_item(cursor, item)
        self.assertEqual(
            chunk_item_first_insert['token_id'], chunk_item_repeated['token_id'])
        self.assertEqual(
            chunk_item_first_insert['chunk_id'], chunk_item_repeated['chunk_id'])
        self.assertEqual(
            chunk_item_first_insert['md5hash'], chunk_item_repeated['md5hash'])