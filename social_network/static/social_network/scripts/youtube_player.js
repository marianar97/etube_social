// 2. This code loads the IFrame Player API code asynchronously.
var tag = document.createElement('script');

tag.src = "https://www.youtube.com/iframe_api";
var firstScriptTag = document.getElementsByTagName('script')[0];
firstScriptTag.parentNode.insertBefore(tag, firstScriptTag);

// 3. This function creates an <iframe> (and YouTube player)
//    after the API code downloads.
var player;
var intervalId;
let vidId;
let idValue; 
let courseId;
let sentVideoWatched = false;

function onYouTubeIframeAPIReady() {
    vidId = document.getElementById("video-id");
    idValue = vidId.getAttribute("videoId");
    player = new YT.Player('player', {
    height: '770',
    width: '1350',
    videoId: idValue,
    playerVars: {
        'playsinline': 1
    },
    events: {
        'onReady': onPlayerReady,
        'onStateChange': onPlayerStateChange
    }
    });
}

// 4. The API will call this function when the video player is ready.
function onPlayerReady(event) {
    event.target.playVideo();
}

// 5. The API calls this function when the player's state changes.
//    The function indicates that when playing a video (state=1),
//    the player should play for six seconds and then stop.
var done = false;

function onPlayerStateChange(event) {
    // if (event.data == YT.PlayerState.PLAYING && !done) {
    //     setTimeout(stopVideo, 6000);
    //     done = true;
    // }

    // Check if the video is playing (state=1)
    if (event.data == YT.PlayerState.PLAYING) {
        // If we haven't already started our interval
        if (!intervalId) {
            // Start an interval to log the current time every 3 seconds
            intervalId = setInterval(function() {
                if (isWatched() == true){
                    document.getElementById(idValue).style.backgroundColor = "rgb(67, 152, 67)";
                    if (sentVideoWatched === false) {
                        sendWatchedVideo();
                    } else {
                        console.log("sent watched video is true")
                    }
                }
            }, 3000); // 3000 milliseconds = 3 seconds
        }
    } else {
        // If the video is not playing and the interval has been set, clear it
        if (intervalId) {
            clearInterval(intervalId);
            intervalId = null; // Clear the interval ID
        }
    }
}

function isWatched(){
    let total_mins = vidId.getAttribute("mins");
    cur = player.getCurrentTime();
    tot_percentage = cur / (total_mins * 60);
    if (tot_percentage > .9) {
        return true;
    } else{
        return false;
    }
}

function sendWatchedVideo(){
    console.log("sending video as watched")
    crsfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');
    vidId = document.getElementById("video-id");
    courseId = vidId.getAttribute("courseId");

    let xhr = new XMLHttpRequest();
    xhr.open("POST", '/video-watched', true);
    xhr.setRequestHeader("Content-Type", "application/x-www-form-urlencoded");  // Set the content type of the request
    xhr.setRequestHeader('X-CSRFToken', crsfToken); 

    xhr.onreadystatechange = function() {
        if (xhr.readyState !== 4) return
        const obj = JSON.parse(this.responseText); 
        document.getElementById("perc_completed").innerHTML = obj.perc_completed;
    }

    xhr.send("videoId=" + encodeURIComponent(idValue) + "&courseId=" + encodeURIComponent(courseId));
    sentVideoWatched = true;

}