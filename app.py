import re
import flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, current_user, login_required, login_user, logout_user
from random import choice, randint
import os
from datetime import date
from time import time
from website_utilities import onetime_generator, id_generator, get_chunk, reset_short_interactions
from apscheduler.schedulers.background import BackgroundScheduler


app = flask.Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///site.db"
app.config["SECRET_KEY"] = "mCa63F18YGdUb4ZsUhR7Wv52LT3tVgdE"
app.config["VIDEO_UPLOAD_FOLDER"] = "videos"
app.config["CHANNEL_BG_UPLOAD_FOLDER"] = "channel_backgrounds"

db = SQLAlchemy(app)
login_manager = LoginManager(app)


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, unique=True)
    password = db.Column(db.String)
    pass_free_ips = db.Column(db.String, default="")
    short_login = db.Column(db.String, default=onetime_generator())
    referral = db.Column(db.String)
    watched_videos = db.Column(db.String, default="")
    interacted_videos = db.Column(db.String, default="")
    followed_creators = db.Column(db.String, default="")
    telephone_number = db.Column(db.String, default="Not Available")


class PayoutAccount(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    account_type = db.Column(db.String)
    account_information = db.Column(db.String)
    account_owner = db.Column(db.String)


class Channel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    channel_name = db.Column(db.String, unique=True)
    channel_explanation = db.Column(db.String)
    date_joined = db.Column(db.String)
    earnings = db.Column(db.Float, default=0)
    owner = db.Column(db.Integer)
    channel_bg = db.Column(db.String)


class Video(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    poster = db.Column(db.Integer)
    explanation = db.Column(db.String)
    likes = db.Column(db.Integer, default=0)
    comments = db.Column(db.String, default="")
    video_id = db.Column(db.String, unique=True)
    video_path = db.Column(db.String)
    tags = db.Column(db.String, default="")
    date = db.Column(db.String, default=date.today().strftime("%d/%m/%Y"))
    status = db.Column(db.String, default="active")
    short_term_interaction = db.Column(db.Integer, default=0)


class ReportPost(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer)
    reported_by = db.Column(db.Integer)
    reason = db.Column(db.String)


sched = BackgroundScheduler(daemon=True)
sched.add_job(reset_short_interactions, 'interval', minutes=10080)
sched.start()


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)


@app.after_request
def after_request(response):
    response.headers.add('Accept-Ranges', 'bytes')
    return response


@app.before_request
def viewTime():
    pass


@app.route("/")
def index():
    if not current_user.is_authenticated:
        return flask.redirect("/signin")
    return flask.render_template("index.html")


@app.route("/createChannel", methods=["POST", "GET"])
@login_required
def createChannel():
    if current_user.username == "anonymous":
        return flask.redirect("/anonymous")
    if flask.request.method == "POST":
        values = flask.request.values
        channel_bg_pic = flask.request.files["channel_bg"]

        filename = os.path.join(app.config["CHANNEL_BG_UPLOAD_FOLDER"],
                                str(randint(999999, 9999999)) + channel_bg_pic.filename)
        channel_bg_pic.save(filename)

        new_channel = Channel(channel_name=values["channel_name"], channel_explanation=values["channel_description"],
                              channel_bg=filename, date_joined=date.today().strftime("%d/%m/%Y"), owner=current_user.id)

        db.session.add(new_channel)
        db.session.commit()

        return flask.redirect("/")

    return flask.render_template("create_channel.html")


@app.route("/view_anonymous")
def view_anonymous():
    login_user(User.query.filter_by(username="anonymous").first())
    return flask.redirect("/")


@app.route("/view_channel/chnl_id=<channel_name>")
@login_required
def channelView(channel_name):
    channel_id = int(Channel.query.filter_by(channel_name=channel_name).first().id)
    videos = Video.query.filter_by(poster=channel_id).all()

    followed = "Follow"

    if str(channel_id) in current_user.followed_creators.split("&&"):
        followed = "Unfollow"

    return flask.render_template("view_channel.html", videos=videos, channel=Channel.query.get(channel_id),
                                 followed=followed)


@app.route("/signup", methods=["POST", "GET"])
def signUp():
    if flask.request.method == "POST":
        values = flask.request.values
        all_referrals = [i.referral for i in User.query.all()]

        if not values["referral"] in all_referrals:
            flask.abort(403)

        new_user = User(username=values["username"], password=values["password"], referral=id_generator())
        db.session.add(new_user)
        db.session.commit()

        return flask.redirect("/")
    return flask.render_template("register.html")


@app.route("/upload_flow/chnl_id=<channel_id>", methods=["POST", "GET"])
@login_required
def uploadFlow(channel_id):
    if not Channel.query.get(int(channel_id)).owner == current_user.id:
        return flask.redirect("/")
    if flask.request.method == "POST":
        file = flask.request.files["file"]
        filename = str(randint(999999, 9999999)) + file.filename
        file.save(os.path.join(app.config["VIDEO_UPLOAD_FOLDER"], filename))

        new_flow = Video(poster=int(channel_id), video_id=id_generator(size=16),
                         video_path=os.path.join(app.config["VIDEO_UPLOAD_FOLDER"], filename), status="uncompleted")

        db.session.add(new_flow)
        db.session.commit()

        return flask.redirect(f"/proceed_new/id={new_flow.id}")

    return flask.render_template("upload_flow.html")


@app.route("/listUserChannels")
@login_required
def listUserChannels():
    return flask.render_template("channel_list.html", channels=Channel.query.filter_by(owner=current_user.id).all())


@app.route("/proceed_new/id=<flow_id>", methods=["POST", "GET"])
@login_required
def flowProceed(flow_id):
    if flask.request.method == "POST":
        video = Video.query.get(int(flow_id))
        values = flask.request.values

        if not Channel.query.get(int(video.poster)).owner == current_user.id:
            return flask.redirect("/")

        video.explanation = values["description"]
        processed_list = values["description"].split(" ")
        tag_list = []

        for i in processed_list:
            if "#" in i:
                tag_list.append(i)

        video.tags = "&&".join(tag_list)
        video.status = "Active"

        db.session.commit()

        return flask.redirect("/")

    return flask.render_template("finish_flow.html")


@app.route("/signout")
@login_required
def signOut():
    if flask.request.headers.getlist("HTTP_X_FORWARDED_FOR"):
        ip = flask.request.headers.getlist("HTTP_X_FORWARDED_FOR")[0]
    else:
        ip = flask.request.remote_addr

    current_user.pass_free_ips = current_user.pass_free_ips.replace(ip, "")
    db.session.commit()

    logout_user()
    return flask.redirect("/")


@app.route("/profile")
@login_required
def profile():
    user = current_user
    liked_videos = current_user.interacted_videos.split("&&")

    liked_final = []
    for i in liked_videos:
        if not i == "":
            liked_final.append(Video.query.get(int(i)))
    return flask.render_template("profile.html", liked_videos=liked_final, user=user)


@app.route("/signin", methods=["POST", "GET"])
def signIn():
    if flask.request.headers.getlist("HTTP_X_FORWARDED_FOR"):
        ip = flask.request.headers.getlist("HTTP_X_FORWARDED_FOR")[0]
    else:
        ip = flask.request.remote_addr
    for i in User.query.all():
        if ip in i.pass_free_ips.split("&&"):
            login_user(i)
            return flask.redirect("/")

    if flask.request.method == "POST":
        values = flask.request.values
        if len(values["username"]) < 2:
            user = User.query.filter_by(short_login=values["short_login"]).first()
            if user:
                login_user(user)
                user.pass_free_ips += ip + "&&"
                db.session.commit()
                return flask.redirect("/")
        user = User.query.filter_by(username=values["username"]).first()
        if user:
            if user.password == values["password"]:
                login_user(user)
                user.pass_free_ips += ip + "&&"
                db.session.commit()

                return flask.redirect("/")

    return flask.render_template("login.html")


@app.route("/getVideo")
@login_required
def getVideo():

    interacted_videos = []
    trend_videos = []
    followed_videos = []

    ranked_recommendations = {
        "strong_recommendation": [],
        "intermediate_recommendation": [],
        "weak_recommendation": []
    }

    tot_short_interaction = 0

    for i in Video.query.all():
        tot_short_interaction += i.short_term_interaction

    for i in current_user.followed_creators.split("&&"):
        if not i == "":
            followed_videos.append(Video.query.filter_by(poster=int(i)).all())

    for i in current_user.interacted_videos.split("&&"):
        if not i == "":
            for c in Video.query.get(int(i)).tags.split("&&"):
                if not c == "":
                    for t in Video.query.filter(Video.tags.like(f"%{c}%")).all():
                        interacted_videos.append(t)

    for i in Video.query.all():
        if not i == "":
            if i.short_term_interaction > tot_short_interaction / len(Video.query.all()):
                trend_videos.append(i)

    for i in interacted_videos:
        if str(i.id) not in current_user.watched_videos.split("&&") and i.status == "Active":
            if i in followed_videos and i in trend_videos:
                ranked_recommendations["strong_recommendation"].append(i)
            elif i in followed_videos:
                ranked_recommendations["intermediate_recommendation"].append(i)
            elif i in trend_videos:
                ranked_recommendations["intermediate_recommendation"].append(i)
            else:
                ranked_recommendations["weak_recommendation"].append(i)
        else:
            interacted_videos.remove(i)

    final_recs = ranked_recommendations["strong_recommendation"]

    if not len(ranked_recommendations["strong_recommendation"]) > 0:
        final_recs = ranked_recommendations["intermediate_recommendation"]

    if not len(ranked_recommendations["intermediate_recommendation"]) > 0:
        final_recs = ranked_recommendations["weak_recommendation"]

    if len(final_recs) == 0:
        secure_videos = []
        for i in Video.query.all():
            if i.status == "Active":
                secure_videos.append(i)
        recommendation = choice(secure_videos)
    else:
        recommendation = choice(final_recs)

    response = flask.jsonify(
        vid_id=recommendation.id,
        vid_path=recommendation.video_path,
        description=recommendation.explanation,
        channel=Channel.query.get(int(recommendation.poster)).channel_name,
        likes=recommendation.likes,
    )

    if not str(recommendation.id) in current_user.watched_videos.split("&&"):
        current_user.watched_videos += str(recommendation.id) + "&&"
        recommendation.short_term_interaction += 1

        db.session.commit()

    return response


@app.route("/returnFixedVideo/id=<vid_id>")
@login_required
def returnFixedVideo(vid_id):
    vid = Video.query.get(vid_id)
    response = flask.jsonify(
        vid_id=vid.id,
        vid_path=vid.video_path,
        description=vid.explanation,
        channel=Channel.query.get(int(vid.poster)).channel_name,
        likes=vid.likes,
    )

    return response


@app.route("/js/<filename>")
def returnJS(filename):
    return flask.send_file(f"javascript/{filename}")


@app.route("/css/<filename>")
def returnCSS(filename):
    return flask.send_file(f"css/{filename}")


@app.route("/comment/save", methods=["POST", "GET"])
@login_required
def commentSave():
    values = flask.request.values

    video = Video.query.get(int(values["vid_id"]))
    video.comments += current_user.username + ": " + values["comment"] + "&&"

    db.session.commit()

    return "Saved"


@app.route("/returnComments/<vid_id>")
@login_required
def returnComments(vid_id):
    comments = Video.query.get(int(vid_id)).comments.split("&&")
    comments.reverse()
    comments.remove("")
    return flask.render_template("comments.html", comments=comments)


@app.route("/searchReturn", methods=["POST", "GET"])
@login_required
def searchReturn():
    all_tags = []
    if flask.request.values.get("search_term") == "":
        return flask.render_template("searchReturn.html", related_tags=["No Results"])

    for i in Video.query.all():
        for c in i.tags.split("&&"):
            if not c == "":
                all_tags.append(c)

    related_tags = []

    for i in all_tags:
        if flask.request.values["search_term"] in i or i in flask.request.values["search_term"] \
                and i not in related_tags:
            related_tags.append(i)

    return flask.render_template("searchReturn.html", related_tags=related_tags)


@app.route("/search")
@login_required
def search():
    return flask.render_template("search.html")


@app.route("/videos/<video_path>")
@login_required
def hostVideo(video_path):
    range_header = flask.request.headers.get('Range', None)
    byte1, byte2 = 0, None
    if range_header:
        match = re.search(r'(\d+)-(\d*)', range_header)
        groups = match.groups()

        if groups[0]:
            byte1 = int(groups[0])
        if groups[1]:
            byte2 = int(groups[1])
    chunk, start, length, file_size = get_chunk(byte1, byte2, video_path)
    resp = flask.Response(chunk, 206, mimetype='video/mp4',
                          content_type='video/mp4', direct_passthrough=True)
    resp.headers.add('Content-Range', 'bytes {0}-{1}/{2}'.format(start, start + length - 1, file_size))
    return resp


@app.route("/host/profile=<empty>/<img_path>")
@login_required
def hostProfileImage(empty, img_path):
    return flask.send_file("channel_backgrounds/" + img_path.replace(empty, ""))


@app.route("/follow/crt_id=<creator_id>")
@login_required
def followCreator(creator_id):
    if creator_id not in current_user.followed_creators.split("&&"):
        current_user.followed_creators += creator_id + "&&"
    else:
        current_user.followed_creators = current_user.followed_creators.replace(creator_id + "&&", "")

    db.session.commit()
    return flask.redirect("/view_channel/chnl_id=" + creator_id)


@app.route("/saveLike", methods=["POST"])
@login_required
def saveLike():
    values = flask.request.values
    if values["status"] == "like":
        if values["vid_id"] in current_user.interacted_videos.split("&&"):
            return "Cannot Save This"
        current_user.interacted_videos += values["vid_id"] + "&&"
        Video.query.get(int(values["vid_id"])).likes += 1
        db.session.commit()
    elif values["status"] == "cancel":
        if values["vid_id"] not in current_user.interacted_videos.split("&&"):
            return "Cannot Save This"
        current_user.interacted_videos = current_user.interacted_videos.replace(values["vid_id"] + "&&", "")
        Video.query.get(int(values["vid_id"])).likes -= 1
        db.session.commit()

    return "Saved"


@app.route("/view_tag/tag=<tag>")
def viewTag(tag):
    related_videos = []
    for i in Video.query.all():
        if tag.replace("**", "#") in i.tags.split("&&"):
            related_videos.append(i)
    return flask.render_template("tag_view.html", related_videos=related_videos)


@app.errorhandler(403)
def unauthorized(e):
    return flask.render_template("unauthorized.html")
