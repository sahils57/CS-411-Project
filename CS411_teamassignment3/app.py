from __future__ import print_function
from flask import Flask, render_template, request, redirect, flash, url_for
import oauth2 as oauth
import urlparse
import urllib
import json
from data import Articles
import twitter
import webbrowser
import pyrebase
from datetime import datetime, date, timedelta


app = Flask(__name__)
config = {
    "apiKey": "AIzaSyC9Lgc_qAajV-HzLR0Rjc38ZlZx6Yi4Srg",
    "authDomain": "cs411-webapp.firebaseapp.com",
    "databaseURL": "https://cs411-webapp.firebaseio.com",
    "storageBucket": "cs411-webapp.appspot.com"
}
firebase = pyrebase.initialize_app(config)
db = firebase.database()

#twitter stuff
#------------------------------------------------------
consumer_key = 'WH3jhSuTMRA3ESj8xInLEsiLe'
consumer_secret = 'c2hPnRpVbv8yudyepiPzZ9ihBbYw6EsnevNDqdi3XnSt3HZH51'
access_token = '976927078489653248-86NxrrQxbrKcdat3Dlxpwaf1aK0euZQ'
access_secret = '3SP5HnQK4VX9D4OBnttCLXtHjQB5bOrvKY59zhTRHvMM6'
#------
request_token_url = 'https://twitter.com/oauth/request_token'
access_token_url = 'https://twitter.com/oauth/access_token'
authorize_url = 'https://twitter.com/oauth/authorize'
show_user_url = 'https://api.twitter.com/1.1/users/show.json'
#------
oauth_store = {}
#-------------------------------------------------------
api = twitter.Api(consumer_key, consumer_secret, access_token, access_secret, tweet_mode="extended")

#print(api.VerifyCredentials())
#credentials = api.VerifyCredentials()

a = api.GetHomeTimeline(contributor_details = True)

#print(a[4].retweeted_status.user.screen_name)
#below only includes non-retweets
#home_timeline = [[i.full_text, i.user.screen_name, i.created_at, i.user.profile_image_url] for i in a if i.retweeted_status == None]

text_file = open("output.txt", "w")
text_file.write(str(a[3]))
#text_file.write(str(a[6]))
text_file.close()

def checkYoutubeTweet(x):
    yt_test = str(x.urls[0].expanded_url)
    yt_test = yt_test.split("/")
    if yt_test[2] == "youtu.be" or yt_test[2] == "youtube":
        return True
    else:
        return False


def generateYoutubeURL(x):         # from a json object
    yt_test = str(x.urls[0].expanded_url)
    yt_test = yt_test.split("/")
    yt_url = yt_test[-1]
    yt_url = "https://www.youtube.com/embed/" + yt_url
    return yt_url

    #
    # def formatTime(twitter_date):
    #     words = twitter_date.replace(':', ' ')
    #     words = words.split()
    #     words = [str(r) for r in words[1:]]
    #     words.remove("+0000")
    #     date = ' '.join(words)
    #     final_date = time.strptime(date, "%b %d %H %M %S %Y")
    #     print(final_date)
    #     final_date = time.mktime(final_date)# time difference zones
    #     current_time = time.time()
    #     print(time.localtime(final_date))
    #     print(time.localtime(current_time))
    #     difference_time = current_time-final_date
    #     return final_date

def formatTime(twitter_date):
    current_date = datetime.today()
    #print(current_date)
    final_date = datetime.strptime(twitter_date, '%a %b %d %H:%M:%S +0000 %Y')
    #print(final_date)
    difference_date = current_date - final_date
    #print(difference_date.seconds)
    return difference_date

#below includes the full text for retweets
def generateTweets(i):
    #make applicable for multiple multimedia links, like image with youtube link in text

    timeline = []

    #retweet vs tweet main loop
    for x in range(i):
        if a[x].retweeted_status == None:
            timeline += [["none", "not_retweeted", a[x].full_text, a[x].user.screen_name, a[x].created_at, a[x].user.profile_image_url]]
        else:
            timeline += [["re_none", a[x].retweeted_status.user.screen_name, a[x].retweeted_status.full_text, a[x].user.screen_name, a[x].created_at, a[x].user.profile_image_url]]

    # media in tweet hosted on twitter
    for z in range(i):
        if a[z].retweeted_status == None:
            if a[z].media != None:
                if a[z].media[0].type == "animated_gif":
                    timeline[z][0] = "gif"
                    timeline[z] += [a[z].media[0].video_info['variants'][0]['url']]
                elif a[z].media[0].type == "video":
                    timeline[z][0] = "video"
                    for j in range(4):
                        if a[z].media[0].video_info['variants'][j]['content_type'] == "video/mp4":
                            timeline[z] += [a[z].media[0].video_info['variants'][j]['url']]
                            break
                        else:
                            continue
                        timeline[z][0] = "none"
                elif a[z].media[0].type == "photo":
                    timeline[z][0] = "photo"
                    timeline[z] += [a[z].media[0].media_url_https]
        else:
            if a[z].retweeted_status.media != None:
                if a[z].retweeted_status.media[0].type == "animated_gif":
                    timeline[z][0] = "re_gif"
                    timeline[z] += [a[z].media[0].video_info['variants'][0]['url']]
                elif a[z].retweeted_status.media[0].type == "video":
                    timeline[z][0] = "re_video"
                    for j in range(4):
                        if a[z].retweeted_status.media[0].video_info['variants'][j]['content_type'] == "video/mp4":
                            timeline[z] += [a[z].retweeted_status.media[0].video_info['variants'][j]['url']]
                            break
                        else:
                            continue
                            timeline[z][0] = "re_none"
                elif a[z].retweeted_status.media[0].type == "photo":
                    timeline[z][0] = "re_photo"
                    timeline[z] += [a[z].retweeted_status.media[0].media_url_https]

    # link in tweeet text
    for y in range(i):
        if timeline[y][0] == "none" or timeline[y][0] == "re_none":
            if a[y].urls != []:
                if checkYoutubeTweet(a[y]):
                    timeline[y][0] = "youtube"
                    timeline[y] += [generateYoutubeURL(a[y])]
                else:
                    timeline[y][0] = "link"
                    timeline[y] += [a[y].urls[0].expanded_url]
    return timeline

