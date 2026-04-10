# Source File Analysis: AI Financial Planning System

## Project Overview

The AI Financial Planning System is a comprehensive, AI-driven platform designed to assist users with financial planning, including Monte Carlo simulations, trade-off analysis, and personalized retirement recommendations. It emphasizes high performance, robust security, and compliance through features like audit logging and controlled AI content generation.

**Key Technologies:**
*   **Backend:** Python (FastAPI, SQLAlchemy, Numba)
*   **Frontend:** React/Next.js (Tailwind CSS, Zustand)
*   **Database:** PostgreSQL
*   **AI/LLM:** OpenAI/Anthropic (configurable)
*   **Containerization:** Docker

**Core Functionalities:**
*   Financial plan creation and management
*   Monte Carlo and scenario simulations
*   AI-driven narrative generation for financial data
*   User authentication and management
*   Comprehensive audit logging for compliance and reproducibility

---

## File Analyses

### 1. /Users/rahulmehta/Desktop/Financial Planning/README.md

*   **Purpose:** Provides a high-level overview of the entire project, including its features, architecture, prerequisites, installation instructions, configuration details, API endpoints, testing procedures, performance considerations, security and compliance measures, deployment guidelines, documentation links, contribution guidelines, licensing, support information, and a project roadmap.
*   **Key Content:**
    *   Project description and core features.
    *   Detailed breakdown of backend (Python/FastAPI), frontend (React/Next.js), and database (PostgreSQL) architecture.
    *   Step-by-step setup instructions for development environment.
    *   Environment variable configurations and API endpoint examples.
    *   Information on testing, performance optimization, and security features.
    *   Links to other important documentation files within the project.
    *   Project roadmap outlining current, next, and future development phases.
*   **Role in Project:** This file serves as the primary entry point for anyone looking to understand, set up, or contribute to the project. It acts as a central hub for essential information and directs users to more detailed documentation where necessary.

---

### 2. /Users/rahulmehta/Desktop/Financial Planning/AI Financial Planner Implementation Guide.md

*   **Purpose:** Provides a detailed technical implementation guide for the AI-driven financial planning system, outlining its architecture, core components, data models, and critical compliance considerations. It serves as a deep-dive into the system's design and functionality.
*   **Key Content:**
    *   **System Architecture:** Expands on the microservices approach, detailing the roles of the backend, database, frontend, and generative AI integration.
    *   **Backend (Python/FastAPI):** In-depth explanation of the Monte Carlo simulation engine (inputs, CMA, portfolio mapping, path generation, outcome calculation, trade-off analysis, Numba/NumPy optimization) and specific FastAPI endpoints with their functionalities.
    *   **Database (PostgreSQL):** Detailed schema design for `plans`, `plan_inputs`, `plan_outputs`, and `audit_logs` tables, emphasizing the importance of `audit_logs` for reproducibility. Discusses JSONB usage and indexing.
    *   **Frontend (React/Next.js):** Describes the multi-step intake form design (personal info, financial snapshot, account buckets, risk preference, retirement goals) and the structure of the results dashboard (baseline, trade-offs, recommended allocation, AI narrative, export option).
    *   **Generative AI Integration:** Explains the narrative generation process using templated prompts, compliance disclaimer integration, and strict controls to prevent free-form financial advice.
    *   **PDF Export:** Details the PDF generation process (data compilation, HTML template rendering, PDF conversion using WeasyPrint/ReportLab) and its backend integration.
    *   **Compliance and Auditability:** Comprehensive section on audit logging (inputs, CMA version, random seed, output summary, timestamp, user ID), transparency of assumptions, and mandatory disclaimers.
    *   **API Endpoints and Data Models:** Provides a summary table of key API endpoints and detailed Pydantic models (`PlanInputModel`, `PlanCreationResponse`, `PlanStatusResponse`, `PlanResultsResponse`) with their fields and descriptions, crucial for understanding data flow.
*   **Role in Project:** This document is a core technical specification, guiding developers on the detailed implementation of various system components. It ensures a shared understanding of the system's design, data structures, and compliance requirements, serving as a foundational reference for development and maintenance.

---

### 3. /Users/rahulmehta/Desktop/Financial Planning/docker-compose.yml

*   **Purpose:** Defines and configures the multi-service Docker environment for the AI Financial Planning System. It orchestrates the setup, networking, and dependencies of various components, enabling easy local development and deployment.
*   **Key Content:**
    *   **Service Definitions:**
        *   `postgres`: PostgreSQL database for persistent data storage.
        *   `redis`: Redis instance for caching and session management.
        *   `backend`: The Python FastAPI application, building from its `Dockerfile` and serving the API.
        *   `frontend`: The Next.js React application, building from its `Dockerfile` and serving the user interface.
        *   `nginx`: An Nginx reverse proxy (activated with the `production` profile) for serving the frontend and backend, handling SSL.
        *   `celery_worker`: A Celery worker for processing background tasks (activated with the `full` profile).
        *   `celery_beat`: A Celery Beat instance for scheduling periodic tasks (activated with the `full` profile).
        *   `flower`: A web-based tool for monitoring Celery tasks (activated with the `full` profile).
    *   **Networking:** Defines a `financial_network` bridge network to facilitate communication between services.
    *   **Volumes:** Specifies `postgres_data` and `redis_data` local volumes for data persistence across container restarts.
    *   **Dependencies:** Clearly outlines service dependencies (e.g., `backend` depends on `postgres` and `redis`).
    *   **Environment Variables:** Sets environment variables for services, such as database connection details and API URLs.
    *   **Commands:** Defines the startup commands for each service (e.g., `uvicorn` for backend, `npm run dev` for frontend).
    *   **Profiles:** Utilizes Docker Compose profiles (`production`, `full`) to enable or disable certain services based on the desired environment or functionality.
*   **Role in Project:** This file is fundamental for setting up the development and production environments. It encapsulates the entire application stack, ensuring consistency and ease of deployment across different machines. It's the go-to file for understanding the project's runtime architecture and how its various microservices are interconnected.

---

### 4. /Users/rahulmehta/Desktop/Financial Planning/backend/requirements.txt

*   **Purpose:** Lists all Python package dependencies required for the backend application, specifying exact versions to ensure consistent environments and reproducible builds.
*   **Key Content:**
    *   **Web Framework & Server:** FastAPI, Uvicorn, Gunicorn.
    *   **Database & ORM:** SQLAlchemy (async), Asyncpg, Alembic, Psycopg2.
    *   **Authentication & Security:** Python-jose, Passlib (bcrypt), Python-decouple, Cryptography, Fernet, Keyring, Argon2-cffi, PyNaCl.
    *   **Data Validation:** Pydantic, Pydantic-settings.
    *   **HTTP Clients:** Httpx, Aiohttp.
    *   **Financial Data & Core Computation:**
        *   Market Data: Yfinance, Alpha-Vantage, IEXFinance.
        *   Data Manipulation: Pandas, NumPy, Polars.
        *   Performance Optimization: Numba.
        *   Scientific Computing & ML: SciPy, Scikit-learn, PyMC, Arviz, Statsmodels, XGBoost, LightGBM.
        *   Financial Calculations: QuantLib-Python, TA-Lib.
        *   Economic Data: Fredapi, Quandl.
        *   Portfolio Optimization & Risk: CVXPY, PyPortfolioOpt, Pyfolio.
        *   Alternative Data: Investpy.
    *   **Caching:** Redis, Aioredis.
    *   **Background Tasks:** Celery, Celery[redis].
    *   **Monitoring & Logging:** Structlog, Sentry-SDK.
    *   **Rate Limiting:** Slowapi.
    *   **Email:** FastAPI-Mail.
    *   **Testing:** Comprehensive suite including Pytest and various plugins for async, mocking, coverage, distributed testing, benchmarking, HTML reports, and security (Safety, Bandit). Also includes Factory-boy, Faker, Freezegun, Responses, Aioresponses, Testcontainers, Locust.
    *   **Development Tools:** Black, Isort, Flake8, Mypy, Pre-commit.
    *   **Environment & Configuration:** Python-dotenv.
    *   **Date & Time:** Python-dateutil, Pytz.
    *   **UUID:** Uuid.
    *   **File Processing:** Openpyxl, Xlsxwriter.
    *   **API Documentation:** FastAPI-Users.
    *   **Websockets:** Websockets, Python-socketio.
    *   **Transaction Analysis & NLP:** SpaCy, TextBlob, NLTK, Word2number, Num2words.
    *   **Voice & Speech Services:** Google-Cloud-Speech, Google-Cloud-Text-to-Speech, Boto3 (Amazon Polly), Pydub, SpeechRecognition, PyAudio, Pyttsx3, WebRTCVAD, Librosa, Soundfile.
    *   **PDF Generation:** Weasyprint, Reportlab, Pillow, PyPDF, Plotly, Kaleido.
    *   **Banking Integration:** Plaid-Python, Yodlee-Python.
*   **Role in Project:** This file is critical for understanding the full technological breadth and capabilities of the backend. It reveals the specific libraries used for core financial computations, AI/ML, data processing, real-time communication, security, and newly identified areas like voice interaction and banking integration. It dictates the Python environment for the backend and serves as a manifest of its functional scope.

---

### 5. /Users/rahulmehta/Desktop/Financial Planning/backend/Dockerfile

*   **Purpose:** Defines the steps to build a Docker image for the FastAPI backend application, ensuring a consistent and isolated runtime environment.
*   **Key Content:**
    *   **Base Image:** Uses `python:3.11-slim` for a lightweight Python environment.
    *   **Environment Variables:** Sets `PYTHONUNBUFFERED`, `PYTHONDONTWRITEBYTECODE`, and pip optimizations.
    *   **Working Directory:** Sets `/app` as the working directory inside the container.
    *   **System Dependencies:** Installs `build-essential`, `libpq-dev` (for PostgreSQL client), `curl`, and `git` using `apt-get`.
    *   **Python Dependencies:** Copies `requirements.txt` and installs all Python packages using `pip`, leveraging Docker's layer caching.
    *   **Application Code:** Copies the entire backend project into the container.
    *   **Security:** Creates and switches to a non-root `appuser` for running the application, improving security posture.
    *   **Port Exposure:** Exposes port `8000`, the default port for the FastAPI application.
    *   **Health Check:** Configures a `HEALTHCHECK` command to verify the application's responsiveness via a `/health` endpoint.
    *   **Startup Command:** Defines the default command to run the FastAPI application using `uvicorn` on container startup.
*   **Role in Project:** This Dockerfile is crucial for containerizing the backend service, enabling consistent development, testing, and deployment across different environments. It defines the exact environment and dependencies required for the backend to run, making it a key component of the project's DevOps strategy.

---

### 6. /Users/rahulmehta/Desktop/Financial Planning/backend/app/main.py

