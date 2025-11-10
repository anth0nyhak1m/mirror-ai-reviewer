import {
  AnalysisApi,
  Configuration,
  EvaluationApi,
  FeedbackApi,
  HealthApi,
  WorkflowsApi,
  Middleware,
} from './generated-api';
import { getSession } from 'next-auth/react';

export const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// Middleware to add Bearer token to all requests
const authMiddleware: Middleware = {
  pre: async (context) => {
    const session = await getSession();

    if (session?.accessToken) {
      context.init.headers = {
        ...context.init.headers,
        Authorization: `Bearer ${session.accessToken}`,
      };
    }
    return context;
  },
};

const config = new Configuration({
  basePath: apiUrl,
  middleware: [authMiddleware],
});

export const analysisApi = new AnalysisApi(config);
export const evaluationApi = new EvaluationApi(config);
export const feedbackApi = new FeedbackApi(config);
export const healthApi = new HealthApi(config);
export const workflowsApi = new WorkflowsApi(config);
