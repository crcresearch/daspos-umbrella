# Copyright (C) 2015-2016, University of Notre Dame
# All rights reserved


class SmartDict(dict):
    def __init__(self, dictionary, default=None, blank=""):
        super(SmartDict, self).__init__(dictionary)
        self.default = default
        self.blank = blank

    def __getitem__(self, key):
        value = self.get(key, self.default)

        if value == self.blank:
            value = self.default

        return value

    def __call__(self, *args, **kwargs):
        default = kwargs.get("default", None)
        blank = kwargs.get("blank", "")

        for item in args:
            value = self.get(item, None)
            if value is not None:
                if value != blank:
                    return value
                else:
                    return default

        return default