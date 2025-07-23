import os, requests

def token(request):
    if not request.headers.get('Authorization'):
        return None, ('Missing Authorization header', 401)

    jwt_token = request.headers.get('Authorization')
    if not jwt_token:
        return None, ('Missing Authorization header', 401)

    response = requests.post(
        f"http://{os.environ.get('AUTH_SVC_ADDRESS')}/api/v1/validate",
        headers={'Authorization': f'Bearer {jwt_token}'},
    )
    if response.status_code == 200:
        return response.text, None
    else:
        return None, (response.text, response.status_code)