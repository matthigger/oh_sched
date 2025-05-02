import datetime
import pathlib
import re
import warnings
from copy import copy
from datetime import datetime, timedelta

import pytz
import yaml

import oh_sched.calendr

OH_ALL = 'ALL'
OH_LEFTOVER = 'LEFTOVER'


class Config:
    def __init__(self, oh_per_ta=1, max_ta_per_oh=None, scale_dict=None,
                 date_start=None, date_end=None, f_out=None, tz=None,
                 f_out_dict=None,
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
            date_start = today.strftime("%b %d %Y")
        self.date_start = str(date_start)

        if date_end is None:
            date_end = (today + timedelta(weeks=1)).strftime(
                "%b %d %Y")
        self.date_end = str(date_end)

        assert (f_out is None) or (f_out_dict is None), \
            'cannot pass both f_out and f_out_dict'

        if f_out is None:
            f_out = 'oh.ics'
        if f_out_dict is None:
            f_out_dict = {f_out: OH_ALL}
        self.f_out_dict = {pathlib.Path(f_out): v
                           for f_out, v in f_out_dict.items()}
        for f_out in self.f_out_dict.keys():
            assert f_out.parent.exists()

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

    def to_ics(self, oh_ta_dict, verbose=True):
        """ writes schedule to ics files

        Args:
            oh_ta_dict (dict): keys are office hour slots (str), values are
                list of str, names of TAs assigned to this slot

        Returns:
            f_dict (dict): keys are file names (from self.f_out_dict.keys()),
                values are oh_ta_dict (of form above) which are relevant for
                corresponding file
        """
        # build f_dict, whose keys are output files and whose strings are the
        # corresponding oh_ta_dict to be written in each
        oh_leftover = set(oh_ta_dict.keys())
        f_leftover = list()
        f_dict = dict()
        for f_out, s_regex in self.f_out_dict.items():
            if s_regex == OH_ALL:
                # all office hours slots in this output
                _oh_ta_dict = oh_ta_dict
                oh_leftover = set()
            elif s_regex == OH_LEFTOVER:
                # leftover office hours slots in this output (handle later)
                f_leftover.append(f_out)
                continue
            else:
                # search for s_regex, include only oh slots which match
                regex = re.compile(s_regex)
                _oh_ta_dict = dict()
                for oh, ta_list in oh_ta_dict.items():
                    if regex.search(oh):
                        # add this office hours to this calendar
                        _oh_ta_dict[oh] = ta_list
                        # remove from leftover
                        oh_leftover.discard(oh)

            f_dict[f_out] = _oh_ta_dict

        # add leftover oh to their corresponding files
        if oh_leftover:
            _oh_ta_dict = {oh: oh_ta_dict[oh] for oh in oh_leftover}
            for f_out in f_leftover:
                f_dict[f_out] = _oh_ta_dict
            if not f_leftover:
                s = sorted(oh_leftover)
                warnings.warn(f'OH not written to any ics outputs: {s}')

        # write ics files
        for f_out, _oh_ta_dict in f_dict.items():
            cal = oh_sched.calendr.build_calendar(_oh_ta_dict,
                                                  date_start=self.date_start,
                                                  date_end=self.date_end,
                                                  tz=self.tz)

            with open(f_out, 'wb') as f:
                f.write(cal.to_ical())

            if verbose:
                print(f'writing calendar file: {f_out}\n')

        return f_dict


if __name__ == '__main__':
    import oh_sched

    # dump default config to test directory
    folder = pathlib.Path(oh_sched.__file__).parents[1] / 'test'
    config = Config()
    config.to_yaml(folder / 'config.yaml')
