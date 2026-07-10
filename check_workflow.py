import urllib.request, json, time, sys

repo = 'vaibhavdubey06/autonomous-enterprise-manager'
run_id = 29074652270

while True:
    req = urllib.request.Request(f'https://api.github.com/repos/{repo}/actions/runs/{run_id}', headers={'User-Agent': 'Mozilla/5.0'})
    res = urllib.request.urlopen(req)
    data = json.loads(res.read())
    status = data['status']
    conclusion = data['conclusion']
    print(f'Status: {status}')
    if status == 'completed':
        print(f'Conclusion: {conclusion}')
        sys.exit(0 if conclusion == 'success' else 1)
    time.sleep(10)
