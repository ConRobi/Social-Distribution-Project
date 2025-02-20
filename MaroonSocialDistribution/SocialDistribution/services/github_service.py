import requests
import re
from django.utils.timezone import now, make_aware
from datetime import datetime
from .models import Post

github_api_url = "https://api.github.com/users/{}/events/public"

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

    # If no username is found in the extraction process
    if not github_username:
        return
    
    url = github_api_url.format(github_username)

    # Send get request to github api
    git_response = requests.get(url)

    if git_response.status_code == 200:
        activities = response.json()
        for activity in activities:
            activity_time = activity['created_at']
            # Parse string into naive datetime
            activity_time = datetime.strptime(activity_time, '%Y-%m-%dT%H:%M:%SZ')

            # Make activity_time timezone aware
            activity_time = make_aware(activity_time)

            # Check for new activity only (checks if the activity time is earlier than the last check)
            # Will skip current iteration if conditional passes
            if author.last_checked and (activity_time < author.last_checked):
                continue
            post_content = f"Github Activity: {activity['type']} in {activity['repo']['name']}"
            Post.objects.create(
                title=f"Github Activity - {activity['type']}",
                description=activity.get("payload", {}).get("commits", [{}]).get("message", "No description"),
                content=post_content,
                author=author,
                visibility='PUBLIC'
            )
            
        # Update last_checked field
        author.last_checked = now()
        author.save()




