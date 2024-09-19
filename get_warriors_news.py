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
        system_prompt = "You are a helpful assistant that summarizes news articles about the Golden State Warriors. If the articles are not related to the Warriors or NBA basketball, state that no relevant news was found."
    elif category == "regenerative":
        query = '"regenerative technology" OR "wise technology"'
        system_prompt = "You are a helpful assistant that summarizes news articles about regenerative technology, including wise technology. If the articles are not related to regenerative technology, state that no relevant news was found."
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
        return f"No recent news about {category} was found."

    articles_text = "\n\n".join([f"Title: {a['title']}\nURL: {a['url']}\nContent: {a['description']} {a['content']}" for a in articles])
    
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Here are several news articles about {category}. Please provide a concise summary of the main news points, mentioning any significant developments or updates. Include relevant links where appropriate. If the articles are not relevant, state that no relevant news was found:\n\n{articles_text}"}
        ]
    )
    
    return response.choices[0].message.content.strip()

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
def create_twitter_thread(summary, local=False):
    if local:
        print("Local mode: Would post the following Twitter thread:")
        tweets = []
        current_tweet = ""
        for word in summary.split():
            if len(current_tweet + " " + word) <= 280:
                current_tweet += " " + word
            else:
                tweets.append(current_tweet.strip())
                current_tweet = word
        if current_tweet:
            tweets.append(current_tweet.strip())
        for i, tweet in enumerate(tweets):
            print(f"Tweet {i+1}: {tweet}")
        return

    auth = tweepy.OAuthHandler(TWITTER_API_KEY, TWITTER_API_SECRET)
    auth.set_access_token(TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_TOKEN_SECRET)
    api = tweepy.API(auth)

    # Split the summary into tweets (max 280 characters each)
    tweets = []
    current_tweet = ""
    for word in summary.split():
        if len(current_tweet + " " + word) <= 280:
            current_tweet += " " + word
        else:
            tweets.append(current_tweet.strip())
            current_tweet = word
    if current_tweet:
        tweets.append(current_tweet.strip())

    # Post the thread
    previous_tweet = None
    for tweet in tweets:
        if previous_tweet:
            status = api.update_status(status=tweet, in_reply_to_status_id=previous_tweet.id)
        else:
            status = api.update_status(status=tweet)
        previous_tweet = status

def parse_arguments():
    parser = argparse.ArgumentParser(description="Run Warriors news summary with optional email and Twitter posting.")
    parser.add_argument("--email", action="store_true", help="Send email summary")
    parser.add_argument("--twitter", action="store_true", help="Post Twitter thread")
    parser.add_argument("--local", action="store_true", help="Run in local testing mode")
    return parser.parse_args()

@record_action("main")
def main():
    args = parse_arguments()

    categories = ["warriors", "regenerative"]
    summaries = {}

    for category in categories:
        summary = fetch_and_summarize_news(category)
        summaries[category] = summary
        print(f"Summary of {category.capitalize()} News:")
        print(summary)
        print("\n" + "="*50 + "\n")

    combined_summary = "\n\n".join([f"{category.capitalize()} News:\n{summary}" for category, summary in summaries.items()])

    if all(summary.startswith("No recent news") for summary in summaries.values()):
        print("No relevant news found for any category. Skipping emails and tweets.")
    else:
        # Send emails to all subscribers
        send_emails("News Summary: Warriors and Regenerative Tech", combined_summary)
        print("Subscriber emails processed.")

        # Post to Twitter if --twitter flag is used
        if args.twitter:
            create_twitter_thread(combined_summary, local=args.local)
            print("Twitter thread processed.")

if __name__ == "__main__":
    main()