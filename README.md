========================================================================
                          FREEDOM SEARCH
               The World's First Unbiased AI Search Engine
========================================================================

Welcome to Freedom Search! This guide explains how our search engine 
works, how we use Artificial Intelligence (AI) to understand your 
queries, and why this provides a better search experience than 
traditional keyword-based systems.

------------------------------------------------------------------------
1. WHAT IS FREEDOM SEARCH?
------------------------------------------------------------------------
Freedom Search is a "Semantic Search Engine." Unlike older search 
engines that only look for exact word matches (like Ctrl+F), Freedom 
Search tries to understand the actual *meaning* and *intent* behind 
your search terms.

------------------------------------------------------------------------
2. HOW THE AI INDEXING WORKS
------------------------------------------------------------------------
Before you even type a query, our system processes millions of words 
from across the web using a specialized AI model called a "Transformer" 
(specifically the BAAI/bge-small-en-v1.5 model).

Step 1: Text Extraction
When we find a web page, we extract the title, the URL, and the main 
written content.

Step 2: Mathematical "Meaning" (Embeddings)
Our AI converts that text into a long string of numbers called an 
"Embedding" or "Vector." These numbers represent where that page sits 
in a multi-dimensional "map of human language." 
- Pages about "Space Exploration" will have numbers that group together.
- Pages about "Cooking Recipes" will group in a different area.

Step 3: The Vector Database
We store these mathematical meanings in a high-performance Vector 
Database (ChromaDB). This allows us to compare meanings instantly.

------------------------------------------------------------------------
3. HOW THE AI SEARCH WORKS
------------------------------------------------------------------------
When you type a search query, the magic happens in three steps:

Step 1: Query Encoding
The AI takes your search phrase (e.g., "how to stay healthy") and 
turns it into the same kind of mathematical "meaning" (Vector) used 
for the web pages.

Step 2: Semantic Similarity (Cosine Similarity)
Instead of looking for pages that literally contain the word "healthy," 
the engine looks for pages whose "meaning numbers" are closest to 
your query's numbers. 
- This means if you search for "automobile," the AI knows to also 
  show you results for "cars" or "vehicles," even if those exact 
  words weren't in your query.

Step 3: Ranking by Relevance
We calculate a "Similarity Score." A score of 100% means the page 
perfectly matches the intent of your search. We rank the results 
so the most relevant content always appears at the top.

------------------------------------------------------------------------
4. WHY USE AI SEARCH?
------------------------------------------------------------------------
- Context Awareness: It understands that "Apple" might mean a fruit 
  or a technology company depending on your other search words.
- Synonym Handling: You don't have to guess the exact words the 
  author used.
- Better Snippets: Our AI finds the most relevant part of a long 
  article to show you in the search results.
- Unbiased Results: We rank based on mathematical meaning and 
  relevance, not on who paid the most for an advertisement.

------------------------------------------------------------------------
5. NAVIGATING THE SITE
------------------------------------------------------------------------
- Search: Use the main search bar to find anything.
- Pagination: If there are many results, use the "Next" and "Previous" 
  buttons at the bottom to explore more.
- Similarity Score: Every result shows a percentage. This is the 
  AI's confidence that the page matches your intent.
- Dark Mode: Use the moon/sun icon in the top right to switch themes 
  for easier reading.

========================================================================
           Thank you for using the future of unbiased search.
========================================================================