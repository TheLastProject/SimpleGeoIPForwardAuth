from functools import lru_cache
import ipaddress
import random

import geoip2.database

import uvicorn
from starlette.applications import Starlette
from starlette.responses import Response

app = Starlette()
app.state.geoip = geoip2.database.Reader('/db/GeoLite2-City.mmdb')


@lru_cache(maxsize=1024)
def _is_allowed(ip, ip_allowlist, location_allowlist, log=True):
    return (
        _in_ip_allowlist(ip, ip_allowlist.split(",") if ip_allowlist else [])
        or
        _is_allowed_area(ip, location_allowlist.split(";") if location_allowlist else [], log)
    )


def _in_ip_allowlist(ip, ip_allowlist):
    if not ip_allowlist:
        return False

    ip = ipaddress.ip_address(ip)
    for allowed_ip in ip_allowlist:
        if ip in ipaddress.ip_network(allowed_ip):
            return True

    return False


def _is_allowed_area(ip, location_allowlist, log):
    try:
        match = app.state.geoip.city(ip)
    except geoip2.errors.AddressNotFoundError:
        if log: print(f"[DENY] {ip}: UNKNOWN REGION")
        return False

    iso_country = match.country.iso_code
    iso_subdiv = match.subdivisions.most_specific.iso_code or "UNK"

    for entry in location_allowlist:
        if ":" in entry:
            country, areas = entry.split(":", 1)
        else:
            country = entry
            areas = None

        if iso_country == country:
            if areas is None:
                if log: print(f"[ALLOW] {ip}: {iso_country} ({iso_subdiv})")
                return True
            else:
                if iso_subdiv in areas.split(","):
                    if log: print(f"[ALLOW] {ip}: {iso_country} ({iso_subdiv})")
                    return True

                if log: print(f"[DENY] {ip}: {iso_country} ({iso_subdiv})")
                return False

    if log: print(f"[DENY] {ip}: {iso_country} ({iso_subdiv})")
    return False


@app.route('/')
async def check_ip(request):
    location_allowlist = request.query_params.get('locations', default='')
    ip_allowlist = request.query_params.get('ips', default='')

    if _is_allowed(request.client.host, ip_allowlist, location_allowlist):
        return Response('OK')

    return Response('FORBIDDEN', status_code=403)


@app.route('/health')
async def health(request):
    # As a health check we
    # 1. Generate a random IPv4 and IPv6
    # 2. Ensure they're blocked if we deny everything
    # 3. Ensure they're allowed if we allow the IP
    # If even this very basic checking doesn't work, something is clearly wrong

    ips = [
      ipaddress.IPv4Address._string_from_ip_int(random.randint(0, ipaddress.IPv4Address._ALL_ONES)),
      ipaddress.IPv6Address._string_from_ip_int(random.randint(0, ipaddress.IPv6Address._ALL_ONES))
    ]

    for ip in ips:
        if _is_allowed(ip, '', '', False):
            return Response(f"Container allowed {ip} when blocking all", status_code=500)

        if not _is_allowed(ip, ip, '', False):
            return Response(f"Container blocked {ip} despite it being on allowlist", status_code=500)

    return Response('OK')


@app.route('/clear_cache')
async def clear_cache(request):
    _is_allowed.cache_clear()

    return Response('OK')

if __name__ == "__main__":
    uvicorn.run(app, host='0.0.0.0', port=8000, proxy_headers=True, forwarded_allow_ips="*")