#home_timeline = generateTweets(18)

#b = api.GetUserTimeline(screen_name='nhuang54')
#user_timeline = [i.text for i in b]

#c = api.GetFriends()
#follows = [i.screen_name for i in c]

def searchApi(keyword):
    result = [[i.text, i.user.screen_name] for i in a if keyword.lower() in i.text.lower() or keyword.lower() in i.user.screen_name.lower()]
    return result

Articles = Articles()

def createFakePerson(id):
    db.child(id).child("settings").child("tumblr_boolean").set("False")
    db.child(id).child("settings").child("twitter_boolean").set("False")

    db.child(id).child("twitter").child("access_token").set("123")
    db.child(id).child("twitter").child("access_secret").set("456")

    db.child(id).child("tumblr").child("access_token").set("123")
    db.child(id).child("tumblr").child("access_secret").set("456")

createFakePerson(456)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/home')
def home():
    home_timeline = []
    return render_template('home.html', tweets = home_timeline)

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/articles')
def articles():
    return render_template('articles.html', articles=Articles)

@app.route('/article/<string:id>')
def article(id):
    return render_template('article.html', id = id, tweets = home_timeline)

@app.route('/settings')
def settings():
    #get twitter status and store in 2 length list
    status = [db.child("1234").child("settings").child("twitter_boolean").get().val(), db.child("1234").child("settings").child("tumblr_boolean").get().val()]
    print(status)
    return render_template('settings.html', status = status)

# @app.route('/twitter')
# def twitter():
#     return render_template('twitter.html')
#
# @app.route('/twitter/hometimeline')
# def hometimeline():
#     return render_template('hometimeline.html', tweets= home_timeline)
#
# @app.route('/twitter/usertimeline')
# def usertimeline():
#     return render_template('usertimeline.html', tweets = user_timeline)
#
# @app.route('/twitter/following')
# def following():
#     return render_template('following.html', follows = follows)

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
    consumer = oauth.Consumer(consumer_key, consumer_secret)
    client = oauth.Client(consumer)

    app_callback_url = url_for('callback', _external = True)

    resp, content = client.request(request_token_url, "POST", body=urllib.urlencode({"oauth_callback": app_callback_url}))
    #resp, content = client.request(request_token_url, "GET")
    #body=urllib.urlencode({"oauth_callback": app_callback_url})
    print(resp)
    print(content)
    print(app_callback_url)
    if resp['status'] != '200':
        error_message = "Invalid response %s" % resp['status']
        return render_template('error.html', error_message = error_message)

    request_token = dict(urlparse.parse_qsl(content))
    oauth_token = request_token['oauth_token']
    oauth_token_secret = request_token['oauth_token_secret']

    ## store oauth token secret somewher
    oauth_store[oauth_token] = oauth_token_secret

    return render_template('start.html', authorize_url=authorize_url, oauth_token = oauth_token,
        request_token_url = request_token_url)


    print("Go to the following link in your browser:")
    print(authorize_url + "?oauth_token=" + request_token['oauth_token'])

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

    consumer = oauth.Consumer(consumer_key, consumer_secret)
    token = oauth.Token(oauth_token, oauth_token_secret)
    token.set_verifier(oauth_verifier)
    client = oauth.Client(consumer, token)

    resp, content = client.request(access_token_url, "POST")
    access_token = dict(urlparse.parse_qsl(content))

    user_id = access_token['user_id']


    # add to database
    db.child(1234).child("settings").child("twitter_boolean").set("True")

    #SAVE THESE TOKENS !
    real_oauth_token = access_token['oauth_token']
    real_oauth_token_secret = access_token['oauth_token_secret']

    real_token = oauth.Token(real_oauth_token, real_oauth_token_secret)
    real_client = oauth.Client(consumer, real_token)
    real_resp, real_content = real_client.request(show_user_url + '?user_id=' + user_id, "GET")

    if real_resp['status'] != '200':
        error_message = "Invalid response from twitter: " + real_resp['status']
        return render_template('error.html', error_message=error_message)

    del oauth_store[oauth_token]


    return redirect(url_for("settings"))

@app.route("/settings/disconnected")
def disconnected():
    db.child(1234).child("settings").child("twitter_boolean").set("False")
    return redirect(url_for("settings"))

if __name__ == '__main__':
    app.run(debug=True)
