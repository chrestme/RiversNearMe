from django.conf.urls import patterns, url

from Rivers import views

urlpatterns = patterns('',
    url(r'^$', views.index, name='index'),
    url(r'add_fav/(?P<placemark>\d+)/', views.add_fav),
    url(r'rem_fav/(?P<placemark>\d+)/', views.rem_fav),
    url(r'my_rivers/$', views.my_rivers),
)