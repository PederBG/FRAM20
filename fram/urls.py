from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('info', views.info, name='info'),
    path('daily', views.daily, name='daily'),
    path('daily/<int:dailyID>', views.read_daily, name='read_daily'),
    path('weekly', views.weekly, name='weekly'),
    path('contact', views.contact, name='contact'),
]
