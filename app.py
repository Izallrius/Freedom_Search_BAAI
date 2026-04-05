from flask import Flask, render_template, request, jsonify
from sqlalchemy import create_engine, func, desc
from sqlalchemy.orm import sessionmaker, scoped_session
from database.models import CrawledPage, crawler_engine, pg_engine, IndexedPage
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv
import time
import json
import os

# Load environment variables from .env
load_dotenv()

app = Flask(__name__)

# Get the directory containing this file
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Create database session for crawler (SQLite)
crawler_session = scoped_session(sessionmaker(bind=crawler_engine))

# Create database session for PostgreSQL (Neon)
pg_session = scoped_session(sessionmaker(bind=pg_engine))

# Initialize embedding model at startup (loaded once, used for all queries)
MODEL_NAME = 'BAAI/bge-small-en-v1.5'
MODEL_PATH = os.path.join(BASE_DIR, "models", "bge-small-en-v1.5")

if not os.path.exists(MODEL_PATH):
    print(f"🚀 Downloading {MODEL_NAME} embedding model at startup (first time)...")
    embedding_model = SentenceTransformer(MODEL_NAME)
    print(f"✓ Model downloaded. Saving to {MODEL_PATH} for future use...")
    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
    embedding_model.save(MODEL_PATH)
else:
    print(f"🚀 Loading embedding model from local storage: {MODEL_PATH}")
    embedding_model = SentenceTransformer(MODEL_PATH)
print("✓ Embedding model loaded successfully!")

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/crawled')
def crawled():
    try:
        pages = crawler_session.query(CrawledPage).order_by(CrawledPage.last_crawled.desc()).all()
        return render_template('crawled.html', pages=pages)
    finally:
        crawler_session.close()

@app.route('/indexed')
def indexed():
    try:
        page_num = request.args.get('page', 1, type=int)
        per_page = 20

        # Get total count from PostgreSQL
        total_count = pg_session.query(IndexedPage).count()
        total_pages = (total_count + per_page - 1) // per_page if total_count > 0 else 1

        # Ensure page is within valid range
        page_num = max(1, min(page_num, total_pages))

        # Get paginated results from PostgreSQL
        offset = (page_num - 1) * per_page

        pages = pg_session.query(IndexedPage).order_by(IndexedPage.crawled_at.desc()).offset(offset).limit(per_page).all()

        return render_template('indexed.html', 
                             pages=pages,
                             current_page=page_num,
                             total_pages=total_pages,
                             total_count=total_count,
                             per_page=per_page,
                             max=max,
                             min=min)
    except Exception as e:
        print(f"Error in /indexed route: {str(e)}")
        return render_template('indexed.html', 
                             pages=[],
                             current_page=1,
                             total_pages=0,
                             total_count=0,
                             per_page=20,
                             error=str(e),
                             max=max,
                             min=min)
    finally:
        pg_session.close()

@app.route('/search')
def search():
    query = request.args.get('q', '')
    page = request.args.get('page', 1, type=int)
    per_page = 20

    if not query:
        return render_template('search_results.html', query='', results=[], search_time=0, current_page=1, total_pages=0)

    start_time = time.time()

    try:
        # Generate embedding for the query using the pre-loaded model
        query_embedding = embedding_model.encode(query, convert_to_numpy=True).tolist()

        # Search PostgreSQL for similar documents using pgvector
        # <=> operator is cosine distance. 1 - distance = cosine similarity
        # We fetch up to 1000 results for total pool
        max_results = 1000

        # Using pgvector's distance operator
        search_query = pg_session.query(
            IndexedPage,
            (1 - IndexedPage.embedding.cosine_distance(query_embedding)).label('similarity')
        ).order_by(
            IndexedPage.embedding.cosine_distance(query_embedding)
        ).limit(max_results).all()

        # Format results
        all_results = []
        for indexed_page, similarity in search_query:
            document = indexed_page.content or ""

            # Create snippet from document content
            snippet = ''
            doc_lower = document.lower()
            query_lower = query.lower()
            idx = doc_lower.find(query_lower)

            if idx >= 0:
                start = max(0, idx - 75)
                end = min(len(document), idx + 75)
                snippet = ("..." if start > 0 else "") + document[start:end] + ("..." if end < len(document) else "")
            else:
                snippet = document[:150] + ("..." if len(document) > 150 else "")

            all_results.append({
                'url': indexed_page.url,
                'title': indexed_page.title or 'Untitled',
                'snippet': snippet,
                'score': float(similarity),
                'distance': 1.0 - float(similarity)
            })

        # Pagination logic
        total_results = len(all_results)
        total_pages = (total_results + per_page - 1) // per_page
        page = max(1, min(page, total_pages)) if total_pages > 0 else 1

        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        results = all_results[start_idx:end_idx]

        search_time = time.time() - start_time
        return render_template('search_results.html', 
                             query=query, 
                             results=results, 
                             search_time=search_time,
                             current_page=page,
                             total_pages=total_pages,
                             total_results=total_results,
                             max=max,
                             min=min)

    except Exception as e:
        print(f"Error in search: {str(e)}")
        search_time = time.time() - start_time
        return render_template('search_results.html', 
                             query=query, 
                             results=[], 
                             search_time=search_time,
                             error=f"Search error: {str(e)}",
                             current_page=1,
                             total_pages=0,
                             max=max,
                             min=min)
    finally:
        pg_session.close()

if __name__ == '__main__':
    app.run(debug=True) 