from django.contrib.sitemaps import Sitemap
from django.shortcuts import reverse

class StaticViewSitemap(Sitemap):
    priority = 0.5
    changefreq = 'monthly'

    def items(self):
        # List the names of your Django views here
        return [
            'index', 'signup', 'login', 'forgot_password',
            'change_email', 'privacy_policy', 'terms_of_service',
            'contact', 'graphic_builder', 'dashboard', 'schedule',
            'ad_manager', 'post_creator', 'brand_settings', 'library',
            'callback', 'add_graphics', 'master_switch', 'all_auth',
            'checkout', 'stripe_webhook', 'success', 'cancel',
            'download', 'start_chat', 'get_chat', 'clear_chat',
            'unlink', 'logout_view', 'process_page_selection', 'get_articles', 'pricing', 'article_detail'
        ]

    def location(self, item):
        return reverse(item)