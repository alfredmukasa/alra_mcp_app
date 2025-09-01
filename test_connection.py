import openai
import anthropic
import httpx
import sys

class NoProxyHttpClient(httpx.Client):
    def __init__(self, **kwargs):
        kwargs.update({
            'timeout': 30.0,
            'limits': httpx.Limits(max_keepalive_connections=5, max_connections=10),
            'follow_redirects': True
        })
        if 'proxies' in kwargs:
            del kwargs['proxies']
        super().__init__(**kwargs)

def test_openai_connection(api_key):
    try:
        client = openai.OpenAI(
            api_key=api_key,
            http_client=NoProxyHttpClient(),
            max_retries=3
        )
        print("Testing OpenAI connection...")
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Say 'test successful'"}],
            max_tokens=5
        )
        print(f"✅ OpenAI connection successful! Response: {response.choices[0].message.content}")
        return True
    except Exception as e:
        print(f"❌ OpenAI connection failed: {str(e)}")
        return False

def test_claude_connection(api_key):
    print("\n=== Testing Claude Connection ===")
    
    # Test 1: Basic API key validation
    if not api_key or not api_key.startswith('sk-ant-'):
        print("❌ Invalid Claude API key format. It should start with 'sk-ant-'")
        return False
    
    # Test 2: Test connection with different configurations
    configs = [
        {"name": "Default config", "timeout": 30.0, "max_retries": 3},
        {"name": "No timeout", "timeout": None, "max_retries": 1},
        {"name": "Short timeout", "timeout": 10.0, "max_retries": 2}
    ]
    
    for config in configs:
        try:
            print(f"\nTesting with {config['name']}...")
            client = anthropic.Anthropic(
                api_key=api_key,
                timeout=config['timeout'],
                max_retries=config['max_retries']
            )
            
            # Simple test request
            response = client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=5,
                messages=[{"role": "user", "content": "Say 'test successful'"}]
            )
            
            # Check response structure
            if not response.content or not hasattr(response.content[0], 'text'):
                print(f"⚠️ Unexpected response format: {response}")
                continue
                
            print(f"✅ Success with {config['name']}! Response: {response.content[0].text}")
            return True
            
        except Exception as e:
            import traceback
            print(f"❌ Failed with {config['name']}:")
            print(f"   Error: {str(e)}")
            print(f"   Type: {type(e).__name__}")
            
            # Check for specific error types
            if "timeout" in str(e).lower():
                print("   ↳ The request timed out. This could be due to network issues or server slowness.")
            elif "connect" in str(e).lower():
                print("   ↳ Connection error. Please check your internet connection and proxy settings.")
            elif "401" in str(e):
                print("   ↳ Authentication failed. Please check your API key.")
            elif "404" in str(e):
                print("   ↳ The requested resource was not found. Check if the API endpoint is correct.")
            
            # Print full traceback for debugging
            print("\nFull traceback for debugging:")
            print("-" * 50)
            print(traceback.format_exc())
            print("-" * 50)
    
    # If we get here, all configurations failed
    print("\n❌ All connection attempts failed. Here are some things to try:")
    print("1. Check your internet connection")
    print("2. Verify your API key is correct")
    print("3. Try using a different network (e.g., mobile hotspot)")
    print("4. Check if your organization has any network restrictions")
    print("5. Try again later in case of temporary service issues")
    
    return False

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python test_connection.py <openai_api_key> <claude_api_key>")
        print("You can also test one at a time by providing just one key and 'none' for the other")
        sys.exit(1)
    
    openai_key = sys.argv[1] if sys.argv[1].lower() != 'none' else None
    claude_key = sys.argv[2] if sys.argv[2].lower() != 'none' else None
    
    if openai_key:
        test_openai_connection(openai_key)
    if claude_key:
        test_claude_connection(claude_key)
