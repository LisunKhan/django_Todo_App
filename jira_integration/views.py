import os
from django.shortcuts import redirect
from django.http import HttpResponse

def jira_auth(request):
    """
    Redirects the user to the Atlassian authorization URL.
    """
    auth_url = os.getenv('ATLASSIAN_AUTH_URL')
    client_id = os.getenv('ATLASSIAN_CLIENT_ID')
    redirect_uri = os.getenv('ATLASSIAN_AUTH_REDIRECT_URL')
    scope = 'read:jira-work manage:jira-project'

    # Construct the authorization URL
    authorization_url = (
        f"{auth_url}/authorize"
        f"?audience=api.atlassian.com"
        f"&client_id={client_id}"
        f"&scope={scope}"
        f"&redirect_uri={redirect_uri}"
        f"&state=YOUR_USER_BOUND_VALUE"
        f"&response_type=code"
        f"&prompt=consent"
    )

    return redirect(authorization_url)

def jira_callback(request):
    """
    Handles the callback from the Atlassian authorization server.
    """
    code = request.GET.get('code')
    if not code:
        return HttpResponse("Authorization code not found.", status=400)

    # Exchange the authorization code for an access token
    token_url = f"{os.getenv('ATLASSIAN_AUTH_URL')}/oauth/token"
    payload = {
        'grant_type': 'authorization_code',
        'client_id': os.getenv('ATLASSIAN_CLIENT_ID'),
        'client_secret': os.getenv('ATLASSIAN_CLIENT_SECRET'),
        'code': code,
        'redirect_uri': os.getenv('ATLASSIAN_AUTH_REDIRECT_URL'),
    }

    import requests

    response = requests.post(token_url, json=payload)

    if response.status_code != 200:
        return HttpResponse(f"Failed to get access token: {response.text}", status=500)

    access_token = response.json().get('access_token')

    # Store the access token in the session
    request.session['jira_access_token'] = access_token

    return HttpResponse("Authorization successful. You can now use the Jira integration.")

def get_projects(request):
    """
    Fetches the list of projects from Jira.
    """
    access_token = request.session.get('jira_access_token')
    if not access_token:
        return redirect('jira_auth')

    api_base_url = os.getenv('ATLASSIAN_API_BASE_URL')
    api_prefix = os.getenv('ATLASSIAN_API_PREFIX')
    api_version = os.getenv('ATLASSIAN_API_VERSION')

    projects_url = f"{api_base_url}{api_prefix}{api_version}/project"

    headers = {
        'Authorization': f'Bearer {access_token}',
        'Accept': 'application/json',
    }

    import requests

    response = requests.get(projects_url, headers=headers)

    if response.status_code != 200:
        return HttpResponse(f"Failed to get projects: {response.text}", status=500)

    projects = response.json()

    from django.shortcuts import render

    return render(request, 'jira_projects.html', {'projects': projects})
