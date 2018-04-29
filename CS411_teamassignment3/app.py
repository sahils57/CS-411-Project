from __future__ import print_function, unicode_literals
from flask import Flask, render_template, request, redirect, flash, url_for
import oauth2 as oauth
import urlparse
import urllib
import json
from data import Articles
import twitter
import webbrowser
import pyrebase
import pytumblr
from html.parser import HTMLParser
from datetime import datetime, date, timedelta
from tumblpy import Tumblpy

app = Flask(__name__)
config = {
    "apiKey": "AIzaSyC9Lgc_qAajV-HzLR0Rjc38ZlZx6Yi4Srg",
    "authDomain": "cs411-webapp.firebaseapp.com",
    "databaseURL": "https://cs411-webapp.firebaseio.com",
    "storageBucket": "cs411-webapp.appspot.com"
}
firebase = pyrebase.initialize_app(config)
db = firebase.database()
auth = firebase.auth()

username = ""

class MLStripper(HTMLParser):
    def __init__(self):
        self.reset()
        self.strict = False
        self.convert_charrefs= True
        self.fed = []
    def handle_data(self, d):
        self.fed.append(d)
    def get_data(self):
        return ''.join(self.fed)

def strip_tags(html):
    s = MLStripper()
    s.feed(html)
    return s.get_data()

#twitter stuff
#------------------------------------------------------
twitter_consumer_key = 'WH3jhSuTMRA3ESj8xInLEsiLe'
twitter_consumer_secret = 'c2hPnRpVbv8yudyepiPzZ9ihBbYw6EsnevNDqdi3XnSt3HZH51'
#------------------------------------------------------
request_token_url = 'https://twitter.com/oauth/request_token'
access_token_url = 'https://twitter.com/oauth/access_token'
authorize_url = 'https://twitter.com/oauth/authorize'
show_user_url = 'https://api.twitter.com/1.1/users/show.json'
#------------------------------------------------------
oauth_store = {}
#------------------------------------------------------

# Check to see if the tweet contains a youtube video
def checkYoutubeTweet(x):
    yt_test = str(x.urls[0].expanded_url)
    yt_test = yt_test.split("/")
    if yt_test[2] == "youtu.be" or yt_test[2] == "youtube":
        return True
    else:
        return False

# Get a youtube URL from the url provided from twitter
def generateYoutubeURL(x):         # from a json object
    yt_test = str(x.urls[0].expanded_url)
    yt_test = yt_test.split("/")
    yt_url = yt_test[-1]
    yt_url = "https://www.youtube.com/embed/" + yt_url
    return yt_url

# Format twitter date to match tumblr date
def formatTimeTwitter(twitter_date):
    final_date = datetime.strptime(twitter_date, '%a %b %d %H:%M:%S +0000 %Y')
    fourhourdifference = final_date + timedelta(hours=-4)
    return fourhourdifference

# Format tumblr date to match twitter date
def formatTimeTumblr(tumblr_date):
    final_date = datetime.strptime(tumblr_date, '%Y-%m-%d %H:%M:%S GMT')
    fourhourdifference = final_date + timedelta(hours=-4)
    return fourhourdifference

