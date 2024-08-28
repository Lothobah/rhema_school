from django.contrib.sitemaps import Sitemap
from django.urls import reverse

class StaticViewSitemap(Sitemap):
    priority = 0.5
    changefreq = 'daily'

    def items(self):
        # Only include views that don't require authentication
        return ['home', 'web_home']  # Add any other public views here

    def location(self, item):
        return reverse(item)
