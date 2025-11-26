# AEGIS Dashboard

A Streamlit-based web interface for the AEGIS (Automated Educational Grading Intelligent System) that allows instructors to submit answer scripts and view AI-generated grading results.

## Features

### 📝 Answer Submission
- Submit student answers for automated grading
- Provide grading rubrics and answer keys
- Real-time progress tracking during evaluation
- Multi-stage agent visualization

### 📊 Results Viewing
- Comprehensive grading results display
- View assessments from all four agents:
  - 🎯 Arbiter: Initial assessment
  - 🔍 Scrutinizer: Detailed analysis
  - ✓ Validator: Quality check
  - 👨‍🏫 Mentor: Personalized feedback
- Download results as JSON

### 📚 History Tracking
- View all past grading sessions
- Filter and search through history
- Quick access to previous results

### 📈 Analytics
- Grading activity timeline
- Success rates and statistics
- Daily/weekly trends

### ℹ️ System Information
- Complete system architecture overview
- Multi-agent workflow explanation
- Technology stack details

## Installation

### Prerequisites
- Python 3.11 or higher
- AEGIS API server running (see `../agents/README.md`)

### Setup

1. **Install dependencies**
   ```bash
   cd dashboard
   pip install -r requirements.txt
   ```

2. **Configure API endpoint** (optional)
   
   Copy the example secrets file:
   ```bash
   copy .streamlit\secrets.toml.example .streamlit\secrets.toml
   ```
   
   Edit `.streamlit/secrets.toml` to set your API URL:
   ```toml
   API_BASE_URL = "http://localhost:8000"
   ```

3. **Run the dashboard**
   ```bash
   streamlit run app.py
   ```

4. **Access the dashboard**
   
   Open your browser to: `http://localhost:8501`

## Usage

### Starting the Full System

1. **Start the AEGIS API server** (in a separate terminal)
   ```bash
   cd agents
   python main.py
   ```

2. **Start the dashboard** (in another terminal)
   ```bash
   cd dashboard
   streamlit run app.py
   ```

### Submitting an Answer for Grading

1. Navigate to the **Submit** tab
2. Enter an **Assignment ID** (e.g., `CS101-Assignment-1`)
3. Paste the **Student's Answer** in the text area
4. Paste the **Grading Rubric/Answer Key** in the text area
5. Click **Submit for Grading**
6. Watch the progress as agents evaluate the answer
7. View results in the **Results** tab

### Viewing Results

- **Results Tab**: View the most recent grading result
- **History Tab**: Browse all past grading sessions
- **Analytics Tab**: See trends and statistics

## Configuration

### API Settings

You can configure the API endpoint in three ways:

1. **Via Streamlit Secrets** (recommended for production)
   ```toml
   # .streamlit/secrets.toml
   API_BASE_URL = "https://your-api-domain.com"
   API_KEY = "your-api-key"  # Optional
   ```

2. **Via Sidebar** (temporary, per-session)
   - Use the "API Base URL" input in the sidebar

3. **Via Environment Variables**
   ```bash
   set API_BASE_URL=http://localhost:8000
   streamlit run app.py
   ```

### Theme Customization

Edit `.streamlit/config.toml` to customize colors and appearance:

```toml
[theme]
primaryColor = "#1f77b4"
backgroundColor = "#ffffff"
secondaryBackgroundColor = "#f0f2f6"
textColor = "#262730"
font = "sans serif"
```

## API Client

The dashboard includes a Python API client (`api_client.py`) that can be used independently:

```python
from api_client import AEGISClient

# Initialize client
client = AEGISClient(base_url="http://localhost:8000")

# Check API health
if client.health_check():
    print("API is running")

# Submit for grading
result = client.submit_for_grading(
    student_answer="Your answer here...",
    rubric="Grading criteria...",
    assignment_id="assignment-001"
)
```

## Troubleshooting

### API Connection Issues

**Problem**: "API Unavailable" error in dashboard

**Solutions**:
1. Verify the AEGIS API server is running:
   ```bash
   curl http://localhost:8000/health
   ```

2. Check the API URL in the sidebar matches your server address

3. Ensure no firewall is blocking port 8000 (API) or 8501 (dashboard)

### Slow Grading Response

**Problem**: Grading takes longer than expected

**Explanation**: The multi-agent pipeline typically takes 30-60 seconds depending on:
- Answer complexity
- Rubric detail
- API model response time

**This is normal** - the system performs thorough evaluation through multiple agents.

### Missing Results

**Problem**: Results don't appear after submission

**Solutions**:
1. Check the browser console for JavaScript errors
2. Verify the API returned a valid response (check Raw API Response)
3. Ensure session state wasn't cleared

## Architecture

```
Dashboard (Streamlit) ─HTTP/REST─> AEGIS API (FastAPI)
     ↓                                    ↓
Session State                    Agent Pipeline
     ↓                                    ↓
History/Analytics          [Arbiter → Loop → Mentor]
```

## File Structure

```
dashboard/
├── app.py                      # Main Streamlit application
├── api_client.py              # API client helper
├── requirements.txt           # Python dependencies
├── README.md                  # This file
└── .streamlit/
    ├── config.toml           # Streamlit configuration
    └── secrets.toml.example  # Example secrets file
```

## Development

### Running in Development Mode

```bash
streamlit run app.py --server.runOnSave true
```

This enables auto-reload when you edit `app.py`.

### Adding New Features

1. Edit `app.py` to add new tabs or components
2. Use `st.session_state` for persistent data
3. Call `st.rerun()` to refresh the UI after state changes

### Custom Styling

Add custom CSS in the `st.markdown()` block at the top of `app.py`:

```python
st.markdown("""
<style>
    .custom-class {
        /* Your styles */
    }
</style>
""", unsafe_allow_html=True)
```

## Deployment

### Local Network Access

To allow access from other devices on your network:

```bash
streamlit run app.py --server.address 0.0.0.0
```

### Docker Deployment

Create a `Dockerfile` in the dashboard directory:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8501

CMD ["streamlit", "run", "app.py", "--server.address", "0.0.0.0"]
```

Build and run:
```bash
docker build -t aegis-dashboard .
docker run -p 8501:8501 aegis-dashboard
```

### Cloud Deployment (Streamlit Cloud)

1. Push your code to GitHub
2. Visit [share.streamlit.io](https://share.streamlit.io)
3. Connect your repository
4. Configure secrets in the Streamlit Cloud dashboard
5. Deploy!

## Support

For issues or questions:
- Check the main project documentation
- Review API server logs
- Contact: nishithp11@gmail.com

## License

Part of the AEGIS project - see main project for license information.
