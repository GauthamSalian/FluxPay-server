import os
from supabase import create_client, Client
from dotenv import load_dotenv

#load environment variables
load_dotenv()

#get supabase credentials from environment variables
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")

#create supabase client
supabase: Client = create_client(supabase_url, supabase_key)