import re
from django.forms import ValidationError
from django.http import HttpResponse, HttpRequest, JsonResponse
from django.shortcuts import redirect, render, get_object_or_404
from django.forms.models import model_to_dict
from urllib.parse import urlparse, parse_qs
from django.urls import reverse
from googleapiclient.discovery import build
from datetime import timedelta
from .models import Playlist, PlaylistVideo, UserPlaylist, UserPlaylistVideo, Video

def courses_view(request: HttpRequest):
    # return render(request, 'social_network/course.html')
    print(f'in course_view: playlist_id: {request.GET}')
    playlist_id = request.GET.get('playlist_id') 
    if playlist_id != '' and playlist_id is not None:
        return redirect(reverse('course',kwargs={'playlist_id':playlist_id}))
        # return course_view(request, playlist_id)
    return render(request, 'social_network/base.html')

def course_view(request:HttpRequest, playlist_id: str):
    playlist = get_object_or_404(Playlist, pk=playlist_id)
    user_playlist, _ = UserPlaylist.objects.get_or_create(
        user=request.user,
        playlist = playlist
    )

    videos_id = PlaylistVideo.objects.filter(playlist=playlist).order_by('position').values_list('video_id', flat=True)

    id = request.GET.get('v')
    first_video = Video.objects.filter(id=id).first()

    videos = [] 
    for video_id in videos_id:
        video = {}
        video['id'] = video_id
        vd = Video.objects.get(id=video_id)
        video['title'] = vd.title 
        user_playlist_video, _ = UserPlaylistVideo.objects.get_or_create(user_playlist=user_playlist, video=vd)
        video['watched'] = user_playlist_video.watched
        duration = _convert_seconds_to_hms(vd.seconds)
        video['duration'] = _get_video_str_duration(duration)
        video['thumbnail'] = vd.thumbnail
        if not first_video and user_playlist_video.watched==False:
            first_video = vd
        videos.append(video)
    
    playlist = model_to_dict(playlist)
    playlist['percent_completed'] = int(user_playlist.percent_completed * 100)
    context = {'playlist': playlist, 'videos': videos, 'current_video': first_video}
    return render(request, 'social_network/course.html', context)


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

def video_watched(request: HttpResponse) -> JsonResponse:
    video_id = request.POST.get('videoId')
    playlist_id = request.POST.get('playlistId')

    playlist = Playlist.objects.filter(id=playlist_id).first()
    if not playlist:
        response_data = {
            'status': 404,
            'message': f'Playlist not found: {playlist_id}',
        }
        return JsonResponse(response_data)
    
    video = Video.objects.filter(id=video_id).first()
    if not video:
        response_data = {
            'status': 404,
            'message': f'Video not found: {video_id}',
        }
        return JsonResponse(response_data)
    
    user_playlist = UserPlaylist.objects.filter(user=request.user, playlist=playlist).first()
    if not user_playlist:
        response_data = {
            'status': 404,
            'message': f'User does not have course: {playlist_id}',
        }
        return JsonResponse(response_data)       

    user_playlist_video = UserPlaylistVideo.objects.filter(user_playlist=user_playlist, video=video).first()
    user_playlist_video.watched = True
    user_playlist_video.save()

    num_videos = playlist.num_videos
    num_watched_videos = UserPlaylistVideo.objects.filter(user_playlist=user_playlist, watched=True).count()
    percentage_watched = num_watched_videos/num_videos
    user_playlist.percent_completed = percentage_watched
    user_playlist.save()

    response_data = {
        'status': 200,
        'message': 'Video updated as watched',
        'videoId': video_id,
        'playlistId': playlist_id,
        'perc_completed': int(percentage_watched*100)
    }
    return JsonResponse(response_data)

def _get_playlist_info(request: HttpRequest, id: str) -> dict:
    playlist = Playlist.objects.filter(id=id).first()
    if playlist: #if playlist in database return
        playlist = model_to_dict(playlist)
        seconds = playlist['seconds']
    else:
        youtube = build('youtube', 'v3', developerKey="")
        playlist = _get_playlist_details(id, youtube)
        num_videos, seconds , videos = _get_playlist_videos_and_duration(id, youtube)
        playlist['num_videos'] = num_videos
        playlist['seconds'] = seconds
        _save_playlist_and_videos(playlist, videos)
    
    duration = _convert_seconds_to_hms(seconds)
    str_duration = _get_video_str_duration(duration)
    playlist['duration'] = str_duration
    return playlist

def _get_video_str_duration(duration: tuple):
    hour, minutes, seconds = duration
    str_duration = ""
    if hour > 0:
        str_duration += f'{hour}'
    if minutes > 0:
        if hour > 0:
            str_duration += f':'
        str_duration += f'{minutes}'
    if seconds > 0:
        if minutes > 0:
            str_duration += f':'
        str_duration += f'{seconds}'
    return str_duration

def _save_playlist_and_videos(playlist: dict , videos: dict) -> None:
    pl = Playlist(
        id= playlist['id'],
        seconds = playlist['seconds'],
        title = playlist['title'],
        thumbnail = playlist['thumbnail'],
        num_videos = playlist['num_videos'],
        channel_title = playlist['channel_title']
    )
    pl.save()

    for video_id, video_info in videos.items():
        video, _ = Video.objects.get_or_create(
            id = video_id,
            title = video_info['title'],
            seconds = video_info['duration'],
            thumbnail = video_info['thumbnail'],
            url = video_info['url'],
        )
        # video.playlist.add(pl)
        PlaylistVideo.objects.create(playlist=pl, video=video, position=video_info['position'])
        video.save()

def _get_str_duration(duration: tuple):
    hours, mins, secs = duration
    dur = ""
    if hours > 0:
        dur += f'{int(hours)} hours'
    if mins > 0:
        dur += f"{int(mins)} minutes"
    if secs > 0:
        dur += f"{int(secs)} seconds"
    return dur

def _get_playlist_details(playlist_id: str, youtube) -> dict:
    request = youtube.playlists().list(
        part="snippet",
        id=playlist_id
    )
    response = request.execute()
    playlist = {'id': playlist_id}
    playlist_info = response['items'][0]['snippet']
    playlist['title'] = playlist_info['title']
    playlist['thumbnail'] = playlist_info['thumbnails']['medium']['url']
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
            video['thumbnail'] = item['snippet']['thumbnails']['medium']['url']
            video['playlist_id'] = playlist_id
            id_video = item['snippet']['resourceId']['videoId']
            videos[id_video] = video
            ids.append(id_video)
                
        vid_request = youtube.videos().list(
                part="contentDetails, player",
                id=",".join(ids)
        )

        vid_response = vid_request.execute()
        for i, video in enumerate(vid_response['items']):
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
            videos[id]['position'] = i
            

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