import requests
import json
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
from openai import OpenAI
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import tweepy
import argparse
from agentops import record_action, init

# Load environment variables from .env file
load_dotenv()

# Get API keys from environment variables
NEWS_API_KEY = os.getenv('NEWS_API_KEY')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
EMAIL_ADDRESS = os.getenv('EMAIL_ADDRESS')
EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD')
TWITTER_API_KEY = os.getenv('TWITTER_API_KEY')
TWITTER_API_SECRET = os.getenv('TWITTER_API_SECRET')
TWITTER_ACCESS_TOKEN = os.getenv('TWITTER_ACCESS_TOKEN')
TWITTER_ACCESS_TOKEN_SECRET = os.getenv('TWITTER_ACCESS_TOKEN_SECRET')
AGENTOPS_API_KEY = os.getenv('AGENTOPS_API_KEY')

# Set up OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)

# Initialize AgentOps
init(api_key=AGENTOPS_API_KEY)

BASE_URL = 'https://newsapi.org/v2/everything'

def get_subscribers():
    subscribers_json = os.getenv('SUBSCRIBERS')
    if subscribers_json:
        return json.loads(subscribers_json)
    return []

@record_action("fetch_and_summarize_news")
def fetch_and_summarize_news(category):
    if category == "warriors":
        query = '"Golden State Warriors" OR (Warriors AND (NBA OR basketball))'
        system_prompt = "You are a social media expert crafting concise, engaging tweets about the Golden State Warriors. Summarize recent news in a Twitter-friendly style. Each summary should be a complete thought, ideally under 200 characters to allow for a link. Don't use numbering or bullet points. Only include relevant Warriors news. If no relevant news is found, state that clearly."
    else:
        raise ValueError(f"Unknown category: {category}")

    params = {
        'q': query,
        'language': 'en',
        'sortBy': 'publishedAt',
        'apiKey': NEWS_API_KEY,
        'from': (datetime.now() - timedelta(days=2)).strftime('%Y-%m-%d')  # Last 2 days
    }

    response = requests.get(BASE_URL, params=params)
    
    if response.status_code != 200:
        return f"Error: Unable to fetch news for {category}. Status code: {response.status_code}"

    news_data = json.loads(response.text)
    articles = news_data['articles']

    if not articles:
        return f"No recent news about the Golden State Warriors was found."

    articles_text = "\n\n".join([f"Title: {a['title']}\nURL: {a['url']}\nContent: {a['description']} {a['content']}" for a in articles])
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",  # Keeping the model as gpt-4o-mini
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Create a series of tweet-length summaries about recent Golden State Warriors news. Each summary should be a complete thought, ideally under 200 characters to allow for a link. Don't use numbering, bullet points, hashtags, or @mentions. Only include relevant Warriors news. If no relevant news is found, return an empty list. Here are the articles:\n\n{articles_text}"}
        ]
    )
    
    summaries = response.choices[0].message.content.strip().split('\n')
    return [(summary, article) for summary, article in zip(summaries, articles) if summary and not summary.startswith("No relevant")]

@record_action("send_emails")
def send_emails(subject, body, local=False):
    if local:
        print(f"Local mode: Would send email to subscribers with subject '{subject}' and body:")
        print(body)
        return

    subscribers = get_subscribers()
    for email in subscribers:
        send_email(email, subject, body)

@record_action("send_email")
def send_email(to_email, subject, body, local=False):
    if local:
        print(f"Local mode: Would send email to {to_email} with subject '{subject}' and body:")
        print(body)
        return

    msg = MIMEMultipart()
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = to_email
    msg['Subject'] = subject

    msg.attach(MIMEText(body, 'plain'))

    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
    text = msg.as_string()
    server.sendmail(EMAIL_ADDRESS, to_email, text)
    server.quit()

@record_action("create_twitter_thread")
def create_twitter_thread(summaries, local=True):
    print("Local mode: Would post the following Twitter thread:")
    tweets = []
    for i, (summary, article) in enumerate(summaries):
        if summary and article['url']:
            tweet = f"{summary.strip()} {article['url']}"
            if len(tweet) <= 280:
                tweets.append(tweet)
            else:
                # If tweet is too long, truncate the summary
                max_summary_length = 277 - len(article['url'])  # 280 - 3 (for "...") - len(url)
                truncated_summary = summary[:max_summary_length] + "..."
                tweets.append(f"{truncated_summary} {article['url']}")
    
    if tweets:
        print(f"🏀 Warriors News Update 🏀")
        for i, tweet in enumerate(tweets):
            print(f"{i+1}/")
            print(tweet)
            print()  # Empty line for readability
    else:
        print("No relevant Warriors news found to create a thread.")
    
    return tweets

def parse_arguments():
    parser = argparse.ArgumentParser(description="Run Warriors news summary with optional email and Twitter posting.")
    parser.add_argument("--email", action="store_true", help="Send email summary")
    parser.add_argument("--twitter", action="store_true", help="Post Twitter thread")
    parser.add_argument("--local", action="store_true", help="Run in local testing mode")
    return parser.parse_args()

@record_action("main")
def main():
    args = parse_arguments()

    categories = ["warriors"]  # Only look for Warriors news
    summaries = {}

    for category in categories:
        summaries[category] = fetch_and_summarize_news(category)
        print(f"Summary of {category.capitalize()} News:")
        for summary, _ in summaries[category]:
            print(summary)
        print("\n" + "="*50 + "\n")

    if isinstance(summaries['warriors'], str) and summaries['warriors'].startswith("No recent news"):
        print("No relevant news found. Skipping tweets.")
    else:
        # Always run in local mode to print potential tweets
        tweets = create_twitter_thread(summaries['warriors'], local=True)
        print(f"Total number of tweets: {len(tweets)}")

if __name__ == "__main__":
    main()