# Generates a list of i tweets
def generateTweets(i):
    access_token = db.child(username).child("twitter").child("access_token").get().val()
    access_secret = db.child(username).child("twitter").child("access_secret").get().val()

    api = twitter.Api(twitter_consumer_key, twitter_consumer_secret, access_token, access_secret, tweet_mode="extended")

    timeline = []

    a = api.GetHomeTimeline(count=(i*2), contributor_details = True)
    #retweet vs tweet main loop
    for x in range(i):
        if a[x].retweeted_status == None:
            timeline += [["twitter", "none", "not_retweeted", a[x].full_text, a[x].user.screen_name, formatTimeTwitter(a[x].created_at), a[x].user.profile_image_url]]
        else:
            timeline += [["twitter", "re_none", a[x].retweeted_status.user.screen_name, a[x].retweeted_status.full_text, a[x].user.screen_name, formatTimeTwitter(a[x].created_at), a[x].user.profile_image_url]]

    # media in tweet hosted on twitter
    for z in range(i):
        if a[z].retweeted_status == None:
            if a[z].media != None:
                if a[z].media[0].type == "animated_gif":
                    timeline[z][1] = "gif"
                    timeline[z] += [a[z].media[0].video_info['variants'][0]['url']]
                elif a[z].media[0].type == "video":
                    timeline[z][1] = "video"
                    for j in range(4):
                        if a[z].media[0].video_info['variants'][j]['content_type'] == "video/mp4":
                            timeline[z] += [a[z].media[0].video_info['variants'][j]['url']]
                            break
                        else:
                            continue
                        timeline[z][1] = "none"
                elif a[z].media[0].type == "photo":
                    timeline[z][1] = "photo"
                    timeline[z] += [a[z].media[0].media_url_https]
        else:
            if a[z].retweeted_status.media != None:
                if a[z].retweeted_status.media[0].type == "animated_gif":
                    timeline[z][1] = "re_gif"
                    timeline[z] += [a[z].retweeted_status.media[0].video_info['variants'][0]['url']]
                elif a[z].retweeted_status.media[0].type == "video":
                    timeline[z][1] = "re_video"
                    for j in range(4):
                        if a[z].retweeted_status.media[0].video_info['variants'][j]['content_type'] == "video/mp4":
                            timeline[z] += [a[z].retweeted_status.media[0].video_info['variants'][j]['url']]
                            break
                        else:
                            continue
                            timeline[z][1] = "re_none"
                elif a[z].retweeted_status.media[0].type == "photo":
                    timeline[z][1] = "re_photo"
                    timeline[z] += [a[z].retweeted_status.media[0].media_url_https]

    # link in tweet text
    for y in range(i):
        if timeline[y][1] == "none" or timeline[y][1] == "re_none":
            if a[y].urls != []:
                if checkYoutubeTweet(a[y]):
                    timeline[y][1] = "youtube"
                    timeline[y] += [generateYoutubeURL(a[y])]
                else:
                    timeline[y][1] = "link"
                    timeline[y] += [a[y].urls[0].expanded_url]
    return timeline

# For assignment 3, search our api results
def searchApi(keyword):
    result = [[i.text, i.user.screen_name] for i in a if keyword.lower() in i.text.lower() or keyword.lower() in i.user.screen_name.lower()]
    return result

#---------------------------------------------------
#                                                  #
#        T U M B L R   S E C T I O N               #
#                                                  #
#---------------------------------------------------
# CONFIG KEYS
tumblr_consumer_key = "EjlO747baBilTHKKbtKEg51o336I6kI0TfCD6wH2EumepSok8d"
tumblr_consumer_secret = "RWMh1eoWxu8tf6jinPUfucTTrmyJzsKGMZqjjrgQREvDPKsFc0"

OAUTH_TOKEN_SECRET = ""

# Generates i tumblr posts
def generate_tumblr_dashboard(i):

    access_token = db.child(username).child("tumblr").child("access_token").get().val()
    access_secret = db.child(username).child("tumblr").child("access_secret").get().val()

    client = pytumblr.TumblrRestClient(tumblr_consumer_key,
        tumblr_consumer_secret, access_token, access_secret)
    dash = client.dashboard(limit=50)
    dashboard = [[] for x in range(i)]
    counter = 0

    for post in dash['posts']:
        if post['type'] == "text":
            if counter == (i):
                break
            dashboard[counter] += ['tumblr']
            dashboard[counter] += ['text'] #keep track of what type
            dashboard[counter] += [post['blog_name']]
            dashboard[counter] += [formatTimeTumblr(post['date'])]
            dashboard[counter] += [post['post_url']]
            dashboard[counter] += [strip_tags(post['body'])] #keep track of the info
            counter += 1
        elif post['type'] == 'photo':
            if counter == (i):
                break
            dashboard[counter] += ['tumblr']
            dashboard[counter] += ['photo'] #keep track of what type
            dashboard[counter] += [post['blog_name']]
            dashboard[counter] += [formatTimeTumblr(post['date'])]
            dashboard[counter] += [post['post_url']]
            dashboard[counter] += [post['photos'][0]['original_size']['url']] #keep track of the info
            counter += 1
        elif post['type'] == 'video':
            if counter == (i):
                break
            dashboard[counter] += ['tumblr']
            dashboard[counter] += ['video'] #keep track of what type
            dashboard[counter] += [post['blog_name']]
            dashboard[counter] += [formatTimeTumblr(post['date'])]
            dashboard[counter] += [post['post_url']]
            dashboard[counter] += [post['video_url']] #keep track of the info
            counter += 1
    return dashboard

