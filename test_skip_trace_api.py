import os
import json
from dotenv import load_dotenv
from reapi_client import SkipTraceClient, MatchRequirements

def print_json(data, indent=2):
    """Helper to pretty print JSON data"""
    print(json.dumps(data, indent=indent))

def main():
    # Load environment variables
    load_dotenv()
    
    # Initialize the client
    client = SkipTraceClient()
    
    print("Testing Skip Trace API...")
    print("-" * 50)
    
    # Test with different combinations of identifiers
    test_cases = [
        {
            "name": "Full Address Lookup",
            "params": {
                "first_name": "John",
                "last_name": "Smith",
                "address": "123 Main St",
                "city": "Austin",
                "state": "TX",
                "zip_code": "78701"
            }
        },
        {
            "name": "Email Only Lookup",
            "params": {
                "email": "test@example.com"
            }
        },
        {
            "name": "Phone Only Lookup",
            "params": {
                "phone": "5551234567"
            }
        }
    ]
    
    for test in test_cases:
        try:
            print(f"\n{'='*20} {test['name']} {'='*20}")
            print(f"Parameters: {test['params']}")
            
            # Add match requirements for the first test case
            if test['name'] == "Full Address Lookup":
                test['params']['match_requirements'] = MatchRequirements(
                    phones=True,
                    emails=True,
                    operator="or"
                )
            
            # Make the API call
            result = client.skip_trace(**test['params'])
            
            # Print the full response for debugging
            print("\nAPI Response:")
            print_json(result)
            
            # Print summary
            print("\nSummary:")
            print(f"Status: {result.get('statusCode', 'N/A')}")
            print(f"Match: {result.get('match', 'N/A')}")
            print(f"Cached: {result.get('cached', 'N/A')}")
            print(f"Request ID: {result.get('requestId', 'N/A')}")
            
            if 'identity' in result:
                identity = result['identity']
                print(f"\nFound identity with {len(identity.get('phones', []))} phone(s) and {len(identity.get('emails', []))} email(s)")
            
        except Exception as e:
            print(f"\nError during {test['name']}:")
            print(f"Type: {type(e).__name__}")
            print(f"Message: {str(e)}")
            
        print("\n" + "-"*50)

if __name__ == "__main__":
    main()

if __name__ == "__main__":
    main()
