timer = null;

fixed_video = new URLSearchParams(window.location.search).get("video");

window.vid_id = "1"
window.jsonObject = {}

var index = 0;
function clearAll() {
    const interval_id = window.setInterval(function(){}, Number.MAX_SAFE_INTEGER);

    for (let i = 1; i < interval_id; i++) {
        window.clearInterval(i);
    }

}

function downframe() {
    var element = document.getElementsByClassName("viewbox")[0]

    if(element.scrollTop < window.innerHeight){
        element.style.overflow = "scroll"
        return;
    }

    element.scrollTop -= window.innerHeight;
}

function improvise(){
    timer = setTimeout(function() {
        interval = setInterval(() => {
            downframe()
        }, 1);
    }, 50);
    setInterval(improvise, 200)
}

setInterval(improvise, 200)

var refresh = function () {
        document.getElementsByClassName("viewbox")[0].scrollTop = 0;
};

function changeVid(){
    if(!fixed_video){
        fetch("/getVideo")
          .then(function(response) {
            return response.json();
          })
          .then(function(jsonResponse) {

            window.jsonObject = jsonResponse;
            document.getElementById("video-frame").src = jsonResponse["vid_path"]
            document.getElementById("video-share-input").value = jsonResponse["vid_id"]

            document.getElementById("description").innerHTML = jsonResponse["description"]
            document.getElementById("channel").innerHTML = "@" + jsonResponse["channel"]
            document.getElementById("likes").innerHTML = jsonResponse["likes"]
            document.getElementById("heart-img").className = "far fa-heart"
            window.vid_id = jsonResponse["vid_id"]

          }).then(function(){
            if(index > 1){
                document.getElementById("video-frame").play()
                document.getElementById("video-frame").controls = false
            }
          });
    }else if(fixed_video){
    fetch("/returnFixedVideo/id=" + fixed_video)
          .then(function(response) {
            return response.json();
          })
          .then(function(jsonResponse) {

            window.jsonObject = jsonResponse;
            document.getElementById("video-frame").src = jsonResponse["vid_path"]
            document.getElementById("video-share-input").value = jsonResponse["vid_id"]

            document.getElementById("description").innerHTML = jsonResponse["description"]
            document.getElementById("channel").innerHTML = "@" + jsonResponse["channel"]
            document.getElementById("likes").innerHTML = jsonResponse["likes"]
            document.getElementById("heart-img").className = "far fa-heart"
            window.vid_id = jsonResponse["vid_id"]

          }).then(function(){
            if(index > 1){
                document.getElementById("video-frame").play()
                document.getElementById("video-frame").controls = false
            }
          });
          }
}

window.addEventListener('load', changeVid());

function switchVid(event) {
    if(timer !== null) {
        clearAll();
    }

    clearTimeout(timer);
    timer_scroll_end = setTimeout( refresh , 150 );

    var element = document.getElementsByClassName("viewbox")[0]
    var b = element.scrollTop;


    if(b < window.innerHeight){
        setnext = true
    }

    if(b > window.innerHeight && setnext){
        index += 1;
        setnext = false

        changeVid()
        interval = setInterval(() => {
            downframe()
        }, 1);
        element.style.overflow = "hidden"
    }
}