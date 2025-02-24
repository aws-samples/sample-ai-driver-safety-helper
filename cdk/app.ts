#!/usr/bin/env node
import { App, Aspects } from 'aws-cdk-lib';
import { AwsSolutionsChecks } from 'cdk-nag';
import { VideoAnalysisStack } from './lib/video-analysis-stack';

const app = new App();
new VideoAnalysisStack(app, 'VideoAnalysisStack');

// Add the cdk-nag AwsSolutions Pack
Aspects.of(app).add(new AwsSolutionsChecks());