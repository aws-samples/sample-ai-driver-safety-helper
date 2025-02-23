import cv2
import numpy as np
import boto3
import json
import base64
import os
import argparse
from typing import List

def add_caption(frame, text):
    """
    Add caption to the top of the frame
    
    Args:
        frame (numpy.ndarray): Input frame
        text (str): Caption text
    """
    text_height = 40
    caption_bg = np.zeros((text_height, frame.shape[1], 3), dtype=np.uint8)
    
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 1
    font_thickness = 2
    text_size = cv2.getTextSize(text, font, font_scale, font_thickness)[0]
    
    text_x = (frame.shape[1] - text_size[0]) // 2
    text_y = (text_height + text_size[1]) // 2
    
    cv2.putText(caption_bg, text, (text_x, text_y), font, font_scale, (255, 255, 255), font_thickness)
    
    return np.vstack((caption_bg, frame))

def analyze_frames_with_bedrock(frame_paths: List[str], inference_profile_arn: str, batch_size: int = 5) -> str:
    """
    Analyze frames using Amazon Bedrock Converse API
    
    Args:
        frame_paths (List[str]): List of paths to frame images
        inference_profile_arn (str): ARN of the Bedrock inference profile
        batch_size (int): Number of frames to process in each batch
    
    Returns:
        str: Summary of the video analysis
    """
    bedrock_runtime = boto3.client(
        service_name="bedrock-runtime",
        region_name=inference_profile_arn.split(":")[3]  # Extract region from ARN
    )

    all_observations = []
    
    # Process frames in batches
    for i in range(0, len(frame_paths), batch_size):
        batch_paths = frame_paths[i:i + batch_size]
        
        # Prepare the messages for conversation
        messages = []
        for frame_path in batch_paths:
            # Read image as bytes without encoding
            with open(frame_path, "rb") as image_file:
                image_bytes = image_file.read()
                
                messages.append({
                    "role": "user",
                    "content": [{
                        "image": {
                            "format": "jpeg",
                            "source": {
                                "bytes": image_bytes  # Send raw bytes directly
                            }
                        }
                    }]
                })
        
        # Add the analysis request message
        messages.append({
            "role": "user",
            "content": [{
                "text": "Analyze these synchronized camera views and describe what you observe. "
                        "Focus on any safety concerns or notable events."
            }]
        })
        
        try:
            # Use the Converse API
            response = bedrock_runtime.converse(
                modelId=inference_profile_arn,
                messages=messages,
                system=[{
                    "text": "You are an expert at analyzing multi-camera surveillance footage. "
                           "Provide detailed observations about activities, risks, and notable events "
                           "from the synchronized camera views (Front, Driver, and Side views)."
                }]
            )
            
            # Extract content from response
            if 'output' in response and 'message' in response['output'] and 'content' in response['output']['message']:
                observation = response['output']['message']['content'][0]['text']
                all_observations.append(observation)
            else:
                print(f"Unexpected response format: {response}")
            
        except Exception as e:
            print(f"Error processing batch starting at frame {i}: {str(e)}")
            continue
    
    # Generate final summary using Converse API
    try:
        # Combine all observations into a single text
        combined_observations = "\n\n".join(all_observations)
        
        final_response = bedrock_runtime.converse(
            modelId=inference_profile_arn,
            messages=[{
                "role": "user",
                "content": [{
                    "text": f"Please provide a concise summary of the following observations:\n\n{combined_observations}"
                }]
            }],
            system=[{
                "text": "Provide a JSON object with two fields, DO NOT provide any preamble; first one is a severity based on a risk of a high impact accident. Use high, medium, low for severity. For second field, include a short paragraph summary of the event."
            }]
        )

        # Extract content from final response
        if 'output' in final_response and 'message' in final_response['output'] and 'content' in final_response['output']['message']:
            return final_response['output']['message']['content'][0]['text']
        else:
            print(f"Unexpected final response format: {final_response}")
            return "Error: Unexpected response format"
    
    except Exception as e:
        print(f"Error generating final summary: {str(e)}")
        return "Error generating summary"






def combine_frames(videos, output_dir='/tmp/combined_frames', target_fps=2):
    """
    Combine frames from multiple videos side by side at specified FPS
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    else:
        # Clean up existing files
        for file in os.listdir(output_dir):
            os.remove(os.path.join(output_dir, file))           

    captions = ["Front View", "Driver View", "Side View"]
    captures = [cv2.VideoCapture(video) for video in videos]
    
    frame_counts = [int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) for cap in captures]
    fps_rates = [cap.get(cv2.CAP_PROP_FPS) for cap in captures]
    
    skip_frames = [int(fps/target_fps) for fps in fps_rates]
    min_frames = min(frame_counts)
    
    frame_number = 0
    output_frame_number = 0
    frame_paths = []
    
    while frame_number < min_frames:
        frames = []
        for cap_idx, cap in enumerate(captures):
            ret, frame = cap.read()
            if not ret:
                break
            
            if frame_number % skip_frames[cap_idx] == 0:
                frames.append(frame)
            else:
                continue
        
        if len(frames) != len(videos):
            frame_number += 1
            continue
            
        heights = [frame.shape[0] for frame in frames]
        min_height = min(heights)
        
        resized_frames = []
        for idx, frame in enumerate(frames):
            aspect_ratio = frame.shape[1] / frame.shape[0]
            new_width = int(min_height * aspect_ratio)
            resized = cv2.resize(frame, (new_width, min_height))
            resized_with_caption = add_caption(resized, captions[idx])
            resized_frames.append(resized_with_caption)
            
        combined_frame = np.hstack(resized_frames)
        
        output_path = os.path.join(output_dir, f'frame_{output_frame_number:04d}.jpg')
        cv2.imwrite(output_path, combined_frame)
        frame_paths.append(output_path)
        
        output_frame_number += 1
        frame_number += 1
    
    for cap in captures:
        cap.release()
    
    return frame_paths, output_frame_number

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='Process videos and analyze with Bedrock Nova Pro')
    parser.add_argument('--front-video', required=True, help='Path to front view video')
    parser.add_argument('--driver-video', required=True, help='Path to driver view video')
    parser.add_argument('--side-video', required=True, help='Path to side view video')
    parser.add_argument('--inference-profile', required=True, help='ARN of the Bedrock inference profile')
    parser.add_argument('--output-dir', default='output_frames', help='Directory for output frames')
    parser.add_argument('--target-fps', type=int, default=2, help='Target frames per second')
    return parser.parse_args()

def main():
    # Parse command line arguments
    args = parse_arguments()
    
    # List of input video files
    video_files = [
        args.front_video,   # Front view
        args.driver_video,  # Driver view
        args.side_video     # Side view
    ]
    
    # Combine frames at specified FPS
    frame_paths, total_frames = combine_frames(
        video_files, 
        output_dir=args.output_dir, 
        target_fps=args.target_fps
    )
    print(f"Successfully processed {total_frames} frames")
    
    # Analyze frames with Bedrock Nova Pro
    print("Analyzing frames with Amazon Bedrock Nova Pro...")
    summary = analyze_frames_with_bedrock(
        frame_paths,
        inference_profile_arn=args.inference_profile
    )
    
    print("\nAnalysis Summary:")
    print(summary)


if __name__ == '__main__':
    main()
