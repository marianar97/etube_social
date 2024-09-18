from django.urls import path
from . import views

urlpatterns = [
    path('playlist_length', views.playlist_length_view, name="playlist-length"),
    path('login', views.login_view, name='login'),
    path('', views.courses_view, name='courses'),
    path('course/<str:playlist_id>', views.course_view, name='course'),
    path('video-watched', views.video_watched, name='video-watched'),
    path('courses', views.courses_view, name='courses'),
    path("logout", views.logout_view, name="logout"),
]