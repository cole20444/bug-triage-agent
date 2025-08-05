#!/usr/bin/env python3
"""
Test script to debug OpenAI API issues
"""

import os
import requests
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_openai_api():
    """Test OpenAI API directly"""
    api_key = os.getenv('OPENAI_API_KEY')
    base_url = "https://api.openai.com/v1/chat/completions"
    
    print(f"🔍 Testing OpenAI API...")
    print(f"API Key length: {len(api_key) if api_key else 0}")
    print(f"API Key starts with: {api_key[:10] if api_key else 'None'}...")
    print(f"Base URL: {base_url}")
    
    if not api_key:
        print("❌ No OpenAI API key found")
        return
    
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    
    data = {
        'model': 'gpt-3.5-turbo',
        'messages': [
            {
                'role': 'system',
                'content': 'You are a helpful assistant.'
            },
            {
                'role': 'user',
                'content': 'Say "Hello, this is a test!"'
            }
        ],
        'max_tokens': 50,
        'temperature': 0.3
    }
    
    try:
        print(f"\n📡 Making API request...")
        response = requests.post(base_url, headers=headers, json=data)
        
        print(f"Response status: {response.status_code}")
        print(f"Response headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            result = response.json()
            content = result['choices'][0]['message']['content']
            print(f"✅ Success! Response: {content}")
        else:
            print(f"❌ Error response: {response.text}")
            
    except Exception as e:
        print(f"❌ Exception: {e}")

if __name__ == "__main__":
    test_openai_api() 