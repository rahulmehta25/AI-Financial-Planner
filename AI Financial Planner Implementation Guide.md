# AI-Driven Financial Planner: Technical Implementation Guide

## 1. Introduction

This document outlines the technical implementation details for the AI-driven financial planning Minimum Viable Product (MVP). The system aims to simulate retirement outcomes, suggest trade-offs, and explain results in simple, auditable language. This guide covers the architecture, core components, data models, and compliance considerations for the system.

## 2. System Architecture

The AI-driven financial planner follows a microservices-oriented architecture, separating concerns into distinct components for scalability, maintainability, and independent deployment. The primary components include a backend for financial logic and simulations, a database for persistent storage, a frontend for user interaction, and integrations with generative AI for narrative explanations and PDF generation for reporting.




### 2.1. Backend (Python/FastAPI)

The backend serves as the core computational engine, handling financial calculations, Monte Carlo simulations, and business logic. It is built using Python with FastAPI for its high performance and ease of API development.

#### 2.1.1. Monte Carlo Simulation Engine

The Monte Carlo simulation engine is responsible for generating 50,000 paths to simulate retirement outcomes. It incorporates capital market assumptions (CMA) based on broad index returns (stocks, bonds, cash) with forward-looking mean/vol/corr. Inflation is co-simulated to provide realistic projections. NumPy and Numba are utilized to optimize computational performance, ensuring simulations complete within the target of 30 seconds.

**Key components of the simulation engine:**

*   **Input Processing:** Takes user inputs such as age, target retirement age, current savings, annual savings rate, income level, debt, account buckets, risk preference, and desired retirement spending.
*   **Capital Market Assumptions (CMA) Integration:** Integrates predefined CMA data to model asset class returns, volatility, and correlations. These assumptions are transparently displayed and logged for auditability.
*   **Portfolio Mapping:** Maps the user's risk preference (conservative, balanced, aggressive) to one of 3-5 predefined model ETF portfolios (e.g., 40/60, 60/40, 80/20 stock/bond allocation).
*   **Path Generation:** Generates 50,000 unique financial paths, simulating market returns, inflation, savings, and spending over the user's financial horizon.
*   **Outcome Calculation:** For each path, calculates the probability of funding the retirement goal, median and 10th percentile balances, and identifies potential shortfalls.
*   **Trade-off Analysis:** Computes the impact of various trade-off levers, such as saving more (+3%), retiring later (+2 years), or reducing retirement spending (-10%).

#### 2.1.2. FastAPI Endpoints

FastAPI provides a robust framework for exposing the backend functionalities as RESTful APIs. Key endpoints will include:

*   `/plan/create`: Accepts user financial inputs and initiates a new financial plan simulation.
*   `/plan/{plan_id}/status`: Retrieves the status of a running simulation.
*   `/plan/{plan_id}/results`: Fetches the simulation results, including baseline outcomes, trade-off scenarios, and recommended allocation.
*   `/plan/{plan_id}/export/pdf`: Triggers the generation and export of a one-page PDF snapshot of the plan.

Input validation and data serialization will be handled by Pydantic models integrated with FastAPI, ensuring data integrity and consistency.




### 2.2. Database (PostgreSQL)

PostgreSQL is chosen as the relational database for its robustness, reliability, and strong support for complex data structures. It will primarily store plan snapshots and audit logs, ensuring data persistence and compliance with auditability requirements.

#### 2.2.1. Schema Design

The database schema will be designed to capture all necessary inputs, outputs, and audit-related information for each financial plan run. Key tables will include:

*   `plans`: Stores metadata for each financial plan, including a unique plan ID, creation timestamp, and references to associated inputs and outputs.
*   `plan_inputs`: Stores all user-provided inputs for a specific plan run (e.g., age, savings, income, risk preference).
*   `plan_outputs`: Stores the simulation results, including probability of success, median/10th percentile balances, and trade-off scenario outcomes.
*   `audit_logs`: Records detailed audit trails for every plan run, including inputs, CMA version, random seed used for Monte Carlo, and a summary of outputs. This ensures 100% reproducibility of results.

