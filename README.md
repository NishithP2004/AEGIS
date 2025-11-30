# AEGIS - Automated Educational Grading Intelligent System

AEGIS is an advanced automated grading system powered by AI agents. It is designed to evaluate student answer scripts against a provided rubric, offering detailed feedback, scoring, and reasoning. The system utilizes a multi-agent architecture to ensure fair, accurate, and comprehensive grading.

## 🚀 Features

*   **Automated Grading:** Instantly grade student answers based on custom rubrics.
*   **Multi-Agent Evaluation:** Uses specialized agents (Arbiter, Scrutinizer, Validator, Mentor) to cross-verify and analyze answers.
*   **Detailed Feedback:** Provides score justification, improvement advice, and detailed analysis.
*   **Interactive Dashboard:** A user-friendly Streamlit interface for submitting assignments and viewing results.
*   **History & Analytics:** Track grading history and view basic analytics.

## 🏗️ Project Structure

The project is divided into two main components:

*   **`agents/`**: The backend service hosting the AI agents. Built with Python, FastAPI, and Google's Agent Development Kit (ADK).
*   **`dashboard/`**: The frontend user interface. Built with Streamlit to provide an interactive experience for users.

```
AEGIS/
├── agents/                 # Backend Agent Service
│   ├── aegis_agent/        # Agent logic and definitions
│   ├── main.py             # FastAPI entry point
│   ├── Dockerfile          # Docker configuration for the agent service
│   └── requirements.txt    # Python dependencies
├── dashboard/              # Frontend Dashboard
│   ├── app.py              # Streamlit application entry point
│   ├── api_client.py       # Client to communicate with the agent service
│   ├── Dockerfile          # Docker configuration for the dashboard
│   └── requirements.txt    # Python dependencies
└── docker-compose.yaml     # Docker Compose file to orchestrate services
```

## 📋 Prerequisites

*   [Docker](https://www.docker.com/) and [Docker Compose](https://docs.docker.com/compose/) installed on your machine.
*   A Google Cloud Project with Vertex AI API enabled (required for the underlying AI models).

## 🛠️ Installation & Setup

1.  **Clone the repository:**

    ```bash
    git clone <repository-url>
    cd AEGIS
    ```

2.  **Environment Configuration:**

    Ensure you have the necessary environment variables set up.

    *   **Backend (Agents):**
        Create a `.env` file in the `agents/` directory with the following variables:
        ```env
        GOOGLE_API_KEY=your_google_api_key
        PROJECT_ID=your_google_cloud_project_id
        ```

    *   **Frontend (Dashboard):**
        Create a `secrets.toml` file in the `dashboard/.streamlit/` directory (create the folder if it doesn't exist). This is required for the dashboard to communicate with the agent service within the Docker network.
        ```toml
        API_BASE_URL = "http://agent:8000"
        
        # Optional: Redis Configuration for History/Analytics
        # REDIS_HOST="your_redis_host"
        # REDIS_PORT=6379
        # REDIS_USERNAME="your_redis_username"
        # REDIS_PASSWORD="your_redis_password"
        ```
        *Note: If you are running the dashboard locally (outside Docker), set `API_BASE_URL = "http://localhost:8000"`.*

3.  **Run with Docker Compose:**

    Build and start the services using Docker Compose:

    ```bash
    docker-compose up --build
    ```

    This command will:
    *   Build the `agent` image.
    *   Build the `dashboard` image.
    *   Start the Agent service on port `8000`.
    *   Start the Dashboard on port `8501`.

## 💻 Usage

1.  **Access the Dashboard:**
    Open your web browser and navigate to [http://localhost:8501](http://localhost:8501).

2.  **Submit an Assignment (Text):**
    *   Go to the **📝 Submit** tab.
    *   Enter an **Assignment ID** (e.g., `CS101-Midterm`).
    *   Paste the **Grading Rubric / Answer Key**.
    *   Paste the **Student Answer**.
    *   Click **🚀 Submit for Grading**.

3.  **Submit an Assignment (OCR):**
    *   Go to the **📄 OCR & Grade** tab.
    *   Enter an **Assignment ID**.
    *   Upload exactly two PDF files (Answer Script and Rubric/Key).
    *   Click **📤 Upload & Process OCR**.

4.  **View Results:**
    *   Once grading is complete, the results will be displayed in the **📊 Results** tab.
    *   You can see the final score, detailed feedback from different agents, and score reasoning.

5.  **Review History & Analytics:**
    *   Check the **📚 History** tab to see past grading sessions.
    *   Check the **📈 Analytics** tab for grading statistics.

## 🔧 API Endpoints

The Agent service exposes the following API endpoints (accessible at `http://localhost:8000`):

*   `POST /evaluate`: Evaluates a student answer.
    *   **Body:** `{"prompt": "..."}` (The prompt should contain the rubric and student answer formatted for the agent).

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

[MIT License](LICENSE)
