from mongoengine import DictField
from model.ApkScannerReport import ApkScannerReport


class MobSFScanReport(ApkScannerReport):
    results = DictField(required=True)

