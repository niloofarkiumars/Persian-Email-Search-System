# Persian Email Search System

## 🎯 Overview

A complete, production-ready Persian/Farsi full-text search system for email data using Elasticsearch and MongoDB.

## 📋 What You Need to Customize

## Persian/Farsi Search Support

The Elasticsearch index uses a custom Persian analyzer instead of the default
standard analyzer. It improves matching for common Persian search issues:

- Arabic `ي` / `ك` are normalized to Persian `ی` / `ک`.
- Alef maksura and related Yeh variants are normalized.
- Persian and Arabic digits are normalized through `decimal_digit`.
- Arabic diacritics are removed.
- Zero-width non-joiner / half-space is treated as a separator, so forms like
  `می‌روم`, `می روم`, and similar variants are easier to match.
- Persian stop words are removed at index time.

After changing analyzer settings, recreate and resync the index:

```python
from Source_code.controllers.sync_controller import SyncController

sync = SyncController()
sync.sync_all(force_recreate_index=True)
```

Elasticsearch analyzers are applied when documents are indexed, so old indexed
documents will not benefit from these changes until they are reindexed.

### Search Modes

```python
from Source_code.controllers.search_controller import SearchController

search = SearchController()

# General Persian full-text search with typo tolerance and ngram partial matching
search.search("گزارش پروژه")

# Exact normalized match while ignoring spaces / half-spaces
search.search_exact_ignore_space("می روم", field="body")

# Search all words in the same order
search.search_words("گزارش پروژه مالی", ordered=True)

# Search all words in any order
search.search_words("گزارش پروژه مالی", ordered=False)

# Search inside one field only: subject, body, from, to, or cc
search.search_field("مدیریت", field="subject")

# Explicit ngram / partial-word search
search.search_ngram("گزار")

# Semantic search requires embeddings generated outside this repo for now.
# The query vector and stored document vectors must come from the same model.
search.semantic_search(query_vector=[0.01, 0.02, ...])

# Offline semantic search by text, no online service or model download required
search.semantic_search_text("گزارش ماهیانه")
```

For semantic search, the app now generates deterministic offline vectors from
normalized Persian words, optional stems, word bigrams, and character ngrams.
This requires no online API and no model download. You can still pass your own
`semanticVector` values if you later choose a stronger local embedding model.
Set `SEMANTIC_VECTOR_DIMS` in `.env` if you need a dimension other than `384`.

Parsivar is supported optionally. If installed, the normalizer uses Parsivar for
Persian normalization, tokenization, and stemming; otherwise it falls back to
the built-in local implementation.

```bash
python3 -m pip install parsivar
```

### Search View

PyCharm can run the file directly:

```bash
ES_HOST=http://localhost:9200 ES_PASSWORD=test python3 Source_code/views/search_view.py
```

The interactive search view uses unordered all-word search, so these two queries
should both match the same monthly report email when that email is indexed:

```text
گزارش ماهیانه
ماهیانه گزارش
```

### Testing

Offline tests that do not require Elasticsearch:

```bash
python3 -m pytest Source_code/tests/test_persian_normalizer.py Source_code/tests/test_persian_search_service.py
```

Full test suite with local Elasticsearch:

```bash
docker run --name persian-search-es-test -d -p 9200:9200 \
  -e discovery.type=single-node \
  -e xpack.security.enabled=false \
  -e ES_JAVA_OPTS='-Xms512m -Xmx512m' \
  docker.elastic.co/elasticsearch/elasticsearch:8.14.1

ES_HOST=http://localhost:9200 ES_PASSWORD=test python3 -m pytest Source_code/tests
```

### 1. Database Schema Mapping

**Most Important**: Your team MUST customize the field mappings in `src/models/email_model.py`:

```python
# In EmailMapper class, change these to match your database columns:

FIELD_MAPPINGS = {
    'message_id': 'YOUR_MESSAGE_ID_COLUMN',     # e.g., '_id' or 'msg_id'
    'subject': 'YOUR_SUBJECT_COLUMN',           # e.g., 'email_subject'
    'body': 'YOUR_BODY_COLUMN',                 # e.g., 'email_body' or 'content'
    'from_address': 'YOUR_FROM_COLUMN',         # e.g., 'sender' or 'from_email'
    'to_addresses': 'YOUR_TO_COLUMN',           # e.g., 'recipients' or 'to'
    'date': 'YOUR_DATE_COLUMN',                 # e.g., 'sent_date' or 'created_at'
    'has_attachment': 'YOUR_ATTACHMENT_COLUMN', # e.g., 'attachments' or 'has_attachments'
}

### 2. Edit .env file with your MongoDB credentials
MONGO_HOST=mongodb://your-mongodb-host:27017/
MONGO_DATABASE=your_database_name
MONGO_COLLECTION=your_collection_name

# Download from:
https://artifacts.elastic.co/downloads/elasticsearch/elasticsearch-8.13.4-windows-x86_64.zip


# Install Persian plugin:
C:\elasticsearch\bin\elasticsearch-plugin.bat install https://artifacts.elastic.co/downloads/elasticsearch-plugins/analysis-icu/analysis-icu-8.13.4.zip

# Start Elasticsearch:
C:\elasticsearch\bin\elasticsearch.bat

# Install Docker Desktop
# Then run:
docker run -d --name mongodb-container -p 27017:27017 mongo:latest
