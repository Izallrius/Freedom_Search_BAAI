from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector
from datetime import datetime
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

Base = declarative_base()

# Crawler Database Models
class CrawledPage(Base):
    __tablename__ = 'crawled_pages'

    id = Column(Integer, primary_key=True)
    url = Column(String, unique=True)
    title = Column(String)
    content = Column(Text)  # Changed to Text for potentially long content
    last_crawled = Column(DateTime, default=datetime.utcnow)
    links = relationship("PageLink", back_populates="page")

class PageLink(Base):
    __tablename__ = 'page_links'

    id = Column(Integer, primary_key=True)
    source_page_id = Column(Integer, ForeignKey('crawled_pages.id'))
    target_url = Column(String)
    page = relationship("CrawledPage", back_populates="links")

# Indexed Pages for PostgreSQL (Vector Storage)
class IndexedPage(Base):
    __tablename__ = 'indexed_pages'

    id = Column(Integer, primary_key=True)
    url = Column(String, unique=True)
    title = Column(String)
    content = Column(Text)
    crawled_at = Column(DateTime)
    embedding = Column(Vector(384))  # Size for BAAI/bge-small-en-v1.5

# Get the directory containing this file
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Crawler engine (SQLite remains for raw crawl data)
crawler_engine = create_engine(f'sqlite:///{os.path.join(BASE_DIR, "..", "crawler.db")}')

# PostgreSQL engine (Neon)
PG_CONN_STRING = os.environ.get('DATABASE_URL', 'postgresql://user:pass@host/dbname')
pg_engine = create_engine(PG_CONN_STRING)

# Create all tables (ensure pgvector is enabled in Postgres)
def init_databases():
    # SQLite
    Base.metadata.create_all(crawler_engine)

    # PostgreSQL
    if "postgresql" in str(pg_engine.url):
        from sqlalchemy import text
        with pg_engine.connect() as conn:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            conn.commit()

    # Only create tables relevant to each engine (filtering by table existence or using different Base metadata if needed)
    # For simplicity, we can create all on both, but ideally we'd separate them.
    # Here we create everything on both.
    Base.metadata.create_all(pg_engine)

if __name__ == "__main__":
    init_databases()