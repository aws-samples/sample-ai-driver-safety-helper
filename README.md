# Video Analysis Application

## Overview
This application processes video files using AWS Lambda and S3 to perform automated analysis of traffic patterns and safety concerns.

## Architecture


## Prerequisites
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

## Local 

1. Clone the repository:
   ```bash   
   cd risk-detector-ai
   ```
2. Local Testing (Optional)
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
## Cloud deployment
3. Initialize and configure the CDK environment (this is a Node.js managed CDK project):
   ```bash
   # Install Node.js dependencies
   cd cdk
   npm install   
   cd ..
   ```
6. Bootstrap your AWS environment (if not already done):
   ```bash
   cdk bootstrap
   ```
7. Deploy the application with the required inference profile ARN:
   ```bash
   cd cdk
   cdk deploy --context inference_profile_arn=arn:aws:bedrock:us-east-1:845368224021:inference-profile/us.amazon.nova-pro-v1:0
   ```

   Replace REGION, ACCOUNT, and PROFILE_NAME with your specific values.

The deployment will create:
- An S3 bucket for video uploads
- A Lambda function for video processing
- Required IAM roles and permissions

## Testing
1. Upload a test video "front.mp4" to the created S3 bucket:
   ```bash
   aws s3 cp front.mp4 s3://your-bucket-name/
   ```

2. Execute the Lambda function:
   - Invoke the Lambda function with your video files from the Lambda console using the sample event format shown below
   ```
   {
   "front_video_key": "front.mp4",
   "driver_video_key": "front.mp4",
   "side_video_key": "front.mp4"
   }
   ```
   When the Lambda function completes, you should see the summary of the video analysis.

3. Monitor the Lambda function execution:
   - Check CloudWatch Logs for processing status


## Cleanup
To avoid incurring charges, clean up the resources when no longer needed:

1. Remove the CDK stack:
   ```bash
   cd cdk
   cdk destroy
   ```

This will remove:
- S3 buckets (ensure they are empty first)
- Lambda function
- IAM roles
- CloudWatch log groups

## Security Considerations
- Ensure proper IAM permissions are configured
- Monitor CloudWatch logs for any security events
- Regularly update dependencies to patch security vulnerabilities
- Follow AWS security best practices for S3 bucket policies


## Code review
- Amazon Q Developer review tool reported 0 issues with code in this project

## Troubleshooting
- Check CloudWatch Logs for Lambda function errors
- If visualization output is not as expected:
  - Verify the correct visualization-mode parameter is being used
  - Check that the output format matches the selected mode (human-readable or JSON)
  - Ensure all video files are properly formatted and accessible
- Verify S3 bucket permissions
- Ensure IAM roles have proper policies attached
- Validate input video format and size requirements

 

