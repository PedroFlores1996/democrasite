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
            elif method.upper() == "DELETE":
                response = requests.delete(url, headers=self.headers(), json=data)
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
        if result and "share_code" in result:
            print(f"✅ Topic created successfully!")
            print(f"📋 Share code: {result['share_code']}")
            print(f"🔢 Internal ID: {result['id']}")
        else:
            print("❌ Topic creation failed")

    def vote_on_topic(self):
        """Vote on a topic"""
        if not self.token:
            print("❌ Please login first")
            return

        print("\n🗳️  Vote on Topic")
        share_code = input("Topic share code: ")

        if not share_code.strip():
            print("❌ Share code cannot be empty")
            return

        # First get topic details to show available answers
        topic_result = self.make_request("GET", f"/topic/{share_code}")
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
        result = self.make_request("POST", f"/topic/{share_code}/votes", data)

        if result:
            print("✅ Vote submitted successfully!")
        else:
            print("❌ Vote submission failed")

    def view_topic(self):
        """View topic details and results"""
        print("\n👀 View Topic")
        share_code = input("Topic share code: ")

        if not share_code.strip():
            print("❌ Share code cannot be empty")
            return

        result = self.make_request("GET", f"/topic/{share_code}")

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

    def manage_topic_users(self):
        """Manage users for a private topic"""
        if not self.token:
            print("❌ Please login first")
            return

        print("\n👥 Manage Topic Users")
        share_code = input("Topic share code: ")
        
        if not share_code.strip():
            print("❌ Share code cannot be empty")
            return

        print("\nUser Management Options:")
        print("1. View allowed users")
        print("2. Add users to access list")
        print("3. Remove users from access list")
        
        choice = input("Choose option (1-3): ").strip()
        
        if choice == "1":
            self._view_topic_users(share_code)
        elif choice == "2":
            self._add_topic_users(share_code)
        elif choice == "3":
            self._remove_topic_users(share_code)
        else:
            print("❌ Invalid choice")

    def _view_topic_users(self, share_code):
        """View users who have access to a topic"""
        result = self.make_request("GET", f"/topic/{share_code}/users")
        
        if result:
            print(f"\n📋 Topic: {result.get('topic_title', 'Unknown')}")
            print(f"Creator: {result.get('creator', 'Unknown')}")
            
            allowed_users = result.get('allowed_users', [])
            vote_details = result.get('vote_details', {})
            
            if allowed_users:
                print(f"\nAllowed users ({len(allowed_users)}):")
                for user in allowed_users:
                    vote_choice = vote_details.get(user, 'Not voted')
                    print(f"  • {user}: {vote_choice}")
            else:
                print("\nNo users have access")
        else:
            print("❌ Failed to get user list")

    def _add_topic_users(self, share_code):
        """Add users to topic access list"""
        print("Enter usernames to add (comma-separated):")
        usernames_input = input("Usernames: ")
        
        if not usernames_input.strip():
            print("❌ No usernames provided")
            return
        
        usernames = [u.strip() for u in usernames_input.split(',')]
        data = {"usernames": usernames}
        
        result = self.make_request("POST", f"/topic/{share_code}/users", data)
        
        if result:
            print("\n📊 Add Users Results:")
            
            if result.get("added_users"):
                print(f"✅ Added users: {', '.join(result['added_users'])}")
            
            if result.get("already_added_users"):
                print(f"ℹ️  Already had access: {', '.join(result['already_added_users'])}")
            
            if result.get("not_found_users"):
                print(f"❌ Users not found: {', '.join(result['not_found_users'])}")
        else:
            print("❌ Failed to add users")

    def _remove_topic_users(self, share_code):
        """Remove users from topic access list"""
        print("Remove users from access list (also removes their votes):")
        usernames_input = input("Usernames (comma-separated): ")
        
        if not usernames_input.strip():
            print("❌ No usernames provided")
            return
        
        usernames = [u.strip() for u in usernames_input.split(',')]
        data = {"usernames": usernames}
        
        result = self.make_request("DELETE", f"/topic/{share_code}/users", data)
        
        if result:
            print("\n📊 User Removal Results:")
            
            if result.get("removed_users"):
                print(f"✅ Removed users: {', '.join(result['removed_users'])}")
            
            if result.get("votes_removed", 0) > 0:
                print(f"🗳️  Votes removed: {result['votes_removed']}")
            
            if result.get("not_found_users"):
                print(f"❌ Users not found: {', '.join(result['not_found_users'])}")
        else:
            print("❌ Failed to remove users")

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
        print("1. Register")
        print("2. Login")
        print("3. Logout")
        print("4. Create topic")
        print("5. Vote on topic")
        print("6. View topic")
        print("7. Manage topic users")
        print("8. Exit")
        print("-" * 50)

    def run(self):
        """Main CLI loop"""
        while True:
            self.show_menu()
            choice = input("Enter choice (1-8): ").strip()

            if choice == "1":
                self.register()
            elif choice == "2":
                self.login()
            elif choice == "3":
                self.logout()
            elif choice == "4":
                self.create_topic()
            elif choice == "5":
                self.vote_on_topic()
            elif choice == "6":
                self.view_topic()
            elif choice == "7":
                self.manage_topic_users()
            elif choice == "8":
                print("👋 Goodbye!")
                break
            else:
                print("❌ Invalid choice")


if __name__ == "__main__":
    cli = DemocrasiteCLI()
    cli.run()
