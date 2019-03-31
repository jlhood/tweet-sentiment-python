# tweet-sentiment

![Build Status](https://codebuild.us-east-1.amazonaws.com/badges?uuid=eyJlbmNyeXB0ZWREYXRhIjoiUm92emZwZEswbVFianZFa21YY3JFblU1NzNhL0lKYVJXVzM2MkdhNlRia3ROSWx2VERSYXFyWVV3NWk1ckJrc3I3UFJIdWNRRHJrM1JyVjJHdTZkUmlnPSIsIml2UGFyYW1ldGVyU3BlYyI6Ik5BNDBydlY5UmFGdWdjMHYiLCJtYXRlcmlhbFNldFNlcmlhbCI6MX0%3D&branch=master)

This serverless app processes tweets for a given Twitter search, calls [Amazon Comprehend](https://aws.amazon.com/comprehend/) to do sentiment analysis on the tweet text, and publishes the sentiment scores as custom metrics to [Amazon CloudWatch](https://aws.amazon.com/cloudwatch/) Metrics.

## App Architecture

![App Architecture](https://github.com/jlhood/tweet-sentiment-python/raw/master/images/app-architecture.png)

1. The aws-serverless-twitter-event-source app is nested and configured to periodically invoke a Lambda function to process tweet search results. The app is used in stream mode, meaning it will remember which tweets have already been processed and only perform sentiment analysis on new tweets.
1. The Lambda function is invoked with a batch of tweets to process and calls Amazon Comprehend to get sentiment scores on the text of the batch of tweets.
1. Tweet sentiment scores are sent as custom metrics to CloudWatch and logged to the Lambda function's CloudWatch Logs log group.
1. The app includes a CloudWatch Dashboard for convenient monitoring of tweet sentiment metrics and logging.

## Installation Instructions

1. [Create an AWS account](https://portal.aws.amazon.com/gp/aws/developer/registration/index.html) if you do not already have one and login. 
1. Since this app uses [aws-serverless-twitter-event-source
](https://serverlessrepo.aws.amazon.com/applications/arn:aws:serverlessrepo:us-east-1:077246666028:applications~aws-serverless-twitter-event-source) as a nested app to provide tweet search results, you need to follow the steps to [create and install Twitter API keys](https://github.com/awslabs/aws-serverless-twitter-event-source#twitter-api-keys) for the aws-serverless-twitter-event-source app to use when calling the Twitter search API.
1. Once you've installed the Twitter API keys, go to the [tweet-sentiment](https://serverlessrepo.aws.amazon.com/#/applications/arn:aws:serverlessrepo:us-east-1:277187709615:applications~tweet-sentiment) Serverless Application Repository page and click "Deploy"
1. Provide the required app parameters (see parameter details below) and click "Deploy"

## Using the CloudWatch Dashboard

The app automatically creates a CloudWatch Dashboard for easy viewing of aggregate sentiment scores as well as top positive/negative tweets. Here are example screenshots where the app was configured to search for 'serverless':

![Dashboard Metrics Screenshot](https://github.com/jlhood/tweet-sentiment-python/raw/master/images/dashboard-screenshot-1.png)

![Dashboard Logs Screenshot](https://github.com/jlhood/tweet-sentiment-python/raw/master/images/dashboard-screenshot-2.png)

Amazon Comprehend returns 4 different sentiment scores for each tweet: Positive, Negative, Neutral, and Mixed. Each score is a value from 0 to 1 representing the likelihood that the sentiment was correctly detected. See the [Amazon Comprehend documentation](https://docs.aws.amazon.com/comprehend/latest/dg/how-sentiment.html) for more information on Amazon Comprehend's sentiment analysis.

The app also logs sentiment scores for each tweet to the TweetSentiment Lambda function's log group. The sentiment scores are logged using a structured format that allows for querying results using [CloudWatch Insights](https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/AnalyzingLogData.html). This allows you to drill down and find specific tweets based on their sentiment scores.

The included CloudWatch Dashboard displays the top positive and negative tweets within the selected time period. If you would like to run your own custom queries against the log data using CloudWatch Insights, on the dashboard, go to one of the CloudWatch Insights widgets and click on the "View in CloudWatch Insights" icon to the right of the widget title.

![Dashboard Logs Icon Screenshot](https://github.com/jlhood/tweet-sentiment-python/raw/master/images/dashboard-screenshot-3.png)

This will take you to the CloudWatch Insights console with the query text area pre-populated with the same query used to generate the Dashboard widget. You can then modify and run the query.

To learn more about querying logs using CloudWatch Insights, see [the documentation](https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/AnalyzingLogData.html).

## App Parameters

1. `SearchText` (required) - Search text to pass to Twitter. You can experiment with the Twitter search API at https://twitter.com/search-home
1. `PollingFrequencyInMinutes` (optional) - Frequency (in minutes) to poll for new tweets. Default: 5
1. `DashboardName` (optional) - CloudWatch dashboard name. If not specified, defaults to let CloudFormation name the Dashboard.
1. `DashboardPeriodInSeconds` (optional) - Period (in seconds) for graphs on CloudWatch dashboard. Valid values are 60 (1 minute), 300 (5 minute), or 3600 (1 hour). Default: 300 (5 minutes)
1. `LogLevel` (optional) - Log level for Lambda function logging, e.g., ERROR, INFO, DEBUG, etc. Default: INFO

## App Outputs

1. `TweetSentimentFunctionName` - TweetSentiment function name.
1. `TweetSentimentFunctionArn` - TweetSentiment function ARN.
1. `DashboardName` - CloudWatch Dashboard name.

## License Summary

This code is made available under the MIT license. See the LICENSE file.