Relationships between these tables will be established using foreign keys to maintain data integrity. The `audit_logs` table is critical for compliance and will be designed for efficient querying and data retrieval.

#### 2.2.2. Data Storage and Retrieval

Plan snapshots will be stored as JSONB columns where appropriate to accommodate flexible data structures for inputs and outputs, while maintaining the benefits of a relational database. This allows for easy storage and retrieval of complex simulation results and user inputs. Indices will be created on frequently queried columns to optimize performance for data retrieval and reporting.




### 2.3. Frontend (React/Next.js)

The frontend provides the user interface for data intake, displaying simulation results, and managing plan exports. React, combined with Next.js, is chosen for its component-based architecture, server-side rendering capabilities (for improved performance and SEO), and robust ecosystem.

#### 2.3.1. Intake Form Design

The intake form is designed for a streamlined user experience, aiming for completion within 10 minutes. It will be structured as a multi-step wizard, guiding users through essential inputs:

*   **Personal Information:** Age, target retirement age, marital status.
*   **Financial Snapshot:** Current savings balance, annual savings rate (% of income), income level, debt (balance + rate).
*   **Account Buckets:** Allocation across taxable, 401k-IRA, and Roth accounts.
*   **Risk Preference:** A clear selection for conservative, balanced, or aggressive risk profiles.
*   **Retirement Goals:** Desired retirement spending per year.

Input validation will be performed client-side for immediate feedback and server-side for data integrity. State management will be handled using React Context or Redux for efficient data flow across components.

#### 2.3.2. Results Dashboard

The results dashboard will present the simulation outcomes in a clear, intuitive, and jargon-free manner. Key sections include:

*   **Baseline Result:** Probability of success at the current financial path, presented prominently.
*   **Three Trade-off Scenarios:** Visualizations and summaries for:
    1.  Saving +3% more annually.
    2.  Retiring 2 years later.
    3.  Reducing retirement spending by 10%.
*   **Recommended Allocation:** Displays the suggested ETF mix based on the user's risk preference.
*   **Client-Friendly Explanation:** A dedicated section for the generative AI-powered narrative, converting complex numbers into an understandable plan.
*   **Export Option:** A clear call-to-action for generating the one-page PDF snapshot.

Data visualization libraries (e.g., Chart.js, Recharts) will be used to render charts and graphs for probability distributions and financial projections, enhancing user comprehension.




### 2.4. Generative AI Integration (OpenAI/Anthropic Wrapper)

Generative AI is employed to convert complex numerical outputs into client-friendly narrative explanations. A wrapper around large language models (LLMs) like OpenAI or Anthropic will be used to ensure controlled and templated explanations, preventing hallucinated numbers or financial advice.

#### 2.4.1. Narrative Generation Process

The process for generating narratives involves:

*   **Data Input:** The simulation results (probability of success, trade-off impacts, recommended allocation) are fed into the generative AI wrapper.
*   **Templated Prompts:** Pre-defined templates with placeholders for numerical data are used to construct prompts for the LLM. This ensures consistency, accuracy, and adherence to compliance guidelines. For example, a template might be: "Based on your current plan, you have a {probability_of_success}% chance of funding your retirement. If you save an additional {savings_increase_percentage}%, your probability increases to {new_probability_of_success}%."
*   **Compliance Disclaimer Integration:** A mandatory disclaimer, "Simulations are estimates, not guarantees," will be appended to all generated narratives to manage user expectations and comply with financial regulations.
*   **Output Formatting:** The LLM's output will be formatted for readability and integrated seamlessly into the frontend's results dashboard.

#### 2.4.2. Controlled Content Generation

To prevent the LLM from generating unverified or misleading information, strict controls will be in place:

*   **No Free-form Financial Advice:** The LLM will only fill in pre-approved templates with data, not generate independent financial recommendations.
*   **Auditable Prompts:** All prompts sent to the LLM, along with the responses, will be logged as part of the audit trail to ensure transparency and reproducibility.
*   **Version Control for Templates:** Narrative templates will be version-controlled to track changes and ensure consistency over time.




