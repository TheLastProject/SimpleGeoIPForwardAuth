import sys

import geoip2.database

with geoip2.database.Reader(sys.argv[1]) as db:
    db.city('8.8.8.8')
