"""Compare freshly computed results with the values reported in the paper (expected_results/)."""
import sys, os, json, csv
EXP, OUT = sys.argv[1:3]
bad = 0
for f in sorted(os.listdir(EXP)):
    a, b = os.path.join(EXP, f), os.path.join(OUT, f)
    if not os.path.exists(b):
        print(f"  MISSING  {f}"); bad += 1; continue
    if f.endswith('.json'):
        same = json.load(open(a)) == json.load(open(b))
    else:
        same = sorted(csv.reader(open(a))) == sorted(csv.reader(open(b)))
    print(f"  {'OK      ' if same else 'DIFFERS '} {f}"); bad += not same
print("All results match the paper." if not bad else f"{bad} file(s) differ - see above.")
sys.exit(1 if bad else 0)
