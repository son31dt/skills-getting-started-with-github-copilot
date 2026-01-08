"""
Tests for the Mergington High School API endpoints
"""
import pytest
from fastapi.testclient import TestClient
from src.app import app, activities


@pytest.fixture
def client():
    """Create a test client for the FastAPI app"""
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_activities():
    """Reset activities to initial state before each test"""
    activities.clear()
    activities.update({
        "Chess Club": {
            "description": "Learn strategies and compete in chess tournaments",
            "schedule": "Fridays, 3:30 PM - 5:00 PM",
            "max_participants": 12,
            "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
        },
        "Programming Class": {
            "description": "Learn programming fundamentals and build software projects",
            "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
            "max_participants": 20,
            "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
        },
        "Gym Class": {
            "description": "Physical education and sports activities",
            "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
            "max_participants": 30,
            "participants": ["john@mergington.edu", "olivia@mergington.edu"]
        },
        "Basketball Team": {
            "description": "Join the team and compete in local tournaments",
            "schedule": "Tuesdays and Thursdays, 4:00 PM - 6:00 PM",
            "max_participants": 15,
            "participants": []
        }
    })


class TestRootEndpoint:
    """Tests for the root endpoint"""

    def test_root_redirects_to_static_index(self, client):
        """Test that root endpoint redirects to static index.html"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"


class TestGetActivities:
    """Tests for GET /activities endpoint"""

    def test_get_activities_returns_all_activities(self, client):
        """Test that GET /activities returns all activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        data = response.json()
        assert "Chess Club" in data
        assert "Programming Class" in data
        assert "Gym Class" in data
        assert "Basketball Team" in data

    def test_get_activities_returns_correct_structure(self, client):
        """Test that activity data has the correct structure"""
        response = client.get("/activities")
        data = response.json()
        
        chess_club = data["Chess Club"]
        assert "description" in chess_club
        assert "schedule" in chess_club
        assert "max_participants" in chess_club
        assert "participants" in chess_club
        assert isinstance(chess_club["participants"], list)

    def test_get_activities_has_no_cache_header(self, client):
        """Test that activities endpoint has no-store cache control"""
        response = client.get("/activities")
        assert response.headers["cache-control"] == "no-store"


class TestSignupForActivity:
    """Tests for POST /activities/{activity_name}/signup endpoint"""

    def test_signup_for_existing_activity(self, client):
        """Test successful signup for an activity"""
        response = client.post(
            "/activities/Basketball Team/signup?email=test@mergington.edu"
        )
        assert response.status_code == 200
        data = response.json()
        assert "Signed up test@mergington.edu for Basketball Team" in data["message"]

    def test_signup_adds_participant_to_list(self, client):
        """Test that signup actually adds participant to the activity"""
        client.post("/activities/Basketball Team/signup?email=test@mergington.edu")
        
        response = client.get("/activities")
        data = response.json()
        assert "test@mergington.edu" in data["Basketball Team"]["participants"]

    def test_signup_for_nonexistent_activity(self, client):
        """Test signup for an activity that doesn't exist"""
        response = client.post(
            "/activities/Nonexistent Club/signup?email=test@mergington.edu"
        )
        assert response.status_code == 404
        assert response.json()["detail"] == "Activity not found"

    def test_duplicate_signup_is_prevented(self, client):
        """Test that a student cannot sign up twice for the same activity"""
        # First signup should succeed
        response1 = client.post(
            "/activities/Basketball Team/signup?email=test@mergington.edu"
        )
        assert response1.status_code == 200

        # Second signup should fail
        response2 = client.post(
            "/activities/Basketball Team/signup?email=test@mergington.edu"
        )
        assert response2.status_code == 400
        assert response2.json()["detail"] == "Student already signed up"

    def test_signup_with_special_characters_in_activity_name(self, client):
        """Test signup with URL-encoded activity name"""
        response = client.post(
            "/activities/Chess%20Club/signup?email=newplayer@mergington.edu"
        )
        assert response.status_code == 200


class TestUnregisterFromActivity:
    """Tests for DELETE /activities/{activity_name}/unregister endpoint"""

    def test_unregister_from_activity(self, client):
        """Test successful unregistration from an activity"""
        response = client.delete(
            "/activities/Chess Club/unregister?email=michael@mergington.edu"
        )
        assert response.status_code == 200
        data = response.json()
        assert "Unregistered michael@mergington.edu from Chess Club" in data["message"]

    def test_unregister_removes_participant_from_list(self, client):
        """Test that unregister actually removes participant from the activity"""
        client.delete("/activities/Chess Club/unregister?email=michael@mergington.edu")
        
        response = client.get("/activities")
        data = response.json()
        assert "michael@mergington.edu" not in data["Chess Club"]["participants"]

    def test_unregister_from_nonexistent_activity(self, client):
        """Test unregister from an activity that doesn't exist"""
        response = client.delete(
            "/activities/Nonexistent Club/unregister?email=test@mergington.edu"
        )
        assert response.status_code == 404
        assert response.json()["detail"] == "Activity not found"

    def test_unregister_when_not_registered(self, client):
        """Test unregister when student is not signed up for the activity"""
        response = client.delete(
            "/activities/Basketball Team/unregister?email=notregistered@mergington.edu"
        )
        assert response.status_code == 400
        assert response.json()["detail"] == "Student not signed up for this activity"

    def test_unregister_with_special_characters(self, client):
        """Test unregister with URL-encoded parameters"""
        response = client.delete(
            "/activities/Chess%20Club/unregister?email=daniel@mergington.edu"
        )
        assert response.status_code == 200


class TestWorkflow:
    """Integration tests for complete workflows"""

    def test_signup_and_unregister_workflow(self, client):
        """Test complete workflow of signing up and then unregistering"""
        # Initial state - no participants
        response = client.get("/activities")
        initial_count = len(response.json()["Basketball Team"]["participants"])

        # Sign up
        signup_response = client.post(
            "/activities/Basketball Team/signup?email=workflow@mergington.edu"
        )
        assert signup_response.status_code == 200

        # Verify signup
        response = client.get("/activities")
        assert len(response.json()["Basketball Team"]["participants"]) == initial_count + 1
        assert "workflow@mergington.edu" in response.json()["Basketball Team"]["participants"]

        # Unregister
        unregister_response = client.delete(
            "/activities/Basketball Team/unregister?email=workflow@mergington.edu"
        )
        assert unregister_response.status_code == 200

        # Verify unregister
        response = client.get("/activities")
        assert len(response.json()["Basketball Team"]["participants"]) == initial_count
        assert "workflow@mergington.edu" not in response.json()["Basketball Team"]["participants"]

    def test_multiple_students_signup(self, client):
        """Test multiple students signing up for the same activity"""
        emails = [
            "student1@mergington.edu",
            "student2@mergington.edu",
            "student3@mergington.edu"
        ]

        for email in emails:
            response = client.post(f"/activities/Basketball Team/signup?email={email}")
            assert response.status_code == 200

        # Verify all students are registered
        response = client.get("/activities")
        participants = response.json()["Basketball Team"]["participants"]
        for email in emails:
            assert email in participants
