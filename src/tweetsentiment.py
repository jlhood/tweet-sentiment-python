"""Lambda function handler."""

# must be the first import in files with lambda function handlers
import lambdainit  # noqa: F401

import boto3

import config
import lambdalogging

LOG = lambdalogging.getLogger(__name__)
COMPREHEND = boto3.client('comprehend')
CLOUDWATCH = boto3.client('cloudwatch')

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
    LOG.debug('Detecting sentiment for tweet text batch: %s', tweet_text)
    sentiment_result = COMPREHEND.batch_detect_sentiment(
        TextList=tweet_text,
        LanguageCode='en'
    )

    _log_sentiment_results(tweets, sentiment_result['ResultList'])

    metric_data = _to_metric_data(sentiment_result)
    LOG.debug('Putting metric data: %s', metric_data)
    CLOUDWATCH.put_metric_data(
        Namespace='TweetSentiment',
        MetricData=metric_data
    )


def _log_sentiment_results(tweets, sentiment_result_list):
    """Log sentiment results in a structured way so it can be queried using CloudWatch Insights."""
    sentiment_result_lookup = {result['Index']: result for result in sentiment_result_list}

    for i, tweet in enumerate(tweets):
        sentiment_result = sentiment_result_lookup.get(i)
        if sentiment_result:
            LOG.info(
                'Tweet Sentiment Result: tweet_url:"%s" Sentiment:%s Positive:%.8f Negative:%.8f '
                'Neutral:%.8f Mixed:%.8f',
                _tweet_url(tweet),
                sentiment_result['Sentiment'].capitalize(),
                sentiment_result['SentimentScore']['Positive'],
                sentiment_result['SentimentScore']['Negative'],
                sentiment_result['SentimentScore']['Neutral'],
                sentiment_result['SentimentScore']['Mixed']
            )


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
