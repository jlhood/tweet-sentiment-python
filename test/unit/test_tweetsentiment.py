import pytest
import test_constants

import tweetsentiment


@pytest.fixture
def mock_comprehend(mocker):
    mocker.patch.object(tweetsentiment, 'COMPREHEND')
    return tweetsentiment.COMPREHEND


@pytest.fixture
def mock_cloudwatch(mocker):
    mocker.patch.object(tweetsentiment, 'CLOUDWATCH')
    return tweetsentiment.CLOUDWATCH


def test_handler(mocker, mock_comprehend, mock_cloudwatch):
    tweets = [
        {
            'id_str': '1',
            'full_text': 'negative',
            'user': {
                'screen_name': 'foo'
            }
        },
        {
            'id_str': '2',
            'full_text': 'positive',
            'user': {
                'screen_name': 'bar'
            }
        },
        {
            'id_str': '3',
            'full_text': 'mixed',
            'user': {
                'screen_name': 'baz'
            }
        }
    ]

    mock_comprehend.batch_detect_sentiment.return_value = {
        'ResultList': [
            {
                'Index': 1,
                'Sentiment': 'POSITIVE',
                'SentimentScore': {
                    'Positive': 0.1,
                    'Negative': 0.2,
                    'Neutral': 0.3,
                    'Mixed': 0.4
                }
            },
            {
                'Index': 0,
                'Sentiment': 'NEGATIVE',
                'SentimentScore': {
                    'Positive': 0.5,
                    'Negative': 0.6,
                    'Neutral': 0.7,
                    'Mixed': 0.8
                }
            },
            {
                'Index': 2,
                'Sentiment': 'MIXED',
                'SentimentScore': {
                    'Positive': 0.4,
                    'Negative': 0.3,
                    'Neutral': 0.2,
                    'Mixed': 0.1
                }
            }
        ]
    }

    tweetsentiment.handler(tweets, None)

    mock_comprehend.batch_detect_sentiment.assert_called_with(
        TextList=['negative', 'positive', 'mixed'],
        LanguageCode='en'
    )

    expected = [{'Dimensions': [{'Name': 'SearchText', 'Value': '#serverless'},
                                {'Name': 'SentimentType', 'Value': 'Positive'}],
                 'MetricName': 'SentimentCount',
                 'Value': 1.0},
                {'Dimensions': [{'Name': 'SearchText', 'Value': '#serverless'},
                                {'Name': 'SentimentType', 'Value': 'Negative'}],
                 'MetricName': 'SentimentCount',
                 'Value': 1.0},
                {'Dimensions': [{'Name': 'SearchText', 'Value': '#serverless'},
                                {'Name': 'SentimentType', 'Value': 'Mixed'}],
                 'MetricName': 'SentimentCount',
                 'Value': 1.0},
                {'Dimensions': [{'Name': 'SearchText', 'Value': '#serverless'},
                                {'Name': 'SentimentType', 'Value': 'Positive'}],
                 'MetricName': 'SentimentScore',
                 'Value': 0.1},
                {'Dimensions': [{'Name': 'SearchText', 'Value': '#serverless'},
                                {'Name': 'SentimentType', 'Value': 'Positive'}],
                 'MetricName': 'SentimentScore',
                 'Value': 0.5},
                {'Dimensions': [{'Name': 'SearchText', 'Value': '#serverless'},
                                {'Name': 'SentimentType', 'Value': 'Positive'}],
                 'MetricName': 'SentimentScore',
                 'Value': 0.4},
                {'Dimensions': [{'Name': 'SearchText', 'Value': '#serverless'},
                                {'Name': 'SentimentType', 'Value': 'Negative'}],
                 'MetricName': 'SentimentScore',
                 'Value': 0.2},
                {'Dimensions': [{'Name': 'SearchText', 'Value': '#serverless'},
                                {'Name': 'SentimentType', 'Value': 'Negative'}],
                 'MetricName': 'SentimentScore',
                 'Value': 0.6},
                {'Dimensions': [{'Name': 'SearchText', 'Value': '#serverless'},
                                {'Name': 'SentimentType', 'Value': 'Negative'}],
                 'MetricName': 'SentimentScore',
                 'Value': 0.3},
                {'Dimensions': [{'Name': 'SearchText', 'Value': '#serverless'},
                                {'Name': 'SentimentType', 'Value': 'Neutral'}],
                 'MetricName': 'SentimentScore',
                 'Value': 0.3},
                {'Dimensions': [{'Name': 'SearchText', 'Value': '#serverless'},
                                {'Name': 'SentimentType', 'Value': 'Neutral'}],
                 'MetricName': 'SentimentScore',
                 'Value': 0.7},
                {'Dimensions': [{'Name': 'SearchText', 'Value': '#serverless'},
                                {'Name': 'SentimentType', 'Value': 'Neutral'}],
                 'MetricName': 'SentimentScore',
                 'Value': 0.2},
                {'Dimensions': [{'Name': 'SearchText', 'Value': '#serverless'},
                                {'Name': 'SentimentType', 'Value': 'Mixed'}],
                 'MetricName': 'SentimentScore',
                 'Value': 0.4},
                {'Dimensions': [{'Name': 'SearchText', 'Value': '#serverless'},
                                {'Name': 'SentimentType', 'Value': 'Mixed'}],
                 'MetricName': 'SentimentScore',
                 'Value': 0.8},
                {'Dimensions': [{'Name': 'SearchText', 'Value': '#serverless'},
                                {'Name': 'SentimentType', 'Value': 'Mixed'}],
                 'MetricName': 'SentimentScore',
                 'Value': 0.1}]

    mock_cloudwatch.put_metric_data.assert_called_with(
        Namespace='TweetSentiment',
        MetricData=expected
    )