# Generate a feed containing i items
def generateFeed(i, twitter_bool, tumblr_bool):
    if twitter_bool == "True" and tumblr_bool == "True":
        feed = []
        twitter_feed = generateTweets(i/2+1)
        twitter_feed.reverse()
        tumblr_feed = generate_tumblr_dashboard(i/2+1)
        tumblr_feed.reverse()
        for j in range(i):
            if j%2==0:
                feed += [twitter_feed[-1]]
                twitter_feed.pop()
            else:
                feed += [tumblr_feed[-1]]
                tumblr_feed.pop()
        return feed
    elif twitter_bool == "True" and tumblr_bool != "True":
        return generateTweets(i)
    elif twitter_bool != "True" and tumblr_bool == "True":
        return generate_tumblr_dashboard(i)
    else:
        return []

# Register a user in database
def register_user(email, password):
    auth.create_user_with_email_and_password(email, password)

    data = {
        "email": email
    }
    db.child("Users").push(data)

# Check to see if user is in database
def check_user(email):
    users = db.child("Users").get()
    if (users.val() == None):
        return False
    for user in users.each():
        if user.val().get('email') == email:
            return True
    return False

@app.route('/', methods=['GET', 'POST'])
def index():
    return render_template('login.html')

@app.route('/logout')
def logout():
    global username
    username = ""
    return render_template('login.html')

@app.route('/echo',  methods=['POST'])
def login_input():
    email = request.form['email']
    password = request.form['password']
    if check_user(email):
        try:
            user = auth.sign_in_with_email_and_password(email, password)
        except Exception as e:
            return render_template('login.html', error = "wrong_pass")

        global username
        username = user['email'].replace(".", "")
        return redirect(url_for('home'))
    else:
        try:
            register_user(email, password)
        except Exception as e:
            return render_template('login.html', error = "short_pass")

        db.child(email.replace(".", "")).child("settings").child("twitter_boolean").set("False")
        db.child(email.replace(".", "")).child("settings").child("tumblr_boolean").set("False")
        return render_template('login.html', error = "new_acc")

@app.route('/home')
def home():
    if username == "":
        return render_template('login.html')
    else:
        status = [db.child(username).child("settings").child("twitter_boolean").get().val(), db.child(username).child("settings").child("tumblr_boolean").get().val()]
        home_timeline = generateFeed(20, status[0], status[1])
        return render_template('home.html', tweets = home_timeline)

@app.route('/about')
def about():
    if username == "":
        return render_template('login.html')
    else:
        return render_template('about.html')

@app.route('/articles')
def articles():
    if username == "":
        return render_template('login.html')
    else:
        return render_template('articles.html', articles=Articles)

@app.route('/article/<string:id>')
def article(id):
    return render_template('article.html', id = id, tweets = home_timeline)

@app.route('/settings')
def settings():
    if username == "":
        return render_template('login.html')
    else:
        status = [db.child(username).child("settings").child("twitter_boolean").get().val(), db.child(username).child("settings").child("tumblr_boolean").get().val()]
        return render_template('settings.html', status = status)

@app.route('/twitter/echo', methods=['POST'])
def user_input():
    foo = request.form['input']
    if foo == "user":
        return redirect('/twitter/usertimeline')
    elif foo == "home":
        return redirect('/twitter/hometimeline')
    elif foo == "following":
        return redirect('/twitter/following')
    else:
        x = searchApi(foo)
        return render_template('search_results.html', results = x)

