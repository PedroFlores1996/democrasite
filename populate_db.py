#!/usr/bin/env python3
"""
Database Population Script for Democrasite

This script populates the database with comprehensive test data to simulate real usage.
Run this script to create realistic demo data for development and testing.

Usage: python3 populate_db.py
"""

import os
import sys
import random
from datetime import datetime, timedelta, timezone
from typing import List

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import sessionmaker
from app.db.database import engine, Base
from app.db.models import User, Topic, Vote, user_topic_favorites
from app.auth.utils import get_password_hash
from app.services.favorites_service import favorites_service
from app.services.topic_service import topic_service

# Create tables
Base.metadata.create_all(bind=engine)

# Create session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def generate_test_users():
    """Generate realistic test users"""
    users_data = [
        {"username": "alice_cooper", "email": "alice.cooper@example.com", "password": "password123"},
        {"username": "bob_builder", "email": "bob.builder@example.com", "password": "password123"},
        {"username": "charlie_dev", "email": "charlie.dev@example.com", "password": "password123"},
        {"username": "diana_explorer", "email": "diana.explorer@example.com", "password": "password123"},
        {"username": "ethan_gamer", "email": "ethan.gamer@example.com", "password": "password123"},
        {"username": "fiona_artist", "email": "fiona.artist@example.com", "password": "password123"},
        {"username": "george_chef", "email": "george.chef@example.com", "password": "password123"},
        {"username": "hannah_writer", "email": "hannah.writer@example.com", "password": "password123"},
        {"username": "ivan_traveler", "email": "ivan.traveler@example.com", "password": "password123"},
        {"username": "julia_scientist", "email": "julia.scientist@example.com", "password": "password123"},
        {"username": "kevin_musician", "email": "kevin.musician@example.com", "password": "password123"},
        {"username": "luna_photographer", "email": "luna.photographer@example.com", "password": "password123"},
        {"username": "marco_athlete", "email": "marco.athlete@example.com", "password": "password123"},
        {"username": "nina_teacher", "email": "nina.teacher@example.com", "password": "password123"},
        {"username": "oscar_entrepreneur", "email": "oscar.entrepreneur@example.com", "password": "password123"},
    ]
    return users_data

