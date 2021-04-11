from telegram.ext import Updater, CommandHandler
from telegram import ParseMode
import datetime
import random
import feedparser
import requests
import requests_cache


covid_url = 'https://coronavirus-19-api.herokuapp.com/countries/belarus'
news_url = 'https://www.mil.by/ru/rss/news/'

requests_cache.install_cache(
    cache_name='covid_cache', backend='sqlite', expire_after=180)


def next_voenka():
    today = datetime.datetime.today()

    tuesday_d = today + datetime.timedelta(days=(6 + 2 - today.weekday()) % 7)
    tuesday_dt = datetime.datetime(
        tuesday_d.year, tuesday_d.month, tuesday_d.day, 8, 30)

    if today > tuesday_dt:
        tuesday_dt += datetime.timedelta(days=7)
    return tuesday_dt


def time_till_voenka():
    today = datetime.datetime.today()
    voenka = next_voenka()
    seconds_total = int((voenka - today).total_seconds())
    hours = seconds_total // (60 * 60)
    minutes = seconds_total // 60 - 60 * hours
    return hours, minutes


class NewsSource:
    def __init__(self, url):
        self.url = url
        self.date = datetime.date(2000, 1, 1)  # impossible date
        self.news_world = []
        self.news = []

    def getNewsBlock(self):
        if self.date != datetime.date.today():
            self.update_news()

        text = "*Новости:*\n"
        for x, y in self.news:
            text += " - " + makeMarkdownLink(x, y) + "\n"

        text += "*В армиях мира:*\n"
        for x, y in self.news_world:
            text += "- " + makeMarkdownLink(x, y) + "\n"
        return text

    def update_news(self):
        nf = feedparser.parse(self.url)
        self.news_world = [(x['title'], x['link']) for x in filter(
            lambda x: x['tags'][0]['term'] == 'В армиях мира', nf.entries)]
        self.news = [(x['title'], x['link']) for x in filter(
            lambda x: x['tags'][0]['term'] == 'Новости', nf.entries)]
        self.date = datetime.date.today()

    def get_news(self):
        if self.date != datetime.date.today():
            self.update_news()
        return self.news_world


def load_jokes():
    with open('jokes-02.txt') as f:
        jokes_text = f.read()
    return jokes_text.split('@@@')


def random_joke(jokes):
    return random.choice(jokes)


def time(update, context):
    h, m = time_till_voenka()
    answer = f'До военки {h} часов {m} минут.'
    update.message.reply_text(answer)


def makeMarkdownLink(text, link):
    return "[" + text + "](" + link + ")"


def news(update, context):
    update.message.reply_text(
        ns.getNewsBlock(), parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True)


def corona(update, context):
    data = requests.get(covid_url).json()
    msg = f"Заражено сейчас: *{data['active']}* (+{data['todayCases']})\n\
Погибло: *{data['deaths']}* (+{data['todayDeaths']})\nВыздоровело: *{data['recovered']}*"

    update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)


jokes = load_jokes()
ns = NewsSource(news_url)


def joke(update, context):
    update.message.reply_text(random_joke(jokes))


updater = Updater('', use_context=True)

updater.dispatcher.add_handler(CommandHandler('news', news))
updater.dispatcher.add_handler(CommandHandler('time', time))
updater.dispatcher.add_handler(CommandHandler('joke', joke))
updater.dispatcher.add_handler(CommandHandler('corona', corona))

updater.start_polling()
updater.idle()

