#!/bin/sh

DB=/db/GeoLite2-City.mmdb

update_db_if_needed() {
# $1 = clear cache
if [ ! -f "$DB" ]; then
    echo "${DB} not found. Downloading..."

    download_db
elif [ $(( $(date +%s) - $(stat -c '%Y' ${DB}) )) -gt 604800 ]; then
    echo "${DB} is older than a week. Downloading update..."

    download_db

    if [ "$1" -eq 1 ]; then
        curl http://localhost:8000/clear_cache
    fi
else
    echo "${DB} is up-to-date"
fi
}

download_db() {
    if [ -z "${SIMPLE_GEOIP_FORWARDAUTH_MAXMIND_LICENSE_KEY}" ]; then
        echo "SIMPLE_GEOIP_FORWARDAUTH_MAXMIND_LICENSE_KEY is not defined! Cannot download database!"
        return
    fi

    echo "Downloading GeoLite2-City.mmdb"
    curl "https://download.maxmind.com/app/geoip_download?edition_id=GeoLite2-City&license_key=${SIMPLE_GEOIP_FORWARDAUTH_MAXMIND_LICENSE_KEY}&suffix=tar.gz" | tar -C /db/ --wildcards --strip-components 1 -xzvf - '*/GeoLite2-City.mmdb'
}

update_db_if_needed 0

python3 app.py &

while true; do
    sleep 86400
    update_db_if_needed 1
done
