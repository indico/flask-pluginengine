# This file is part of Flask-PluginEngine.
# Copyright (C) 2014-2017 CERN
#
# Flask-PluginEngine is free software; you can redistribute it
# and/or modify it under the terms of the Revised BSD License.

import sys

if sys.version_info[0] > 2:
    string_types = (str,)

    def iteritems(arg, **kwargs):
        return iter(arg.items(**kwargs))
else:
    string_types = (basestring,)

    def iteritems(arg, **kwargs):
        return iter(arg.iteritems(**kwargs))
