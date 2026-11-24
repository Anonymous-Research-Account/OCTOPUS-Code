"""Step 2: dynamic analyses on (run, UID group) instances.
Usage: python3 02_dynamic.py <data dir> <out dir>"""
import sys, os, json, re, itertools
import pandas as pd, numpy as np, pyarrow.parquet as pq
DATA, OUT = sys.argv[1:3]
R = {}
t = pd.read_parquet(os.path.join(OUT, 'traffic_agg.parquet'))
t['is_ip'] = t.real_domain.fillna('').str.match(r'^[0-9.]+$')

# ---------- vendors of runs ----------
s = pq.read_table(os.path.join(DATA, 'static_analysis.parquet'),
                  columns=['firmware_id', 'os_vendor', 'application.handle', 'tracker_names']).to_pandas()
vend = s[['firmware_id', 'os_vendor']].drop_duplicates().set_index('firmware_id').os_vendor
runs = t.groupby('run').agg(image=('image', 'first'), app=('os', lambda x: (~x).any()))
runs['vendor'] = runs.image.map(vend).fillna('n/a')
def internet(g): return (~g.real_domain.fillna('').str.match(r'^(224\.|239\.|127\.|10\.0\.2\.)')).any()
runs['internet'] = t.groupby('run').apply(internet)
R['runs_total'] = len(runs); R['images_total'] = runs.image.nunique()
R['runs_by_vendor'] = runs.groupby('vendor').size().to_dict()
R['runs_internet_by_vendor'] = runs[runs.internet].groupby('vendor').size().to_dict()
R['runs_app_by_vendor'] = runs[runs.app].groupby('vendor').size().to_dict()
R['images_twice'] = int((runs.groupby('image').size() > 1).sum())
R['images_twice_app_both'] = int((runs[runs.app].groupby('image').size() > 1).sum())

# ---------- instances ----------
a = t[~t.os].copy()
OWN = [('Google', r'(google|gstatic|googleapis|doubleclick|googlesyndication|googleadservices|googletagmanager|google-analytics|app-measurement|youtube|ytimg|ggpht|googleusercontent|gvt1)\.'),
       ('Yahoo', r'(yahoo|yimg|ipqs)\.'), ('Microsoft', r'(live|microsoft|msauth|msftauth|office|copilot)\.'),
       ('Verizon', r'verizon')]
def owner(d):
    if not isinstance(d, str) or re.match(r'^[0-9.]+$', d): return 'IP literal'
    for o, p in OWN:
        if re.search(p, d): return o
    return 'Other'
a['owner'] = a.real_domain.map(owner)
s['tr'] = s.tracker_names.map(lambda x: json.loads(x) if isinstance(x, str) else list(x))
inst = a[['run', 'image', 'grp']].drop_duplicates()
mem = inst.assign(pkg=inst.grp.str.split(', ')).explode('pkg')
mem = mem.merge(s[['firmware_id', 'application.handle', 'tr']], left_on=['image', 'pkg'], right_on=['firmware_id', 'application.handle'], how='left')
st = mem.groupby(['run', 'grp']).agg(has_static=('tr', lambda x: x.notna().any()),
                                     trackers=('tr', lambda x: sorted(set(v for l in x.dropna() for v in l))),
                                     n_members=('pkg', 'nunique')).reset_index()
ad = a[a.adtrack].groupby(['run', 'grp']).real_domain.agg(lambda x: sorted(set(x))).rename('ad_domains').reset_index()
inst = st.merge(ad, on=['run', 'grp'], how='left')
inst['ad_domains'] = inst.ad_domains.apply(lambda x: x if isinstance(x, list) else [])
inst = inst[inst.has_static].copy()
inst['shared_uid'] = inst.n_members > 1
R['instances'] = len(inst); R['instances_runs'] = inst.run.nunique(); R['instances_groups'] = inst.grp.nunique()
R['instances_shared_uid'] = int(inst.shared_uid.sum())
def cat(r):
    S, D = bool(r.trackers), bool(r.ad_domains)
    return {(False, False): 'none', (True, False): 'static_only', (True, True): 'both', (False, True): 'dynamic_only'}[(S, D)]
inst['cat'] = inst.apply(cat, axis=1)
R['cat_counts'] = inst['cat'].value_counts().to_dict()
R['cat_shared'] = inst.groupby('cat').shared_uid.sum().astype(int).to_dict()
R['dynamic_only_groups'] = inst[inst['cat'] == 'dynamic_only'].grp.value_counts().to_dict()

# ---------- tracker-level matching: each SDK vs its own endpoint family ----------
ENDPOINTS = {'Google Firebase Analytics': ['app-measurement.com', 'firebaseio.com', 'firebase.com', 'firebaselogging.googleapis.com', 'firebase-settings.crashlytics.com'],
             'Google Analytics': ['google-analytics.com'],
             'Google AdMob': ['googleads.g.doubleclick.net', 'pagead2.googlesyndication.com', 'googlesyndication.com', 'admob.com', 'adservice.google.com', 'googleadservices.com', 'doubleclick.net'],
             'Google CrashLytics': ['crashlytics.com', 'crashlyticsreports-pa.googleapis.com'],
             'Google Tag Manager': ['googletagmanager.com']}
