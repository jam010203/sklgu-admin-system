# Supabase Integration Example
# Add your Supabase URL and API Key as environment variables in Fly.io
# Example usage in Python (admin_system/app.py):

import os
from supabase import create_client, Client

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Example: Fetch all users
def fetch_users():
    response = supabase.table("users").select("*").execute()
    return response.data

# Add your Supabase logic in your Flask routes as needed.
