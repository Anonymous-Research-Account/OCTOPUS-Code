"""Step 1: classify every contacted domain against the released blocklists and
aggregate app-attributed traffic to (run, UID group) instances.
Usage: python3 01_blocklists_traffic.py <unzipped Blocklists dir> <data dir> <out dir>"""
import sys, os, re, json, collections
import pyarrow.parquet as pq, pandas as pd
BL, DATA, OUT = sys.argv[1:4]

# Feeds whose primary purpose is advertising/tracking/telemetry. All other feeds
# (malware, phishing, scam, NSFW, crypto, threat intelligence) are "security/content".
ADTRACK = ['StevenBlack/hosts', 'lists/tracking.txt', 'lists/advertising.txt', 'oisd', 'adservers.txt',
           'anudeepND/blacklist/master/facebook.txt', 'hagezi/dns-blocklists@latest/domains/native.',
           'protoconsent_advanced_tracking', 'protoconsent_third_parties', 'protoconsent_personalization',
           'protoconsent_analytics', 'protoconsent_ads', 'AdguardDNS', 'Admiral', 'Easylist', 'Easyprivacy',
           'Prigent-Ads', 'pgl.yoyo.org', 'UncheckyAds', 'add.2o7Net', 'bigdargon', 'WindowsSpyBlocker',
           'firstparty-trackers', 'kitsapcreator.com/social/tiktok']

import pyarrow as pa, pyarrow.compute as pc
tab = pq.read_table(os.path.join(DATA, 'app_traffic.parquet'), columns=['firmware_id', 'package_name', 'real_domain', 'length', 'dst_port'])
# aggregate to (run, UID group, domain, port) to keep memory small
agg = tab.group_by(['firmware_id', 'package_name', 'real_domain', 'dst_port']).aggregate([('length', 'sum'), ('length', 'count')])
del tab
t = agg.to_pandas().rename(columns={'length_sum': 'bytes', 'length_count': 'flows_pkts'})
domains = set(t.real_domain.dropna().unique())
def parents(d):
    p = d.split('.'); return ['.'.join(p[i:]) for i in range(len(p) - 1)]
cand = set(x for d in domains for x in parents(d)) | domains

hit = collections.defaultdict(set)   # listed name -> feeds
dom_re = re.compile(r'^(?:0\.0\.0\.0|127\.0\.0\.1|::1?)?\s*\|{0,2}\*?\.?([a-z0-9][a-z0-9.\-_]*[a-z0-9])\^?(?:\$.*)?\s*$')
nfeeds = 0; nentries = 0
for root, _, files in os.walk(BL):
    for f in files:
        if f.startswith('00_') or f.startswith('.'): continue   # skip the URL index and macOS .DS_Store files
        path = os.path.join(root, f); rel = os.path.relpath(path, BL); nfeeds += 1
        with open(path, errors='ignore') as fh:
            for line in fh:
                line = line.strip().lower()
                if not line or line[0] in '#!': continue
                m = dom_re.match(line.split('#')[0].strip())
                if not m: continue
                nentries += 1
                d = m.group(1)
                if d in cand: hit[d].add(rel)

def classify(d):
    feeds = set()
    for x in [d] + parents(d):   # domain or any parent domain listed
        feeds |= hit.get(x, set())
    ad = any(any(k in f for k in ADTRACK) for f in feeds)
    sec = any(not any(k in f for k in ADTRACK) for f in feeds)
    return pd.Series({'listed': bool(feeds), 'adtrack': ad, 'security_only': bool(feeds) and not ad, 'n_feeds': len(feeds)})
dc = pd.DataFrame({'real_domain': sorted(domains)})
dc = pd.concat([dc, dc.real_domain.apply(classify)], axis=1)
# listing via a parent that is a broad first-party root (e.g. google.com) would flag all of Google: report it
dc['listed_via'] = dc.real_domain.map(lambda d: next((x for x in [d] + parents(d) if x in hit), None))
dc.to_csv(os.path.join(OUT, 'domain_classification.csv'), index=False)
json.dump({'feeds_parsed': nfeeds, 'entries_parsed': nentries}, open(os.path.join(OUT, 'blocklist_stats.json'), 'w'))

t['run'] = t.firmware_id.astype(str); t['image'] = t.run.str[:24]
t['grp'] = t.package_name.astype(str); t['os'] = t.grp.str.startswith('UID 0')
t = t.merge(dc[['real_domain', 'adtrack', 'listed']], on='real_domain', how='left')
t.drop(columns=['firmware_id', 'package_name']).to_parquet(os.path.join(OUT, 'traffic_agg.parquet'))
print(nfeeds, nentries, dc.listed.sum(), dc.adtrack.sum())
print(dc[dc.listed].sort_values('real_domain').to_string())