def match(d, eps): return any(d == e or d.endswith('.' + e) for e in eps)
rows = []
for r in inst.itertuples():
    for tr in r.trackers:
        eps = ENDPOINTS.get(tr)
        rows.append({'tracker': tr, 'mapped': eps is not None,
                     'confirmed': bool(eps) and any(match(d, eps) for d in r.ad_domains), 'grp': r.grp})
tl = pd.DataFrame(rows)
R['tracker_level'] = tl.groupby('tracker').agg(instances=('confirmed', 'size'), confirmed=('confirmed', 'sum'),
                                              groups=('grp', 'nunique')).astype(int).sort_values('instances', ascending=False).to_dict('index')
R['tracker_level_total'] = {'pairs': len(tl), 'confirmed': int(tl.confirmed.sum())}
# ad/tracking domains not explained by a static tracker of the same instance
unexpl = []
for r in inst.itertuples():
    eps = [e for tr in r.trackers for e in ENDPOINTS.get(tr, [])]
    for d in r.ad_domains:
        if not match(d, eps): unexpl.append({'grp': r.grp, 'domain': d, 'owner': owner(d)})
ue = pd.DataFrame(unexpl)
R['unexplained_pairs'] = len(ue)
R['unexplained_by_owner_grp'] = ue.groupby(['owner', 'grp']).size().sort_values(ascending=False).to_dict() if len(ue) else {}
R['unexplained_by_owner_grp'] = {f'{k[0]} | {k[1]}': int(v) for k, v in R['unexplained_by_owner_grp'].items()}

# ---------- ad/tracking traffic volume by owner and group ----------
adt = a[a.adtrack]
R['adtrack_pkts_by_grp_owner'] = {f'{k[0]} | {k[1]}': int(v) for k, v in adt.groupby(['grp', 'owner']).flows_pkts.sum().sort_values(ascending=False).items()}
R['adtrack_pkts_total'] = int(adt.flows_pkts.sum())
R['adtrack_domains_by_owner'] = adt.groupby('owner').real_domain.nunique().to_dict()
# non-Google endpoints reached by Gmail
gm = a[a.grp == 'com.google.android.gm']
R['gmail_nonGoogle_domains'] = sorted(gm[gm.owner.isin(['Yahoo', 'Microsoft'])].real_domain.unique())
R['gmail_nonGoogle_runs'] = int(gm[gm.owner.isin(['Yahoo', 'Microsoft'])].run.nunique()); R['gmail_runs'] = int(gm.run.nunique())

# ---------- stability across images (natural replicates) ----------
stab = []
for g, x in a[~a.is_ip].groupby('grp'):
    sets = [set(v.real_domain) for _, v in x.groupby('run')]
    if len(sets) < 10: continue
    js = [len(p & q) / len(p | q) for p, q in itertools.combinations(sets, 2)]
    adr = x[x.adtrack].run.nunique() / x.run.nunique()
    stab.append({'grp': g, 'runs': len(sets), 'jaccard_mean': round(float(np.mean(js)), 2),
                 'core_domains': len(set.intersection(*sets)), 'adtrack_share_runs': round(adr, 2)})
stab = pd.DataFrame(stab).sort_values('runs', ascending=False)
stab.to_csv(os.path.join(OUT, 'stability.csv'), index=False)
R['stability_n_groups'] = len(stab); R['stability_median_jaccard'] = float(stab.jaccard_mean.median())
R['stability'] = stab.set_index('grp').to_dict('index')

# ---------- carrier software and local-network discovery ----------
R['verizon'] = {'runs': int(a[a.grp == 'com.verizon.mips.services'].run.nunique()),
                'runs_verizon_domain': int(a[(a.grp == 'com.verizon.mips.services') & (a.owner == 'Verizon')].run.nunique()),
                'domains': sorted(a[a.grp == 'com.verizon.mips.services'].real_domain.dropna().unique())}
lan = t[t.dst_port.isin([5353, 1900])]
R['lan'] = {f'{int(p)} | {g}': int(n) for (p, g), n in lan.groupby(['dst_port', 'grp']).run.nunique().items()}
R['lan_app_runs'] = int(lan[~lan.os].run.nunique())

# ---------- coverage vs. category ----------
_cov = os.path.join(DATA, 'coverage_summary.csv')  # name used by notebook 04; on Zenodo the file is coverage.csv
if not os.path.exists(_cov): _cov = os.path.join(DATA, 'coverage.csv')
cov = pd.read_csv(_cov)
cov['pct'] = cov['Cov.'].str.rstrip('%').astype(float)
g2 = inst.assign(pkg=inst.grp.str.split(', ')).explode('pkg')
cm = cov.merge(g2, left_on=['Firmware_ID', 'Package'], right_on=['run', 'pkg'])
R['coverage_overlap'] = {'instances': len(cm), 'packages': int(cm.Package.nunique()), 'runs': int(cm.run.nunique())}
R['coverage_by_cat'] = cm.groupby('cat').pct.describe()[['count', 'mean', '50%', 'max']].round(2).to_dict('index')
R['coverage_by_cat_pkgs'] = cm.groupby('cat').Package.unique().map(list).to_dict()
inst.to_parquet(os.path.join(OUT, 'instances.parquet'))
json.dump(R, open(os.path.join(OUT, 'dynamic_results.json'), 'w'), indent=1, default=str)
print(json.dumps(R, indent=1, default=str))