*   **Purpose:** Serves as the main entry point and configuration hub for the FastAPI backend application. It initializes the FastAPI instance, sets up global middleware, includes API routes, defines custom exception handling, and manages application startup events and health checks.
*   **Key Content:**
    *   **FastAPI App Initialization:** Creates the `FastAPI` application instance, pulling metadata (title, description, version, OpenAPI/docs URLs) from `app.core.config.settings`.
    *   **Middleware Configuration:**
        *   `CORSMiddleware`: Configures Cross-Origin Resource Sharing based on `settings.BACKEND_CORS_ORIGINS`, allowing secure communication with the frontend.
        *   `TrustedHostMiddleware`: Protects against HTTP Host header attacks by restricting allowed hosts.
    *   **API Routing:** Includes the `api_router` from `app.api.v1.api`, effectively mounting all API endpoints under a versioned prefix (e.g., `/api/v1`). This indicates a clear API versioning strategy.
    *   **Custom Exception Handling:** Implements a handler for `CustomException` to provide standardized error responses.
    *   **Startup Event (`on_event("startup")`):** Executes `init_db()` from `app.database.init_db` when the application starts, ensuring database readiness.
    *   **Health Check Endpoints:** Provides `/` (basic) and `/health` (detailed) endpoints to report the application's status, version, database connection, and simulation engine readiness.
*   **Role in Project:** This file is central to the backend's operation. It acts as the orchestrator, bringing together various components (configuration, API routes, database initialization, error handling) to form a cohesive and functional web service.

---

### 7. /Users/rahulmehta/Desktop/Financial Planning/backend/app/ai/README.md

*   **Purpose:** Provides a comprehensive overview and technical documentation for the AI Narrative Generation System, detailing its functionalities, architecture, configuration, API, and operational guidelines.
*   **Key Content:**
    *   **Overview:** Explains the system's role in generating intelligent, context-aware financial narratives using OpenAI GPT-4 and Anthropic Claude.
    *   **Core Capabilities:** Highlights dual LLM integration, templated prompts, multi-language support (English, Spanish, Chinese), robust compliance and safety features (disclaimers, content filtering, audit logging), Redis-based caching, A/B testing framework, and fallback mechanisms.
    *   **Narrative Types:** Lists specific financial narrative categories generated (e.g., Simulation Summary, Trade-Off Analysis, Recommendations).
    *   **Architecture:** Outlines the directory structure and the role of each Python file within the `app/ai` module (e.g., `llm_client.py`, `narrative_generator.py`, `safety_controller.py`).
    *   **Configuration:** Details environment variables for API keys and optional settings for AI behavior, caching, and auditing.
    *   **API Endpoints:** Provides examples and descriptions for generating single or batch narratives, listing templates, and submitting feedback.
    *   **Template System:** Explains the use of Jinja2 syntax, variable types, and the process for creating custom narrative templates.
    *   **Multi-Language Support:** Describes language detection and localized number formatting.
    *   **Compliance & Safety:** Emphasizes disclaimers, content validation (numerical consistency, PII detection), and detailed audit logging of LLM interactions.
    *   **Caching Strategy:** Details Redis integration for performance optimization.
    *   **A/B Testing Framework:** Describes how A/B tests are configured and what metrics are tracked.
    *   **Error Handling:** Outlines a multi-stage fallback strategy for LLM failures and common error types.
    *   **Performance Optimization:** Discusses batch processing and token optimization techniques.
    *   **Integration Examples:** Illustrates how the AI module integrates with other parts of the financial planning system.
    *   **Monitoring & Analytics:** Defines key performance metrics and provides a dedicated health check endpoint.
    *   **Best Practices & Troubleshooting:** Offers guidelines for development, template design, API usage, security, and common issue resolution.
*   **Role in Project:** This README is the definitive guide for understanding the AI component of the system. It serves as a critical resource for developers working on AI features, ensuring adherence to design principles, compliance requirements, and operational best practices. It also provides valuable context for anyone trying to understand the system's AI capabilities and how they are implemented.

---

### 8. /Users/rahulmehta/Desktop/Financial Planning/backend/app/ai/llm_client.py

*   **Purpose:** Manages the interaction with various Large Language Model (LLM) providers (OpenAI, Anthropic) and implements a robust system for generating AI narratives, including provider selection, caching, and a multi-stage fallback mechanism.
*   **Key Content:**
    *   **`NarrativeType` Enum:** Defines categories for financial narratives.
    *   **`LLMResponse` BaseModel:** Standardizes the structure of responses received from LLMs.
    *   **`BaseLLMClient` (ABC):** An abstract class defining the common interface (`generate`, `validate_api_key`) for all LLM client implementations.
    *   **`OpenAIClient`:** Concrete implementation for OpenAI's GPT models, handling API calls, system/user prompt construction, error logging, and API key validation.
    *   **`AnthropicClient`:** Concrete implementation for Anthropic's Claude models, with similar functionalities to `OpenAIClient`.
    *   **`FallbackClient`:** Provides static, pre-defined narratives as a last resort when external LLM APIs are unavailable, ensuring graceful degradation.
    *   **`LLMClientManager`:** The central class orchestrating LLM interactions:
        *   Initializes and manages instances of all LLM clients.
        *   Integrates **Redis caching** for responses, improving performance and reducing API calls.
        *   Implements a sophisticated **provider selection logic**, including A/B testing capabilities to compare different LLM approaches.
        *   Features a **multi-stage fallback strategy** (primary LLM -> secondary LLM -> static fallback) to ensure high availability and resilience.
        *   Performs **API key validation** for external providers.
        *   Logs all LLM generation attempts and outcomes to an `AuditLogger` for compliance and debugging.
*   **Role in Project:** This file is fundamental to the AI capabilities of the system. It abstracts away the complexities of interacting with different LLM providers, provides a resilient and performant mechanism for generating narratives, and ensures that AI interactions are auditable and compliant. It directly supports the "AI Integration" feature mentioned in the project's `README.md`.

---

### 9. /Users/rahulmehta/Desktop/Financial Planning/backend/app/ai/narrative_generator.py

*   **Purpose:** Implements the core business logic for generating AI-driven financial narratives. It orchestrates the process of rendering templates, interacting with Large Language Models (LLMs), ensuring content safety and compliance, and managing caching and A/B testing.
*   **Key Content:**
    *   **Initialization:** Sets up `TemplateManager`, `SafetyController`, and `AuditLogger`. It directly initializes synchronous OpenAI and Anthropic clients, using `asyncio.to_thread` for asynchronous execution.
    *   **`generate_narrative` (Main Workflow):**
        *   Renders a Jinja2 template with financial data.
        *   Performs **prompt safety validation** using `SafetyController`.
        *   Logs prompts to `AuditLogger`.
        *   Selects an LLM provider (OpenAI, Anthropic, or fallback) with **A/B testing logic**.
        *   Interacts with the chosen LLM to generate the narrative.
        *   Performs **output safety validation** and sanitization.
        *   Adds **compliance disclaimers** to the generated narrative.
        *   Logs the LLM response details (content, provider, tokens, latency) to `AuditLogger`.
        *   Includes **in-memory caching** (currently a placeholder, suggesting a more robust caching solution like Redis might be used elsewhere or intended).
        *   Tracks **A/B testing metrics** (latency, errors) for performance comparison.
        *   Implements robust **error handling** with fallback mechanisms.
    *   **`_generate_with_llm`:** Manages the actual LLM API calls, including constructing strict `system_prompt`s to guide LLM behavior (e.g., "NEVER provide specific investment advice"). It also handles retries and fallbacks between LLM providers.
    *   **`_call_openai` and `_call_anthropic`:** Methods for direct interaction with the respective LLM APIs, wrapped with `asyncio.to_thread` for non-blocking calls.
    *   **`_create_system_prompt`:** Generates critical system instructions for the LLMs, enforcing compliance rules and template adherence.
    *   **`_select_provider`:** Contains the logic for A/B testing and selecting the LLM provider.
    *   **Caching Logic:** Includes methods for generating cache keys, checking, and storing responses, though the current implementation uses a simple in-memory placeholder.
    *   **Fallback Mechanisms:** Provides methods to generate narratives without LLM interaction when errors occur or APIs are unavailable.
    *   **A/B Testing Analysis:** Methods to track and retrieve A/B test results.
    *   **`generate_batch_narratives`:** Supports concurrent generation of multiple narratives.
*   **Relationship with `llm_client.py`:** There appears to be some overlap in functionality (LLM client management, caching, fallback) with `llm_client.py`. `narrative_generator.py` directly initializes synchronous LLM clients and uses `asyncio.to_thread`, while `llm_client.py` uses asynchronous clients and a more centralized `LLMClientManager` for caching and fallbacks. This suggests potential for refactoring or a deliberate architectural choice for different layers of LLM interaction.
*   **Role in Project:** This file is central to the system's ability to generate client-friendly financial narratives. It embodies the core AI logic, ensuring that generated content is accurate, compliant, safe, and performant. It directly implements the "Generative AI Narratives" feature and the "Controlled Content Generation" principles outlined in the project documentation.

---

### 10. /Users/rahulmehta/Desktop/Financial Planning/backend/app/ai/safety_controller.py

*   **Purpose:** Enforces strict safety and compliance rules for AI-generated financial narratives, preventing the output of misleading, inaccurate, or harmful content. It acts as a guardian for the integrity and regulatory adherence of the AI system.
*   **Key Content:**
    *   **`SafetyViolationType` Enum:** Categorizes various types of potential safety and compliance breaches (e.g., `PROHIBITED_CONTENT`, `NUMERICAL_INCONSISTENCY`, `PII_DETECTED`, `ADVICE_VIOLATION`, `PROMPT_INJECTION`).
    *   **Rule Initialization:** Defines comprehensive sets of rules:
        *   `prohibited_terms`: Phrases that suggest specific, non-compliant financial advice (e.g., "guaranteed return").
        *   `injection_patterns`: Regular expressions to detect attempts at prompt injection.
        *   `pii_patterns`: Regular expressions to identify Personally Identifiable Information (PII) like SSNs, credit card numbers, emails, etc.
        *   `advice_patterns`: Phrases indicating the generation of specific financial advice, which is prohibited.
        *   `disclaimers`: Pre-defined legal disclaimers (general, projection, risk, tax) that must be included.
    *   **`validate_prompt`:** Checks incoming user prompts for prompt injection attempts, PII, and requests for specific financial advice.
    *   **`validate_output`:** A critical method that scrutinizes the AI-generated narrative for:
        *   Presence of prohibited terms, PII, and specific financial advice.
        *   **Numerical consistency:** Verifies that numbers present in the narrative align with the original numerical data provided, flagging potential hallucinations or inconsistencies.
        *   Presence of all **required disclaimers** based on the narrative's content type.
    *   **`_verify_numerical_consistency`:** Implements the logic for extracting and comparing numbers from the text against source data, with a defined tolerance.
    *   **`add_disclaimers`:** Programmatically inserts the necessary legal disclaimers into the narrative at specified positions.
    *   **`sanitize_output`:** Redacts PII and removes potentially malicious content (HTML/script tags, URLs) from the generated text.
    *   **Violation Logging and Reporting:** Tracks all detected safety violations and provides a `get_violation_report` method for monitoring and auditing purposes.
