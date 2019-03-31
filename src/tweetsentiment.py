"""Lambda function handler."""

# must be the first import in files with lambda function handlers
import lambdainit  # noqa: F401

from operator import itemgetter

import boto3

import config
import lambdalogging

LOG = lambdalogging.getLogger(__name__)
COMPREHEND = boto3.client('comprehend')
CLOUDWATCH = boto3.client('cloudwatch')

# BatchDetectSentiment API only supports some languages
SUPPORTED_LANGUAGE_CODES = set(['de', 'pt', 'en', 'it', 'fr', 'es'])
SENTIMENT_SCORE_TYPES = [
    'Positive',
    'Negative',
    'Neutral',
    'Mixed'
]


def handler(tweets, context):
    """Lambda function handler."""
    LOG.debug('Received tweets: %s', tweets)

    tweet_text = [tweet['full_text'] for tweet in tweets]
    LOG.debug('Detecting dominant language for tweet text batch: %s', tweet_text)
    language_result = COMPREHEND.batch_detect_dominant_language(
        TextList=tweet_text
    )

    tweets_by_language = _get_tweets_by_language(tweets, language_result['ResultList'])
    LOG.debug('Tweets by language: %s', tweets_by_language)

    sentiment_result_logs = []
    metric_data = []
    for language_code, language_tweets in tweets_by_language.items():
        if language_code not in SUPPORTED_LANGUAGE_CODES:
            continue

        language_tweet_text = [tweet['full_text'] for tweet in language_tweets]
        LOG.debug('Detecting sentiment: language_code: %s, tweet text: %s', language_code, language_tweet_text)
        sentiment_result = COMPREHEND.batch_detect_sentiment(
            TextList=language_tweet_text,
            LanguageCode=language_code
        )

        sentiment_result_logs += _get_sentiment_result_logs(
            language_tweets, language_code, sentiment_result['ResultList'])
        metric_data += _to_metric_data(sentiment_result)

    for log in sentiment_result_logs:
        LOG.info(log)

    if metric_data:
        LOG.debug('Putting metric data: %s', metric_data)
        CLOUDWATCH.put_metric_data(
            Namespace='TweetSentiment',
            MetricData=metric_data
        )


def _get_tweets_by_language(tweets, language_result_list):
    result_lookup = {result['Index']: result for result in language_result_list}
    tweets_by_language = {}
    for i, tweet in enumerate(tweets):
        result = result_lookup.get(i)
        # default to English if we can't determine language
        language_code = 'en'
        if result and result['Languages']:
            language_code = sorted(result['Languages'], key=itemgetter('Score'), reverse=True)[0]['LanguageCode']

        tweets_by_language.setdefault(language_code, []).append(tweet)

    return tweets_by_language


def _get_sentiment_result_logs(tweets, language_code, sentiment_result_list):
    """Log sentiment results in a structured way so it can be queried using CloudWatch Insights."""
    sentiment_result_lookup = {result['Index']: result for result in sentiment_result_list}

    result_logs = []
    for i, tweet in enumerate(tweets):
        sentiment_result = sentiment_result_lookup.get(i)
        if sentiment_result:
            result_logs.append(
                'Tweet Sentiment Result: tweet_url:"{}" LanguageCode:{} Sentiment:{} Positive:{:.8f} Negative:{:.8f} '
                'Neutral:{:.8f} Mixed:{:.8f}'.format(
                    _tweet_url(tweet),
                    language_code,
                    sentiment_result['Sentiment'].capitalize(),
                    sentiment_result['SentimentScore']['Positive'],
                    sentiment_result['SentimentScore']['Negative'],
                    sentiment_result['SentimentScore']['Neutral'],
                    sentiment_result['SentimentScore']['Mixed']
                )
            )
    return result_logs


def _tweet_url(tweet):
    return 'https://twitter.com/{}/status/{}'.format(tweet['user']['screen_name'], tweet['id_str'])


def _to_metric_data(sentiment_result):
    sentiment_metric_data = [_to_sentiment_metric_datum(result) for result in sentiment_result['ResultList']]
    sentiment_score_metric_data = [_to_sentiment_score_metric_datum(score_type, result)
                                   for score_type in SENTIMENT_SCORE_TYPES
                                   for result in sentiment_result['ResultList']]
    return sentiment_metric_data + sentiment_score_metric_data


def _to_sentiment_metric_datum(result):
    return {
        'MetricName': 'SentimentCount',
        'Dimensions': [
            {
                'Name': 'SearchText',
                'Value': config.SEARCH_TEXT
            },
            {
                'Name': 'SentimentType',
                'Value': result['Sentiment'].capitalize()
            }
        ],
        'Value': 1.0
    }


def _to_sentiment_score_metric_datum(score_type, result):
    return {
        'MetricName': 'SentimentScore',
        'Dimensions': [
            {
                'Name': 'SearchText',
                'Value': config.SEARCH_TEXT
            },
            {
                'Name': 'SentimentType',
                'Value': score_type
            }
        ],
        'Value': result['SentimentScore'][score_type]
    }
