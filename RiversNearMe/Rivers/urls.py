from django.conf.urls import patterns, url

from Rivers import views

urlpatterns = patterns('',
    url(r'^$', views.index, name='index')
)