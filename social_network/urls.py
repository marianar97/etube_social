from django.urls import path
from . import views

urlpatterns = [
    path('', views.playlist_length_view, name="playlist-length"),
    path('login', views.login_view, name='login')
]