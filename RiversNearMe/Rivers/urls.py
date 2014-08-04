from django.conf.urls import patterns, url

from Rivers import views

urlpatterns = patterns('',
    url(r'^$', views.index, name='index'),
    url(r'/add_fav/', views.add_fav),
)