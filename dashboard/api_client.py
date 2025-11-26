"""
API Client Helper for AEGIS Dashboard
Handles communication with the AEGIS grading API.
"""

import requests
from typing import Dict, Optional, List
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AEGISClient:
    """Client for interacting with the AEGIS grading API."""
    
    def __init__(self, base_url: str = "http://localhost:8000", api_key: Optional[str] = None):
        """
        Initialize the AEGIS API client.
        
        Args:
            base_url: Base URL of the AEGIS API server
            api_key: Optional API key for authentication
        """
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.session = requests.Session()
        
        if api_key:
            self.session.headers.update({"Authorization": f"Bearer {api_key}"})
    
    def health_check(self) -> bool:
        """
        Check if the API is healthy and reachable.
        
        Returns:
            True if API is healthy, False otherwise
        """
        try:
            # ADK API server exposes /list-apps which is a good health check
            response = self.session.get(f"{self.base_url}/list-apps", timeout=5)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False
    
    def submit_for_grading(
        self,
        student_answer: str,
        rubric: str,
        assignment_id: str,
        agent_name: str = "aegis-agent"
    ) -> Optional[Dict]:
        """
        Submit an answer for grading (non-streaming).
        
        Args:
            student_answer: The student's answer text
            rubric: The grading rubric/answer key
            assignment_id: Unique identifier for the assignment
            agent_name: Name of the agent to invoke (default: aegis-agent)
            
        Returns:
            API response dict or None if error
        """
        try:
            endpoint = f"{self.base_url}/run"
            
            message_text = f"Student Answer:\n{student_answer}\n\nRubric:\n{rubric}\n\nAssignment ID: {assignment_id}"
            
            payload = {
                "appName": agent_name,
                "userId": "user",  # Default user
                "sessionId": assignment_id,
                "newMessage": {
                    "role": "user",
                    "parts": [{"text": message_text}]
                }
            }
            
            logger.info(f"Submitting answer for assignment: {assignment_id}")
            response = self.session.post(endpoint, json=payload, timeout=120)
            response.raise_for_status()
            
            # ADK returns a list of events. We might want to process this.
            # For now, return the raw list or the last event's content?
            # The original code expected a dict.
            result = response.json()
            logger.info(f"Grading completed successfully for {assignment_id}")
            return result
            
        except requests.exceptions.Timeout:
            logger.error("Request timed out")
            return None
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error: {e}")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return None

    def submit_for_grading_streaming(
        self,
        student_answer: str,
        rubric: str,
        assignment_id: str,
        agent_name: str = "aegis-agent"
    ):
        """
        Submit an answer for grading with streaming response.
        
        Args:
            student_answer: The student's answer text
            rubric: The grading rubric/answer key
            assignment_id: Unique identifier for the assignment
            agent_name: Name of the agent to invoke (default: aegis-agent)
            
        Yields:
            Dict containing event data
        """
        try:
            endpoint = f"{self.base_url}/run_sse"
            
            message_text = f"Student Answer:\n{student_answer}\n\nRubric:\n{rubric}\n\nAssignment ID: {assignment_id}"
            
            payload = {
                "appName": agent_name,
                "userId": "user",
                "sessionId": assignment_id,
                "newMessage": {
                    "role": "user",
                    "parts": [{"text": message_text}]
                },
                "streaming": True
            }
            
            logger.info(f"Submitting answer for assignment (streaming): {assignment_id}")
            
            with self.session.post(endpoint, json=payload, stream=True, timeout=120) as response:
                response.raise_for_status()
                
                import json
                
                for line in response.iter_lines():
                    if line:
                        decoded_line = line.decode('utf-8')
                        if decoded_line.startswith('data: '):
                            json_str = decoded_line[6:]  # Remove 'data: ' prefix
                            try:
                                data = json.loads(json_str)
                                yield data
                            except json.JSONDecodeError:
                                logger.warning(f"Failed to decode JSON: {json_str}")
                                
        except Exception as e:
            logger.error(f"Streaming error: {e}")
            yield {"error": str(e)}
    
    def get_session(self, session_id: str) -> Optional[Dict]:
        """
        Retrieve a grading session by ID.
        
        Args:
            session_id: The session ID to retrieve
            
        Returns:
            Session data or None if error
        """
        try:
            endpoint = f"{self.base_url}/sessions/{session_id}"
            response = self.session.get(endpoint, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error retrieving session {session_id}: {e}")
            return None
    
    def list_sessions(self, limit: int = 100) -> Optional[List[Dict]]:
        """
        List recent grading sessions.
        
        Args:
            limit: Maximum number of sessions to retrieve
            
        Returns:
            List of session data or None if error
        """
        try:
            endpoint = f"{self.base_url}/sessions"
            params = {"limit": limit}
            response = self.session.get(endpoint, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error listing sessions: {e}")
            return None

    def evaluate_answer(
        self,
        student_answer: str,
        rubric: str,
        assignment_id: str
    ) -> Optional[Dict]:
        """
        Submit an answer for evaluation using the /evaluate endpoint.
        
        Args:
            student_answer: The student's answer text
            rubric: The grading rubric/answer key
            assignment_id: Unique identifier for the assignment
            
        Returns:
            API response dict or None if error
        """
        try:
            endpoint = f"{self.base_url}/evaluate"
            
            prompt = f"Student Answer:\n{student_answer}\n\nRubric:\n{rubric}\n\nAssignment ID: {assignment_id}"
            
            payload = {
                "prompt": prompt
            }
            
            logger.info(f"Submitting answer for evaluation: {assignment_id}")
            # Increased timeout as agent execution might take time
            response = self.session.post(endpoint, json=payload, timeout=300)
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Evaluation completed successfully for {assignment_id}")
            return result
            
        except Exception as e:
            logger.error(f"Evaluation error: {e}")
            return None


# Example usage
if __name__ == "__main__":
    # Initialize client
    client = AEGISClient()
    
    # Check health
    if client.health_check():
        print("✅ API is healthy")
    else:
        print("❌ API is not reachable")
    
    # Example grading submission
    result = client.submit_for_grading(
        student_answer="Python is a high-level programming language...",
        rubric="Answer should include: 1) Definition of Python, 2) Key features...",
        assignment_id="test-001"
    )
    
    if result:
        print("✅ Grading successful")
        print(result)
    else:
        print("❌ Grading failed")
