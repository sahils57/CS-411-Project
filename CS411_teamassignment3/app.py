from flask import Flask, render_template
from data import Articles
import twitter

app = Flask(__name__)

#twitter stuff
#------------------------------------------------------
consumer_key = 'WH3jhSuTMRA3ESj8xInLEsiLe'
consumer_secret = 'c2hPnRpVbv8yudyepiPzZ9ihBbYw6EsnevNDqdi3XnSt3HZH51'
access_token = '976927078489653248-86NxrrQxbrKcdat3Dlxpwaf1aK0euZQ'
access_secret = '3SP5HnQK4VX9D4OBnttCLXtHjQB5bOrvKY59zhTRHvMM6'
#-------------------------------------------------------
api = twitter.Api(consumer_key=consumer_key,
 consumer_secret=consumer_secret,
 access_token_key=access_token,
 access_token_secret=access_secret)

#print(api.VerifyCredentials())
credentials = api.VerifyCredentials()

a = api.GetHomeTimeline(contributor_details = True)
home_timeline = [[i.text, i.user.screen_name] for i in a]
#home_timeline_users = [i.user for i in a]

b = api.GetUserTimeline(screen_name='nhuang54')
user_timeline = [i.text for i in b]

c = api.GetFriends()
follows = [i.screen_name for i in c]


#print(following)

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

if __name__ == '__main__':
    app.run(debug=True)
