import os
import json
from dotenv import load_dotenv
from reapi_client import SkipTraceClient, MatchRequirements

def main():
    # Load environment variables
    load_dotenv()
    
    # Initialize the client
    client = SkipTraceClient()
    
    print("Testing Skip Trace API with specific address...")
    print("-" * 50)
    
    try:
        # Parse the address components
        street = "31799 Corte Padrera"
        city = "Temecula"
        state = "CA"
        zip_code = "92592"
        
        print(f"\nTesting address: {street}, {city}, {state} {zip_code}")
        
        # Make the API call with just the address first
        result = client.skip_trace(
            address=street,
            city=city,
            state=state,
            zip_code=zip_code,
            match_requirements=MatchRequirements(
                phones=True,
                emails=True,
                operator="or"
            )
        )
        
        # Print the full response
        print("\nAPI Response:")
        print(json.dumps(result, indent=2))
        
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
        print(f"\nError during skip trace:")
        print(f"Type: {type(e).__name__}")
        print(f"Message: {str(e)}")
        
        # If there's a response in the exception, print it
        if hasattr(e, 'response') and e.response is not None:
            try:
                print("\nError response:")
                print(json.dumps(e.response.json(), indent=2))
            except:
                print(f"Response text: {e.response.text}")

if __name__ == "__main__":
    main()
