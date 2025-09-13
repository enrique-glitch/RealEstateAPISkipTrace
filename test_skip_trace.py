import os
from dotenv import load_dotenv
from reapi_client import SkipTracingAPIClient

def main():
    # Load environment variables
    load_dotenv()
    
    # Initialize the client
    client = SkipTracingAPIClient()
    
    # Example: Skip trace by address
    try:
        result = client.skip_trace(
            addresses=[
                {
                    "address": "123 Main St",
                    "city": "Austin",
                    "state": "TX",
                    "zip": "78701"
                }
            ],
            live=False  # Test mode - won't consume credits
        )
        print("Skip trace results:")
        print(result)
    except Exception as e:
        print(f"Error during skip trace: {str(e)}")

if __name__ == "__main__":
    main()
