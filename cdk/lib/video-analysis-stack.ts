import { Stack, StackProps, RemovalPolicy, Duration } from 'aws-cdk-lib';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as s3 from 'aws-cdk-lib/aws-s3';
import * as iam from 'aws-cdk-lib/aws-iam';
import { Construct } from 'constructs';
import { NagSuppressions } from 'cdk-nag';

export class VideoAnalysisStack extends Stack {
  constructor(scope: Construct, id: string, props?: StackProps) {
    super(scope, id, props);
   
    // Get inference profile ARN from context
    const inferenceProfileArn = this.node.tryGetContext('inference_profile_arn');
    if (!inferenceProfileArn) {
      throw new Error('inference_profile_arn must be provided in context');
    }

    // Create input S3 bucket
    const inputBucket = new s3.Bucket(this, 'VideoInputBucket', {
      removalPolicy: RemovalPolicy.DESTROY,
      autoDeleteObjects: true,
      encryption: s3.BucketEncryption.S3_MANAGED,
      enforceSSL: true,
      serverAccessLogsPrefix: 'logs/',
      blockPublicAccess: s3.BlockPublicAccess.BLOCK_ALL,
      lifecycleRules: [
        {
          expiration: Duration.days(1)
        }
      ]
    });   

    // Create Lambda function from Docker image
    const lambdaFunction = new lambda.DockerImageFunction(this, 'VideoAnalysisFunction', {
      code: lambda.DockerImageCode.fromImageAsset('../app', {
        file: 'Dockerfile'
      }),
      timeout: Duration.minutes(15),
      memorySize: 2048,
      environment: {
        INPUT_BUCKET_NAME: inputBucket.bucketName,
        INFERENCE_PROFILE_ARN: inferenceProfileArn,
        PYTHONPATH: '/var/task'
      }
    });

    // Grant permissions
    inputBucket.grantRead(lambdaFunction);

    // Grant Bedrock permissions
    lambdaFunction.addToRolePolicy(
      new iam.PolicyStatement({
        actions: [
          'bedrock:InvokeModel',
          'bedrock:InvokeModelWithResponseStream'
        ],
        resources: [
          inferenceProfileArn,
          // Add foundation model access based on inference profile pattern - region is replaced with a * for cross region support
          inferenceProfileArn.replace(/arn:aws:bedrock:[^:]+:[0-9]+:inference-profile\/.+/, 'arn:aws:bedrock:*::foundation-model/*')
        ]  // Allow access to both inference profile and foundation model
      })
    );

    // Add stack-level suppressions for Lambda basic execution role, S3 read access, and Bedrock cross-region inference
    NagSuppressions.addStackSuppressions(this, [
      {
        id: 'AwsSolutions-IAM4',
        reason: 'Lambda basic execution role is acceptable for this use case'
      },
      {
        id: 'AwsSolutions-IAM5',
        reason: 'Lambda S3 grantRead and Bedrock require cross-region access',
      }
    ]);

  }
}