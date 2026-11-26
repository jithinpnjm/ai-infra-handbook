import re

text = """Left KV arithmetic with 147,456 B per token and a 50.6 GB KV budget (assumed). 'One long request: 30,000 tokens = 4.42 GB'. 'One normal request: 2,500 tokens = 0.37 GB'. Bar A 'normal requests alone: 50.6 / 0.369 = 137 fit'. Bar B 'long requests that fill the GPU: 50.6 / 4.42 = 11'. Bar C 'left for others when 11 long run: 50.6 - 48.7 = 1.94 GB = 5 requests'. Headline 'eleven long requests take capacity from 137 down to 5 for everyone else: the case for charging by cost (tokens x context), not request count'. Right: 'cap at 25 percent of KV: 12.65 / 4.42 = 2 long requests'. Failure line 'cap is per replica but the router sends all of the tenant's long requests to one replica: the cap must hold across the pool'. Isolation tiers 'shared pool, long-context pool, dedicated endpoint'. Text at least 24px."""

# Notice tenant's has an apostrophe!
# The actual labels are:
# 1. 'One long request: 30,000 tokens = 4.42 GB'
# 2. 'One normal request: 2,500 tokens = 0.37 GB'
# 3. Bar A 'normal requests alone: 50.6 / 0.369 = 137 fit'
# 4. Bar B 'long requests that fill the GPU: 50.6 / 4.42 = 11'
# 5. Bar C 'left for others when 11 long run: 50.6 - 48.7 = 1.94 GB = 5 requests'
# 6. Headline 'eleven long requests take capacity from 137 down to 5 for everyone else: the case for charging by cost (tokens x context), not request count'
# 7. Right: 'cap at 25 percent of KV: 12.65 / 4.42 = 2 long requests'
# 8. Failure line 'cap is per replica but the router sends all of the tenant's long requests to one replica: the cap must hold across the pool'
# 9. Isolation tiers 'shared pool, long-context pool, dedicated endpoint'

labels = [
    "One long request: 30,000 tokens = 4.42 GB",
    "One normal request: 2,500 tokens = 0.37 GB",
    "normal requests alone: 50.6 / 0.369 = 137 fit",
    "long requests that fill the GPU: 50.6 / 4.42 = 11",
    "left for others when 11 long run: 50.6 - 48.7 = 1.94 GB = 5 requests",
    "eleven long requests take capacity from 137 down to 5 for everyone else: the case for charging by cost (tokens x context), not request count",
    "cap at 25 percent of KV: 12.65 / 4.42 = 2 long requests",
    "cap is per replica but the router sends all of the tenant's long requests to one replica: the cap must hold across the pool",
    "shared pool, long-context pool, dedicated endpoint"
]

for l in labels:
    assert l in text, f"Missing: {l}"
print("All 9 quoted labels found perfectly!")

