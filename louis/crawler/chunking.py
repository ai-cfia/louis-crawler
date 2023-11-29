"""
This module contains functions to chunk a web page into 512 tokens chunks
"""
import json
import re

import tiktoken
from bs4 import BeautifulSoup

enc = tiktoken.get_encoding("cl100k_base")

HEADERS_RE = re.compile('^h[1-6]$')

def compute_tokens(block):
    """Compute the tokens and token count of a block, caching the result in the block"""
    if 'tokens' in block.attrs:
        # content is cached in block
        text_content = block.attrs['text_content']
        token_count = int(block.attrs['token_count'])
        tokens = json.loads(block.attrs['tokens'])
        title = block.get('title', '')
    else:
        # extract and clean up block text content, storing it in block
        text_content = re.sub(r'\s+', ' ', block.get_text()).strip()
        tokens = enc.encode(text_content)
        token_count = len(tokens)
        block.attrs['tokens'] = str(tokens)
        block.attrs['token_count'] = str(token_count)
        block.attrs['text_content'] = text_content
        title = block.get('title', '')
    return {
        'text_content': text_content,
        'tokens': tokens,
        'token_count': token_count,
        'title': title
    }

def mark_parent(block):
    """Mark the parent of a block as a parent, recursively"""
    # ok, parent is already identified as parent
    if 'parent' in block.attrs:
        return

    # set parent flag
    block.attrs['parent'] = True

    # if we're at the body block, we're done
    if block.name == 'body':
        return

    # otherwise we keep going
    if block.parent:
        return mark_parent(block.parent)

    return

def find_next_parent_div(block):
    """Find the next parent block div of a block, recursively"""
    return block.find_parent(class_='blocks')

def mark_processed(block):
    """Mark a block as processed, recursively"""
    block.attrs['processed'] = True
    child_blocks = block.find_all(class_='blocks')
    for child_block in child_blocks:
        child_block.attrs['processed'] = True

def estimate_best_bucket_size(total, min_tokens, max_tokens):
    """Estimate the best bucket size for a total number of tokens"""
    maximizing_divider = max_tokens
    max_remainder = 0
    for i in range(max_tokens, min_tokens, -1):
        remainder = total % i
        if remainder > max_remainder:
            maximizing_divider = i
            max_remainder = remainder
    return maximizing_divider

def split_chunk_into_subchunks(large_chunk, min_tokens=256, max_tokens=512):
    """some leafs might be bigger than desired. split text into smaller chunks"""
    assert large_chunk['token_count'] > max_tokens, (
        "chunk must be bigger than max_tokens")
    text_content = large_chunk['text_content']
    sentences = text_content.split('.')

    sentence_chunks = []
    for sentence in sentences:
        tokens = enc.encode(sentence)
        token_count = len(tokens)
        sentence_chunks.append({
            'text_content': sentence,
            'tokens': tokens,
            'token_count': token_count,
            'title': large_chunk.get('title', '')
        })

    # it's possible it is just one long list of sentences without .
    if len(sentence_chunks) == 1:
        return sentence_chunks

    # TODO: smarter sentence bin packing
    # total_count = sum(c['token_count'] for c in sentence_chunks)
    # target_bucket_size = estimate_best_bucket_size(total_count, min_tokens, max_tokens)  # noqa: E501

    target_bucket_size = 409
    buckets = [[]]
    bucket = buckets[0]
    bucket_size = 0
    for sentence_chunk in sentence_chunks:
        # need to be careful, maybe this sentence_chunk is already over the limit but
        # there's also nothing in the bucket yet
        predicted_bucket_size = bucket_size + sentence_chunk['token_count']
        if bucket_size > 0 and predicted_bucket_size >= target_bucket_size:
            # we're over the limit, we start a new bucket
            bucket = []
            buckets.append(bucket)
            bucket_size = 0

        bucket.append(sentence_chunk)
        bucket_size += sentence_chunk['token_count']

    smaller_chunks = []
    for bucket in buckets:
        assert len(bucket) > 0, (
            "bucket must not be empty: {} for large_chunk {}"
            .format(bucket, large_chunk))
        small_chunk = combine_chunks_into_single_chunk(bucket)
        smaller_chunks.append(small_chunk)
    return smaller_chunks

def collect_chunks_from_block(block, total_token_count, chunks):
    """Collect chunks of text, starting from a block,
       until the total token count is at most 512"""
    if 'processed' not in block.attrs:
        chunk = compute_tokens(block)
        prospective_total = total_token_count + int(chunk['token_count'])
        if prospective_total <= 512:
            # this is a good chunk as-is, we add it to the list
            # although it may be smaller than we want
            chunks.append(chunk)
            mark_processed(block)
            # we'll continue to see if we can add more siblings
        elif prospective_total > 512:
            # too big, we skip it and let next iteration handle it
            return
    else:
        # this is already processed, nothing changes and we skip to the next sibling
        # or more likely the next parent
        prospective_total = total_token_count
    sibling = block.find_next_sibling(class_='blocks')
    if sibling:
        # there's a sibling, let's see how much we can fit in
        return collect_chunks_from_block(sibling, prospective_total, chunks)

    # no more siblings so we go up the tree to the parent block
    # which includes this one and all the siblings
    # if successful, we reset chunks to the parent chunks
    parent_div = find_next_parent_div(block)
    if parent_div:
        parent_chunks = []
        if 'title' not in parent_div.attrs:
            parent_div.attrs['title'] = ";".join([c['title'] for c in chunks])
        collect_chunks_from_block(parent_div, 0, parent_chunks)
        if len(parent_chunks) > 0:
            chunks.clear()
            chunks.extend(parent_chunks)
    return

