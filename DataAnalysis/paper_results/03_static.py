"""Step 3: static analyses (vendor, partition, version, AOSP-namespace hosts and their privileges).
Usage: python3 03_static.py <data dir> <out dir>"""
import sys, os, json
import pandas as pd, numpy as np, pyarrow.parquet as pq
DATA, OUT = sys.argv[1:3]
R = {}
cols = ['firmware_id', 'os_vendor', 'version_detected', 'partition_name', 'application.handle', 'tracker_names', 'apk.checksum']
s = pq.read_table(os.path.join(DATA, 'static_analysis.parquet'), columns=cols).to_pandas()
s['n'] = s.tracker_names.map(lambda x: len(json.loads(x)) if isinstance(x, str) else len(x))
s['has'] = s.n > 0
R['apps'] = len(s); R['images'] = s.firmware_id.nunique(); R['apps_with_tracker'] = int(s.has.sum())
R['share_with_tracker'] = round(100 * s.has.mean(), 1)
img = s.groupby('firmware_id').agg(vendor=('os_vendor', 'first'), apps=('has', 'size'), tr_apps=('has', 'sum'))
v = s.groupby('os_vendor').agg(apps=('has', 'size'), share=('has', 'mean'), images=('firmware_id', 'nunique'))
v['tr_apps_per_image_median'] = img.groupby('vendor').tr_apps.median()
v['share'] = (100 * v.share).round(1)
v = v.sort_values('images', ascending=False)
v.to_csv(os.path.join(OUT, 'static_by_vendor.csv'))
R['vendors_ge10_images'] = v[v.images >= 10].to_dict('index')
R['by_partition'] = (100 * s.groupby('partition_name').has.mean()).round(1).to_dict()
R['apps_by_partition'] = s.groupby('partition_name').size().to_dict()
R['by_version'] = (100 * s.groupby('version_detected').has.mean()).round(1).to_dict()
R['images_by_version'] = s.groupby('version_detected').firmware_id.nunique().to_dict()
R['tr_apps_per_image_median_all'] = float(img.tr_apps.median())
# AOSP-namespace packages (com.android.*) carrying trackers; com.android.vending (Play Store) and
# com.android.chrome are proprietary Google apps and are excluded.
EXCL = {'com.android.vending', 'com.android.chrome'}
ao = s[s['application.handle'].str.startswith('com.android.') & s.has & ~s['application.handle'].isin(EXCL)]
R['aosp_hosts'] = {'instances': len(ao), 'packages': int(ao['application.handle'].nunique()),
                   'apks': int(ao['apk.checksum'].nunique()), 'images': int(ao.firmware_id.nunique()),
                   'vendors': int(ao.os_vendor.nunique()),
                   'pkg_vendor_pairs': int(ao[['application.handle', 'os_vendor']].drop_duplicates().shape[0]),
                   'by_vendor': ao.os_vendor.value_counts().to_dict(),
                   'by_package': ao['application.handle'].value_counts().to_dict(),
                   'max_trackers': ao.groupby('application.handle').n.max().sort_index().sort_values(ascending=False, kind='stable').head(5).to_dict()}
# requested permissions of these hosts (read only for the selected rows)
perm = pq.read_table(os.path.join(DATA, 'static_analysis.parquet'), columns=['application.permissions']).to_pandas()['application.permissions']
pl = perm.loc[ao.index].map(lambda x: json.loads(x) if isinstance(x, str) else list(x))
P = ['WRITE_SECURE_SETTINGS', 'INTERACT_ACROSS_USERS', 'READ_PRIVILEGED_PHONE_STATE', 'READ_PHONE_STATE', 'QUERY_ALL_PACKAGES',
     'READ_CONTACTS', 'PACKAGE_USAGE_STATS', 'ACCESS_FINE_LOCATION', 'READ_SMS', 'RECORD_AUDIO', 'CAMERA', 'INSTALL_PACKAGES']
R['aosp_hosts_perm_share'] = {p: round(100 * pl.map(lambda l: any(str(e).endswith('.' + p) for e in l)).mean(), 1) for p in P}
# baseline: same permissions among all apps with trackers
del perm
json.dump(R, open(os.path.join(OUT, 'static_results.json'), 'w'), indent=1, default=str)

# Figure: tracker prevalence per vendor (vendors with >= 10 images)
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
matplotlib.rcParams['pdf.fonttype'] = 42; matplotlib.rcParams['ps.fonttype'] = 42
vv = v[v.images >= 10].sort_values('share')
fig, ax = plt.subplots(figsize=(3.4, 2.6))
ax.barh([f'{i} ({int(r.images)})' for i, r in vv.iterrows()], vv.share, color='#4C72B0')
ax.axvline(100 * s.has.mean(), color='#555', ls='--', lw=0.8)
ax.set_xlabel('Apps with $\\geq$1 Exodus tracker (%)', fontsize=8); ax.tick_params(labelsize=7)
for sp in ['top', 'right']: ax.spines[sp].set_visible(False)
fig.tight_layout(); fig.savefig(os.path.join(OUT, 'tracker_share_by_vendor.pdf'))
print(json.dumps(R, indent=1, default=str))
