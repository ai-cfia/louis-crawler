"""test database functions"""
import unittest
import time
import uuid

import louis.crawler.items as items
import louis.db as db

import louis.models.openai

embedding_table = """
create table if not exists public."{embedding_model}" (
	id uuid default uuid_generate_v4 (),
	token_id uuid references public.token(id),
	embedding vector(1536),
	primary key(id),
	unique(token_id)
);
"""

class TestDB(unittest.TestCase):
    """Test the database functions"""
    def setUp(self):
        self.connection = db.connect_db()

    def tearDown(self):
        self.connection.close()

    def test_schema(self):
        """sample test to check if the schema is correct and idempotent"""
        with open("db/dumps/louis_v002/schema.sql", encoding='utf-8') as schema_file:
            schema = schema_file.read()
            schema = schema.replace('louis_v002', 'test')
        with db.cursor(self.connection) as cursor:
            cursor.execute(schema)
            self.connection.rollback()

    def test_store_chunk_item(self):
        """sample test to check if store_chunk_item works"""""
        with db.cursor(self.connection) as cursor:
            db.store_chunk_item(cursor, items.ChunkItem({
                "url": "https://inspection.canada.ca/splash",
                "title": "Test Title",
                "text_content": "Test Text Content",
                "token_count": 3,
                "tokens": [1,2,3],
            }))
            self.connection.rollback()

    def test_store_crawl_item(self):
        """sample test to check if store_crawl_item work"""
        with db.cursor(self.connection) as cursor:
            db.store_crawl_item(cursor, items.CrawlItem({
                "url": "https://inspection.canada.ca/splash",
                "title": "Test Title",
                "lang": "fr",
                "html_content": "<html><body><p>Test Text Content</p></body></html>",
                "last_updated": "2023-06-01",
                "last_crawled": time.time()
            }))
            self.connection.rollback()

    def test_store_embedding_item(self):
        """sample test to check if store_embedding_item works"""
        with db.cursor(self.connection) as cursor:
            db.store_embedding_item(cursor, items.EmbeddingItem({
                "token_id": "00000000-0000-0000-0000-000000000000",
                "embedding": list(range(0, 1536)),
                "embedding_model": "ada_002"
            }))
            self.connection.rollback()

    def test_link_pages_and_fetch_links(self):
        """sample test to check if link_pages works"""
        with db.cursor(self.connection) as cursor:
            source_url = "https://inspection.canada.ca/splash"
            destination_url = "https://inspection.canada.ca/animal-health/terrestrial-animals/exports/pets/australia/eng/1321292836314/1321292933011"
            db.link_pages(cursor, source_url, destination_url)
            links = db.fetch_links(cursor, "https://inspection.canada.ca/splash")
            self.connection.rollback()
        self.assertEqual(links, [destination_url])

    def test_fetch_crawl_row(self):
        """sample test to check if fetch_crawl_row works"""
        with db.cursor(self.connection) as cursor:
            row = db.fetch_crawl_row(cursor, "https://inspection.canada.ca/splash")
            self.connection.rollback()
        self.assertEqual(row['url'], "https://inspection.canada.ca/splash")
        self.assertEqual(row['title'], "Canadian Food Inspection Agency / Agence canadienne d'inspection des aliments")

    def test_fetch_chunk_row(self):
        """sample test to check if fetch_chunk_row works"""
        with db.cursor(self.connection) as cursor:
            # select id from chunk join crawl ON public.chunk.crawl_id = public.crawl.id where url = 'https://inspection.canada.ca/splash'
            row = db.fetch_chunk_token_row(cursor, "postgresql://inspection.canada.ca/public/chunk/469812c5-190c-4e56-9f88-c8621592bcb5")
            self.connection.rollback()
        self.assertEqual(len(row['tokens']), 76)
        self.assertEqual(str(row['chunk_id']), "469812c5-190c-4e56-9f88-c8621592bcb5")
        self.assertEqual(str(row['token_id']), 'dbb7b498-2cbf-4ae9-aa10-3169cc72f285')


    def test_fetch_chunk_id_without_embedding(self):
        """sample test to check if fetch_chunk_id_without_embedding works"""
        with db.cursor(self.connection) as cursor:
            cursor.execute(embedding_table.format(embedding_model='test-model'))
            rows = db.fetch_chunk_id_without_embedding(cursor, 'test-model')
            entity_id = rows[0]
            self.connection.rollback()

    def test_create_postgresql_url(self):
        """sample test to check if create_parse_postgresql_url works"""
        entity_uuid = '5cef886d-8408-4868-9a69-0f0ca2167941'
        url = db.create_postgresql_url(
            "inspection.canada.ca",
            "chunk", entity_uuid,
            {'encoding': 'cl100k_base'})
        self.assertEqual(url, f"postgresql://inspection.canada.ca/public/chunk/{entity_uuid}?encoding=cl100k_base")
        parsed = db.parse_postgresql_url(url)
        self.assertEqual(parsed['dbname'], "inspection.canada.ca")
        self.assertEqual(parsed['tablename'], "chunk")
        self.assertEqual(parsed['entity_uuid'], entity_uuid)
        self.assertEqual(parsed['parameters']['encoding'][0], "cl100k_base")

    def test_match_documents_text_query(self):
        with db.cursor(self.connection) as cursor:
            docs = db.match_documents_from_text_query(cursor, 'what are the cooking temperatures for e.coli?')
            self.connection.rollback()
        self.assertEqual(len(docs), 10)

    def test_president_of_cfia(self):
        with db.cursor(self.connection) as cursor:
            docs = db.match_documents_from_text_query(cursor, 'who is the president of the CFIA?')
            self.connection.rollback()
        self.assertEqual(docs[0]['title'], 'Dr. Harpreet S. Kochhar - Canadian Food Inspection Agency')
