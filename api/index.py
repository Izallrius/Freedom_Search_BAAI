from flask import Flask, render_template, request, jsonify
from sqlalchemy import create_engine, func, desc
from sqlalchemy.orm import sessionmaker, scoped_session
from database.models import CrawledPage, crawler_engine, pg_engine, IndexedPage
import requests
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

# Hugging Face Inference API Configuration
MODEL_ID = "BAAI/bge-small-en-v1.5"
API_URL = f"https://router.huggingface.co/hf-inference/models/{MODEL_ID}"
HF_TOKEN = os.getenv("HUGGINGFACE_TOKEN")

def get_embedding(text):
    """Get embedding for a single text using Hugging Face Inference API."""
    if not HF_TOKEN or HF_TOKEN == "your_huggingface_token_here":
        raise ValueError("HUGGINGFACE_TOKEN not set in .env file")
        
    headers = {"Authorization": f"Bearer {HF_TOKEN}"}
    # For BGE models, queries should be prefixed with an instruction
    instruction = "Represent this sentence for searching relevant passages: "
    payload = {"inputs": f"{instruction}{text}", "options": {"wait_for_model": True}}
    
    response = requests.post(API_URL, headers=headers, json=payload)
    
    if response.status_code != 200:
        raise Exception(f"Hugging Face API error: {response.status_code} - {response.text}")
        
    result = response.json()
    
    # Handle potential nested list response (e.g., if API returns batch result)
    if isinstance(result, list) and len(result) > 0:
        if isinstance(result[0], list):
            # If it's [[[...]]] (token embeddings), we might need pooling, 
            # but usually for feature-extraction on sentence-transformers it's [[...]]
            return result[0]
    
    return result

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
        # Generate embedding for the query using the Hugging Face Inference API
        query_embedding = get_embedding(query)

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
