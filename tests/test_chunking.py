# test chunking

import os
import unittest

from bs4 import BeautifulSoup

from louis.crawler.chunking import segment_blocks_into_chunks, chunk_html

EXAMPLE1 = (
    "<html><body>"
    "<h1>high-level title</h1>"
    "<h2>second-level title</h2>"
    "<p>paragraph below second-level</p>"
    "<h2>another second-level</h2>"
    "<p>paragraph within 2nd level</p>"
    "<h3>third-level title</h3>"
    "<p>paragraph below third-level heading</p>"
    "<h1>last high-level title, sibling to the first</h1>"
    "</html></body>"
)


EXPECTED_TOKENS = [
    12156,
    11852,
    2316,
    5686,
    11852,
    2316,
    28827,
    3770,
    2132,
    11852,
    43063,
    2132,
    11852,
    28827,
    2949,
    220,
    17,
    303,
    2237,
    32827,
    11852,
    2316,
    28827,
    3770,
    4948,
    11852,
    14836,
    4354,
    1579,
    11852,
    2316,
    11,
    45323,
    311,
    279,
    1176,
]

CWD = os.path.dirname(os.path.abspath(__file__))

def get_html(filename):
    with open(f"{CWD}/responses/{filename}.html", encoding="UTF-8") as f:
        return f.read()

class TestChunking(unittest.TestCase):
    def test_chunking(self):
        """Test chunking on a simple example"""
        soup, chunks = chunk_html(EXAMPLE1)
        # print(chunks)
        # print(chunks[0]['tokens'])
        self.assertEqual(chunks[0]["tokens"], EXPECTED_TOKENS)
        self.assertEqual(
            chunks[0]["title"],
            "high-level title;last high-level title, sibling to the first",
        )

    def test_chunking_sample1(self):
        """Test chunking on a real example"""
        html = get_html("1547741756885")
        soup, chunks = chunk_html(html)
        # sentences = []
        # text_content = ''
        # for c in chunks:
        #     text_content += c['text_content']
        # split_text = [s.strip() for s in text_content.split('.')]
        # print(split_text)
        # self.assertEqual(sentences, split_text)

    def test_chunking_sample2(self):
        """Test chunking on a real example"""
        html = get_html("1430250287405")
        soup, chunks = chunk_html(html)
        # sentences = soup.get_text(strip=True).split('.')
        # text_content = ''
        # for c in chunks:
        #     text_content += c['text_content']
        # split_text = [s.strip() for s in text_content.split('.')]
        # print(split_text)
        # self.assertEqual(sentences, split_text)
        titles = [c["title"] for c in chunks]
        unique_titles_sorted = sorted(list(set(titles)))
        # print(unique_titles_sorted)
        self.assertEqual(
            unique_titles_sorted,
            [
                "A",
                "B",
                "C",
                "D",
                "E",
                "F",
                "G",
                "I",
                "L",
                "M",
                "N",
                "O",
                "P",
                "Q",
                "R",
                "S",
                "T",
                "V",
                "Z",
                "À retenir",
            ],
        )
        # print(chunks)
        # print(soup.prettify())

    def test_chunking_fragment2(self):
        """Test chunking on a real example"""
        html = get_html("fragment2")
        soup, chunks = chunk_html(html)
        # print(soup.prettify())
        # print(chunks)
        self.assertEqual(
            chunks[0]["text_content"],
            ("Z Zoonose (Zoonosis) Le terme « zoonose » n'est pas employé dans la "
             "Loi sur la salubrité des aliments au Canada ni dans le Règlement sur "
             "la salubrité des aliments au Canada. En général, le terme « zoonose » "
             "indique infection ou maladie pouvant être transmise entre les animaux "
             "et les humains."))

        self.assertEqual(chunks[0]["title"], "Glossary")

    def test_block_by_heading(self):
        """Test chunking on a real example"""
        html = get_html("wrapped")
        soup = BeautifulSoup(html, "lxml")
        blocks = soup.select(".blocks")
        chunks = segment_blocks_into_chunks(blocks)
        self.assertEqual(
            chunks,
            [
                {
                    "text_content": "h1a\nh2a",
                    "tokens": [],
                    "token_count": 510,
                    "title": "high-level title;second-level title",
                },
                {"text_content": "h2b", "tokens": [],
                    "token_count": 512, "title": "second-level title b"},
                {"text_content": "h2c", "tokens": [], "token_count": 510,
                    "title": "third-level title;third-level title"},
                {"text_content": "h1a", "tokens": [], "token_count": 255,
                    "title": "last high-level title, sibling to the first"},
            ],
        )

    def test_chunking_with_summary_details_block(self):
        html = get_html("1648871138011")
        soup, chunks = chunk_html(html)
        for c in chunks:
            self.assertTrue(c["token_count"] > 32,
                            f"{c['text_content']} is too short")

    def test_chunking_body_not_found(self):
        html = get_html("1445601296610")
        soup, chunks = chunk_html(html)
        self.assertEqual(len(chunks), 8)

    def test_chunking_no_chunks(self):
        # postgresql://inspectioncanadaca/louis_v004/crawl/66064032-4acc-4d30-b836-2d3f4db13311
        # https://inspection.canada.ca/sante-des-animaux/produits-biologiques-veterinaires/avis/fra/1299161124455/1320703838068
        html = get_html("1320703838068")
        soup, chunks = chunk_html(html)
        self.assertIsInstance(chunks, list)
        self.assertIsInstance(chunks[0], dict)
        self.assertEqual(len(chunks), 1)

    def test_chunking_no_chunks2(self):
        html = get_html('1637767398789')
        soup, chunks = chunk_html(html)
        self.assertIsInstance(chunks, list)
        self.assertIsInstance(chunks[0], dict)