### 2.5. PDF Export (WeasyPrint/ReportLab)

An essential feature of the MVP is the ability to export a one-page PDF snapshot of the financial plan. WeasyPrint or ReportLab will be used for this purpose, leveraging their capabilities to convert HTML/CSS content into high-quality PDF documents.

#### 2.5.1. PDF Generation Process

The PDF generation process will involve:

*   **Data Compilation:** All relevant data points from the simulation results, including inputs, baseline outcomes, trade-off scenarios, recommended allocation, and the generative AI narrative, will be compiled.
*   **HTML Template Rendering:** A pre-designed HTML template, styled with CSS, will be populated with the compiled data. This template will ensure a consistent and professional layout for the PDF.
*   **PDF Conversion:** WeasyPrint (or ReportLab) will convert the rendered HTML into a PDF document. This approach allows for flexible design and easy updates to the PDF layout.
*   **Audit Trail Inclusion:** The PDF will include a summary of the audit trail, such as the CMA version and a unique plan ID, to link it back to the detailed logs in the database.
*   **Disclaimer:** The compliance disclaimer, "Simulations are estimates, not guarantees," will be prominently displayed on the PDF.

#### 2.5.2. Integration with Backend

The PDF export functionality will be exposed via a FastAPI endpoint (e.g., `/plan/{plan_id}/export/pdf`). When this endpoint is called, the backend will retrieve the necessary data, render the HTML template, generate the PDF, and return it as a downloadable file.




## 3. Compliance and Auditability

Compliance and auditability are paramount for a financial planning system. The system is designed to ensure transparency, reproducibility, and adherence to regulatory requirements.

### 3.1. Audit Logging

Every plan run will generate a comprehensive audit log, stored in the PostgreSQL database. This log is crucial for reproducing results and demonstrating compliance. The `audit_logs` table will capture:

*   **Inputs:** All user-provided inputs used for the simulation.
*   **CMA Version:** The specific version of the Capital Market Assumptions used for the simulation. This ensures that if CMAs are updated, historical runs can still be reproduced with the exact assumptions.
*   **Random Seed:** The random seed used for the Monte Carlo simulation. This is critical for 100% reproducibility of the 50,000 paths generated.
*   **Output Summary:** A summary of the key outputs, including the probability of funding the retirement goal and the trade-off scenarios.
*   **Timestamp:** The exact time and date of the plan run.
*   **User ID:** (If applicable) An identifier for the user who initiated the plan run.

This detailed logging ensures that any financial plan generated can be fully audited and reproduced at any point in the future, meeting compliance-grade auditability requirements.

### 3.2. Transparency of Assumptions

All assumptions used in the financial planning model will be transparently displayed to the user. This includes:

*   **Capital Market Assumptions:** Details on the broad index returns, mean, volatility, and correlations used for stocks, bonds, and cash.
*   **Inflation Assumptions:** The inflation rate co-simulated with the Monte Carlo paths.
*   **Portfolio Allocations:** The specific asset allocations for each risk preference (conservative, balanced, aggressive) and their corresponding model ETF portfolios.

These assumptions will be accessible within the frontend and explicitly mentioned in the generated PDF reports.

### 3.3. Disclaimers

A clear and prominent disclaimer will be displayed throughout the application and on all generated reports:

> *“Simulations are estimates, not guarantees.”*

This disclaimer manages user expectations and clarifies that the system provides projections based on assumptions, not guaranteed outcomes. The generative AI narratives will also integrate this disclaimer to ensure consistent messaging.




## 4. API Endpoints and Data Models

The interaction between the frontend and backend will be facilitated through a well-defined set of RESTful API endpoints. Data will be exchanged using JSON payloads, validated against Pydantic models to ensure data integrity.

### 4.1. API Endpoints Summary

