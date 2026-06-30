# Known Limitations in v1.0.0

While v1.0.0 is certified for production enterprise use, administrators should be aware of the following known limitations and planned enhancements:

1. **LLM Provider Agnosticism**
   - **Current State**: Hardcoded dependency on Google GenAI SDK (`google.genai`).
   - **Impact**: You cannot easily swap to OpenAI, Anthropic, or Local LLMs via configuration yet.
   - **Roadmap**: An abstraction layer for LLM providers is planned for v1.1.0.

2. **IAM/CloudWatch Cloudformation**
   - **Current State**: AWS definitions exist structurally as JSON templates, but they are not bundled into a one-click CloudFormation or Terraform stack.
   - **Impact**: DevOps must manually apply the IAM roles and CloudWatch alarms using the AWS CLI or Console.

3. **Rate Limiting**
   - **Current State**: Global rate limiting is applied via `SecurityMiddleware`.
   - **Impact**: Finer-grained, per-tenant or per-user rate limiting requires manual overrides.

4. **Webhooks / Event Emissions**
   - **Current State**: The Event system operates synchronously in the local FastAPI loop or via basic redis pubsub. 
   - **Impact**: Large scale event streaming (e.g. Apache Kafka) is not yet integrated.
