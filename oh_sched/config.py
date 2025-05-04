import datetime
import pathlib
from copy import copy
from datetime import datetime, timedelta

import pandas as pd
import pytz
import yaml


class Config:
    def __init__(self, oh_per_ta=1, max_ta_per_oh=None, scale_dict=None,
                 date_start=None, date_end=None, f_out=None, tz=None,
                 verbose=True):

        self.oh_per_ta = int(oh_per_ta)
        assert self.oh_per_ta > 0

        self.max_ta_per_oh = max_ta_per_oh
        if self.max_ta_per_oh is not None:
            self.max_ta_per_oh = int(max_ta_per_oh)
            assert self.max_ta_per_oh > 0

        self.scale_dict = scale_dict
        if self.scale_dict is not None:
            self.scale_dict = {str(k): float(v) for k, v in scale_dict.items()}

        today = datetime.today()
        if date_start is None:
            date_start = today.strftime('%b %d %Y')
        self.date_start = str(date_start)

        if date_end is None:
            datetime_start = pd.to_datetime(self.date_start)
            date_end = datetime_start + timedelta(days=6)
            date_end = date_end.strftime('%b %d %Y')
        self.date_end = str(date_end)

        self.f_out = f_out
        if self.f_out is not None:
            self.f_out = pathlib.Path(self.f_out)
            assert self.f_out.parent.exists()

        self.tz = tz
        if self.tz is None:
            self.tz = 'US/Eastern'
        else:
            if self.tz not in pytz.all_timezones:
                raise AttributeError(f'timezone not found in IANA database')

        self.verbose = bool(verbose)

    @classmethod
    def from_yaml(cls, f_yaml):
        with open(str(f_yaml), 'r') as f:
            config = yaml.safe_load(f)
        return Config(**config)

    def to_yaml(self, f_yaml):
        with open(str(f_yaml), 'w') as f:
            yaml.dump(self.to_dict(), f)

    def to_dict(self):
        d = copy(self.__dict__)
        if d['f_out'] is not None:
            d['f_out'] = str(d['f_out'])
        return d

    def __eq__(self, other):
        return self.__dict__ == other.__dict__
