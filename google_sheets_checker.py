#!/usr/bin/env python3
"""
Google Sheets Checker Module
Checks if a value exists in a specific Google Sheet column
"""

import os
import time
import logging
from typing import List, Optional, Set
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

logger = logging.getLogger(__name__)

class GoogleSheetsChecker:
    """Check values against a Google Sheet"""
    
    def __init__(self, credentials_path: str = 'credentials.json'):
        """
        Initialize with Google service account credentials
        
        Args:
            credentials_path: Path to service account JSON file
        """
        if not os.path.exists(credentials_path):
            raise FileNotFoundError(f"Credentials file not found: {credentials_path}")
            
        # Initialize credentials
        self.credentials = service_account.Credentials.from_service_account_file(
            credentials_path,
            scopes=['https://www.googleapis.com/auth/spreadsheets.readonly']
        )
        
        # Build service
        self.service = build('sheets', 'v4', credentials=self.credentials)
        
        # Cache for sheet values
        self._cache = {}
        self._cache_timeout = 300  # 5 minutes
        self._last_cache_time = {}
        
        logger.info("Google Sheets Checker initialized")
    
    def get_column_values(self, spreadsheet_id: str, sheet_name: str, column: str) -> List[str]:
        """
        Get all values from a specific column
        
        Args:
            spreadsheet_id: Google Sheet ID
            sheet_name: Name of the sheet (default is first sheet)
            column: Column letter (e.g., 'A', 'B', etc.)
            
        Returns:
            List of values in the column
        """
        try:
            # Check cache
            cache_key = f"{spreadsheet_id}:{sheet_name}:{column}"
            if cache_key in self._cache:
                if time.time() - self._last_cache_time.get(cache_key, 0) < self._cache_timeout:
                    logger.debug(f"Using cached values for {cache_key}")
                    return self._cache[cache_key]
            
            # Construct range
            range_name = f"{sheet_name}!{column}:{column}" if sheet_name else f"{column}:{column}"
            
            # Get values from sheet
            result = self.service.spreadsheets().values().get(
                spreadsheetId=spreadsheet_id,
                range=range_name
            ).execute()
            
            values = result.get('values', [])
            
            # Flatten the list and convert to strings
            column_values = []
            for row in values:
                if row:  # Skip empty rows
                    value = str(row[0]).strip()
                    if value:  # Skip empty cells
                        column_values.append(value)
            
            # Update cache
            self._cache[cache_key] = column_values
            self._last_cache_time[cache_key] = time.time()
            
            logger.info(f"Retrieved {len(column_values)} values from {spreadsheet_id} column {column}")
            return column_values
            
        except HttpError as e:
            logger.error(f"Error accessing Google Sheet: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            raise
    
    def check_value_exists(self, 
                          value: str, 
                          spreadsheet_id: str, 
                          sheet_name: str = "", 
                          column: str = "A",
                          case_sensitive: bool = False) -> bool:
        """
        Check if a value exists in a specific column
        
        Args:
            value: Value to search for
            spreadsheet_id: Google Sheet ID
            sheet_name: Name of the sheet
            column: Column letter
            case_sensitive: Whether to do case-sensitive comparison
            
        Returns:
            True if value exists, False otherwise
        """
        try:
            # Get column values
            column_values = self.get_column_values(spreadsheet_id, sheet_name, column)
            
            # Normalize search value
            search_value = value.strip()
            if not case_sensitive:
                search_value = search_value.lower()
            
            # Check if value exists
            for sheet_value in column_values:
                compare_value = sheet_value
                if not case_sensitive:
                    compare_value = compare_value.lower()
                
                if compare_value == search_value:
                    logger.info(f"Found match for '{value}' in sheet")
                    return True
            
            logger.info(f"No match found for '{value}' in sheet")
            return False
            
        except Exception as e:
            logger.error(f"Error checking value: {str(e)}")
            return False
    
    def get_matching_values(self,
                           search_values: List[str],
                           spreadsheet_id: str,
                           sheet_name: str = "",
                           column: str = "A",
                           case_sensitive: bool = False) -> Set[str]:
        """
        Get all matching values from a list
        
        Args:
            search_values: List of values to search for
            spreadsheet_id: Google Sheet ID
            sheet_name: Name of the sheet
            column: Column letter
            case_sensitive: Whether to do case-sensitive comparison
            
        Returns:
            Set of matching values
        """
        try:
            # Get column values
            column_values = self.get_column_values(spreadsheet_id, sheet_name, column)
            
            # Create normalized sets for comparison
            if case_sensitive:
                sheet_set = set(v.strip() for v in column_values)
                search_set = set(v.strip() for v in search_values)
            else:
                sheet_set = set(v.strip().lower() for v in column_values)
                search_set = set(v.strip().lower() for v in search_values)
            
            # Find matches
            matches = sheet_set.intersection(search_set)
            
            # Return original case values
            if not case_sensitive and matches:
                # Find original values
                original_matches = set()
                for value in search_values:
                    if value.strip().lower() in matches:
                        original_matches.add(value.strip())
                return original_matches
            
            return matches
            
        except Exception as e:
            logger.error(f"Error getting matching values: {str(e)}")
            return set()
    
    def clear_cache(self):
        """Clear the cache"""
        self._cache.clear()
        self._last_cache_time.clear()
        logger.info("Cache cleared")


# Singleton instance
_sheets_checker = None

def get_sheets_checker(credentials_path: str = 'credentials.json') -> GoogleSheetsChecker:
    """Get or create sheets checker instance"""
    global _sheets_checker
    if _sheets_checker is None:
        _sheets_checker = GoogleSheetsChecker(credentials_path)
    return _sheets_checker


# Convenience functions
def check_employee_in_sheet(employee_name: str, 
                           spreadsheet_id: str = "1qqmTsIfLwGVPVj7kHnvb3AvAdFcMw37dh0RCoBxYViQ",
                           column: str = "A") -> bool:
    """
    Check if an employee name exists in the personnel sheet
    
    Args:
        employee_name: Employee name to check
        spreadsheet_id: Google Sheet ID (default is the personnel sheet)
        column: Column to check (default is A)
        
    Returns:
        True if employee exists, False otherwise
    """
    try:
        checker = get_sheets_checker()
        return checker.check_value_exists(
            employee_name,
            spreadsheet_id,
            sheet_name="",  # Use first sheet
            column=column,
            case_sensitive=False
        )
    except Exception as e:
        logger.error(f"Error checking employee: {str(e)}")
        return False


if __name__ == "__main__":
    # Test the module
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python google_sheets_checker.py <employee_name>")
        print("Example: python google_sheets_checker.py 'علی محمدی'")
        sys.exit(1)
    
    employee_name = sys.argv[1]
    sheet_id = "1qqmTsIfLwGVPVj7kHnvb3AvAdFcMw37dh0RCoBxYViQ"
    
    print(f"Checking if '{employee_name}' exists in Google Sheet...")
    
    try:
        exists = check_employee_in_sheet(employee_name, sheet_id)
        
        if exists:
            print(f"✅ Employee '{employee_name}' found in the sheet!")
        else:
            print(f"❌ Employee '{employee_name}' not found in the sheet.")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")