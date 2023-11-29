from louis.crawler.chunking import chunk_html

from louis.crawler.items import ChunkItem
from louis.crawler.items import EmbeddingItem

from ailab.models.openai import fetch_embedding

def convert_html_content_to_chunk_items(url, html_content):
    soup, chunks = chunk_html(html_content)
    for chunk in chunks:
        yield ChunkItem(
            {
                "url": url,
                "title": chunk['title'],
                "text_content": chunk['text_content'],
                "token_count": chunk['token_count'],
                "tokens": chunk['tokens'],
            }
        )

def convert_chunk_token_to_embedding_items(chunk_token):
    embedding = fetch_embedding(chunk_token['tokens'])
    yield EmbeddingItem(
        {
            "token_id": chunk_token['token_id'],
            "embedding": embedding,
            "embedding_model": 'ada_002'
        }
    )
