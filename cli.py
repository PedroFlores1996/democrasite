#!/usr/bin/env python3
"""
Democrasite CLI - Interactive command-line interface for the Democrasite API
"""

import requests
import sys
import os
import subprocess
from typing import Optional, Dict, Any

BASE_URL = "http://localhost:8000"
TOKEN_FILE = ".democrasite_token"


class DemocrasiteCLI:
    def __init__(self):
        self.token = self.load_token()

    def load_token(self) -> Optional[str]:
        """Load stored auth token"""
        if os.path.exists(TOKEN_FILE):
            with open(TOKEN_FILE, "r") as f:
                return f.read().strip()
        return None

    def save_token(self, token: str):
        """Save auth token to file"""
        with open(TOKEN_FILE, "w") as f:
            f.write(token)
        self.token = token

    def clear_token(self):
        """Clear stored auth token"""
        if os.path.exists(TOKEN_FILE):
            os.remove(TOKEN_FILE)
        self.token = None

    def headers(self) -> Dict[str, str]:
        """Get headers with auth token if available"""
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def make_request(
        self, method: str, endpoint: str, data: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Make HTTP request to API"""
        url = f"{BASE_URL}{endpoint}"
        try:
            if method.upper() == "GET":
                response = requests.get(url, headers=self.headers())
            elif method.upper() == "POST":
                response = requests.post(url, headers=self.headers(), json=data)
            else:
                raise ValueError(f"Unsupported method: {method}")

            if response.status_code in [200, 201]:
                return response.json()
            else:
                print(f"❌ Error {response.status_code}: {response.text}")
                return {}
        except requests.exceptions.ConnectionError:
            print("❌ Connection error. Is the server running?")
            return {}
        except Exception as e:
            print(f"❌ Request failed: {e}")
            return {}

    def start_server(self):
        """Start the FastAPI server"""
        print("🚀 Starting Democrasite server...")
        try:
            subprocess.run([sys.executable, "main.py"], check=True)
        except KeyboardInterrupt:
            print("\n🛑 Server stopped")
        except Exception as e:
            print(f"❌ Failed to start server: {e}")

    def register(self):
        """Register a new user"""
        print("\n👤 User Registration")
        username = input("Username: ")
        password = input("Password: ")

        data = {"username": username, "password": password}
        result = self.make_request("POST", "/register", data)

        if result and "access_token" in result:
            self.save_token(result["access_token"])
            print(f"✅ Registration successful! Logged in as {username}")
        else:
            print("❌ Registration failed")

    def login(self):
        """Login existing user"""
        print("\n🔐 User Login")
        username = input("Username: ")
        password = input("Password: ")

        data = {"username": username, "password": password}
        result = self.make_request("POST", "/login", data)

        if result and "access_token" in result:
            self.save_token(result["access_token"])
            print(f"✅ Login successful! Welcome back {username}")
        else:
            print("❌ Login failed")

    def logout(self):
        """Logout current user"""
        self.clear_token()
        print("✅ Logged out successfully")

    def create_topic(self):
        """Create a new topic"""
        if not self.token:
            print("❌ Please login first")
            return

        print("\n📝 Create New Topic")
        title = input("Topic title: ")

        # Get answers
        print("Enter possible answers (1-1000). Type 'done' when finished:")
        answers = []
        while len(answers) < 1000:
            answer = input(f"Answer {len(answers) + 1}: ")
            if answer.lower() == "done":
                break
            if answer.strip():
                answers.append(answer.strip())

        if not answers:
            print("❌ At least one answer is required")
            return

        # Public or private
        is_public = input("Public topic? (y/N): ").lower().startswith("y")

        data = {"title": title, "answers": answers, "is_public": is_public}

        # If private, get allowed users
        if not is_public:
            print("Enter allowed usernames (comma-separated):")
            allowed_users_input = input("Allowed users: ")
            if allowed_users_input.strip():
                allowed_users = [u.strip() for u in allowed_users_input.split(",")]
                data["allowed_users"] = allowed_users

        result = self.make_request("POST", "/topics", data)
        print(result)
        if result and "id" in result:
            print(f"✅ Topic created successfully! ID: {result['id']}")
        else:
            print("❌ Topic creation failed")

    def vote_on_topic(self):
        """Vote on a topic"""
        if not self.token:
            print("❌ Please login first")
            return

        print("\n🗳️  Vote on Topic")
        topic_id = input("Topic ID: ")

        try:
            topic_id = int(topic_id)
        except ValueError:
            print("❌ Invalid topic ID")
            return

        # First get topic details to show available answers
        topic_result = self.make_request("GET", f"/topic/{topic_id}")
        if not topic_result:
            return

        print(f"\nTopic: {topic_result.get('title', 'Unknown')}")
        print("Available answers:")
        answers = topic_result.get("answers", [])
        for i, answer in enumerate(answers, 1):
            print(f"  {i}. {answer}")

        choice_input = input("\nEnter your choice (number or text): ")

        # Try to parse as number first
        try:
            choice_num = int(choice_input)
            if 1 <= choice_num <= len(answers):
                choice = answers[choice_num - 1]
            else:
                print("❌ Invalid choice number")
                return
        except ValueError:
            # Use as text
            choice = choice_input.strip()
            if choice not in answers:
                print("❌ Invalid choice. Must match one of the available answers")
                return

        data = {"choice": choice}
        result = self.make_request("POST", f"/topic/{topic_id}/vote", data)

        if result:
            print("✅ Vote submitted successfully!")
        else:
            print("❌ Vote submission failed")

    def view_topic(self):
        """View topic details and results"""
        print("\n👀 View Topic")
        topic_id = input("Topic ID: ")

        try:
            topic_id = int(topic_id)
        except ValueError:
            print("❌ Invalid topic ID")
            return

        result = self.make_request("GET", f"/topic/{topic_id}")

        if result:
            print(f"\n📊 Topic: {result.get('title', 'Unknown')}")
            print(f"Public: {'Yes' if result.get('is_public') else 'No'}")
            print(f"Total votes: {result.get('total_votes', 0)}")
            print(f"Created: {result.get('created_at', 'Unknown')}")

            print("\nAnswers and votes:")
            vote_breakdown = result.get("vote_breakdown", {})
            for answer in result.get("answers", []):
                votes = vote_breakdown.get(answer, 0)
                print(f"  • {answer}: {votes} votes")
        else:
            print("❌ Failed to get topic details")

    def show_menu(self):
        """Show main menu"""
        print("\n" + "=" * 50)
        print("🏛️  DEMOCRASITE CLI")
        print("=" * 50)

        if self.token:
            print("✅ Logged in")
        else:
            print("❌ Not logged in")

        print("\nCommands:")
        print("1. Start server")
        print("2. Register")
        print("3. Login")
        print("4. Logout")
        print("5. Create topic")
        print("6. Vote on topic")
        print("7. View topic")
        print("8. Exit")
        print("-" * 50)

    def run(self):
        """Main CLI loop"""
        while True:
            self.show_menu()
            choice = input("Enter choice (1-8): ").strip()

            if choice == "1":
                self.start_server()
            elif choice == "2":
                self.register()
            elif choice == "3":
                self.login()
            elif choice == "4":
                self.logout()
            elif choice == "5":
                self.create_topic()
            elif choice == "6":
                self.vote_on_topic()
            elif choice == "7":
                self.view_topic()
            elif choice == "8":
                print("👋 Goodbye!")
                break
            else:
                print("❌ Invalid choice")


if __name__ == "__main__":
    cli = DemocrasiteCLI()
    cli.run()
