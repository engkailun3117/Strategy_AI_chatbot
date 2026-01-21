#!/usr/bin/env python3
"""
Test script to verify Gemini API is working correctly
"""
import os
from google import genai
from google.genai import types
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get API key from environment
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    print("❌ GEMINI_API_KEY not set in environment or .env file")
    print("   Please create a .env file with: GEMINI_API_KEY=your_api_key_here")
    exit(1)

print(f"✅ API Key loaded: {GEMINI_API_KEY[:20]}...")

# Create client
try:
    client = genai.Client(api_key=GEMINI_API_KEY)
    print("✅ Gemini client created successfully")
except Exception as e:
    print(f"❌ Failed to create client: {e}")
    exit(1)

# Test available models
print("\n📋 Testing model access...")
models_to_test = [
    "gemini-2.5-flash",
    "gemini-2.0-flash-exp",
    "gemini-1.5-flash",
    "gemini-1.5-pro"
]

for model_name in models_to_test:
    try:
        print(f"\n🧪 Testing model: {model_name}")

        # Create a simple test message
        contents = [
            types.Content(
                role="user",
                parts=[types.Part(text="請回答「收到」")]
            )
        ]

        # Try to generate content
        response = client.models.generate_content(
            model=model_name,
            contents=contents,
            config=types.GenerateContentConfig(temperature=0.7)
        )

        # Check response
        if response.candidates and len(response.candidates) > 0:
            candidate = response.candidates[0]
            if candidate.content and candidate.content.parts:
                text = "".join([p.text for p in candidate.content.parts if hasattr(p, 'text') and p.text])
                print(f"   ✅ Model works! Response: {text[:50]}...")
        else:
            print(f"   ⚠️ Model responded but no candidates")

    except Exception as e:
        print(f"   ❌ Model failed: {str(e)[:100]}")

# Test function calling
print("\n\n🔧 Testing function calling...")
try:
    contents = [
        types.Content(
            role="user",
            parts=[types.Part(text="我的計畫類型是行銷")]
        )
    ]

    # Define function
    function_declarations = [
        types.FunctionDeclaration(
            name="save_project_type",
            description="儲存使用者的計畫類型",
            parameters={
                "type": "object",
                "properties": {
                    "project_type": {
                        "type": "string",
                        "description": "計畫類型：研發或行銷"
                    }
                },
                "required": ["project_type"]
            }
        )
    ]

    response = client.models.generate_content(
        model="gemini-2.0-flash-exp",  # Use the most reliable model
        contents=contents,
        config=types.GenerateContentConfig(
            tools=[types.Tool(function_declarations=function_declarations)],
            temperature=0.7
        )
    )

    print("\n📦 Response structure:")
    if response.candidates and len(response.candidates) > 0:
        candidate = response.candidates[0]
        if candidate.content and candidate.content.parts:
            for i, part in enumerate(candidate.content.parts):
                print(f"\nPart {i}:")
                print(f"  Type: {type(part)}")
                print(f"  Has text: {hasattr(part, 'text')}")
                print(f"  Has function_call: {hasattr(part, 'function_call')}")

                if hasattr(part, 'text') and part.text:
                    print(f"  Text: {part.text[:100]}")

                if hasattr(part, 'function_call') and part.function_call:
                    print(f"  ✅ Function call detected!")
                    print(f"     Name: {part.function_call.name}")
                    print(f"     Args: {dict(part.function_call.args)}")
        else:
            print("  No parts in candidate")
    else:
        print("  No candidates in response")

except Exception as e:
    print(f"❌ Function calling test failed: {e}")
    import traceback
    traceback.print_exc()

print("\n✅ Test completed!")
