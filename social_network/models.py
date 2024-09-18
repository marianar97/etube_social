from django.db import models
from django.contrib.auth.models import User

class Playlist(models.Model):
    id = models.CharField(primary_key=True, max_length=300)
    seconds = models.PositiveIntegerField()
    title = models.CharField(max_length=200)
    thumbnail =  models.CharField(max_length=300)
    num_videos = models.IntegerField(default=0)
    channel_title = models.CharField(max_length=255)
    description = models.TextField(default="")

    def __str__(self):
        return f"id={self.id}, title={self.title}"
    

class Video(models.Model):
    id = models.CharField(primary_key=True, max_length=300)
    playlist = models.ManyToManyField(Playlist, through="PlaylistVideo")
    title = models.CharField(max_length=255)
    seconds = models.IntegerField()
    thumbnail = models.CharField(max_length=300)
    url = models.CharField(max_length=300)

    def __str__(self):
        return f"id={self.id}, title={self.title}"
    
class PlaylistVideo(models.Model):
    playlist = models.ForeignKey(Playlist, on_delete=models.CASCADE)
    video = models.ForeignKey(Video, on_delete=models.CASCADE)
    position = models.IntegerField()

    def __str__(self):
        return f"{self.playlist} - {self.video} position {self.position}"

class UserPlaylist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    playlist = models.ForeignKey(Playlist, on_delete=models.CASCADE)
    percent_completed = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.user.username} - {self.playlist.title}"


class UserPlaylistVideo(models.Model):
    user_playlist = models.ForeignKey(UserPlaylist, on_delete=models.CASCADE)
    video = models.ForeignKey(Video, on_delete=models.CASCADE)
    watched = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user_playlist.user.username} - {self.video.title} - {'Watched' if self.watched else 'Not Watched'}"
