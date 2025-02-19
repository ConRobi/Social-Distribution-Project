import requests
import re
from datetime import datetime
from .models import Post

def extract_github_username(profile_url):
    '''
    Extract github username from author's github url
    '''
    # Capture only the username from the url
    match = re.search(r'github\.com/([^/]+)', profile_url)

    # Checks if the username is found from the url
    if match:
        return match.group(1) # Return the first capture group (username)
    else:
        return None

def fetch_github_activity(author):
    '''
    Fetch recent github activity from author's github account and
    convert it into a Post object
    '''
    # Extract github username from author's github field
    github_username = extract_github_username(author.github)
