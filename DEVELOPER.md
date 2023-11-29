# crawlers

## Overview

We use scrapy as a generic job queue processing facility from crawling pages (from a live connection of a cached disk version) to processing rows of data in the database. The architecture and multiprocessing facilities let us organize the code and scrapy offer a number of builtin services to monitor and manage long job queues.

Flows as follow:

* spider (such as louis/spiders/kurt.py) is instantiated and start_requests is called
  * start_request generates a series of requests (possibly from rows in the db) bound for a method of spider (parse)
* requests are handled by louis/middleware.py
  * the content for each request is fetched from a web server, filesystem or database
  * the content is turned into a response
* responses are sent back to the spider. The spider generates Item from the responses
* items are received by the louis/pipeline.py
  * items are store in the database

## layers

* louis.crawler:
  * .requests: creation of requests here
  * .responses: creation of responses here
  * .settings: configuration of the crawler. reads from .env
  * .chunking.py: chunking logic (splitting docs into logical blocks)

## running the crawlers

We use the crawlers in a little bit of a non-standard way.

Instead of hitting a website, we pick up the URL from disk

As a second step, we pick up rows from the database

As a third step, we pick up rows from the database to pass to the embedding API

goldie crawler: HTML from disk dump in Cache/:

```
scrapy crawl goldie --logfile logs/goldie.log
```

hawn crawler: crawl table to chunk and token:

```
scrapy crawl hawn --logfile logs/hawn.log
```

kurt crawler: crawl tokens to embedding

```
scrapy crawl kurt --logfile logs/kurt.log
```

## Developing with ailab-db

Database operations are done within the ailab-db package.

To test and develop concurrently between the crawler and the the ailab-db package, install editable version of the ailab-db dependency:

```bash
pip install -e git+https://github.com/ai-cfia/ailab-db@main#egg=ailab_db
```
this will clone ailab_db in sources allowing you to submit pull requests too

## References

* [Chunking Strategies for LLM Applications](https://www.pinecone.io/learn/chunking-strategies/)
* [Scrapy](https://docs.scrapy.org/en/latest/index.html)
* [Scrapy: saving to postgres](https://scrapeops.io/python-scrapy-playbook/scrapy-save-data-postgres/)