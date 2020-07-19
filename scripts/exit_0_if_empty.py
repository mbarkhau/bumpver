#!/usr/bin/env python
# if you know a bash one liner for this, be my guest
import sys

data     = open(sys.argv[1]).read(10)
has_data = len(data) > 0

sys.exit(has_data)
