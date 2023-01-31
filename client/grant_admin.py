# Grant admin to user
# Usage: `python grant_admin.py <username>`

import argparse
import scirisweb as sw
import nutrition_app as onwa
import os

parser = argparse.ArgumentParser()
parser.add_argument("username")
args = parser.parse_args()

redis_url = onwa.config.REDIS_URL
datastore = sw.make_datastore(redis_url)
user = datastore.loaduser(args.username)
user.is_admin=True
datastore.saveuser(user)
print(f'"{args.username}" is now an admin')