*   **Role in Project:** This file is paramount for the system's legal and ethical operation. It directly implements the "Compliance & Safety" features, particularly "Content filtering" and "Numerical validation," ensuring that the AI-generated narratives are not only helpful but also legally sound and trustworthy. It acts as a crucial gatekeeper for all AI outputs.

---

### 11. /Users/rahulmehta/Desktop/Financial Planning/backend/app/ai/template_manager.py

*   **Purpose:** Manages the creation, retrieval, and rendering of pre-defined templates used for generating AI narratives. It is a cornerstone of the "Controlled Content Generation" strategy, ensuring structured and compliant output from the LLMs.
*   **Key Content:**
    *   **`TemplateType` Enum:** Defines a comprehensive set of categories for financial narratives (e.g., `BASELINE_SUMMARY`, `SCENARIO_COMPARISON`, `RISK_ASSESSMENT`, `ACTION_RECOMMENDATION`, `GOAL_PROGRESS`, `PORTFOLIO_REVIEW`, `MARKET_OUTLOOK`, `TAX_IMPLICATIONS`).
    *   **Initialization:** Configures a Jinja2 environment to load templates from a specified directory (`backend/app/ai/templates`) and includes security features like autoescaping. It also initializes hardcoded default templates.
    *   **Default Templates:** Contains multi-line string definitions of various default narrative templates, pre-populated with Jinja2 placeholders for dynamic data insertion and formatting.
    *   **`get_template`:** Retrieves a template, prioritizing file-based templates over hardcoded defaults, allowing for customization and extensibility.
    *   **`render_template`:** The core method that takes a `TemplateType` and a dictionary of `data`, then populates the corresponding Jinja2 template. It includes:
        *   Optional **data validation** to ensure all required fields for a template are present.
        *   Addition of **default values** for any missing optional fields.
        *   Whitespace cleanup for clean output.
    *   **Data Validation Logic:** Methods like `_validate_template_data` and `_get_required_fields` ensure that the input data for rendering a template is complete and meets expectations.
    *   **`_add_default_values`:** Provides a mechanism to inject sensible default values for optional template variables.
    *   **`get_template_hash`:** Generates a hash of template content for versioning and caching purposes.
    *   **`list_available_templates`:** Provides metadata about all managed templates, including their type, name, hash, and required data fields.
*   **Role in Project:** This file is fundamental to ensuring the consistency, compliance, and quality of AI-generated narratives. By providing structured templates, it guides the LLMs to produce predictable and relevant content, preventing "hallucinations" and ensuring that critical financial information is presented accurately and in a standardized format. It directly supports the project's goal of auditable and compliant AI integration.

---

### 12. /Users/rahulmehta/Desktop/Financial Planning/backend/app/ai/audit_logger.py

*   **Purpose:** Implements a comprehensive and robust audit logging system specifically designed for the AI narrative generation process. It records detailed events related to LLM interactions, safety checks, caching, and A/B testing, ensuring traceability, compliance, and debugging capabilities.
*   **Key Content:**
    *   **`AuditEventType` Enum:** Defines a granular set of event types (e.g., `PROMPT_SUBMITTED`, `RESPONSE_GENERATED`, `SAFETY_VIOLATION`, `API_CALL`, `CACHE_HIT`, `AB_TEST`, `FALLBACK_USED`), providing fine-grained control over what is logged.
    *   **Initialization:** Configures log directory (`/var/log/financial_ai`), an in-memory buffer for batch writing to disk, and log file rotation settings. It sets up a structured Python logger that writes JSON Lines (`.jsonl`) to files.
    *   **Core Logging (`log_event`):** A central method that creates structured event dictionaries, buffers them, updates internal statistics, and triggers a flush to disk when the buffer is full.
    *   **Specific Logging Methods:** Provides dedicated asynchronous methods for various events:
        *   `log_prompt`: Records details of prompts sent to LLMs.
        *   `log_response`: Records details of generated AI narratives.
        *   `log_api_call`: Logs interactions with external LLM APIs (successes and errors).
        *   `log_safety_violation`: Records instances where safety rules are triggered.
        *   `log_cache_event`: Tracks cache hits and misses.
        *   `log_ab_test`: Logs A/B test participation and outcomes.
    *   **`flush` Method:** Asynchronously writes buffered log events to disk, ensuring data persistence.
    *   **Statistics & Reporting:** Maintains real-time statistics (e.g., total prompts, cache hits, API errors) and provides a `get_statistics` method to retrieve aggregated metrics like cache hit rate and API success rate.
    *   **Log Management & Analysis:** Includes powerful features for:
        *   `search_logs`: Searching historical logs by date range, event type, and user ID.
        *   `export_logs`: Exporting logs to files, with optional GZIP compression.
        *   `cleanup_old_logs`: Automatically deleting old log files based on a retention policy.
*   **Role in Project:** This file is fundamental for the system's compliance, auditability, and operational transparency. It provides the necessary infrastructure to maintain a complete and immutable record of all AI-related activities, which is critical for a financial application. It supports debugging, performance monitoring, and regulatory requirements by offering detailed, structured, and searchable logs.

---

### 13. /Users/rahulmehta/Desktop/Financial Planning/backend/app/ai/config.py

*   **Purpose:** Centralizes and manages all configuration settings for the AI narrative generation system. It defines parameters for LLM interaction, safety, caching, A/B testing, auditing, and compliance, allowing for easy environment-specific overrides via environment variables.
*   **Key Content:**
    *   **`LLMProvider` Enum:** Defines supported LLM providers (OpenAI, Anthropic, Fallback).
    *   **`Language` Enum:** Defines supported languages (English, Spanish, Chinese).
    *   **`AIConfig` (Pydantic `BaseSettings`):**
        *   **API Keys:** Loaded securely from environment variables (`OPENAI_API_KEY`, `ANTHROPIC_API_KEY`).
        *   **Model Configuration:** Default LLM models for each provider.
        *   **Temperature Settings:** `narrative_temperature`, `summary_temperature` to control LLM creativity (lower for factual content).
        *   **Token Limits:** `max_input_tokens`, `max_output_tokens` for managing LLM usage.
        *   **Safety Settings:** Boolean flags to enable/disable content filtering, prompt validation, and output validation.
        *   **Retry Configuration:** `max_retries`, `retry_delay` for API call resilience.
        *   **Cache Configuration:** `enable_response_caching`, `cache_ttl_seconds` for Redis caching.
        *   **A/B Testing:** `enable_ab_testing`, `ab_test_percentage` for configuring the A/B test framework.
        *   **Audit Settings:** `enable_audit_logging`, `audit_log_path` for controlling audit trail.
        *   **Rate Limiting:** `max_requests_per_minute`, `max_requests_per_hour` for API usage control.
        *   **Template Settings:** `template_version`, `strict_template_mode` (enforcing template-only responses) for controlled generation.
        *   **Language Settings:** `default_language`, `supported_languages`.
        *   **Compliance Settings:** `include_disclaimers`, `disclaimer_position` for legal disclaimers.
        *   **Numerical Validation:** `verify_numerical_consistency`, `numerical_tolerance` for data integrity checks.
    *   **`Config` Inner Class:** Specifies loading environment variables from `.env` file.
    *   **Global Instance:** `ai_config = AIConfig()` provides a singleton instance for easy access throughout the application.
*   **Role in Project:** This file is foundational for the entire AI module. It acts as the single source of truth for all AI-related operational parameters, ensuring consistent behavior across different components and environments. Its comprehensive nature directly supports the project's emphasis on configurability, compliance, safety, and performance in its AI capabilities.

---

### 14. /Users/rahulmehta/Desktop/Financial Planning/frontend/package.json

*   **Purpose:** Defines the frontend application's metadata, scripts for development and build processes, and lists all project dependencies (libraries and frameworks) and development tools. It serves as the manifest for the Next.js React application.
*   **Key Content:**
    *   **Project Metadata:** Name, version, description, and private status.
    *   **Scripts:** A comprehensive set of scripts for:
        *   Development (`dev`, `start`)
        *   Building (`build`)
        *   Code Quality (`lint`, `lint:fix`, `type-check`, `format`)
        *   Testing (`test`, `test:watch`, `test:coverage`)
        *   UI Component Development (`storybook`, `build-storybook`)
    *   **Dependencies:**
        *   **Core:** Next.js, React, React DOM, TypeScript.
        *   **Styling:** Tailwind CSS and related utilities (`tailwindcss-animate`, `class-variance-authority`, `clsx`, `tailwind-merge`).
        *   **UI Components:** Extensive use of Radix UI components for building accessible and customizable UI elements.
        *   **Icons:** Lucide React, Heroicons React.
        *   **Charting/Data Visualization:** Multiple libraries including Recharts, D3, Visx, Chart.js, and React Chart.js 2, indicating rich interactive data visualization capabilities.
        *   **Data Fetching:** Axios, React Query, SWR for efficient data management.
        *   **State Management & Forms:** Zustand (confirming the chosen state management solution), React Hook Form, Zod for form validation.
        *   **Animations:** Framer Motion, React Spring.
        *   **PDF Generation (Frontend):** `pdf-lib`, `jspdf`, `html2canvas` suggest client-side PDF generation or manipulation capabilities, complementing backend PDF generation.
        *   **Financial Calculations (Frontend):** `currency.js`, `big.js` for precise client-side financial arithmetic.
        *   **Other Utilities:** Date-fns, React Day Picker, Next Themes, React Hot Toast, Sonner, Cmdk, React Resizable Panels, Vaul, Embla Carousel, React Dropzone, Numeral, Lodash, UUID, React Intersection Observer, React Window, React Virtualized Auto Sizer.
    *   **Dev Dependencies:** Includes tools for type checking, linting (ESLint), formatting (Prettier), testing (Jest, React Testing Library), and Storybook for UI development.
    *   **Code Quality Enforcement:** Configuration for `husky`, `lint-staged`, and `commitlint` to enforce code style and commit message standards via Git hooks.
    *   **Engines & Browserslist:** Specifies compatible Node.js/npm versions and target browser environments.
*   **Role in Project:** This file is the central configuration for the frontend development environment and runtime. It dictates the technologies, libraries, and development practices used to build the user interface. Its comprehensive nature highlights the project's commitment to a modern, performant, and well-tested frontend experience, particularly in data visualization and user interaction.

---

### 15. /Users/rahulmehta/Desktop/Financial Planning/frontend/Dockerfile