def group_heading_by_block(soup):
    """Wrap each heading and its siblings into a div,
       including other heading of a higher level"""
    body = soup.select('body')[0]
    body.attrs['class'] = body.attrs.get('class', []) + ["blocks", "h0-block"]
    if soup.title:
        body.attrs['title'] = soup.title.text.strip()

    parent_div = None

    # we unwrap additional tags around headers where the header
    # is alone in the wrapping tag
    for block in list(soup.find_all(HEADERS_RE)):
        if (not HEADERS_RE.match(block.parent.name)
            and len(block.find_next_siblings()) == 0):
            # example of this is a <summary><h1>...</h1></summary>
            block.parent.unwrap()

    for block in list(soup.find_all(HEADERS_RE)):
        # get siblings before we wrap the current block
        siblings = list(block.next_siblings)
        # we nest the current block into a div representing the heading
        parent_div = block.wrap(soup.new_tag(
            "div", **{
                "class": f"{block.name}-block blocks",
                "title": block.text.strip()
            }))

        # we append every sibling to the current div up to the next heading
        for sibling in siblings:
            if sibling.name and re.match(HEADERS_RE, sibling.name):
                if sibling.name[1] <= block.name[1]:
                    # sibling header is of same or lower level
                    break
            parent_div.append(sibling)

        # we recursively mark all the block div above as a parent block
        # any non-parent block left at the end will be a leaf
        mark_parent(parent_div.parent)

def combine_chunks_into_single_chunk(chunks):
    """Combine list of chunks into a single chunk"""
    assert len(chunks) > 0, "list of chunks must not be empty"

    # we return when there's only a single chunk left
    if len(chunks) == 1:
        chunk = chunks[0]
        return chunk

    chunk = chunks[0]
    for next_chunk in chunks[1:]:
        chunk['text_content'] += "\n" + next_chunk['text_content']
        chunk['tokens'] += next_chunk['tokens']
        chunk['token_count'] += next_chunk['token_count']

        # this may be from a splitted chunk so we check that the title isn't already
        # the same as what we would append
        if next_chunk['title'] != chunk['title']:
            chunk['title'] += ";" + next_chunk['title']
        assert chunk['token_count'] <= 512
    return chunk

def segment_blocks_into_chunks(blocks):
    """Segment blocks into chunks of 256-512 tokens"""
    # collect chunks from leafs
    all_chunks = []
    for block in blocks:
        # this chunk is a parent, we start at the leafs
        if 'parent' in block.attrs:
            continue
        # this chunk is already taken care of
        if 'processed' in block.attrs:
            continue
        chunk = compute_tokens(block)
        if chunk['token_count'] <= 512:
            if chunk['token_count'] >= 256:
                # perfect sized chunk
                all_chunks.append(chunk)
                mark_processed(block)
            else: # < 256:
                # chunk too small
                chunks = []
                # we collect siblings until we reach 256 tokens
                collect_chunks_from_block(block, 0, chunks)
                chunk = combine_chunks_into_single_chunk(chunks)
                all_chunks.append(chunk)
        else:
            # chunk too big
            subchunks = split_chunk_into_subchunks(chunk)
            all_chunks.extend(subchunks)
            mark_processed(block)

    return all_chunks

def chunk_html(html_content):
    """Chunk an HTML document into a list of chunks.

     chunks are made up of a title, and a body

     the body is a list of subheadings and paragraphs

    each chunk should have between 256 and 512 tokens (ada tokens)
    or less if the entire document is less than 256 tokens

    returns a list of chunks, each chunk is a tuple (text_content, tokens, token_count)
    """
    # chunks are organized by headings in a graph
    # we organize leaf nodes contents into chunks
    # html_content = html_content.replace('\n', ' ')
    soup = BeautifulSoup(html_content, "lxml")

    # make sure html fragments are wrapped in html and body blocks
    soup.smooth()

    group_heading_by_block(soup)
    blocks = soup.select('.blocks')
    chunks = segment_blocks_into_chunks(blocks)

    return (soup, chunks)


if __name__ == '__main__':
    # open file from first parameter
    import sys
    with open(sys.argv[1], encoding='UTF-8') as f:
        html = f.read()

    soup, chunks = chunk_html(html)
    # print(soup.prettify())
    # print(chunks)
    for chunk in chunks:
        print(f"{chunk['title']}: {chunk['token_count']}")
