import urllib.request
import json
url = 'https://api.github.com/repos/vaibhavdubey06/autonomous-enterprise-manager/actions/runs'
req = urllib.request.Request(url, headers={'Accept': 'application/vnd.github.v3+json'})
with urllib.request.urlopen(req) as response:
    data = json.loads(response.read().decode())
    runs = data.get('workflow_runs', [])
    for run in runs[:5]:
        msg = run['head_commit']['message'].splitlines()[0]
        print(f"ID: {run['id']}, Status: {run['status']}, Conclusion: {run['conclusion']}, Commit: {msg}")
