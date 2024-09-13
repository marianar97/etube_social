from googleapiclient.discovery import build

youtube = build('youtube', 'v3', developerKey="AIzaSyDtsJ92iKmspU1G1mblmnRjmV1IjLr4LrY")
playlist_id = "PL4cUxeGkcC9gZD-Tvwfod2gaISzfRiP9d"
def a():
    next_page_token = None
    videos = {}
    total_mins  = 0

    while True:
        pl_request = youtube.playlistItems().list(
            part="snippet",
            playlistId=playlist_id,
            maxResults=50  # You can fetch up to 50 items per request
        )

        pl_response = pl_request.execute()
        print(f"pl response: {pl_response}")
        # print(f"pl_response: {len(pl_response)}")

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
                continue
            
            id = video['id']
            # duration = get_video_mins_duration(video['contentDetails']['duration'])
            # videos[id]['duration'] = duration
            iframe_string = video['player']['embedHtml']
            # match = re.search(r'//([a-zA-Z0-9./_-]+)"', iframe_string)
            # src = match.group(1)
            # total_mins += duration    
            # videos[id]['url'] = '//'+src    

        next_page_token = pl_response.get('nextPageToken')
        if not next_page_token:
            break

    return total_mins, videos

def playlist():
    youtube = build('youtube', 'v3', developerKey="AIzaSyDtsJ92iKmspU1G1mblmnRjmV1IjLr4LrY")
    request = youtube.playlists().list(
        part="snippet",
        id="PL4cUxeGkcC9gZD-Tvwfod2gaISzfRiP9d"
    )
    response = request.execute()
    playlist = {}
    playlist_info = response['items'][0]['snippet']
    playlist['title'] = playlist_info['title']
    playlist['img'] = playlist_info['thumbnails']['medium']['url']
    print(playlist)


playlist()