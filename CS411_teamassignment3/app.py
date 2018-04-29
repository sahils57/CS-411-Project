from __future__ import print_function
from flask import Flask, render_template, request, redirect, flash, url_for, session
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
from flask_login import LoginManager, UserMixin


app = Flask(__name__)
config = {
    "apiKey": "AIzaSyC9Lgc_qAajV-HzLR0Rjc38ZlZx6Yi4Srg",
    "authDomain": "cs411-webapp.firebaseapp.com",
    "databaseURL": "https://cs411-webapp.firebaseio.com",
    "storageBucket": "cs411-webapp.appspot.com"
}
firebase = pyrebase.initialize_app(config)
db = firebase.database()
login_manager = LoginManager()
login_manager.init_app(app)




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
#twitter_access_token = '976927078489653248-86NxrrQxbrKcdat3Dlxpwaf1aK0euZQ'
#twitter_access_secret = '3SP5HnQK4VX9D4OBnttCLXtHjQB5bOrvKY59zhTRHvMM6'
twitter_access_token = ""
twitter_access_secret = ""
#------
request_token_url = 'https://twitter.com/oauth/request_token'
access_token_url = 'https://twitter.com/oauth/access_token'
authorize_url = 'https://twitter.com/oauth/authorize'
show_user_url = 'https://api.twitter.com/1.1/users/show.json'
#------
oauth_store = {}
#-------------------------------------------------------

#print(api.VerifyCredentials())
#credentials = api.VerifyCredentials()



#print(a[4].retweeted_status.user.screen_name)
#below only includes non-retweets
#home_timeline = [[i.full_text, i.user.screen_name, i.created_at, i.user.profile_image_url] for i in a if i.retweeted_status == None]
#
# text_file = open("output.txt", "w")
# text_file.write(str(a[3]))
# text_file.close()

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

def formatTimeTwitter(twitter_date):
    #current_date = datetime.today()
    #print(current_date)
    final_date = datetime.strptime(twitter_date, '%a %b %d %H:%M:%S +0000 %Y')
    fourhourdifference = final_date + timedelta(hours=-4)
    #print(final_date)
    #difference_date = current_date - final_date
    #print(difference_date.seconds)
    return fourhourdifference

def formatTimeTumblr(tumblr_date):
    final_date = datetime.strptime(tumblr_date, '%Y-%m-%d %H:%M:%S GMT')
    fourhourdifference = final_date + timedelta(hours=-4)
    return fourhourdifference

#below includes the full text for retweets
def generateTweets(i):
    #make applicable for multiple multimedia links, like image with youtube link in text
    api = twitter.Api(twitter_consumer_key, twitter_consumer_secret, twitter_access_token, twitter_access_secret, tweet_mode="extended")

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

    # link in tweeet text
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
tumblr_access_token = ""
tumblr_access_secret = ""
#tumblr_access_token = "otjThytAozKKBOLFPoZbaqfo8HMtvTzciABrWR6uX0sj670f6E"
#tumblr_access_secret = "Ye0VNDcGbSIG3D5hB6cGugafoWY1ryEQcszhygTdC2vVaoI8py"
OAUTH_TOKEN_SECRET = ""

def generate_tumblr_dashboard(i):
    client = pytumblr.TumblrRestClient(tumblr_consumer_key,
        tumblr_consumer_secret, tumblr_access_token, tumblr_access_secret)
    dash = client.dashboard(limit=50)
    print(len(dash['posts']))
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
    print(len(dashboard))
    print(dashboard)
    return dashboard


# possibly add time-based feed? maybe not
# example of how an alternating feed could be generated
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
    elif twitter_bool == "True" and tumblr_bool == "False":
        print("twitter access secret is " + twitter_access_secret)
        print("twitter access token is " + twitter_access_token)

        return generateTweets(i)
    elif twitter_bool == "False" and tumblr_bool == "True":
        return generate_tumblr_dashboard(i)
    else:
        return []





Articles = Articles()

def createFakePerson(id, tw_bool, tu_bool):
    db.child(id).child("settings").child("tumblr_boolean").set(tu_bool)
    db.child(id).child("settings").child("twitter_boolean").set(tw_bool)

    db.child(id).child("twitter").child("access_token").set("123")
    db.child(id).child("twitter").child("access_secret").set("456")

    db.child(id).child("tumblr").child("access_token").set("123")
    db.child(id).child("tumblr").child("access_secret").set("456")

createFakePerson(1234, "False", "False")
@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)

@app.route('/')
def index():
    #return render_template('index.html')
    return redirect(url_for('home'))

@app.route('/home')
def home():
    status = [db.child("1234").child("settings").child("twitter_boolean").get().val(), db.child("1234").child("settings").child("tumblr_boolean").get().val()]
    print(status)
    home_timeline = generateFeed(20, status[0], status[1])
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

    return render_template('start.html', authorize_url=authorize_url, oauth_token = oauth_token,
        request_token_url = request_token_url)


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


    # add to database
    db.child(1234).child("settings").child("twitter_boolean").set("True")

    #SAVE THESE TOKENS !
    real_oauth_token = access_token['oauth_token']
    real_oauth_token_secret = access_token['oauth_token_secret']

    global twitter_access_token
    global twitter_access_secret
    twitter_access_token = real_oauth_token
    twitter_access_secret = real_oauth_token_secret

    print(twitter_consumer_key)
    print(twitter_consumer_secret)
    print(twitter_access_token)
    print(twitter_access_secret)

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
    # if checker, check if the user pressed YES, and then store the tokens received

    url_after = request.url
    if url_after == "http://localhost:5000/callbacktumblr":
        return render_template('error.html', error_message = "OAuth request denied by this user")

    oauth_token = request.args.get('oauth_token')
    oauth_verifier = request.args.get('oauth_verifier')
    t = Tumblpy(tumblr_consumer_key, tumblr_consumer_secret,
            oauth_token, OAUTH_TOKEN_SECRET)
    authorized_tokens = t.get_authorized_tokens(oauth_verifier)
    # throw error if needed
    final_oauth_token = authorized_tokens['oauth_token']
    final_oauth_token_secret = authorized_tokens['oauth_token_secret']

    global tumblr_access_token
    global tumblr_access_secret
    tumblr_access_token = final_oauth_token
    tumblr_access_secret = final_oauth_token_secret

    db.child(1234).child("settings").child("tumblr_boolean").set("True")


    print(final_oauth_token)
    print(final_oauth_token_secret)

    return redirect(url_for('settings'))

@app.route("/settings/twitter/disconnected")
def tw_disconnected():
    db.child(1234).child("settings").child("twitter_boolean").set("False")
    return redirect(url_for("settings"))

@app.route("/settings/tumblr/disconnected")
def tu_disconnected():
    db.child(1234).child("settings").child("tumblr_boolean").set("False")
    return redirect(url_for("settings"))

if __name__ == '__main__':
    app.run(debug=True)
