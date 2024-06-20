# louis-crawler

Crawler related facilities

## Running the crawler

Run-as:

```
scrapy crawl russell
```

## Editing database functions simultaneously

You'll often want to add, move or modify existing database layer functions found in louis-db.

To edit, you can install an editable version of the package dependencies such as:

```
pip install -e git+https://github.com/ai-cfia/louis-db#egg=louis_db
```

this will checkout the latest source in a local git in src/louis-db allowing edits in that directory to be immediately available for use by louis-crawler.

## Developer

For developer information, see [DEVELOPER.md](DEVELOPER.md)