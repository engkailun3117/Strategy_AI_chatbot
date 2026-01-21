#!/usr/bin/env python3
"""
Generate a test JWT token for the subsidy chatbot test interface
"""
from jose import jwt
from datetime import datetime, timedelta

# Your external JWT secret
EXTERNAL_JWT_SECRET = "pcvu6CZu56YXhqo7vgp_vwV6SmiTHmg-aybT6JuMiF4"
ALGORITHM = "HS256"

# Create JWT payload with fields expected by backend
# The backend expects: user_id and username (see auth.py line 100-101)
payload = {
    "user_id": "test_user_001",
    "username": "Test User",
    "exp": datetime.utcnow() + timedelta(days=365)  # Valid for 1 year
}

# Generate token
token = jwt.encode(payload, EXTERNAL_JWT_SECRET, algorithm=ALGORITHM)

print("=" * 80)
print("Generated JWT Token for Test Interface")
print("=" * 80)
print(f"\nPayload:")
print(f"  user_id: {payload['user_id']}")
print(f"  username: {payload['username']}")
print(f"  exp: {payload['exp']}")
print(f"\nToken:\n{token}")
print("\n" + "=" * 80)
print("✅ Copy this token and use it in test-chatbot.html")
print("=" * 80)
