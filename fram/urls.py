from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('map', views.map, name='map'),
    path('info', views.info, name='info'),
    path('daily', views.daily, name='daily'),
    path('daily/<int:dailyID>', views.read_daily, name='read_daily'),
    path('weekly', views.weekly, name='weekly'),
    path('links', views.links, name='links'),
    path('contact', views.contact, name='contact'),
    path('cookiepolicy', views.cookiepolicy, name='cookiepolicy'),
]
