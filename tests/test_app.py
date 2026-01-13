"""
Tests for the Mergington High School Activities API
"""

import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Add src directory to path to import app
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app import app, activities


@pytest.fixture
def client():
    """Create a test client for the FastAPI app"""
    return TestClient(app)


@pytest.fixture
def reset_activities():
    """Reset activities to initial state before each test"""
    # Store original state
    original_activities = {
        key: {
            "description": val["description"],
            "schedule": val["schedule"],
            "max_participants": val["max_participants"],
            "participants": val["participants"].copy()
        }
        for key, val in activities.items()
    }
    
    yield
    
    # Restore original state after test
    for key, val in original_activities.items():
        activities[key]["participants"] = val["participants"].copy()


class TestGetActivities:
    """Tests for GET /activities endpoint"""
    
    def test_get_activities_returns_200(self, client):
        """Test that get activities endpoint returns 200 status code"""
        response = client.get("/activities")
        assert response.status_code == 200
    
    def test_get_activities_returns_dict(self, client):
        """Test that get activities returns a dictionary"""
        response = client.get("/activities")
        assert isinstance(response.json(), dict)
    
    def test_get_activities_has_expected_keys(self, client):
        """Test that response contains expected activity names"""
        response = client.get("/activities")
        data = response.json()
        expected_activities = [
            "Basketball Team",
            "Soccer Club",
            "Art Club",
            "Drama Club",
            "Debate Team",
            "Math Club",
            "Chess Club",
            "Programming Class",
            "Gym Class"
        ]
        for activity in expected_activities:
            assert activity in data
    
    def test_activity_has_required_fields(self, client):
        """Test that each activity has required fields"""
        response = client.get("/activities")
        data = response.json()
        required_fields = ["description", "schedule", "max_participants", "participants"]
        
        for activity_name, activity_data in data.items():
            for field in required_fields:
                assert field in activity_data, f"Missing {field} in {activity_name}"


class TestSignupForActivity:
    """Tests for POST /activities/{activity_name}/signup endpoint"""
    
    def test_signup_new_participant(self, client, reset_activities):
        """Test signing up a new participant"""
        response = client.post(
            "/activities/Basketball%20Team/signup?email=student@example.com"
        )
        assert response.status_code == 200
        assert "Signed up" in response.json()["message"]
    
    def test_signup_updates_participants_list(self, client, reset_activities):
        """Test that signup adds participant to activity"""
        email = "student@example.com"
        client.post(f"/activities/Basketball%20Team/signup?email={email}")
        
        response = client.get("/activities")
        data = response.json()
        assert email in data["Basketball Team"]["participants"]
    
    def test_signup_nonexistent_activity(self, client, reset_activities):
        """Test signing up for nonexistent activity returns 404"""
        response = client.post(
            "/activities/NonExistent/signup?email=student@example.com"
        )
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]
    
    def test_signup_duplicate_participant(self, client, reset_activities):
        """Test signing up same person twice returns 400"""
        email = "student@example.com"
        # First signup
        client.post(f"/activities/Basketball%20Team/signup?email={email}")
        
        # Second signup with same email
        response = client.post(
            f"/activities/Basketball%20Team/signup?email={email}"
        )
        assert response.status_code == 400
        assert "already signed up" in response.json()["detail"]
    
    def test_signup_with_existing_participant(self, client, reset_activities):
        """Test signup with activity that has existing participants"""
        response = client.post(
            "/activities/Chess%20Club/signup?email=newstudent@example.com"
        )
        assert response.status_code == 200
        
        # Verify new student is added to existing participants
        activities_response = client.get("/activities")
        data = activities_response.json()
        assert "newstudent@example.com" in data["Chess Club"]["participants"]
        assert "michael@mergington.edu" in data["Chess Club"]["participants"]


class TestUnregisterFromActivity:
    """Tests for POST /activities/{activity_name}/unregister endpoint"""
    
    def test_unregister_existing_participant(self, client, reset_activities):
        """Test unregistering an existing participant"""
        response = client.post(
            "/activities/Chess%20Club/unregister?email=michael@mergington.edu"
        )
        assert response.status_code == 200
        assert "Unregistered" in response.json()["message"]
    
    def test_unregister_updates_participants_list(self, client, reset_activities):
        """Test that unregister removes participant from activity"""
        email = "michael@mergington.edu"
        client.post(f"/activities/Chess%20Club/unregister?email={email}")
        
        response = client.get("/activities")
        data = response.json()
        assert email not in data["Chess Club"]["participants"]
    
    def test_unregister_nonexistent_activity(self, client, reset_activities):
        """Test unregistering from nonexistent activity returns 404"""
        response = client.post(
            "/activities/NonExistent/unregister?email=student@example.com"
        )
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]
    
    def test_unregister_non_participant(self, client, reset_activities):
        """Test unregistering someone not signed up returns 400"""
        response = client.post(
            "/activities/Basketball%20Team/unregister?email=notstudent@example.com"
        )
        assert response.status_code == 400
        assert "not signed up" in response.json()["detail"]
    
    def test_signup_then_unregister(self, client, reset_activities):
        """Test full signup and unregister flow"""
        email = "student@example.com"
        activity = "Basketball%20Team"
        
        # Sign up
        response = client.post(f"/activities/{activity}/signup?email={email}")
        assert response.status_code == 200
        
        # Verify participant added
        get_response = client.get("/activities")
        assert email in get_response.json()["Basketball Team"]["participants"]
        
        # Unregister
        response = client.post(f"/activities/{activity}/unregister?email={email}")
        assert response.status_code == 200
        
        # Verify participant removed
        get_response = client.get("/activities")
        assert email not in get_response.json()["Basketball Team"]["participants"]


class TestRoot:
    """Tests for GET / endpoint"""
    
    def test_root_redirects(self, client):
        """Test that root endpoint redirects"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"
