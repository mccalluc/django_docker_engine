from django.conf.urls import include, url

from . import views

urlpatterns = [
    url(r'^$', views.index),
    url(r'^login/$', views.login),
    url(r'^logout/$', views.logout),
    url(r'^launch/$', views.launch),
    url(r'^kill/(.*)$', views.kill),
    url(r'^logs/(.*)$', views.logs),
    url(r'^history/(.*)$', views.history),
    url(r'^upload/(.*)$', views.upload),
    url(r'^docker/', include(__package__ + '.proxy_url_patterns'))
]
