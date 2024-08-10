from django.contrib.sitemaps import Sitemap
from django.shortcuts import reverse
from .sitemap_functions import get_articles_from_firestore_with_cache  # Adjust import as necessary

class StaticViewSitemap(Sitemap):
    priority = 0.5
    changefreq = 'monthly'

    def items(self):
        return [
            'index', 'privacy_policy', 'terms_of_service', 'pricing'
        ]

    def location(self, item):
        return reverse(item)
    
class FirebaseArticleSitemap(Sitemap):
    changefreq = "daily"
    priority = 0.7

    def items(self):
        # Fetch your articles list from cache
        return get_articles_from_firestore_with_cache()

    def location(self, item):
        # Assuming each item has a 'slug' attribute
        return reverse('article_detail', kwargs={'article_slug': item['slug']})