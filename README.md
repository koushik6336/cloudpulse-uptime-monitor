# project title : CloudPulse – Serverless Uptime & Latency Monitor

## Project Overview
CloudPulse is a serverless monitoring system built on AWS that automatically checks whether a website is up or down and measures its response time.

## Architecture
- Amazon S3 – Hosts the static website
- Amazon EventBridge – Runs every 5 minutes
- AWS Lambda – Checks uptime and latency
- Amazon DynamoDB – Stores monitoring results

## Workflow
1. A static website is hosted on Amazon S3.
2. Amazon EventBridge triggers every 5 minutes.
3. EventBridge invokes an AWS Lambda function.
4. Lambda checks website availability and response time.
5. Results are stored in DynamoDB.

## Project Structure
cloudpulse-uptime-monitor/
├── lambda/
│   └── uptime_check.py
├── website/
│   ├── index.html
│   └── style.css
├── architecture/
│   └── architecture-flow.txt
├── README.md
└── .gitignore

## Current Status (Till Day 4)
- Website hosted on Amazon S3
- Automated monitoring every 5 minutes
- Lambda function implemented
- Data stored in DynamoDB

- ## Day 5 – Latency Trend Detection
The system analyzes historical latency data stored in DynamoDB 
and detects performance degradation using moving average comparison.

## Technologies Used
- AWS Lambda
- Amazon S3
- Amazon EventBridge
- Amazon DynamoDB

## Future Enhancements
- Latency trend detection
- SLA calculation
- Alerting using Amazon SNS
- Auto-recovery mechanisms

