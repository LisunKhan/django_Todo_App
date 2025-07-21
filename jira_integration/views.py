import os
import urllib.parse

from django.shortcuts import redirect
from django.http import HttpResponse, JsonResponse


# def jira_auth(request):
#     """
#     Redirects the user to the Atlassian authorization URL.
#     """
#     auth_url = os.getenv('ATLASSIAN_AUTH_URL')
#     client_id = os.getenv('ATLASSIAN_CLIENT_ID')
#     redirect_uri = os.getenv('ATLASSIAN_AUTH_REDIRECT_URL')
#     scope = 'read:jira-work manage:jira-project'
#
#     # Construct the authorization URL
#     authorization_url = (
#         f"{auth_url}/authorize"
#         f"?audience=api.atlassian.com"
#         f"&client_id={client_id}"
#         f"&scope={scope}"
#         f"&redirect_uri={redirect_uri}"
#         f"&state=YOUR_USER_BOUND_VALUE"
#         f"&response_type=code"
#         f"&prompt=consent"
#     )
#
#     return redirect(authorization_url)

def jira_auth(request):
    """
    Redirects the user to the Atlassian authorization URL.
    """
    auth_url = os.getenv('ATLASSIAN_AUTH_URL', 'https://auth.atlassian.com')
    client_id = os.getenv('ATLASSIAN_CLIENT_ID')
    redirect_uri = os.getenv('ATLASSIAN_AUTH_REDIRECT_URL', 'http://localhost:3000/integrations/jira')
    state = "your_user_bound_state_value"  # You can generate a real one per user/session

    # Scopes from your URL
    scopes = [
        "read:jira-work",
        "manage:jira-project",
        "manage:jira-configuration",
        "read:jira-user",
        "write:jira-work",
        "manage:jira-webhook",
        "manage:jira-data-provider"
    ]
    scope_str = urllib.parse.quote(" ".join(scopes))

    # Construct the authorization URL
    authorization_url = (
        f"{auth_url}/authorize"
        f"?audience=api.atlassian.com"
        f"&client_id={client_id}"
        f"&scope={scope_str}"
        f"&redirect_uri={urllib.parse.quote(redirect_uri)}"
        f"&state={state}"
        f"&response_type=code"
        f"&prompt=consent"
    )

    return redirect(authorization_url)

def jira_callback(request):
    """
    Handles the callback from the Atlassian authorization server.
    """
    code = "eyJhbGciOiJIUzI1NiJ9.eyJqdGkiOiIzMzlhZDM4OS1lOWMwLTRhODEtOTBkOC1hYTljZTQ4OWY5ODYiLCJzdWIiOiI3MTIwMjA6ZWM5ZWU1MDMtZjc3Zi00NzRiLWJjYjItZDJiM2U1OTU0MDZiIiwibmJmIjoxNzUyNjcyMDMxLCJpc3MiOiJhdXRoLmF0bGFzc2lhbi5jb20iLCJpYXQiOjE3NTI2NzIwMzEsImV4cCI6MTc1MjY3MjMzMSwiYXVkIjoiWGh0NXpsWjM3RVNFYnM3NXdWeTZTN0NLcW1VV2xNb3QiLCJjbGllbnRfYXV0aF90eXBlIjoiUE9TVCIsImh0dHBzOi8vaWQuYXRsYXNzaWFuLmNvbS92ZXJpZmllZCI6dHJ1ZSwiaHR0cHM6Ly9pZC5hdGxhc3NpYW4uY29tL3VqdCI6IjMzOWFkMzg5LWU5YzAtNGE4MS05MGQ4LWFhOWNlNDg5Zjk4NiIsInNjb3BlIjpbIm1hbmFnZTpqaXJhLWNvbmZpZ3VyYXRpb24iLCJtYW5hZ2U6amlyYS1kYXRhLXByb3ZpZGVyIiwibWFuYWdlOmppcmEtcHJvamVjdCIsIm1hbmFnZTpqaXJhLXdlYmhvb2siLCJyZWFkOmppcmEtdXNlciIsInJlYWQ6amlyYS13b3JrIiwid3JpdGU6amlyYS13b3JrIl0sImh0dHBzOi8vaWQuYXRsYXNzaWFuLmNvbS9hdGxfdG9rZW5fdHlwZSI6IkFVVEhfQ09ERSIsImh0dHBzOi8vaWQuYXRsYXNzaWFuLmNvbS9oYXNSZWRpcmVjdFVyaSI6dHJ1ZSwiaHR0cHM6Ly9pZC5hdGxhc3NpYW4uY29tL3Nlc3Npb25faWQiOiJkNWFlYTk4NC00NDkzLTRhYmUtYTBiYi1kOWIyZTYyNGE0ZmUiLCJodHRwczovL2lkLmF0bGFzc2lhbi5jb20vcHJvY2Vzc1JlZ2lvbiI6InVzLWVhc3QtMSJ9._Zl4Za4K4mDFCka-JcVYGoTFJUiVmDLTxFZVyachpLA"
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
    print(access_token)

    cloud_response = requests.get(
        "https://api.atlassian.com/oauth/token/accessible-resources",
        headers={
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/json"
        }
    )

    if cloud_response.status_code != 200:
        return JsonResponse({'error': 'Failed to fetch cloud info', 'details': cloud_response.text},
                            status=cloud_response.status_code)

    cloud_data = cloud_response.json()
    print(cloud_data)

    # Store the access token in the session
    request.session['jira_access_token'] = access_token

    return HttpResponse("Authorization successful. You can now use the Jira integration.")

def get_jira_cloud_info(request):
    """
    Fetches accessible Jira cloud instances using the access token.
    Returns cloud_id, site name, and base URL.
    """
    access_token = request.session.get('jira_access_token')
    if not access_token:
        return JsonResponse({'error': 'No access token found. Please authenticate first.'}, status=401)

    import requests

    try:
        cloud_response = requests.get(
            "https://api.atlassian.com/oauth/token/accessible-resources",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/json"
            }
        )

        if cloud_response.status_code != 200:
            return JsonResponse({'error': 'Failed to fetch cloud info', 'details': cloud_response.text}, status=cloud_response.status_code)

        cloud_data = cloud_response.json()
        print(cloud_data)

        if not cloud_data:
            return JsonResponse({'error': 'No accessible Jira resources found'}, status=404)

        # Return full list of accessible resources
        return JsonResponse({
            'accessible_resources': cloud_data
        }, status=200)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


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
