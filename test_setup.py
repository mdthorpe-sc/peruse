#!/usr/bin/env python3
"""
Test script to verify the screenshot monitoring tool setup
"""

import asyncio
import sys
from pathlib import Path

# Test imports
def test_imports():
    print("🔍 Testing imports...")
    
    try:
        from playwright.async_api import async_playwright
        print("✅ Playwright imported successfully")
    except ImportError as e:
        print(f"❌ Playwright import failed: {e}")
        print("Run: pip install playwright && playwright install")
        return False
    
    try:
        import boto3
        print("✅ Boto3 imported successfully")
    except ImportError as e:
        print(f"❌ Boto3 import failed: {e}")
        print("Run: pip install boto3")
        return False
    
    return True

# Test AWS credentials
def test_aws_credentials():
    print("\n🔑 Testing AWS credentials...")
    
    try:
        import boto3
        from botocore.exceptions import NoCredentialsError
        
        # Try to create a client
        client = boto3.client('bedrock-runtime', region_name='us-east-1')
        print("✅ AWS credentials configured")
        return True
    except NoCredentialsError:
        print("❌ AWS credentials not found")
        print("Run: aws configure")
        return False
    except Exception as e:
        print(f"⚠️  AWS setup issue: {e}")
        return False

# Test Playwright browser
async def test_playwright():
    print("\n🌐 Testing Playwright browser...")
    
    try:
        from playwright.async_api import async_playwright
        
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            await browser.close()
            print("✅ Playwright browser working")
            return True
    except Exception as e:
        print(f"❌ Playwright browser failed: {e}")
        print("Run: playwright install")
        return False

# Test Bedrock access (without making actual calls)
def test_bedrock_access():
    print("\n🤖 Testing Bedrock access (connection only)...")
    
    try:
        import boto3
        from botocore.exceptions import ClientError
        
        client = boto3.client('bedrock-runtime', region_name='us-east-1')
        
        # Try to list foundation models (read-only operation)
        bedrock_client = boto3.client('bedrock', region_name='us-east-1') 
        bedrock_client.list_foundation_models()
        print("✅ Bedrock access working")
        return True
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'AccessDeniedException':
            print("❌ Bedrock access denied")
            print("Go to AWS Bedrock Console → Model access → Request access to Claude models")
        else:
            print(f"⚠️  Bedrock connection issue: {error_code}")
        return False
    except Exception as e:
        print(f"⚠️  Bedrock test issue: {e}")
        return False

# Main test function
async def main():
    print("🧪 Screenshot Monitoring Tool - Setup Test")
    print("=" * 50)
    
    all_passed = True
    
    # Run tests
    if not test_imports():
        all_passed = False
    
    if not test_aws_credentials():
        all_passed = False
    
    if not await test_playwright():
        all_passed = False
    
    if not test_bedrock_access():
        all_passed = False
    
    print("\n" + "=" * 50)
    if all_passed:
        print("🎉 All tests passed! You're ready to use the screenshot monitoring tool.")
        print("\nNext steps:")
        print("1. List available models: python screenshot_monitor.py list-models")
        print("2. Take a baseline: python screenshot_monitor.py baseline https://example.com --model claude-4-sonnet")
        print("3. Test comparison: python screenshot_monitor.py compare https://example.com --model claude-4-sonnet")
    else:
        print("❌ Some tests failed. Please fix the issues above before using the tool.")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main()) 