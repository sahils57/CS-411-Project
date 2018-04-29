from flask import Flask, render_template, request, redirect
from data import Articles
import twitter
import pyrebase

app = Flask(__name__)

app.config.from_pyfile('config.cfg')

#twitter stuff
#------------------------------------------------------
consumer_key = app.config['CONSUMER_KEY']
consumer_secret = app.config['CONSUMER_SECRET']
access_token = app.config['ACCESS_TOKEN']
access_secret = app.config['ACCESS_SECRET']
#-------------------------------------------------------
api = twitter.Api(consumer_key=consumer_key,
 consumer_secret=consumer_secret,
 access_token_key=access_token,
 access_token_secret=access_secret)

config = {
    "apiKey": app.config['APIKEY'],
    "authDomain": "cs411-webapp.firebaseapp.com",
    "databaseURL": "https://cs411-webapp.firebaseio.com",
    "storageBucket": "cs411-webapp.appspot.com"
}

firebase = pyrebase.initialize_app(config)
db = firebase.database()

#print(api.VerifyCredentials())
#credentials = api.VerifyCredentials()

a = api.GetHomeTimeline(contributor_details = True)
home_timeline = [[i.text, i.user.screen_name] for i in a]
#home_timeline_users = [i.user for i in a]

b = api.GetUserTimeline(screen_name='nhuang54')
user_timeline = [i.text for i in b]

c = api.GetFriends()
follows = [i.screen_name for i in c]

def searchApi(keyword):
    print("pulls from api")
    result = [[i.text, i.user.screen_name] for i in a if keyword.lower() in i.text.lower() or keyword.lower() in i.user.screen_name.lower()]
    return result

def storeTweets(result):
    for item in result:
        db.child("tweets").push(item)

def getTweets(keyword):
    print("searching db")
    result = []
    tweets = db.child("tweets").get()
    if tweets.val() == None:
        return result
    for tweet in tweets.each():
        user = tweet.val()[1]
        msg = tweet.val()[0]
        if (keyword.lower() in user.lower() or keyword.lower() in msg.lower()):
            #print(tweet.val())
            result.append(tweet.val())
    return result

Articles = Articles()

@app.route('/')
def index():
    return render_template('home.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/articles')
def articles():
    return render_template('articles.html', articles=Articles)

@app.route('/article/<string:id>')
def article(id):
    return render_template('article.html', id = id)

@app.route('/twitter')
def twitter():
    return render_template('twitter.html')

@app.route('/twitter/hometimeline')
def hometimeline():
    return render_template('hometimeline.html', tweets= home_timeline)

@app.route('/twitter/usertimeline')
def usertimeline():
    return render_template('usertimeline.html', tweets = user_timeline)

@app.route('/twitter/following')
def following():
    return render_template('following.html', follows = follows)

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
        result = getTweets(foo)
        if (result == []):
            x = searchApi(foo)
            storeTweets(x)
            return render_template('search_results.html', results = x)
        else:
            print("pulling from db")
            return render_template('search_results.html', results = result)

if __name__ == '__main__':
    app.run(debug=True)
