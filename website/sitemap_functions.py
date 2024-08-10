from django.core.cache import cache
from firebase_admin import firestore, auth, credentials

def get_articles_from_firestore_with_cache():
    cached_articles = cache.get('cached_articles_list')
    if not cached_articles:
        db = firestore.client()
        articles_ref = db.collection('articles').order_by('publishedDate', direction=firestore.Query.DESCENDING)
        docs = articles_ref.stream()
        cached_articles = [doc.to_dict() for doc in docs]
        cache.set('cached_articles_list', cached_articles, timeout=3600)  # Cache for 1 hour
    return cached_articles
