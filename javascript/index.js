function copyShareURL() {
  var copyText = document.getElementById("video-share-input");

  alert("URL: " + window.location.href + "?video=" + copyText.value);
}
function commentSave(){
  var xhr = new XMLHttpRequest();
  xhr.open("POST", '/comment/save', true);

  xhr.setRequestHeader("Content-Type", "application/x-www-form-urlencoded");

  xhr.send("vid_id=" + window.vid_id + "&comment=" + document.getElementById('comment_input').value);
  openComments()
}
function openComments(){
document.getElementById("video-frame").pause()

fetch("/returnComments/" + window.vid_id)
  .then(function(response) {
    return response.text();
  }).then(function(responseText) {
    document.getElementById("comment-content-div").innerHTML = responseText
  })
document.getElementById("comments").style.display = "block";
}
function closeComments(){
document.getElementById("video-frame").play()
document.getElementById("comments").style.display = "none";
}
function like(element){
if(element.className == 'far fa-heart'){
  document.getElementById('likes').innerHTML = parseInt(document.getElementById('likes').innerHTML) + 1;
  element.className = 'fas fa-heart'

  var xhr = new XMLHttpRequest();
  xhr.open("POST", '/saveLike', true);

  xhr.setRequestHeader("Content-Type", "application/x-www-form-urlencoded");

  xhr.send("vid_id=" + window.vid_id + "&status=like");
}else{
  document.getElementById('likes').innerHTML = parseInt(document.getElementById('likes').innerHTML) - 1;
  element.className = 'far fa-heart'

  var xhr = new XMLHttpRequest();
  xhr.open("POST", '/saveLike', true);

  xhr.setRequestHeader("Content-Type", "application/x-www-form-urlencoded");
  xhr.send("vid_id=" + window.vid_id + "&status=cancel");
}
}

function muteVideo(video_element){
    video_element.muted = !video_element.muted
}