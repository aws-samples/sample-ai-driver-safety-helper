# Runtime: Python 3.12
import os
import json
import os
import shutil
import tempfile

import boto3
from detect import combine_frames, analyze_frames_with_bedrock

# Create clients
s3 = boto3.client('s3')

# Constants
TMP_DIR = tempfile.gettempdir()

def download_video_from_s3(bucket: str, key: str) -> str:
    """Downloads a video from S3 and returns the local path"""
    local_path = os.path.join(TMP_DIR, os.path.basename(key))
    s3.download_file(bucket, key, local_path)
    return local_path

def lambda_handler(event, context):
    try:
        # Get input bucket from environment variable
        input_bucket = os.environ['INPUT_BUCKET_NAME']
        front_video_key = event['front_video_key']
        driver_video_key = event['driver_video_key']
        side_video_key = event['side_video_key']
        inference_profile_arn = os.environ['INFERENCE_PROFILE_ARN']
        target_fps = event.get('target_fps', 2)
        
        # Download videos from S3
        front_video = download_video_from_s3(input_bucket, front_video_key)
        driver_video = download_video_from_s3(input_bucket, driver_video_key)
        side_video = download_video_from_s3(input_bucket, side_video_key)
        
        # List of input video files
        video_files = [front_video, driver_video, side_video]
        
        # Create temporary output directory
        output_dir = os.path.join(TMP_DIR, 'output_frames')
        os.makedirs(output_dir, exist_ok=True)
        
        # Combine frames
        frame_paths, total_frames = combine_frames(
            video_files,
            output_dir=output_dir,
            target_fps=target_fps
        )
        
        # Analyze frames with Bedrock
        summary = analyze_frames_with_bedrock(
            frame_paths,
            inference_profile_arn=inference_profile_arn
        )
        
        # No longer uploading to S3 - return summary directly
        
        # Cleanup temporary files
        for file in video_files + frame_paths:
            if os.path.exists(file):
                os.remove(file)
        if os.path.exists(output_dir):
            os.rmdir(output_dir)
        
        return {
            'statusCode': 200,
            'body': {
                'message': f'Successfully analyzed {total_frames} frames',
                'summary': summary
            }
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'body': {
                'error': str(e)
            }
        }