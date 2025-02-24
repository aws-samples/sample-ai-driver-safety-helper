# Video Analysis Application

## Overview
This application processes near real-time multi-camera video feeds captured from highway vehicles using Amazon S3, AWS Lambda, and Amazon Nova Pro model to perform automated analysis of traffic patterns and safety concerns. The system detects and analyzes potential hazards including:

- Vehicle proximity warnings
- Lane departure risks
- Sudden brake events
- Unsafe merging behavior
- Adverse weather conditions
- Road obstacles and debris

The analysis pipeline works in two stages:

- Video Processing: The application processes multi-camera video feeds in near real-time, converting them into synchronized frame sequences for comprehensive vehicle surroundings coverage.
- Intelligent Analysis: Using Amazon Nova Pro model, the system analyzes the combined frames to generate detailed event summaries and risk assessments, with typical processing latency of a few seconds.

The outcomes are delivered through:

- Near real-time driver alerts via dashboard integration
- Mobile app notifications for fleet managers
- Detailed event logs for safety analysis
- Weekly/monthly safety reports for fleet optimization

This approach to hazard detection and driver notification helps prevent accidents and improve overall road safety while building a valuable database of traffic patterns and risk scenarios.

Below is a composite image frame that demonstrates how the application synchronizes and combines footage from multiple vehicle cameras to create a comprehensive view of the vehicle's surroundings:
![Sample picture frame](./images/sample-combined-frame.png)

Below is a representative analysis output from the Amazon Nova Pro model, demonstrating how the system identifies and categorizes potential road hazards and safety concerns:
```json
{
  "severity": "high",
  "summary": "The observations indicate a high-risk situation primarily due to distracted driving. The driver is using a mobile phone, significantly increasing the likelihood of an accident. Additionally, the close proximity of vehicles, especially behind a large truck, poses a risk of rear-end collisions if the driver is not attentive. The varying speeds of vehicles and predominant use of the left lane also contribute to potential safety hazards. Environmental conditions are currently clear, but the overcast sky could affect visibility if it leads to rain."
}
```

## Architecture
![Solution Archtiecture](./images/solution-architecture.png)

## Deployment
### Prerequisites
- AWS Account with appropriate permissions
- Node.js 18.x or later
- AWS CDK CLI installed (`npm install -g aws-cdk`)
- TypeScript knowledge for infrastructure customization
- Python 3.12 or later
- AWS CLI installed and configured
- Docker (for local development)
- Model access to Amazon Nova Pro 
- Inference profile ARN for using Amazon Nova Pro
- 3 video files that show views of the road on the front, and side, and a driver facing view (you can use Amazon Nova Reel to generate videos for testing)

### Clone repository
   ```bash   
   cd sample-ai-driver-safety-helper
   ```
### Local Testing 
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows use: .venv\Scripts\activate
   pip install -r requirements.txt
   python detect.py \
      --front-video ./front.mp4 \
      --driver-video ./driver.mp4 \
      --side-video ./side.mp4 \
      --inference-profile "arn:aws:bedrock:us-east-1:845368224021:inference-profile/us.amazon.nova-pro-v1:0" \
      --output-dir output_frames \
      --target-fps 1 
   ```
### Cloud deployment
- Initialize and configure the CDK environment (this is a Node.js managed CDK project):
   ```bash
   # Install Node.js dependencies
   cd cdk
   npm install   
   cd ..
   ```
- Bootstrap your AWS environment (if not already done):
   ```bash
   cdk bootstrap
   ```
- Deploy the application with the required inference profile ARN:
   ```bash
   cd cdk
   cdk deploy --context inference_profile_arn=arn:aws:bedrock:us-east-1:account_id:inference-profile/us.amazon.nova-pro-v1:0
   ```
The deployment will create:
- An S3 bucket for video uploads
- A Lambda function for video processing
- Required IAM roles and permissions
### Cloud Testing
- Upload a test video "front.mp4" to the created S3 bucket:
   ```bash
   aws s3 cp front.mp4 s3://your-bucket-name/
   ```
- Execute the Lambda function:
   - Invoke the Lambda function with your video files from the Lambda console using the sample event format shown below
   ```
   {
   "front_video_key": "front.mp4",
   "driver_video_key": "driver.mp4",
   "side_video_key": "side.mp4"
   }
   ```
   When the Lambda function completes, you will see the summary of the video analysis.
## Cleanup
To avoid incurring charges, clean up the resources when no longer needed:
- Remove the CDK stack:
   ```bash
   cd cdk
   cdk destroy
   ```
## Security
- The input S3 bucket is setup to block public access, enforce SSL, and with a lifecycle policy
- The process Lambda function's IAM role is setup with the minimum permissions required for S3, and Bedrock access
- Amazon Q Developer full project scan run reported 0 issues
- S3 permissions: Uses the S3 bucket's `grantRead()` method which creates least-privilege read permissions
- Bedrock permissions: Uses a specific policy statement with exact actions needed:
   - `bedrock:InvokeModel`
   - `bedrock:InvokeModelWithResponseStream`
- cdk_nag library and bandit tool are used to confirm infrastructure and application code patterns are using secure constructs




 

