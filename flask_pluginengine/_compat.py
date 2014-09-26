# This file is part of Flask-PluginEngine.
# Copyright (C) 2014 CERN
#
# Flask-PluginEngine is free software; you can redistribute it
# and/or modify it under the terms of the Revised BSD License.

import sys

if sys.version_info[0] > 2:
    def iteritems(arg, **kwargs):
        return iter(arg.items(**kwargs))
else:
    def iteritems(arg, **kwargs):
        return iter(arg.iteritems(**kwargs))
