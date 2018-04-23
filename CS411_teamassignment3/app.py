from flask import Flask, render_template, request, redirect
from data import Articles
import twitter
from datetime import datetime, date, timedelta

app = Flask(__name__)

#twitter stuff
#------------------------------------------------------
consumer_key = 'WH3jhSuTMRA3ESj8xInLEsiLe'
consumer_secret = 'c2hPnRpVbv8yudyepiPzZ9ihBbYw6EsnevNDqdi3XnSt3HZH51'
access_token = '976927078489653248-86NxrrQxbrKcdat3Dlxpwaf1aK0euZQ'
access_secret = '3SP5HnQK4VX9D4OBnttCLXtHjQB5bOrvKY59zhTRHvMM6'
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
                    print(timeline[3][0])
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

home_timeline = generateTweets(18)

b = api.GetUserTimeline(screen_name='nhuang54')
user_timeline = [i.text for i in b]

c = api.GetFriends()
follows = [i.screen_name for i in c]

def searchApi(keyword):
    result = [[i.text, i.user.screen_name] for i in a if keyword.lower() in i.text.lower() or keyword.lower() in i.user.screen_name.lower()]
    return result


Articles = Articles()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/home')
def home():
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
        x = searchApi(foo)
        return render_template('search_results.html', results = x)

if __name__ == '__main__':
    app.run(debug=True)
