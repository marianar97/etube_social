import re
from django.forms import ValidationError
from django.http import HttpResponse, HttpRequest
from django.shortcuts import render
from django.forms.models import model_to_dict
from urllib.parse import urlparse, parse_qs
from googleapiclient.discovery import build
from datetime import timedelta
from .models import Playlist, Video

def courses_view(request: HttpRequest):
    # return render(request, 'social_network/course.html')
    # print(f'playlist_id: {request.GET}')
    return render(request, 'social_network/base.html')

# Create your views here.
def login_view(request: HttpRequest):
    return render(request, 'social_network/login.html')

def playlist_length_view(request: HttpRequest):
    if request.method == "GET":
        return render(request, 'social_network/playlist_length.html')
    
    context = {"post": True}
    if request.method == "POST":
        if not 'playlist_id' in request.POST:
            context['message'] = 'Please enter a playlist identifier'
            return render(request, 'social_network/playlist_length.html', context)
        else:
            playlist_input = request.POST['playlist_id']
            id = _get_playlsit_id(playlist_input)
            if not id:
                context['message'] = 'Enter a valid Youtube url'
                return render(request, 'social_network/playlist_length.html', context)
            return _playlists_details_view(request, id)
    
def _playlists_details_view(request: HttpResponse, id:str ):
    playlist_details = _get_playlist_info(request, id)
    print(f'playlist details: {playlist_details}')
    return render(request, 'social_network/playlist_length.html', {'post': True, 'playlist': playlist_details})


def _get_playlist_info(request: HttpRequest, id: str) -> dict:
    playlist = Playlist.objects.get(id=id)
    if playlist: #if playlist in database return
        print(f'playlist exists: {playlist}')
        return model_to_dict(playlist)

    youtube = build('youtube', 'v3', developerKey="")
    playlist = _get_playlist_details(id, youtube)
    num_videos, seconds , videos = _get_playlist_videos_and_duration(id, youtube)
    duration = _convert_seconds_to_hms(seconds)
    str_duration = _get_str_duration(duration)
    playlist['num_videos'] = num_videos
    playlist['duration'] = str_duration
    playlist['seconds'] = seconds
    _save_playlist_and_videos(request, playlist, videos)
    return playlist

def _save_playlist_and_videos(request: HttpRequest, playlist: dict , videos: dict) -> None:
    pl = Playlist(
        id= playlist['playlist_id'],
        seconds = playlist['seconds'],
        title = playlist['title'],
        thumbnail = playlist['img'],
        num_videos = playlist['num_videos']
    )
    pl.save()

    for video_id, video_info in videos.items():
        vd = Video (
            id = video_id,
            playlist = pl,
            title = video_info['title'],
            seconds = video_info['duration'],
            thumbnail = video_info['thumbnail'],
            url = video_info['url']
        )
        vd.save()

def _get_str_duration(duration: tuple):
    hours, mins, secs = duration
    dur = ""
    if hours > 0:
        dur += f'{int(hours)} hours'
    if mins > 0:
        if hours > 0:
            dur += f", {int(mins)} minutes"
        else:
            dur += f"{int(mins)} minutes"
    if secs > 0:
        if mins > 0 or hours > 0:
            dur += f", {int(secs)} seconds"
        else:
            dur += f"{int(secs)} seconds"
    return dur

def _get_playlist_details(playlist_id: str, youtube) -> dict:
    request = youtube.playlists().list(
        part="snippet",
        id=playlist_id
    )
    response = request.execute()
    playlist = {'playlist_id': playlist_id}
    playlist_info = response['items'][0]['snippet']
    playlist['title'] = playlist_info['title']
    playlist['img'] = playlist_info['thumbnails']['medium']['url']
    playlist['channel_title'] = playlist_info['channelTitle']
    return playlist

def _get_playlist_videos_and_duration(playlist_id: str, youtube):
    next_page_token = None
    videos = {}
    seconds  = 0
    num_videos = 0

    while True:
        pl_request = youtube.playlistItems().list(
            part="snippet",
            playlistId=playlist_id,
            maxResults=50  # You can fetch up to 50 items per request
        )

        pl_response = pl_request.execute()
        # print(f"pl_response: {len(pl_response)}")

        num_videos += len(pl_response['items'])
        ids = []
        for item in pl_response['items']:
            # print(f"item: {item}")
            video = {}
            video['title'] = item['snippet']['title']
            # video['description'] = item['snippet']['description']
            video['thumbnail'] = item['snippet']['thumbnails']

            video['playlist_id'] = playlist_id
            id_video = item['snippet']['resourceId']['videoId']
            videos[id_video] = video
            ids.append(id_video)
                
        vid_request = youtube.videos().list(
                part="contentDetails, player",
                id=",".join(ids)
        )

        vid_response = vid_request.execute()
        for video in vid_response['items']:
            if video['id'] not in videos:
                continue # if video not in the playlist 
            
            id = video['id']
            duration = _get_video_secs_duration(video['contentDetails']['duration'])
            videos[id]['duration'] = duration
            iframe_string = video['player']['embedHtml']
            match = re.search(r'//([a-zA-Z0-9./_-]+)"', iframe_string)
            src = match.group(1)
            seconds += duration    
            videos[id]['url'] = '//'+src    

        next_page_token = pl_response.get('nextPageToken')
        if not next_page_token:
            break
    
    return num_videos, seconds, videos

def _convert_seconds_to_hms(total_seconds: int):
    # Calculate hours
    hours = total_seconds // 3600
    
    # Calculate remaining seconds after extracting hours
    remaining_seconds = total_seconds % 3600
    
    # Calculate minutes from remaining seconds
    minutes = remaining_seconds // 60
    
    # Calculate remaining seconds after extracting minutes
    seconds = remaining_seconds % 60
    
    return hours, minutes, seconds


def _get_video_secs_duration(duration: str) -> int:
    hours_pattern = re.compile(r'(\d+)H')
    minutes_pattern = re.compile(r'(\d+)M')
    seconds_pattern = re.compile(r'(\d+)S')

    hours = hours_pattern.search(duration)
    minutes = minutes_pattern.search(duration)
    seconds = seconds_pattern.search(duration)

    hours = int(hours.group(1)) if hours else 0
    minutes = int(minutes.group(1)) if minutes else 0
    seconds = int(seconds.group(1) if seconds else 0)

    total_seconds = timedelta(
        hours = hours,
        minutes = minutes,
        seconds = seconds
    ).total_seconds()

    return total_seconds

def _get_youtube_id(url:str):
    # Parse the URL
    parsed_url = urlparse(url)
    
    # Parse the query string
    query_params = parse_qs(parsed_url.query)
    
    # Get the value of the 'list' parameter
    list_id = query_params.get('list')
    
    # Return the first item if the 'list' parameter exists, else return None
    if list_id:
        return list_id[0]
    return None

def _get_playlsit_id(playlist_input: str):
    if not _is_valid_youtube_url(playlist_input):
        return None
    id = _get_youtube_id(playlist_input)
    return id

def _is_valid_youtube_url(url):
    # Define a regular expression pattern for YouTube URLs
    youtube_regex = (
        r'^(https?\:\/\/)?(www\.youtube\.com|youtu\.?be)\/.+$'
    )
    # Use the re.match function to check if the URL matches the pattern
    if not re.match(youtube_regex, url):
        return False

    return True