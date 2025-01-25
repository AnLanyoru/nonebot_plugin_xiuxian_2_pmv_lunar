try:
    import ujson as json
except ImportError:
    import json
from pathlib import Path

from .impart_all import impart_all

PATH_PERSON = Path() / "data" / "xiuxian" / "impart"


class ImpartData(object):
    def __init__(self):
        self.data_all = impart_all

    def data_all_keys(self):
        return list(self.data_all.keys())

    def data_all_(self):
        return self.data_all


impart_data_json = ImpartData()