@app.route('/authorize/twitter', methods=['GET', 'POST'])
def auth_tw():
    consumer = oauth.Consumer(twitter_consumer_key, twitter_consumer_secret)
    request_token_url = request_token_url
    client = oauth.Client(consumer)

    app_callback_url = url_for('callback', _external = True)

    resp, content = client.request(request_token_url, "POST", body=urllib.urlencode({"oauth_callback": app_callback_url}))

    if resp['status'] != '200':
        error_message = "Invalid response %s" % resp['status']
        return render_template('error.html', error_message = error_message)

    request_token = dict(urlparse.parse_qsl(content))
    oauth_token = request_token['oauth_token']
    oauth_token_secret = request_token['oauth_token_secret']

    oauth_store[oauth_token] = oauth_token_secret

    return render_template('start.html', authorize_url=authorize_url, oauth_token = oauth_token)


@app.route('/callback')
def callback():
    oauth_token = request.args.get('oauth_token')
    oauth_verifier = request.args.get('oauth_verifier')
    oauth_denied = request.args.get('denied')

    if oauth_denied:
        if oauth_denied in oauth_store:
            del oauth_store[oauth_denied]
        return render_template('error.html', error_message="OAuth request denied by this user")

    if not oauth_token or not oauth_verifier:
        return render_template('error.html', error_message="callback param(s) missing")

    if oauth_token not in oauth_store:
        return render_template('error.html', error_message="oauth_token not found locally")


    oauth_token_secret = oauth_store[oauth_token]

    consumer = oauth.Consumer(twitter_consumer_key, twitter_consumer_secret)
    token = oauth.Token(oauth_token, oauth_token_secret)
    token.set_verifier(oauth_verifier)
    client = oauth.Client(consumer, token)

    resp, content = client.request(access_token_url, "POST")
    access_token = dict(urlparse.parse_qsl(content))

    user_id = access_token['user_id']

    db.child(username).child("settings").child("twitter_boolean").set("True")

    real_oauth_token = access_token['oauth_token']
    real_oauth_token_secret = access_token['oauth_token_secret']

    db.child(username).child("twitter").child("access_token").set(real_oauth_token)
    db.child(username).child("twitter").child("access_secret").set(real_oauth_token_secret)

    real_token = oauth.Token(real_oauth_token, real_oauth_token_secret)
    real_client = oauth.Client(consumer, real_token)
    real_resp, real_content = real_client.request(show_user_url + '?user_id=' + user_id, "GET")

    if real_resp['status'] != '200':
        error_message = "Invalid response from twitter: " + real_resp['status']
        return render_template('error.html', error_message=error_message)

    del oauth_store[oauth_token]


    return redirect(url_for("settings"))


@app.route('/authorize/tumblr', methods=['GET', 'POST'])
def auth_tumblr():
    t = Tumblpy(tumblr_consumer_key, tumblr_consumer_secret)

    auth_props = t.get_authentication_tokens(callback_url= "http://localhost:5000/callbacktumblr")
    auth_url = auth_props['auth_url']
    global OAUTH_TOKEN_SECRET
    OAUTH_TOKEN_SECRET = auth_props['oauth_token_secret']

    return redirect(auth_url)

@app.route('/callbacktumblr')
def callback_tumblr():
    oauth_verifier = request.args.get('oauth_verifier')
    t = Tumblpy(tumblr_consumer_key, tumblr_consumer_secret,
            oauth_token, OAUTH_TOKEN_SECRET)
    authorized_tokens = t.get_authorized_tokens(oauth_verifier)

    final_oauth_token = authorized_tokens['oauth_token']
    final_oauth_token_secret = authorized_tokens['oauth_token_secret']

    db.child(username).child("settings").child("tumblr_boolean").set("True")

    db.child(username).child("tumblr").child("access_token").set(final_oauth_token)
    db.child(username).child("tumblr").child("access_secret").set(final_oauth_token_secret)

    return redirect(url_for('settings'))

@app.route("/settings/twitter/disconnected")
def tw_disconnected():
    db.child(username).child("settings").child("twitter_boolean").set("False")
    return redirect(url_for("settings"))

@app.route("/settings/tumblr/disconnected")
def tu_disconnected():
    db.child(username).child("settings").child("tumblr_boolean").set("False")
    return redirect(url_for("settings"))

    oauth_token = request.args.get('oauth_token')
if __name__ == '__main__':
    app.run(debug=True)
