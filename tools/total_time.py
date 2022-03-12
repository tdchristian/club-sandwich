# To get commits
# git log --pretty=format:"%ad" --date=format:'%Y-%m-%d %H:%M:%S'

commits = """"""

import datetime

threshold = datetime.timedelta(hours=1)

total_seconds = 0
newer = None

for commit in commits.split('\n'):
    dt = datetime.datetime.strptime(commit, '%Y-%m-%d %H:%M:%S')
    
    if newer:
        delta = newer - dt
        if delta <= threshold:
            total_seconds += delta.seconds
    
    newer = dt

delta = datetime.timedelta(seconds=total_seconds)
print(delta)
