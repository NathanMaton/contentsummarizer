# Warriors News Summary

This project fetches and summarizes news about the Golden State Warriors, sends email updates to subscribers, and optionally posts updates to Twitter.

## Setup

1. Clone the repository
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Set up your `.env` file with the necessary API keys and credentials:
   ```
   NEWS_API_KEY=your_news_api_key
   OPENAI_API_KEY=your_openai_api_key
   EMAIL_ADDRESS=your_email@example.com
   EMAIL_PASSWORD=your_email_password
   TWITTER_API_KEY=your_twitter_api_key
   TWITTER_API_SECRET=your_twitter_api_secret
   TWITTER_ACCESS_TOKEN=your_twitter_access_token
   TWITTER_ACCESS_TOKEN_SECRET=your_twitter_access_token_secret
   AGENTOPS_API_KEY=your_agentops_api_key
   DATABASE_URL=postgresql://username:password@localhost/dbname
   ```

## Local Testing

### Running the Script

The `get_warriors_news.py` script can be run with various flags for testing:

1. Basic run (fetches news but doesn't send emails or tweet):
   ```
   python get_warriors_news.py --local
   ```

2. Test email functionality:
   ```
   python get_warriors_news.py --local --email
   ```

3. Test Twitter functionality:
   ```
   python get_warriors_news.py --local --twitter
   ```

4. Test both email and Twitter:
   ```
   python get_warriors_news.py --local --email --twitter
   ```

### Flag Explanations

- `--local`: Runs the script in local mode, preventing actual emails from being sent or tweets from being posted.
- `--email`: In local mode, this will simulate sending a test email to the address specified in EMAIL_ADDRESS.
- `--twitter`: In local mode, this will simulate posting a tweet thread.

### Testing the Web Application

To test the Flask web application locally:

1. Run the Flask app:
   ```
   python app.py
   ```

2. Open a web browser and go to `http://localhost:5000`

3. You should see a simple form where you can subscribe an email address.

### Database Setup

Make sure you have PostgreSQL installed and running locally. Create a database for the project:

```
createdb warriors_news
```

The script and web app will automatically create the necessary tables when run.

## Deployment

This project is designed to be deployed on Heroku. Make sure to set all environment variables in your Heroku app settings and set up the