def generate_test_topics():
    """Generate diverse realistic topics"""
    topics_data = [
        # Technology Topics
        {
            "title": "Should AI replace human customer service?",
            "answers": ["Yes, AI is more efficient", "No, humans provide better empathy", "Hybrid approach is best", "Only for simple queries"],
            "tags": ["TECHNOLOGY", "AI", "CUSTOMER SERVICE"],
            "is_public": True,
            "is_editable": False,
            "allow_multi_select": False
        },
        {
            "title": "Best programming language for beginners in 2024?",
            "answers": ["Python", "JavaScript", "Java", "C++", "Go", "Rust"],
            "tags": ["PROGRAMMING", "EDUCATION", "TECHNOLOGY"],
            "is_public": True,
            "is_editable": True,
            "allow_multi_select": True  # Allow multiple languages
        },
        {
            "title": "Remote work vs Office work - What's better?",
            "answers": ["Remote work", "Office work", "Hybrid model", "Depends on the job"],
            "tags": ["WORK", "PRODUCTIVITY", "LIFESTYLE"],
            "is_public": True,
            "is_editable": False
        },
        
        # Entertainment Topics
        {
            "title": "Best streaming platform for original content?",
            "answers": ["Netflix", "Amazon Prime", "Disney+", "HBO Max", "Apple TV+", "Hulu"],
            "tags": ["ENTERTAINMENT", "STREAMING", "TV"],
            "is_public": True,
            "is_editable": True
        },
        {
            "title": "Should movie theaters survive the streaming era?",
            "answers": ["Yes, nothing beats the cinema experience", "No, streaming is more convenient", "Only for blockbusters", "Transform into experience centers"],
            "tags": ["MOVIES", "ENTERTAINMENT", "TECHNOLOGY"],
            "is_public": True,
            "is_editable": False
        },
        
        # Food & Lifestyle
        {
            "title": "Best coffee brewing method?",
            "answers": ["French Press", "Espresso Machine", "Pour Over", "Cold Brew", "Aeropress", "Instant Coffee"],
            "tags": ["COFFEE", "LIFESTYLE", "FOOD"],
            "is_public": True,
            "is_editable": True
        },
        {
            "title": "Should we all go vegetarian for the environment?",
            "answers": ["Yes, completely vegetarian", "Reduce meat consumption", "No, personal choice", "Focus on sustainable farming"],
            "tags": ["ENVIRONMENT", "FOOD", "SUSTAINABILITY"],
            "is_public": True,
            "is_editable": False
        },
        
        # Travel & Adventure
        {
            "title": "Best camping destination in North America?",
            "answers": ["Yellowstone", "Yosemite", "Banff", "Grand Canyon", "Zion", "Glacier National Park"],
            "tags": ["CAMPING", "TRAVEL", "NATURE"],
            "is_public": True,
            "is_editable": True
        },
        {
            "title": "Solo travel vs Group travel - Which is better?",
            "answers": ["Solo travel - more freedom", "Group travel - more fun", "Depends on destination", "Mix of both"],
            "tags": ["TRAVEL", "ADVENTURE", "LIFESTYLE"],
            "is_public": True,
            "is_editable": False
        },
        
        # Education & Learning
        {
            "title": "Most important skill to learn in 2024?",
            "answers": ["Critical thinking", "Digital literacy", "Emotional intelligence", "Data analysis", "Communication", "Adaptability"],
            "tags": ["EDUCATION", "SKILLS", "CAREER"],
            "is_public": True,
            "is_editable": True,
            "allow_multi_select": True  # Can learn multiple skills
        },
        {
            "title": "Should college education be free?",
            "answers": ["Yes, education is a right", "No, maintain quality through cost", "Partially subsidized", "Income-based repayment"],
            "tags": ["EDUCATION", "POLITICS", "ECONOMICS"],
            "is_public": True,
            "is_editable": False
        },
        
        # Health & Fitness
        {
            "title": "Best exercise for overall health?",
            "answers": ["Running", "Swimming", "Weight lifting", "Yoga", "Cycling", "Walking"],
            "tags": ["FITNESS", "HEALTH", "LIFESTYLE"],
            "is_public": True,
            "is_editable": True
        },
        {
            "title": "Should health tracking apps be mandatory?",
            "answers": ["Yes, for public health", "No, privacy concerns", "Optional with incentives", "Only during pandemics"],
            "tags": ["HEALTH", "TECHNOLOGY", "PRIVACY"],
            "is_public": True,
            "is_editable": False
        },
        
        # Private Topics (Team/Company decisions)
        {
            "title": "Which project management tool should our team use?",
            "answers": ["Jira", "Trello", "Asana", "Monday.com", "Notion", "Linear"],
            "tags": ["PROJECT MANAGEMENT", "PRODUCTIVITY", "TEAM"],
            "is_public": False,
            "is_editable": True
        },
        {
            "title": "Office lunch catering - What cuisine this Friday?",
            "answers": ["Italian", "Mexican", "Asian", "Mediterranean", "Indian", "American"],
            "tags": ["FOOD", "OFFICE", "TEAM"],
            "is_public": False,
            "is_editable": False
        },
        
        # Gaming
        {
            "title": "Game of the Year 2024 candidates?",
            "answers": ["Baldur's Gate 3", "Spider-Man 2", "Starfield", "Hogwarts Legacy", "Tears of the Kingdom", "Street Fighter 6"],
            "tags": ["GAMING", "ENTERTAINMENT", "AWARDS"],
            "is_public": True,
            "is_editable": True
        },
        {
            "title": "PC vs Console gaming in 2024?",
            "answers": ["PC - better performance", "Console - ease of use", "Both have their place", "Mobile gaming is the future"],
            "tags": ["GAMING", "TECHNOLOGY", "ENTERTAINMENT"],
            "is_public": True,
            "is_editable": False
        },
        
        # Environment & Sustainability
        {
            "title": "Most effective way to reduce carbon footprint?",
            "answers": ["Use public transport", "Eat less meat", "Buy renewable energy", "Reduce air travel", "Buy local products", "All of the above"],
            "tags": ["ENVIRONMENT", "SUSTAINABILITY", "CLIMATE"],
            "is_public": True,
            "is_editable": True
        },
        {
            "title": "Should plastic bags be completely banned?",
            "answers": ["Yes, ban all plastic bags", "Only single-use bags", "No, better recycling instead", "Use biodegradable alternatives"],
            "tags": ["ENVIRONMENT", "POLICY", "SUSTAINABILITY"],
            "is_public": True,
            "is_editable": False
        },
        
        # Sports
        {
            "title": "Most exciting sport to watch?",
            "answers": ["Football (Soccer)", "Basketball", "American Football", "Tennis", "Formula 1", "Hockey"],
            "tags": ["SPORTS", "ENTERTAINMENT"],
            "is_public": True,
            "is_editable": True
        },
        {
            "title": "Should esports be in the Olympics?",
            "answers": ["Yes, it's the future", "No, not a traditional sport", "Only certain games", "Create separate esports Olympics"],
            "tags": ["ESPORTS", "OLYMPICS", "GAMING"],
            "is_public": True,
            "is_editable": False
        }
    ]
    return topics_data

def create_users(db, users_data):
    """Create users in the database"""
    users = []
    print("Creating users...")
    
    for user_data in users_data:
        # Check if user already exists
        existing_user = db.query(User).filter(User.username == user_data["username"]).first()
        if existing_user:
            users.append(existing_user)
            continue
            
        user = User(
            username=user_data["username"],
            email=user_data["email"],
            hashed_password=get_password_hash(user_data["password"]),
            created_at=datetime.now(timezone.utc) - timedelta(days=random.randint(1, 90))
        )
        db.add(user)
        users.append(user)
    
    db.commit()
    print(f"Created {len(users)} users")
    return users

