import os
from typing import Any, Dict, List, Optional, Literal, Union
from dataclasses import dataclass
import requests

@dataclass
class MatchRequirements:
    """Specify requirements for matching in skip trace requests"""
    phones: bool = False
    emails: bool = False
    operator: Literal["and", "or"] = "and"

class SkipTraceClient:
    def __init__(
        self,
        base_url: str = "https://api.realestateapi.com",
        api_key: str = None,
        user_id: str = None,
        timeout_seconds: int = 30,
    ) -> None:
        """
        Initialize the SkipTrace API client.
        
        Args:
            base_url: Base URL for the API (defaults to production)
            api_key: API key (defaults to REAPI_API_KEY environment variable)
            user_id: Optional user identifier for tracking
            timeout_seconds: Request timeout in seconds
        """
        self.base_url = base_url.rstrip("/")
        self.skip_trace_url = f"{self.base_url}/v1/SkipTrace"
        self.api_key = api_key or os.getenv("REAPI_API_KEY")
        self.user_id = user_id or os.getenv("REAPI_USER_ID")
        self.timeout_seconds = timeout_seconds
        
        if not self.api_key:
            raise ValueError("API key is required. Set REAPI_API_KEY environment variable or pass api_key parameter.")

    def _headers(self) -> Dict[str, str]:
        """Generate headers for API requests"""
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "x-api-key": self.api_key
        }
        if self.user_id:
            headers["x-user-id"] = self.user_id
        return headers

    def skip_trace(
        self,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        middle_name: Optional[str] = None,
        name_prefix: Optional[str] = None,
        name_suffix: Optional[str] = None,
        address: Optional[str] = None,
        unit: Optional[str] = None,
        city: Optional[str] = None,
        state: Optional[str] = None,
        zip_code: Optional[str] = None,
        match_requirements: Optional[MatchRequirements] = None,
        live: bool = False
    ) -> Dict[str, Any]:
        """
        Perform a skip trace lookup using available identifiers.
        
        Args:
            email: Email address to look up
            phone: 10-digit phone number to look up
            first_name: First name of the person
            last_name: Last name of the person
            middle_name: Middle name of the person
            name_prefix: Name prefix (e.g., Mr., Mrs., Dr.)
            name_suffix: Name suffix (e.g., Jr., Sr., III)
            address: Street address (for property or mailing address)
            unit: Apartment/unit number
            city: City name
            state: 2-letter state code
            zip_code: 5 or 9-digit ZIP code
            match_requirements: Optional requirements for matching
            live: If False, uses test mode (no credits consumed)
            
        Returns:
            Dictionary containing skip trace results including identity, demographics, and metadata
            
        Raises:
            ValueError: If no valid identifiers are provided
            requests.exceptions.HTTPError: If the API request fails
        """
        payload: Dict[str, Any] = {}
        
        # Add identifiers if provided
        if email:
            payload["email"] = email
        if phone:
            # Clean phone number (remove non-digits)
            clean_phone = "".join(c for c in str(phone) if c.isdigit())
            if len(clean_phone) == 10:
                payload["phone"] = clean_phone
            else:
                raise ValueError("Phone number must be 10 digits")
                
        # Add name components
        name_parts = {}
        if first_name:
            name_parts["first_name"] = first_name
        if last_name:
            name_parts["last_name"] = last_name
        if middle_name:
            name_parts["middle_name"] = middle_name
        if name_prefix:
            name_parts["name_prefix"] = name_prefix
        if name_suffix:
            name_parts["name_suffix"] = name_suffix
            
        if name_parts:
            payload.update(name_parts)
            
        # Add address components
        if any([address, city, state, zip_code]):
            if address:
                payload["address"] = address
            if unit:
                payload["unit"] = unit
            if city:
                payload["city"] = city
            if state:
                if len(state) != 2:
                    raise ValueError("State must be a 2-letter code")
                payload["state"] = state.upper()
            if zip_code:
                clean_zip = "".join(c for c in str(zip_code) if c.isdigit())
                if len(clean_zip) in (5, 9):
                    payload["zip"] = clean_zip
                else:
                    raise ValueError("ZIP code must be 5 or 9 digits")
        
        # Add match requirements if provided
        if match_requirements:
            payload["match_requirements"] = {
                "phones": match_requirements.phones,
                "emails": match_requirements.emails,
                "operator": match_requirements.operator
            }
        
        # Note: Removed 'live' parameter as it's not allowed by the API
        # Validate at least one identifier was provided
        if not any([email, phone, name_parts, address, city, state, zip_code]):
            raise ValueError("At least one identifier (email, phone, name, or address) is required")
        
        # Make the API request
        try:
            response = requests.post(
                self.skip_trace_url,
                headers=self._headers(),
                json=payload,
                timeout=self.timeout_seconds
            )
            self._raise_for_status(response)
            return response.json()
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Skip trace request failed: {str(e)}") from e
    
    def _raise_for_status(self, response: requests.Response) -> None:
        """Raise an exception if the request was not successful"""
        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            try:
                error_data = response.json()
                error_msg = error_data.get("message", str(e))
                raise requests.exceptions.HTTPError(
                    f"{response.status_code} {response.reason}: {error_msg}",
                    response=response
                ) from e
            except ValueError:
                raise requests.exceptions.HTTPError(
                    f"{response.status_code} {response.reason}",
                    response=response
                ) from e
