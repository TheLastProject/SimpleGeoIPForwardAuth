#!/bin/sh

download_db() {
    echo "Downloading GeoLite2-City.mmdb"
    curl "https://download.maxmind.com/app/geoip_download?edition_id=GeoLite2-City&license_key=${SIMPLE_GEOIP_FORWARDAUTH_MAXMIND_LICENSE_KEY}&suffix=tar.gz" | tar -C /db/ --wildcards --strip-components 1 -xzvf - '*/GeoLite2-City.mmdb'
}

if [ ! -f "/db/GeoLite2-City.mmdb" ]; then
    echo "GeoLite2-City.mmdb not found in /db/. Downloading..."
    if [ -z "${SIMPLE_GEOIP_FORWARDAUTH_MAXMIND_LICENSE_KEY}" ]; then
        echo "SIMPLE_GEOIP_FORWARDAUTH_MAXMIND_LICENSE_KEY is not defined! Cannot download database!"
        exit 1
    fi

    download_db
fi

flask run --host=0.0.0.0
