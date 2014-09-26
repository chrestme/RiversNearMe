from django.conf.urls import patterns, include, url

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    url(r'^$', 'Rivers.views.index', name='home'),
    # url(r'^blog/', include('blog.urls')),
    url(r'^rivers/', include('Rivers.urls')),
    url(r'^admin/', include(admin.site.urls)),
    url(r"^accounts/", include('registration.backends.simple.urls')),
    url(r"^accounts/login/$", 'django.contrib.auth.views.login'),
    url(r"^accounts/logout/$", 'django.contrib.auth.views.logout'),
    url(r"^accounts/password_change/$", 'django.contrib.auth.views.password_change', {'post_change_redirect': '/'}),
    url(r'^weblog/', include('zinnia.urls')),
    url(r'^comments/', include('django.contrib.comments.urls')),
)