*   **Purpose:** Defines the multi-stage Docker build process for the Next.js frontend application, resulting in an optimized and secure production-ready image.
*   **Key Content:**
    *   **Multi-Stage Build:** Uses two stages: `builder` and `runner`.
    *   **`builder` Stage:**
        *   Uses `node:18-alpine` as the base image.
        *   Installs production dependencies using `npm ci --only=production`.
        *   Copies the entire frontend source code.
        *   Executes `npm run build` to compile the Next.js application for production.
    *   **`runner` Stage (Production Image):**
        *   Uses a fresh `node:18-alpine` base image to keep the final image small.
        *   Sets `NODE_ENV=production` and disables Next.js telemetry.
        *   Creates a non-root user (`nextjs`) and group (`nodejs`) for enhanced security.
        *   Copies only the necessary built artifacts from the `builder` stage: `public` assets, `.next/standalone` (Next.js's self-contained output), and `.next/static` assets.
        *   Changes ownership of the application directory to the non-root user and switches to this user.
        *   Exposes port `3000`.
        *   Configures a `HEALTHCHECK` to verify the application's responsiveness via `http://localhost:3000/api/health`.
        *   Defines the `CMD` to start the Next.js production server (`node server.js`).
*   **Role in Project:** This Dockerfile is essential for containerizing the frontend service, enabling consistent and efficient deployment across various environments. Its multi-stage approach and focus on security (non-root user) and optimization (standalone output) are critical for delivering a performant and reliable user interface in production.

---

### 16. /Users/rahulmehta/Desktop/Financial Planning/frontend/src/app/page.tsx

*   **Purpose:** Serves as the main page component and orchestrator for the frontend application. It manages the overall user flow, transitioning between different application states (form input, loading, results display, error handling) and integrating various UI components and data services.
*   **Key Content:**
    *   **Client Component:** Declared with `"use client"`, indicating client-side rendering and interactivity.
    *   **State Management:** Utilizes React's `useState` for local component state (`appState`, `error`, `simulationResult`) and integrates with a global Zustand store (`useFinancialPlanningStore`) for shared application state (form data, loading indicators, notifications, stored results).
    *   **Lifecycle Management:** `useEffect` hooks handle loading existing simulation results from the store and setting up event listeners for form submissions.
    *   **`handleFormSubmit`:** The core logic for initiating a financial simulation. It includes:
        *   **Environment-based Logic:** Uses `process.env.NODE_ENV` to switch between mock data (for development, with simulated delay) and actual API calls (`financialPlanningAPI.runSimulation`) to the backend.
        *   Updates application state (`loading`, `simulationResult`, `appState`) and displays user notifications.
    *   **`handleExportPDF`:** Triggers client-side PDF generation using `exportToPDF` from `@/lib/pdfExport`, confirming the frontend's capability to create reports.
    *   **User Flow Control:** Functions like `handleRunNewSimulation`, `handleApplyScenario` (placeholder for future implementation), and `handleRetry` manage user navigation and state resets.
    *   **`LoadingScreen` Component:** Provides detailed visual feedback during the simulation process, including animated steps and estimated time, aligning with the backend's performance goals.
    *   **`ErrorScreen` Component:** Displays user-friendly error messages and options to retry or start over.
    *   **Conditional Rendering:** Dynamically renders `FormWizard`, `LoadingScreen`, `ErrorScreen`, or `ResultsDashboard` based on the current `appState`.
*   **Role in Project:** This file is the user's primary interaction point with the financial planning system. It binds together the user interface, application logic, and data flow, providing a seamless and interactive experience. Its robust state management, API integration, and user feedback mechanisms are crucial for the usability and perceived performance of the frontend application.

---

### 14. /Users/rahulmehta/Desktop/Financial Planning/frontend/package.json

*   **Purpose:** Defines the frontend application's metadata, scripts for development and build processes, and lists all project dependencies (libraries and frameworks) and development tools. It serves as the manifest for the Next.js React application.
*   **Key Content:**
    *   **Project Metadata:** Name, version, description, and private status.
    *   **Scripts:** A comprehensive set of scripts for:
        *   Development (`dev`, `start`)
        *   Building (`build`)
        *   Code Quality (`lint`, `lint:fix`, `type-check`, `format`)
        *   Testing (`test`, `test:watch`, `test:coverage`)
        *   UI Component Development (`storybook`, `build-storybook`)
    *   **Dependencies:**
        *   **Core:** Next.js, React, React DOM, TypeScript.
        *   **Styling:** Tailwind CSS and related utilities (`tailwindcss-animate`, `class-variance-authority`, `clsx`, `tailwind-merge`).
        *   **UI Components:** Extensive use of Radix UI components for building accessible and customizable UI elements.
        *   **Icons:** Lucide React, Heroicons React.
        *   **Charting/Data Visualization:** Multiple libraries including Recharts, D3, Visx, Chart.js, and React Chart.js 2, indicating rich interactive data visualization capabilities.
        *   **Data Fetching:** Axios, React Query, SWR for efficient data management.
        *   **State Management & Forms:** Zustand (confirming the chosen state management solution), React Hook Form, Zod for form validation.
        *   **Animations:** Framer Motion, React Spring.
        *   **PDF Generation (Frontend):** `pdf-lib`, `jspdf`, `html2canvas` suggest client-side PDF generation or manipulation capabilities, complementing backend PDF generation.
        *   **Financial Calculations (Frontend):** `currency.js`, `big.js` for precise client-side financial arithmetic.
        *   **Other Utilities:** Date-fns, React Day Picker, Next Themes, React Hot Toast, Sonner, Cmdk, React Resizable Panels, Vaul, Embla Carousel, React Dropzone, Numeral, Lodash, UUID, React Intersection Observer, React Window, React Virtualized Auto Sizer.
    *   **Dev Dependencies:** Includes tools for type checking, linting (ESLint), formatting (Prettier), testing (Jest, React Testing Library), and Storybook for UI development.
    *   **Code Quality Enforcement:** Configuration for `husky`, `lint-staged`, and `commitlint` to enforce code style and commit message standards via Git hooks.
    *   **Engines & Browserslist:** Specifies compatible Node.js/npm versions and target browser environments.
*   **Role in Project:** This file is the central configuration for the frontend development environment and runtime. It dictates the technologies, libraries, and development practices used to build the user interface. Its comprehensive nature highlights the project's commitment to a modern, performant, and well-tested frontend experience, particularly in data visualization and user interaction.

---

### 15. /Users/rahulmehta/Desktop/Financial Planning/frontend/Dockerfile

*   **Purpose:** Defines the multi-stage Docker build process for the Next.js frontend application, resulting in an optimized and secure production-ready image.
*   **Key Content:**
    *   **Multi-Stage Build:** Uses two stages: `builder` and `runner`.
    *   **`builder` Stage:**
        *   Uses `node:18-alpine` as the base image.
        *   Installs production dependencies using `npm ci --only=production`.
        *   Copies the entire frontend source code.
        *   Executes `npm run build` to compile the Next.js application for production.
    *   **`runner` Stage (Production Image):**
        *   Uses a fresh `node:18-alpine` base image to keep the final image small.
        *   Sets `NODE_ENV=production` and disables Next.js telemetry.
        *   Creates a non-root user (`nextjs`) and group (`nodejs`) for enhanced security.
        *   Copies only the necessary built artifacts from the `builder` stage: `public` assets, `.next/standalone` (Next.js's self-contained output), and `.next/static` assets.
        *   Changes ownership of the application directory to the non-root user and switches to this user.
        *   Exposes port `3000`.
        *   Configures a `HEALTHCHECK` to verify the application's responsiveness via `http://localhost:3000/api/health`.
        *   Defines the `CMD` to start the Next.js production server (`node server.js`).
*   **Role in Project:** This Dockerfile is essential for containerizing the frontend service, enabling consistent and efficient deployment across various environments. Its multi-stage approach and focus on security (non-root user) and optimization (standalone output) are critical for delivering a performant and reliable user interface in production.

---

### 16. /Users/rahulmehta/Desktop/Financial Planning/frontend/src/app/page.tsx

*   **Purpose:** Serves as the main page component and orchestrator for the frontend application. It manages the overall user flow, transitioning between different application states (form input, loading, results display, error handling) and integrating various UI components and data services.
*   **Key Content:**
    *   **Client Component:** Declared with `"use client"`, indicating client-side rendering and interactivity.
    *   **State Management:** Utilizes React's `useState` for local component state (`appState`, `error`, `simulationResult`) and integrates with a global Zustand store (`useFinancialPlanningStore`) for shared application state (form data, loading indicators, notifications, stored results).
    *   **Lifecycle Management:** `useEffect` hooks handle loading existing simulation results from the store and setting up event listeners for form submissions.
    *   **`handleFormSubmit`:** The core logic for initiating a financial simulation. It includes:
        *   **Environment-based Logic:** Uses `process.env.NODE_ENV` to switch between mock data (for development, with simulated delay) and actual API calls (`financialPlanningAPI.runSimulation`) to the backend.
        *   Updates application state (`loading`, `simulationResult`, `appState`) and displays user notifications.
    *   **`handleExportPDF`:** Triggers client-side PDF generation using `exportToPDF` from `@/lib/pdfExport`, confirming the frontend's capability to create reports.
    *   **User Flow Control:** Functions like `handleRunNewSimulation`, `handleApplyScenario` (placeholder for future implementation), and `handleRetry` manage user navigation and state resets.
    *   **`LoadingScreen` Component:** Provides detailed visual feedback during the simulation process, including animated steps and estimated time, aligning with the backend's performance goals.
    *   **`ErrorScreen` Component:** Displays user-friendly error messages and options to retry or start over.
    *   **Conditional Rendering:** Dynamically renders `FormWizard`, `LoadingScreen`, `ErrorScreen`, or `ResultsDashboard` based on the current `appState`.
*   **Role in Project:** This file is the user's primary interaction point with the financial planning system. It binds together the user interface, application logic, and data flow, providing a seamless and interactive experience. Its robust state management, API integration, and user feedback mechanisms are crucial for the usability and perceived performance of the frontend application.

---

### 17. /Users/rahulmehta/Desktop/Financial Planning/mobile/package.json

*   **Purpose:** Defines the mobile application's metadata, scripts for development and build processes, and lists all project dependencies and development tools. It serves as the manifest for the React Native mobile application.
*   **Key Content:**
    *   **Project Metadata:** Name, version, and private status.
    *   **Scripts:** Standard React Native scripts for running on Android/iOS, starting the bundler, testing, linting, and platform-specific build commands (`build:android`, `build:ios`, `pods`).
    *   **Dependencies:**
        *   **Core:** React, React Native.
        *   **Navigation:** Comprehensive navigation solutions (`@react-navigation/*`).
        *   **State Management:** Redux Toolkit (`@reduxjs/toolkit`, `react-redux`, `redux-persist`) for global state with persistence.
        *   **Data Fetching:** React Query (`react-query`) for server state management.
        *   **Local Storage:** Async Storage, MMKV (high-performance key-value store) for persistent local data.
        *   **Firebase:** Firebase App and Messaging for push notifications and other services.
        *   **Security/Biometrics:** React Native Biometrics, React Native Keychain for secure local authentication and credential storage.
        *   **Camera & Document Scanning:** Camera Roll, React Native Camera, React Native Document Scanner Plugin, suggesting capabilities for image capture, photo library access, and document scanning (e.g., receipts).
        *   **PDF Handling:** React Native PDF for displaying PDF documents.
        *   **Background Tasks:** React Native Background Job for executing tasks in the background.
        *   **Local Database:** WatermelonDB (`react-native-watermelondb`), indicating an observable, offline-first local database for robust data persistence and synchronization.
        *   **UI/Animation:** Various libraries for UI components, animations, and performance (e.g., `react-native-animatable`, `react-native-reanimated`, `FlashList`).
        *   **Networking:** NetInfo, RN Fetch Blob for network status and file handling.
    *   **Dev Dependencies:** Standard React Native development tools (Babel, ESLint, Jest, TypeScript).
    *   **Engines:** Specifies compatible Node.js version.
*   **Role in Project:** This file is crucial for defining the mobile application's technical stack and capabilities. It indicates that the mobile app is a feature-rich, potentially offline-first financial management tool, capable of advanced functionalities like document scanning, secure local data storage, and background processing, going beyond a simple companion app.

---

### 18. /Users/rahulmehta/Desktop/Financial Planning/mobile/App.tsx

*   **Purpose:** Serves as the root component and main entry point for the React Native mobile application. It sets up the global application environment, including navigation, state management, and initialization of various platform-specific services.
*   **Key Content:**
    *   **Core Setup:** Imports and integrates essential React Native libraries and components:
        *   `NavigationContainer` for managing app navigation.
        *   `Provider` (from `react-redux`) and `PersistGate` (from `redux-persist`) for Redux-based global state management with data persistence.
        *   `SplashScreen` for controlling the native splash screen visibility.
        *   `GestureHandlerRootView` and `SafeAreaProvider` for gesture handling and safe area management.
    *   **Service Initialization:** Uses a `useEffect` hook to asynchronously initialize critical services like `NotificationService` and `BiometricService` upon app startup. It also manages hiding the splash screen after initialization.
    *   **Global Hooks:** Integrates custom hooks (`useNetworkStatus`, `useAppStateHandler`) via dedicated, non-rendering components (`NetworkStatusHandler`, `AppStateHandler`) to manage global concerns like network connectivity and application foreground/background state.
    *   **Navigation Orchestration:** Renders `AppNavigator`, which is responsible for defining and managing the application's screen hierarchy and navigation flow.
    *   **UI Configuration:** Sets the `StatusBar` style based on the platform.
    *   **Loading State:** Displays a `LoadingScreen` while the Redux store is being rehydrated by `PersistGate`.
*   **Role in Project:** This file is the foundational layer of the mobile application. It ensures that all necessary services are initialized, the global state is managed and persisted, and the navigation structure is in place before the user interacts with the app. It is crucial for the overall stability, performance, and user experience of the mobile financial planning tool.

---

### 17. /Users/rahulmehta/Desktop/Financial Planning/mobile/package.json

*   **Purpose:** Defines the mobile application's metadata, scripts for development and build processes, and lists all project dependencies and development tools. It serves as the manifest for the React Native mobile application.
*   **Key Content:**
    *   **Project Metadata:** Name, version, and private status.
    *   **Scripts:** Standard React Native scripts for running on Android/iOS, starting the bundler, testing, linting, and platform-specific build commands (`build:android`, `build:ios`, `pods`).
    *   **Dependencies:**
        *   **Core:** React, React Native.
        *   **Navigation:** Comprehensive navigation solutions (`@react-navigation/*`).
        *   **State Management:** Redux Toolkit (`@reduxjs/toolkit`, `react-redux`, `redux-persist`) for global state with persistence.
        *   **Data Fetching:** React Query (`react-query`) for server state management.
        *   **Local Storage:** Async Storage, MMKV (high-performance key-value store) for persistent local data.
        *   **Firebase:** Firebase App and Messaging for push notifications and other services.
        *   **Security/Biometrics:** React Native Biometrics, React Native Keychain for secure local authentication and credential storage.
        *   **Camera & Document Scanning:** Camera Roll, React Native Camera, React Native Document Scanner Plugin, suggesting capabilities for image capture, photo library access, and document scanning (e.g., receipts).
        *   **PDF Handling:** React Native PDF for displaying PDF documents.
        *   **Background Tasks:** React Native Background Job for executing tasks in the background.
        *   **Local Database:** WatermelonDB (`react-native-watermelondb`), indicating an observable, offline-first local database for robust data persistence and synchronization.
        *   **UI/Animation:** Various libraries for UI components, animations, and performance (e.g., `react-native-animatable`, `react-native-reanimated`, `FlashList`).
        *   **Networking:** NetInfo, RN Fetch Blob for network status and file handling.
    *   **Dev Dependencies:** Standard React Native development tools (Babel, ESLint, Jest, TypeScript).
    *   **Engines:** Specifies compatible Node.js version.
*   **Role in Project:** This file is crucial for defining the mobile application's technical stack and capabilities. It indicates that the mobile app is a feature-rich, potentially offline-first financial management tool, capable of advanced functionalities like document scanning, secure local data storage, and background processing, going beyond a simple companion app.

---

### 14. /Users/rahulmehta/Desktop/Financial Planning/frontend/package.json

*   **Purpose:** Defines the frontend application's metadata, scripts for development and build processes, and lists all project dependencies (libraries and frameworks) and development tools. It serves as the manifest for the Next.js React application.
*   **Key Content:**
    *   **Project Metadata:** Name, version, description, and private status.
    *   **Scripts:** A comprehensive set of scripts for:
        *   Development (`dev`, `start`)
        *   Building (`build`)
        *   Code Quality (`lint`, `lint:fix`, `type-check`, `format`)
        *   Testing (`test`, `test:watch`, `test:coverage`)
        *   UI Component Development (`storybook`, `build-storybook`)
    *   **Dependencies:**
        *   **Core:** Next.js, React, React DOM, TypeScript.
        *   **Styling:** Tailwind CSS and related utilities (`tailwindcss-animate`, `class-variance-authority`, `clsx`, `tailwind-merge`).
        *   **UI Components:** Extensive use of Radix UI components for building accessible and customizable UI elements.
        *   **Icons:** Lucide React, Heroicons React.
        *   **Charting/Data Visualization:** Multiple libraries including Recharts, D3, Visx, Chart.js, and React Chart.js 2, indicating rich interactive data visualization capabilities.
        *   **Data Fetching:** Axios, React Query, SWR for efficient data management.
        *   **State Management & Forms:** Zustand (confirming the chosen state management solution), React Hook Form, Zod for form validation.
        *   **Animations:** Framer Motion, React Spring.
        *   **PDF Generation (Frontend):** `pdf-lib`, `jspdf`, `html2canvas` suggest client-side PDF generation or manipulation capabilities, complementing backend PDF generation.
        *   **Financial Calculations (Frontend):** `currency.js`, `big.js` for precise client-side financial arithmetic.
        *   **Other Utilities:** Date-fns, React Day Picker, Next Themes, React Hot Toast, Sonner, Cmdk, React Resizable Panels, Vaul, Embla Carousel, React Dropzone, Numeral, Lodash, UUID, React Intersection Observer, React Window, React Virtualized Auto Sizer.
    *   **Dev Dependencies:** Includes tools for type checking, linting (ESLint), formatting (Prettier), testing (Jest, React Testing Library), and Storybook for UI development.
    *   **Code Quality Enforcement:** Configuration for `husky`, `lint-staged`, and `commitlint` to enforce code style and commit message standards via Git hooks.
    *   **Engines & Browserslist:** Specifies compatible Node.js/npm versions and target browser environments.
*   **Role in Project:** This file is the central configuration for the frontend development environment and runtime. It dictates the technologies, libraries, and development practices used to build the user interface. Its comprehensive nature highlights the project's commitment to a modern, performant, and well-tested frontend experience, particularly in data visualization and user interaction.

---

### 15. /Users/rahulmehta/Desktop/Financial Planning/frontend/Dockerfile

*   **Purpose:** Defines the multi-stage Docker build process for the Next.js frontend application, resulting in an optimized and secure production-ready image.
*   **Key Content:**
    *   **Multi-Stage Build:** Uses two stages: `builder` and `runner`.
    *   **`builder` Stage:**
        *   Uses `node:18-alpine` as the base image.
        *   Installs production dependencies using `npm ci --only=production`.
        *   Copies the entire frontend source code.
        *   Executes `npm run build` to compile the Next.js application for production.
    *   **`runner` Stage (Production Image):**
        *   Uses a fresh `node:18-alpine` base image to keep the final image small.
        *   Sets `NODE_ENV=production` and disables Next.js telemetry.
        *   Creates a non-root user (`nextjs`) and group (`nodejs`) for enhanced security.
        *   Copies only the necessary built artifacts from the `builder` stage: `public` assets, `.next/standalone` (Next.js's self-contained output), and `.next/static` assets.
        *   Changes ownership of the application directory to the non-root user and switches to this user.
        *   Exposes port `3000`.
        *   Configures a `HEALTHCHECK` to verify the application's responsiveness via `http://localhost:3000/api/health`.
        *   Defines the `CMD` to start the Next.js production server (`node server.js`).
*   **Role in Project:** This Dockerfile is essential for containerizing the frontend service, enabling consistent and efficient deployment across various environments. Its multi-stage approach and focus on security (non-root user) and optimization (standalone output) are critical for delivering a performant and reliable user interface in production.

---

### 14. /Users/rahulmehta/Desktop/Financial Planning/frontend/package.json

*   **Purpose:** Defines the frontend application's metadata, scripts for development and build processes, and lists all project dependencies (libraries and frameworks) and development tools. It serves as the manifest for the Next.js React application.
*   **Key Content:**
    *   **Project Metadata:** Name, version, description, and private status.
    *   **Scripts:** A comprehensive set of scripts for:
        *   Development (`dev`, `start`)
        *   Building (`build`)
        *   Code Quality (`lint`, `lint:fix`, `type-check`, `format`)
        *   Testing (`test`, `test:watch`, `test:coverage`)
        *   UI Component Development (`storybook`, `build-storybook`)
    *   **Dependencies:**
        *   **Core:** Next.js, React, React DOM, TypeScript.
        *   **Styling:** Tailwind CSS and related utilities (`tailwindcss-animate`, `class-variance-authority`, `clsx`, `tailwind-merge`).
        *   **UI Components:** Extensive use of Radix UI components for building accessible and customizable UI elements.
        *   **Icons:** Lucide React, Heroicons React.
        *   **Charting/Data Visualization:** Multiple libraries including Recharts, D3, Visx, Chart.js, and React Chart.js 2, indicating rich interactive data visualization capabilities.
        *   **Data Fetching:** Axios, React Query, SWR for efficient data management.
        *   **State Management & Forms:** Zustand (confirming the chosen state management solution), React Hook Form, Zod for form validation.
        *   **Animations:** Framer Motion, React Spring.
        *   **PDF Generation (Frontend):** `pdf-lib`, `jspdf`, `html2canvas` suggest client-side PDF generation or manipulation capabilities, complementing backend PDF generation.
        *   **Financial Calculations (Frontend):** `currency.js`, `big.js` for precise client-side financial arithmetic.
        *   **Other Utilities:** Date-fns, React Day Picker, Next Themes, React Hot Toast, Sonner, Cmdk, React Resizable Panels, Vaul, Embla Carousel, React Dropzone, Numeral, Lodash, UUID, React Intersection Observer, React Window, React Virtualized Auto Sizer.
    *   **Dev Dependencies:** Includes tools for type checking, linting (ESLint), formatting (Prettier), testing (Jest, React Testing Library), and Storybook for UI development.
    *   **Code Quality Enforcement:** Configuration for `husky`, `lint-staged`, and `commitlint` to enforce code style and commit message standards via Git hooks.
    *   **Engines & Browserslist:** Specifies compatible Node.js/npm versions and target browser environments.
*   **Role in Project:** This file is the central configuration for the frontend development environment and runtime. It dictates the technologies, libraries, and development practices used to build the user interface. Its comprehensive nature highlights the project's commitment to a modern, performant, and well-tested frontend experience, particularly in data visualization and user interaction.

---

### 9. /Users/rahulmehta/Desktop/Financial Planning/backend/app/ai/narrative_generator.py

*   **Purpose:** Implements the core business logic for generating AI-driven financial narratives. It orchestrates the process of rendering templates, interacting with Large Language Models (LLMs), ensuring content safety and compliance, and managing caching and A/B testing.
*   **Key Content:**
    *   **Initialization:** Sets up `TemplateManager`, `SafetyController`, and `AuditLogger`. It directly initializes synchronous OpenAI and Anthropic clients, using `asyncio.to_thread` for asynchronous execution.
    *   **`generate_narrative` (Main Workflow):**
        *   Renders a Jinja2 template with financial data.
        *   Performs **prompt safety validation** using `SafetyController`.
        *   Logs prompts to `AuditLogger`.
        *   Selects an LLM provider (OpenAI, Anthropic, or fallback) with **A/B testing logic**.
        *   Interacts with the chosen LLM to generate the narrative.
        *   Performs **output safety validation** and sanitization.
        *   Adds **compliance disclaimers** to the generated narrative.
        *   Logs the LLM response details (content, provider, tokens, latency) to `AuditLogger`.
        *   Includes **in-memory caching** (currently a placeholder, suggesting a more robust caching solution like Redis might be used elsewhere or intended).
        *   Tracks **A/B testing metrics** (latency, errors) for performance comparison.
        *   Implements robust **error handling** with fallback mechanisms.
    *   **`_generate_with_llm`:** Manages the actual LLM API calls, including constructing strict `system_prompt`s to guide LLM behavior (e.g., "NEVER provide specific investment advice"). It also handles retries and fallbacks between LLM providers.
    *   **`_call_openai` and `_call_anthropic`:** Methods for direct interaction with the respective LLM APIs, wrapped with `asyncio.to_thread` for non-blocking calls.
    *   **`_create_system_prompt`:** Generates critical system instructions for the LLMs, enforcing compliance rules and template adherence.
    *   **`_select_provider`:** Contains the logic for A/B testing and selecting the LLM provider.
    *   **Caching Logic:** Includes methods for generating cache keys, checking, and storing responses, though the current implementation uses a simple in-memory placeholder.
    *   **Fallback Mechanisms:** Provides methods to generate narratives without LLM interaction when errors occur or APIs are unavailable.
    *   **A/B Testing Analysis:** Methods to track and retrieve A/B test results.
    *   **`generate_batch_narratives`:** Supports concurrent generation of multiple narratives.
*   **Relationship with `llm_client.py`:** There appears to be some overlap in functionality (LLM client management, caching, fallback) with `llm_client.py`. `narrative_generator.py` directly initializes synchronous LLM clients and uses `asyncio.to_thread`, while `llm_client.py` uses asynchronous clients and a more centralized `LLMClientManager` for caching and fallbacks. This suggests potential for refactoring or a deliberate architectural choice for different layers of LLM interaction.
*   **Role in Project:** This file is central to the system's ability to generate client-friendly financial narratives. It embodies the core AI logic, ensuring that generated content is accurate, compliant, safe, and performant. It directly implements the "Generative AI Narratives" feature and the "Controlled Content Generation" principles outlined in the project documentation.

---

### 10. /Users/rahulmehta/Desktop/Financial Planning/backend/app/ai/safety_controller.py

*   **Purpose:** Enforces strict safety and compliance rules for AI-generated financial narratives, preventing the output of misleading, inaccurate, or harmful content. It acts as a guardian for the integrity and regulatory adherence of the AI system.
*   **Key Content:**
    *   **`SafetyViolationType` Enum:** Categorizes various types of potential safety and compliance breaches (e.g., `PROHIBITED_CONTENT`, `NUMERICAL_INCONSISTENCY`, `PII_DETECTED`, `ADVICE_VIOLATION`, `PROMPT_INJECTION`).
    *   **Rule Initialization:** Defines comprehensive sets of rules:
        *   `prohibited_terms`: Phrases that suggest specific, non-compliant financial advice (e.g., "guaranteed return").
        *   `injection_patterns`: Regular expressions to detect attempts at prompt injection.
        *   `pii_patterns`: Regular expressions to identify Personally Identifiable Information (PII) like SSNs, credit card numbers, emails, etc.
        *   `advice_patterns`: Phrases indicating the generation of specific financial advice, which is prohibited.
        *   `disclaimers`: Pre-defined legal disclaimers (general, projection, risk, tax) that must be included.
    *   **`validate_prompt`:** Checks incoming user prompts for prompt injection attempts, PII, and requests for specific financial advice.
    *   **`validate_output`:** A critical method that scrutinizes the AI-generated narrative for:
        *   Presence of prohibited terms, PII, and specific financial advice.
        *   **Numerical consistency:** Verifies that numbers present in the narrative align with the original numerical data provided, flagging potential hallucinations or inconsistencies.
        *   Presence of all **required disclaimers** based on the narrative's content type.
    *   **`_verify_numerical_consistency`:** Implements the logic for extracting and comparing numbers from the text against source data, with a defined tolerance.
    *   **`add_disclaimers`:** Programmatically inserts the necessary legal disclaimers into the narrative at specified positions.
    *   **`sanitize_output`:** Redacts PII and removes potentially malicious content (HTML/script tags, URLs) from the generated text.
    *   **Violation Logging and Reporting:** Tracks all detected safety violations and provides a `get_violation_report` method for monitoring and auditing purposes.
*   **Role in Project:** This file is paramount for the system's legal and ethical operation. It directly implements the "Compliance & Safety" features, particularly "Content filtering" and "Numerical validation," ensuring that the AI-generated narratives are not only helpful but also legally sound and trustworthy. It acts as a crucial gatekeeper for all AI outputs.

---

### 11. /Users/rahulmehta/Desktop/Financial Planning/backend/app/ai/template_manager.py

*   **Purpose:** Manages the creation, retrieval, and rendering of pre-defined templates used for generating AI narratives. It is a cornerstone of the "Controlled Content Generation" strategy, ensuring structured and compliant output from the LLMs.
*   **Key Content:**
    *   **`TemplateType` Enum:** Defines a comprehensive set of categories for financial narratives (e.g., `BASELINE_SUMMARY`, `SCENARIO_COMPARISON`, `RISK_ASSESSMENT`, `ACTION_RECOMMENDATION`, `GOAL_PROGRESS`, `PORTFOLIO_REVIEW`, `MARKET_OUTLOOK`, `TAX_IMPLICATIONS`).
    *   **Initialization:** Configures a Jinja2 environment to load templates from a specified directory (`backend/app/ai/templates`) and includes security features like autoescaping. It also initializes hardcoded default templates.
    *   **Default Templates:** Contains multi-line string definitions of various default narrative templates, pre-populated with Jinja2 placeholders for dynamic data insertion and formatting.
    *   **`get_template`:** Retrieves a template, prioritizing file-based templates over hardcoded defaults, allowing for customization and extensibility.
    *   **`render_template`:** The core method that takes a `TemplateType` and a dictionary of `data`, then populates the corresponding Jinja2 template. It includes:
        *   Optional **data validation** to ensure all required fields for a template are present.
        *   Addition of **default values** for any missing optional fields.
        *   Whitespace cleanup for clean output.
    *   **Data Validation Logic:** Methods like `_validate_template_data` and `_get_required_fields` ensure that the input data for rendering a template is complete and meets expectations.
    *   **`_add_default_values`:** Provides a mechanism to inject sensible default values for optional template variables.
    *   **`get_template_hash`:** Generates a hash of template content for versioning and caching purposes.
    *   **`list_available_templates`:** Provides metadata about all managed templates, including their type, name, hash, and required data fields.
*   **Role in Project:** This file is fundamental to ensuring the consistency, compliance, and quality of AI-generated narratives. By providing structured templates, it guides the LLMs to produce predictable and relevant content, preventing "hallucinations" and ensuring that critical financial information is presented accurately and in a standardized format. It directly supports the project's goal of auditable and compliant AI integration.

---

### 12. /Users/rahulmehta/Desktop/Financial Planning/backend/app/ai/audit_logger.py

*   **Purpose:** Implements a comprehensive and robust audit logging system specifically designed for the AI narrative generation process. It records detailed events related to LLM interactions, safety checks, caching, and A/B testing, ensuring traceability, compliance, and debugging capabilities.
*   **Key Content:**
    *   **`AuditEventType` Enum:** Defines a granular set of event types (e.g., `PROMPT_SUBMITTED`, `RESPONSE_GENERATED`, `SAFETY_VIOLATION`, `API_CALL`, `CACHE_HIT`, `AB_TEST`, `FALLBACK_USED`), providing fine-grained control over what is logged.
    *   **Initialization:** Configures log directory (`/var/log/financial_ai`), an in-memory buffer for batch writing to disk, and log file rotation settings. It sets up a structured Python logger that writes JSON Lines (`.jsonl`) to files.
    *   **Core Logging (`log_event`):** A central method that creates structured event dictionaries, buffers them, updates internal statistics, and triggers a flush to disk when the buffer is full.
    *   **Specific Logging Methods:** Provides dedicated asynchronous methods for various events:
        *   `log_prompt`: Records details of prompts sent to LLMs.
        *   `log_response`: Records details of generated AI narratives.
        *   `log_api_call`: Logs interactions with external LLM APIs (successes and errors).
        *   `log_safety_violation`: Records instances where safety rules are triggered.
        *   `log_cache_event`: Tracks cache hits and misses.
        *   `log_ab_test`: Logs A/B test participation and outcomes.
    *   **`flush` Method:** Asynchronously writes buffered log events to disk, ensuring data persistence.
    *   **Statistics & Reporting:** Maintains real-time statistics (e.g., total prompts, cache hits, API errors) and provides a `get_statistics` method to retrieve aggregated metrics like cache hit rate and API success rate.
    *   **Log Management & Analysis:** Includes powerful features for:
        *   `search_logs`: Searching historical logs by date range, event type, and user ID.
        *   `export_logs`: Exporting logs to files, with optional GZIP compression.
        *   `cleanup_old_logs`: Automatically deleting old log files based on a retention policy.
*   **Role in Project:** This file is fundamental for the system's compliance, auditability, and operational transparency. It provides the necessary infrastructure to maintain a complete and immutable record of all AI-related activities, which is critical for a financial application. It supports debugging, performance monitoring, and regulatory requirements by offering detailed, structured, and searchable logs.

---

### 9. /Users/rahulmehta/Desktop/Financial Planning/backend/app/ai/narrative_generator.py

*   **Purpose:** Implements the core business logic for generating AI-driven financial narratives. It orchestrates the process of rendering templates, interacting with Large Language Models (LLMs), ensuring content safety and compliance, and managing caching and A/B testing.
*   **Key Content:**
    *   **Initialization:** Sets up `TemplateManager`, `SafetyController`, and `AuditLogger`. It directly initializes synchronous OpenAI and Anthropic clients, using `asyncio.to_thread` for asynchronous execution.
    *   **`generate_narrative` (Main Workflow):**
        *   Renders a Jinja2 template with financial data.
        *   Performs **prompt safety validation** using `SafetyController`.
        *   Logs prompts to `AuditLogger`.
        *   Selects an LLM provider (OpenAI, Anthropic, or fallback) with **A/B testing logic**.
        *   Interacts with the chosen LLM to generate the narrative.
        *   Performs **output safety validation** and sanitization.
        *   Adds **compliance disclaimers** to the generated narrative.
        *   Logs the LLM response details (content, provider, tokens, latency) to `AuditLogger`.
        *   Includes **in-memory caching** (currently a placeholder, suggesting a more robust caching solution like Redis might be used elsewhere or intended).
        *   Tracks **A/B testing metrics** (latency, errors) for performance comparison.
        *   Implements robust **error handling** with fallback mechanisms.
    *   **`_generate_with_llm`:** Manages the actual LLM API calls, including constructing strict `system_prompt`s to guide LLM behavior (e.g., "NEVER provide specific investment advice"). It also handles retries and fallbacks between LLM providers.
    *   **`_call_openai` and `_call_anthropic`:** Methods for direct interaction with the respective LLM APIs, wrapped with `asyncio.to_thread` for non-blocking calls.
    *   **`_create_system_prompt`:** Generates critical system instructions for the LLMs, enforcing compliance rules and template adherence.
    *   **`_select_provider`:** Contains the logic for A/B testing and selecting the LLM provider.
    *   **Caching Logic:** Includes methods for generating cache keys, checking, and storing responses, though the current implementation uses a simple in-memory placeholder.
    *   **Fallback Mechanisms:** Provides methods to generate narratives without LLM interaction when errors occur or APIs are unavailable.
    *   **A/B Testing Analysis:** Methods to track and retrieve A/B test results.
    *   **`generate_batch_narratives`:** Supports concurrent generation of multiple narratives.
*   **Relationship with `llm_client.py`:** There appears to be some overlap in functionality (LLM client management, caching, fallback) with `llm_client.py`. `narrative_generator.py` directly initializes synchronous LLM clients and uses `asyncio.to_thread`, while `llm_client.py` uses asynchronous clients and a more centralized `LLMClientManager` for caching and fallbacks. This suggests potential for refactoring or a deliberate architectural choice for different layers of LLM interaction.
*   **Role in Project:** This file is central to the system's ability to generate client-friendly financial narratives. It embodies the core AI logic, ensuring that generated content is accurate, compliant, safe, and performant. It directly implements the "Generative AI Narratives" feature and the "Controlled Content Generation" principles outlined in the project documentation.

---

### 10. /Users/rahulmehta/Desktop/Financial Planning/backend/app/ai/safety_controller.py

*   **Purpose:** Enforces strict safety and compliance rules for AI-generated financial narratives, preventing the output of misleading, inaccurate, or harmful content. It acts as a guardian for the integrity and regulatory adherence of the AI system.
*   **Key Content:**
    *   **`SafetyViolationType` Enum:** Categorizes various types of potential safety and compliance breaches (e.g., `PROHIBITED_CONTENT`, `NUMERICAL_INCONSISTENCY`, `PII_DETECTED`, `ADVICE_VIOLATION`, `PROMPT_INJECTION`).
    *   **Rule Initialization:** Defines comprehensive sets of rules:
        *   `prohibited_terms`: Phrases that suggest specific, non-compliant financial advice (e.g., "guaranteed return").
        *   `injection_patterns`: Regular expressions to detect attempts at prompt injection.
        *   `pii_patterns`: Regular expressions to identify Personally Identifiable Information (PII) like SSNs, credit card numbers, emails, etc.
        *   `advice_patterns`: Phrases indicating the generation of specific financial advice, which is prohibited.
        *   `disclaimers`: Pre-defined legal disclaimers (general, projection, risk, tax) that must be included.
    *   **`validate_prompt`:** Checks incoming user prompts for prompt injection attempts, PII, and requests for specific financial advice.
    *   **`validate_output`:** A critical method that scrutinizes the AI-generated narrative for:
        *   Presence of prohibited terms, PII, and specific financial advice.
        *   **Numerical consistency:** Verifies that numbers present in the narrative align with the original numerical data provided, flagging potential hallucinations or inconsistencies.
        *   Presence of all **required disclaimers** based on the narrative's content type.
    *   **`_verify_numerical_consistency`:** Implements the logic for extracting and comparing numbers from the text against source data, with a defined tolerance.
    *   **`add_disclaimers`:** Programmatically inserts the necessary legal disclaimers into the narrative at specified positions.
    *   **`sanitize_output`:** Redacts PII and removes potentially malicious content (HTML/script tags, URLs) from the generated text.
    *   **Violation Logging and Reporting:** Tracks all detected safety violations and provides a `get_violation_report` method for monitoring and auditing purposes.
*   **Role in Project:** This file is paramount for the system's legal and ethical operation. It directly implements the "Compliance & Safety" features, particularly "Content filtering" and "Numerical validation," ensuring that the AI-generated narratives are not only helpful but also legally sound and trustworthy. It acts as a crucial gatekeeper for all AI outputs.

---

### 11. /Users/rahulmehta/Desktop/Financial Planning/backend/app/ai/template_manager.py

*   **Purpose:** Manages the creation, retrieval, and rendering of pre-defined templates used for generating AI narratives. It is a cornerstone of the "Controlled Content Generation" strategy, ensuring structured and compliant output from the LLMs.
*   **Key Content:**
    *   **`TemplateType` Enum:** Defines a comprehensive set of categories for financial narratives (e.g., `BASELINE_SUMMARY`, `SCENARIO_COMPARISON`, `RISK_ASSESSMENT`, `ACTION_RECOMMENDATION`, `GOAL_PROGRESS`, `PORTFOLIO_REVIEW`, `MARKET_OUTLOOK`, `TAX_IMPLICATIONS`).
    *   **Initialization:** Configures a Jinja2 environment to load templates from a specified directory (`backend/app/ai/templates`) and includes security features like autoescaping. It also initializes hardcoded default templates.
    *   **Default Templates:** Contains multi-line string definitions of various default narrative templates, pre-populated with Jinja2 placeholders for dynamic data insertion and formatting.
    *   **`get_template`:** Retrieves a template, prioritizing file-based templates over hardcoded defaults, allowing for customization and extensibility.
    *   **`render_template`:** The core method that takes a `TemplateType` and a dictionary of `data`, then populates the corresponding Jinja2 template. It includes:
        *   Optional **data validation** to ensure all required fields for a template are present.
        *   Addition of **default values** for any missing optional fields.
        *   Whitespace cleanup for clean output.
    *   **Data Validation Logic:** Methods like `_validate_template_data` and `_get_required_fields` ensure that the input data for rendering a template is complete and meets expectations.
    *   **`_add_default_values`:** Provides a mechanism to inject sensible default values for optional template variables.
    *   **`get_template_hash`:** Generates a hash of template content for versioning and caching purposes.
    *   **`list_available_templates`:** Provides metadata about all managed templates, including their type, name, hash, and required data fields.
*   **Role in Project:** This file is fundamental to ensuring the consistency, compliance, and quality of AI-generated narratives. By providing structured templates, it guides the LLMs to produce predictable and relevant content, preventing "hallucinations" and ensuring that critical financial information is presented accurately and in a standardized format. It directly supports the project's goal of auditable and compliant AI integration.

---

### 9. /Users/rahulmehta/Desktop/Financial Planning/backend/app/ai/narrative_generator.py

*   **Purpose:** Implements the core business logic for generating AI-driven financial narratives. It orchestrates the process of rendering templates, interacting with Large Language Models (LLMs), ensuring content safety and compliance, and managing caching and A/B testing.
*   **Key Content:**
    *   **Initialization:** Sets up `TemplateManager`, `SafetyController`, and `AuditLogger`. It directly initializes synchronous OpenAI and Anthropic clients, using `asyncio.to_thread` for asynchronous execution.
    *   **`generate_narrative` (Main Workflow):**
        *   Renders a Jinja2 template with financial data.
        *   Performs **prompt safety validation** using `SafetyController`.
        *   Logs prompts to `AuditLogger`.
        *   Selects an LLM provider (OpenAI, Anthropic, or fallback) with **A/B testing logic**.
        *   Interacts with the chosen LLM to generate the narrative.
        *   Performs **output safety validation** and sanitization.
        *   Adds **compliance disclaimers** to the generated narrative.
        *   Logs the LLM response details (content, provider, tokens, latency) to `AuditLogger`.
        *   Includes **in-memory caching** (currently a placeholder, suggesting a more robust caching solution like Redis might be used elsewhere or intended).
        *   Tracks **A/B testing metrics** (latency, errors) for performance comparison.
        *   Implements robust **error handling** with fallback mechanisms.
    *   **`_generate_with_llm`:** Manages the actual LLM API calls, including constructing strict `system_prompt`s to guide LLM behavior (e.g., "NEVER provide specific investment advice"). It also handles retries and fallbacks between LLM providers.
    *   **`_call_openai` and `_call_anthropic`:** Methods for direct interaction with the respective LLM APIs, wrapped with `asyncio.to_thread` for non-blocking calls.
    *   **`_create_system_prompt`:** Generates critical system instructions for the LLMs, enforcing compliance rules and template adherence.
    *   **`_select_provider`:** Contains the logic for A/B testing and selecting the LLM provider.
    *   **Caching Logic:** Includes methods for generating cache keys, checking, and storing responses, though the current implementation uses a simple in-memory placeholder.
    *   **Fallback Mechanisms:** Provides methods to generate narratives without LLM interaction when errors occur or APIs are unavailable.
    *   **A/B Testing Analysis:** Methods to track and retrieve A/B test results.
    *   **`generate_batch_narratives`:** Supports concurrent generation of multiple narratives.
*   **Relationship with `llm_client.py`:** There appears to be some overlap in functionality (LLM client management, caching, fallback) with `llm_client.py`. `narrative_generator.py` directly initializes synchronous LLM clients and uses `asyncio.to_thread`, while `llm_client.py` uses asynchronous clients and a more centralized `LLMClientManager` for caching and fallbacks. This suggests potential for refactoring or a deliberate architectural choice for different layers of LLM interaction.
*   **Role in Project:** This file is central to the system's ability to generate client-friendly financial narratives. It embodies the core AI logic, ensuring that generated content is accurate, compliant, safe, and performant. It directly implements the "Generative AI Narratives" feature and the "Controlled Content Generation" principles outlined in the project documentation.

---

### 10. /Users/rahulmehta/Desktop/Financial Planning/backend/app/ai/safety_controller.py

*   **Purpose:** Enforces strict safety and compliance rules for AI-generated financial narratives, preventing the output of misleading, inaccurate, or harmful content. It acts as a guardian for the integrity and regulatory adherence of the AI system.
*   **Key Content:**
    *   **`SafetyViolationType` Enum:** Categorizes various types of potential safety and compliance breaches (e.g., `PROHIBITED_CONTENT`, `NUMERICAL_INCONSISTENCY`, `PII_DETECTED`, `ADVICE_VIOLATION`, `PROMPT_INJECTION`).
    *   **Rule Initialization:** Defines comprehensive sets of rules:
        *   `prohibited_terms`: Phrases that suggest specific, non-compliant financial advice (e.g., "guaranteed return").
        *   `injection_patterns`: Regular expressions to detect attempts at prompt injection.
        *   `pii_patterns`: Regular expressions to identify Personally Identifiable Information (PII) like SSNs, credit card numbers, emails, etc.
        *   `advice_patterns`: Phrases indicating the generation of specific financial advice, which is prohibited.
        *   `disclaimers`: Pre-defined legal disclaimers (general, projection, risk, tax) that must be included.
    *   **`validate_prompt`:** Checks incoming user prompts for prompt injection attempts, PII, and requests for specific financial advice.
    *   **`validate_output`:** A critical method that scrutinizes the AI-generated narrative for:
        *   Presence of prohibited terms, PII, and specific financial advice.
        *   **Numerical consistency:** Verifies that numbers present in the narrative align with the original numerical data provided, flagging potential hallucinations or inconsistencies.
        *   Presence of all **required disclaimers** based on the narrative's content type.
    *   **`_verify_numerical_consistency`:** Implements the logic for extracting and comparing numbers from the text against source data, with a defined tolerance.
    *   **`add_disclaimers`:** Programmatically inserts the necessary legal disclaimers into the narrative at specified positions.
    *   **`sanitize_output`:** Redacts PII and removes potentially malicious content (HTML/script tags, URLs) from the generated text.
    *   **Violation Logging and Reporting:** Tracks all detected safety violations and provides a `get_violation_report` method for monitoring and auditing purposes.
*   **Role in Project:** This file is paramount for the system's legal and ethical operation. It directly implements the "Compliance & Safety" features, particularly "Content filtering" and "Numerical validation," ensuring that the AI-generated narratives are not only helpful but also legally sound and trustworthy. It acts as a crucial gatekeeper for all AI outputs.

---

### 9. /Users/rahulmehta/Desktop/Financial Planning/backend/app/ai/narrative_generator.py

*   **Purpose:** Implements the core business logic for generating AI-driven financial narratives. It orchestrates the process of rendering templates, interacting with Large Language Models (LLMs), ensuring content safety and compliance, and managing caching and A/B testing.
*   **Key Content:**
    *   **Initialization:** Sets up `TemplateManager`, `SafetyController`, and `AuditLogger`. It directly initializes synchronous OpenAI and Anthropic clients, using `asyncio.to_thread` for asynchronous execution.
    *   **`generate_narrative` (Main Workflow):**
        *   Renders a Jinja2 template with financial data.
        *   Performs **prompt safety validation** using `SafetyController`.
        *   Logs prompts to `AuditLogger`.
        *   Selects an LLM provider (OpenAI, Anthropic, or fallback) with **A/B testing logic**.
        *   Interacts with the chosen LLM to generate the narrative.
        *   Performs **output safety validation** and sanitization.
        *   Adds **compliance disclaimers** to the generated narrative.
        *   Logs the LLM response details (content, provider, tokens, latency) to `AuditLogger`.
        *   Includes **in-memory caching** (currently a placeholder, suggesting a more robust caching solution like Redis might be used elsewhere or intended).
        *   Tracks **A/B testing metrics** (latency, errors) for performance comparison.
        *   Implements robust **error handling** with fallback mechanisms.
    *   **`_generate_with_llm`:** Manages the actual LLM API calls, including constructing strict `system_prompt`s to guide LLM behavior (e.g., "NEVER provide specific investment advice"). It also handles retries and fallbacks between LLM providers.
    *   **`_call_openai` and `_call_anthropic`:** Methods for direct interaction with the respective LLM APIs, wrapped with `asyncio.to_thread` for non-blocking calls.
    *   **`_create_system_prompt`:** Generates critical system instructions for the LLMs, enforcing compliance rules and template adherence.
    *   **`_select_provider`:** Contains the logic for A/B testing and selecting the LLM provider.
    *   **Caching Logic:** Includes methods for generating cache keys, checking, and storing responses, though the current implementation uses a simple in-memory placeholder.
    *   **Fallback Mechanisms:** Provides methods to generate narratives without LLM interaction when errors occur or APIs are unavailable.
    *   **A/B Testing Analysis:** Methods to track and retrieve A/B test results.
    *   **`generate_batch_narratives`:** Supports concurrent generation of multiple narratives.
*   **Relationship with `llm_client.py`:** There appears to be some overlap in functionality (LLM client management, caching, fallback) with `llm_client.py`. `narrative_generator.py` directly initializes synchronous LLM clients and uses `asyncio.to_thread`, while `llm_client.py` uses asynchronous clients and a more centralized `LLMClientManager` for caching and fallbacks. This suggests potential for refactoring or a deliberate architectural choice for different layers of LLM interaction.
*   **Role in Project:** This file is central to the system's ability to generate client-friendly financial narratives. It embodies the core AI logic, ensuring that generated content is accurate, compliant, safe, and performant. It directly implements the "Generative AI Narratives" feature and the "Controlled Content Generation" principles outlined in the project documentation.

---

### 7. /Users/rahulmehta/Desktop/Financial Planning/backend/app/ai/README.md

*   **Purpose:** Provides a comprehensive overview and technical documentation for the AI Narrative Generation System, detailing its functionalities, architecture, configuration, API, and operational guidelines.
*   **Key Content:**
    *   **Overview:** Explains the system's role in generating intelligent, context-aware financial narratives using OpenAI GPT-4 and Anthropic Claude.
    *   **Core Capabilities:** Highlights dual LLM integration, templated prompts, multi-language support (English, Spanish, Chinese), robust compliance and safety features (disclaimers, content filtering, audit logging), Redis-based caching, A/B testing framework, and fallback mechanisms.
    *   **Narrative Types:** Lists specific financial narrative categories generated (e.g., Simulation Summary, Trade-Off Analysis, Recommendations).
    *   **Architecture:** Outlines the directory structure and the role of each Python file within the `app/ai` module (e.g., `llm_client.py`, `narrative_generator.py`, `safety_controller.py`).
    *   **Configuration:** Details environment variables for API keys and optional settings for AI behavior, caching, and auditing.
    *   **API Endpoints:** Provides examples and descriptions for generating single or batch narratives, listing templates, and submitting feedback.
    *   **Template System:** Explains the use of Jinja2 syntax, variable types, and the process for creating custom narrative templates.
    *   **Multi-Language Support:** Describes language detection and localized number formatting.
    *   **Compliance & Safety:** Emphasizes disclaimers, content validation (numerical consistency, PII detection), and detailed audit logging of LLM interactions.
    *   **Caching Strategy:** Details Redis integration for performance optimization.
    *   **A/B Testing Framework:** Describes how A/B tests are configured and what metrics are tracked.
    *   **Error Handling:** Outlines a multi-stage fallback strategy for LLM failures and common error types.
    *   **Performance Optimization:** Discusses batch processing and token optimization techniques.
    *   **Integration Examples:** Illustrates how the AI module integrates with other parts of the financial planning system.
    *   **Monitoring & Analytics:** Defines key performance metrics and provides a dedicated health check endpoint.
    *   **Best Practices & Troubleshooting:** Offers guidelines for development, template design, API usage, security, and common issue resolution.
*   **Role in Project:** This README is the definitive guide for understanding the AI component of the system. It serves as a critical resource for developers working on AI features, ensuring adherence to design principles, compliance requirements, and operational best practices. It also provides valuable context for anyone trying to understand the system's AI capabilities and how they are implemented.

---

### 5. /Users/rahulmehta/Desktop/Financial Planning/backend/Dockerfile

*   **Purpose:** Defines the steps to build a Docker image for the FastAPI backend application, ensuring a consistent and isolated runtime environment.
*   **Key Content:**
    *   **Base Image:** Uses `python:3.11-slim` for a lightweight Python environment.
    *   **Environment Variables:** Sets `PYTHONUNBUFFERED`, `PYTHONDONTWRITEBYTECODE`, and pip optimizations.
    *   **Working Directory:** Sets `/app` as the working directory inside the container.
    *   **System Dependencies:** Installs `build-essential`, `libpq-dev` (for PostgreSQL client), `curl`, and `git` using `apt-get`.
    *   **Python Dependencies:** Copies `requirements.txt` and installs all Python packages using `pip`, leveraging Docker's layer caching.
    *   **Application Code:** Copies the entire backend project into the container.
    *   **Security:** Creates and switches to a non-root `appuser` for running the application, improving security posture.
    *   **Port Exposure:** Exposes port `8000`, the default port for the FastAPI application.
    *   **Health Check:** Configures a `HEALTHCHECK` command to verify the application's responsiveness via a `/health` endpoint.
    *   **Startup Command:** Defines the default command to run the FastAPI application using `uvicorn` on container startup.
*   **Role in Project:** This Dockerfile is crucial for containerizing the backend service, enabling consistent development, testing, and deployment across different environments. It defines the exact environment and dependencies required for the backend to run, making it a key component of the project's DevOps strategy.

---