| Endpoint | Method | Description | Request Body | Response Body |
| :------- | :----- | :---------- | :----------- | :------------ |
| `/plan/create` | `POST` | Initiates a new financial plan simulation. | `PlanInputModel` | `PlanCreationResponse` |
| `/plan/{plan_id}/status` | `GET` | Retrieves the status of a running simulation. | None | `PlanStatusResponse` |
| `/plan/{plan_id}/results` | `GET` | Fetches the simulation results. | None | `PlanResultsResponse` |
| `/plan/{plan_id}/export/pdf` | `GET` | Triggers PDF generation and returns the PDF file. | None | PDF File |

### 4.2. Data Models (Pydantic)

#### 4.2.1. `PlanInputModel`

This model defines the structure of the input data required to create a new financial plan. All fields are mandatory to ensure a complete simulation.

```python
from pydantic import BaseModel, Field
from typing import Literal

class PlanInputModel(BaseModel):
    age: int = Field(..., ge=18, le=100, description="Current age of the user.")
    target_retirement_age: int = Field(..., ge=age + 1, le=100, description="Target age for retirement.")
    marital_status: Literal["single", "married"] = Field(..., description="Marital status of the user.")
    current_savings_balance: float = Field(..., ge=0, description="Current total savings balance.")
    annual_savings_rate_percentage: float = Field(..., ge=0, le=100, description="Percentage of income saved annually.")
    income_level: float = Field(..., ge=0, description="Current annual income level.")
    debt_balance: float = Field(..., ge=0, description="Total outstanding debt balance.")
    debt_interest_rate_percentage: float = Field(..., ge=0, le=100, description="Annual interest rate on debt.")
    account_buckets_taxable: float = Field(..., ge=0, description="Percentage of savings in taxable accounts.")
    account_buckets_401k_ira: float = Field(..., ge=0, description="Percentage of savings in 401k/IRA accounts.")
    account_buckets_roth: float = Field(..., ge=0, description="Percentage of savings in Roth accounts.")
    risk_preference: Literal["conservative", "balanced", "aggressive"] = Field(..., description="User's risk preference.")
    desired_retirement_spending_per_year: float = Field(..., ge=0, description="Desired annual spending in retirement.")

    # Validator for account_buckets_taxable + account_buckets_401k_ira + account_buckets_roth == 100
    # (Implementation details for Pydantic validator would be added in actual code)

```

#### 4.2.2. `PlanCreationResponse`

Response model for successful plan creation.

```python
class PlanCreationResponse(BaseModel):
    plan_id: str = Field(..., description="Unique identifier for the created financial plan.")
    status: str = Field("processing", description="Current status of the plan simulation.")
```

#### 4.2.3. `PlanStatusResponse`

Response model for checking the status of a plan simulation.

```python
class PlanStatusResponse(BaseModel):
    plan_id: str = Field(..., description="Unique identifier for the financial plan.")
    status: Literal["processing", "completed", "failed"] = Field(..., description="Current status of the plan simulation.")
    progress: float = Field(..., ge=0, le=100, description="Simulation progress in percentage.")
    message: str | None = Field(None, description="Additional status message.")
```

#### 4.2.4. `PlanResultsResponse`

Response model for fetching the simulation results.

```python
class PlanResultsResponse(BaseModel):
    plan_id: str = Field(..., description="Unique identifier for the financial plan.")
    baseline_probability_of_success: float = Field(..., ge=0, le=100, description="Probability of funding retirement goal at current path.")
    median_balance: float = Field(..., description="Median balance at retirement.")
    tenth_percentile_balance: float = Field(..., description="10th percentile balance at retirement.")
    
    # Trade-off scenarios
    save_more_scenario_probability: float = Field(..., ge=0, le=100, description="Probability of success if saving +3% more.")
    retire_later_scenario_probability: float = Field(..., ge=0, le=100, description="Probability of success if retiring 2 years later.")
    spend_less_scenario_probability: float = Field(..., ge=0, le=100, description="Probability of success if reducing retirement spending by 10%.")
    
    recommended_allocation: str = Field(..., description="Recommended ETF mix based on risk preference.")
    client_friendly_narrative: str = Field(..., description="Generative AI-powered narrative explanation.")
    disclaimer: str = Field("Simulations are estimates, not guarantees.", description="Compliance disclaimer.")
```



