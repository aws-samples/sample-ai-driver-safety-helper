#!/usr/bin/env node
import { App } from 'aws-cdk-lib';
import { VideoAnalysisStack } from './lib/video-analysis-stack';

const app = new App();
new VideoAnalysisStack(app, 'VideoAnalysisStack');