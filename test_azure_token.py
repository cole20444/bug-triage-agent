#!/usr/bin/env python3
"""
Test script to verify Azure DevOps token functionality
"""

import os
from dotenv import load_dotenv
from azure_integration import azure_analyzer

# Load environment variables
load_dotenv()

def test_azure_token():
    """Test Azure DevOps token and API access"""
    print("🔍 Testing Azure DevOps Token...")
    
    # Check if token exists
    token = os.getenv('AZURE_DEVOPS_TOKEN')
    if not token:
        print("❌ No AZURE_DEVOPS_TOKEN found in .env file")
        return False
    
    print(f"✅ Token found: {token[:10]}...{token[-10:]}")
    
    # Test repository URL parsing
    test_url = "https://dev.azure.com/popagency/washington%20national%20park%20fund/_git/washington%20national%20park%20fund"
    
    try:
        org, project, repo, repo_id = azure_analyzer.extract_repo_info(test_url)
        print(f"✅ URL parsing successful:")
        print(f"   Organization: {org}")
        print(f"   Project: {project}")
        print(f"   Repository: {repo}")
        print(f"   Repo ID: {repo_id}")
    except Exception as e:
        print(f"❌ URL parsing failed: {e}")
        return False
    
    # Test API access
    print("\n🔍 Testing API access...")
    try:
        commits = azure_analyzer.get_recent_commits(test_url, days=7, branch="develop")
        print(f"✅ API access successful!")
        print(f"   Found {len(commits)} recent commits")
        
        if commits:
            print("\n📋 Recent commits:")
            for i, commit in enumerate(commits[:3]):
                print(f"   {i+1}. {commit['sha']} - {commit['message'][:50]}...")
                print(f"      Author: {commit['author']}")
                print(f"      Date: {commit['date']}")
                print(f"      Files changed: {len(commit['files_changed'])}")
        else:
            print("   No commits found in the last 7 days")
            
    except Exception as e:
        print(f"❌ API access failed: {e}")
        return False
    
    # Test repository stats
    print("\n🔍 Testing repository stats...")
    try:
        stats = azure_analyzer.get_repository_stats(test_url, branch="develop")
        if stats:
            print("✅ Repository stats retrieved:")
            for key, value in stats.items():
                print(f"   {key}: {value}")
        else:
            print("⚠️  No repository stats available")
    except Exception as e:
        print(f"❌ Repository stats failed: {e}")
    
    print("\n🎉 Azure DevOps token test completed!")
    return True

if __name__ == "__main__":
    test_azure_token() 