def create_topics(db, users, topics_data):
    """Create topics in the database"""
    topics = []
    print("Creating topics...")
    
    for i, topic_data in enumerate(topics_data):
        # Check if topic already exists
        existing_topic = db.query(Topic).filter(Topic.title == topic_data["title"]).first()
        if existing_topic:
            topics.append(existing_topic)
            continue
            
        creator = random.choice(users)
        
        topic = Topic(
            title=topic_data["title"],
            answers=topic_data["answers"],
            tags=topic_data["tags"],
            is_public=topic_data["is_public"],
            is_editable=topic_data["is_editable"],
            allow_multi_select=topic_data.get("allow_multi_select", False),
            created_by=creator.id,
            created_at=datetime.now(timezone.utc) - timedelta(days=random.randint(1, 30), hours=random.randint(0, 23)),
            share_code=topic_service.generate_share_code()  # Generate proper 8-char share code
        )
        
        db.add(topic)
        db.flush()  # Get the topic ID
        
        # Add creator to private topics access using the relationship
        if not topic.is_public:
            topic.accessible_users.append(creator)
        
        topics.append(topic)
    
    db.commit()
    print(f"Created {len(topics)} topics")
    return topics

def create_votes(db, users, topics):
    """Create realistic voting patterns"""
    print("Creating votes...")
    
    votes_created = 0
    for topic in topics:
        # Random number of voters for each topic (20-80% of users)
        num_voters = random.randint(int(len(users) * 0.2), int(len(users) * 0.8))
        voters = random.sample(users, num_voters)
        
        for voter in voters:
            # Check if vote already exists
            existing_vote = db.query(Vote).filter(
                Vote.user_id == voter.id,
                Vote.topic_id == topic.id
            ).first()
            if existing_vote:
                continue
                
            # Choose a random answer, with some bias towards first few options
            weights = [max(1, len(topic.answers) - i) for i in range(len(topic.answers))]
            chosen_answer = random.choices(topic.answers, weights=weights)[0]
            
            vote = Vote(
                user_id=voter.id,
                topic_id=topic.id,
                choice=chosen_answer,
                created_at=topic.created_at + timedelta(
                    hours=random.randint(1, 24 * 7)  # Vote within a week of topic creation
                )
            )
            db.add(vote)
            votes_created += 1
    
    db.commit()
    
    # Update denormalized vote counts
    print("Updating vote counts...")
    for topic in topics:
        vote_count = db.query(Vote).filter(Vote.topic_id == topic.id).count()
        topic.vote_count = vote_count
    
    db.commit()
    print(f"Created {votes_created} votes")

def create_favorites(db, users, topics):
    """Create realistic favorite patterns"""
    print("Creating favorites...")
    
    favorites_created = 0
    for user in users:
        # Each user favorites 10-30% of topics
        num_favorites = random.randint(int(len(topics) * 0.1), int(len(topics) * 0.3))
        favorite_topics = random.sample(topics, num_favorites)
        
        for topic in favorite_topics:
            # Check if favorite already exists
            existing_favorite = db.query(user_topic_favorites).filter(
                user_topic_favorites.c.user_id == user.id,
                user_topic_favorites.c.topic_id == topic.id
            ).first()
            if existing_favorite:
                continue
                
            # Add to favorites using the service to maintain denormalized counts
            try:
                favorites_service.add_to_favorites(db, topic, user)
                favorites_created += 1
            except Exception as e:
                # Topic might already be favorited
                pass
    
    print(f"Created {favorites_created} favorites")

def main():
    """Main function to populate the database"""
    print("🚀 Starting database population...")
    print("This will create comprehensive test data for Democrasite")
    print("-" * 50)
    
    db = SessionLocal()
    
    try:
        # Generate data
        users_data = generate_test_users()
        topics_data = generate_test_topics()
        
        # Create users
        users = create_users(db, users_data)
        
        # Create topics
        topics = create_topics(db, users, topics_data)
        
        # Create votes
        create_votes(db, users, topics)
        
        # Create favorites
        create_favorites(db, users, topics)
        
        print("-" * 50)
        print("✅ Database population completed successfully!")
        print(f"📊 Summary:")
        print(f"   - Users: {len(users)}")
        print(f"   - Topics: {len(topics)}")
        print(f"   - Public topics: {sum(1 for t in topics if t.is_public)}")
        print(f"   - Private topics: {sum(1 for t in topics if not t.is_public)}")
        print("")
        print("🔐 Test user credentials (all passwords: 'password123'):")
        for user_data in users_data[:5]:  # Show first 5 users
            print(f"   - {user_data['username']}")
        print(f"   - ... and {len(users_data)-5} more users")
        print("")
        print("🎯 You can now test the application with realistic data!")
        print("   Start the server: python3 main.py")
        print("   Login with any test user and explore the topics")
        
    except Exception as e:
        print(f"❌ Error populating database: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    main()