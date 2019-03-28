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

    metric_data = _to_metric_data(sentiment_result)
    LOG.debug('Putting metric data: %s', metric_data)
    CLOUDWATCH.put_metric_data(
        Namespace='TweetSentiment',
        MetricData=metric_data
    )


def _to_metric_data(sentiment_result):
    return [_to_sentiment_metric_datum(score_type, result)
            for score_type in SENTIMENT_SCORE_TYPES
            for result in sentiment_result['ResultList']]


def _to_sentiment_metric_datum(score_type, result):
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
