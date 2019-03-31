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
            'full_text': 'negative en',
            'user': {
                'screen_name': 'foo'
            }
        },
        {
            'id_str': '2',
            'full_text': 'positive en',
            'user': {
                'screen_name': 'bar'
            }
        },
        {
            'id_str': '3',
            'full_text': 'mixed de',
            'user': {
                'screen_name': 'baz'
            }
        }
    ]

    # testing cases where no result is returned or no languages are returned as well as case where results are returned
    mock_comprehend.batch_detect_dominant_language.return_value = {
        'ResultList': [
            {
                'Index': 1,
                'Languages': []
            },
            {
                'Index': 2,
                'Languages': [
                    {
                        'LanguageCode': 'en',
                        'Score': 0.1
                    },
                    {
                        'LanguageCode': 'de',
                        'Score': 1.0
                    },
                    {
                        'LanguageCode': 'fr',
                        'Score': 0.5
                    }
                ]
            }
        ]
    }

    mock_comprehend.batch_detect_sentiment.side_effect = [
        {
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
                }
            ]
        },
        {
            'ResultList': [
                {
                    'Index': 0,
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
    ]

    tweetsentiment.handler(tweets, None)

    mock_comprehend.batch_detect_sentiment.assert_any_call(
        TextList=['negative en', 'positive en'],
        LanguageCode='en'
    )
    mock_comprehend.batch_detect_sentiment.assert_any_call(
        TextList=['mixed de'],
        LanguageCode='de'
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
                                {'Name': 'SentimentType', 'Value': 'Positive'}],
                 'MetricName': 'SentimentScore',
                 'Value': 0.1},
                {'Dimensions': [{'Name': 'SearchText', 'Value': '#serverless'},
                                {'Name': 'SentimentType', 'Value': 'Positive'}],
                 'MetricName': 'SentimentScore',
                 'Value': 0.5},
                {'Dimensions': [{'Name': 'SearchText', 'Value': '#serverless'},
                                {'Name': 'SentimentType', 'Value': 'Negative'}],
                 'MetricName': 'SentimentScore',
                 'Value': 0.2},
                {'Dimensions': [{'Name': 'SearchText', 'Value': '#serverless'},
                                {'Name': 'SentimentType', 'Value': 'Negative'}],
                 'MetricName': 'SentimentScore',
                 'Value': 0.6},
                {'Dimensions': [{'Name': 'SearchText', 'Value': '#serverless'},
                                {'Name': 'SentimentType', 'Value': 'Neutral'}],
                 'MetricName': 'SentimentScore',
                 'Value': 0.3},
                {'Dimensions': [{'Name': 'SearchText', 'Value': '#serverless'},
                                {'Name': 'SentimentType', 'Value': 'Neutral'}],
                 'MetricName': 'SentimentScore',
                 'Value': 0.7},
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
                 'MetricName': 'SentimentCount',
                 'Value': 1.0},
                {'Dimensions': [{'Name': 'SearchText', 'Value': '#serverless'},
                                {'Name': 'SentimentType', 'Value': 'Positive'}],
                 'MetricName': 'SentimentScore',
                 'Value': 0.4},
                {'Dimensions': [{'Name': 'SearchText', 'Value': '#serverless'},
                                {'Name': 'SentimentType', 'Value': 'Negative'}],
                 'MetricName': 'SentimentScore',
                 'Value': 0.3},
                {'Dimensions': [{'Name': 'SearchText', 'Value': '#serverless'},
                                {'Name': 'SentimentType', 'Value': 'Neutral'}],
                 'MetricName': 'SentimentScore',
                 'Value': 0.2},
                {'Dimensions': [{'Name': 'SearchText', 'Value': '#serverless'},
                                {'Name': 'SentimentType', 'Value': 'Mixed'}],
                 'MetricName': 'SentimentScore',
                 'Value': 0.1}]

    mock_cloudwatch.put_metric_data.assert_called_with(
        Namespace='TweetSentiment',
        MetricData=expected
    )


def test_handler_unsupported_language(mocker, mock_comprehend, mock_cloudwatch):
    tweets = [
        {
            'id_str': '1',
            'full_text': 'unsupported language',
            'user': {
                'screen_name': 'foo'
            }
        }
    ]

    # testing cases where no result is returned or no languages are returned as well as case where results are returned
    mock_comprehend.batch_detect_dominant_language.return_value = {
        'ResultList': [
            {
                'Index': 0,
                'Languages': [
                    {
                        'LanguageCode': 'unsupported',
                        'Score': 1.0
                    }
                ]
            }
        ]
    }

    tweetsentiment.handler(tweets, None)

    mock_comprehend.batch_detect_sentiment.assert_not_called()
    mock_cloudwatch.put_metric_data.assert_not_called()
