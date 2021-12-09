from functools import lru_cache
import ipaddress

import geoip2.database

import uvicorn
from starlette.applications import Starlette
from starlette.responses import Response

app = Starlette()
app.state.geoip = geoip2.database.Reader('/db/GeoLite2-City.mmdb')


@lru_cache(max_size=1024)
def _is_allowed(ip, ip_allowlist, location_allowlist):
    return (
        _in_ip_allowlist(ip, ip_allowlist)
        or
        _is_allowed_area(ip, location_allowlist)
    )


def _in_ip_allowlist(ip, ip_allowlist):
    if not ip_allowlist:
        return False

    ip = ipaddress.ip_address(ip)
    for allowed_ip in ip_allowlist:
        if ip in ipaddress.ip_network(allowed_ip):
            return True

    return False


def _is_allowed_area(ip, location_allowlist):
    countries = location_allowlist.split(";")

    try:
        match = app.state.geoip.city(ip)
    except geoip2.errors.AddressNotFoundError:
        print(f"[DENY] {ip}: UNKNOWN REGION")
        return False

    iso_country = match.country.iso_code
    iso_subdiv = match.subdivisions.most_specific.iso_code

    for entry in countries:
        if ":" in entry:
            country, areas = entry.split(":", 1)
        else:
            country = entry
            areas = None

        if iso_country == country:
            if areas is None:
                print(f"[ALLOW] {ip}: {iso_country} ({iso_subdiv})")
                return True
            else:
                for area in areas.split(","):
                    if iso_subdiv == area:
                        print(f"[ALLOW] {ip}: {iso_country} ({iso_subdiv})")
                        return True
                print(f"[DENY] {ip}: {iso_country} ({iso_subdiv})")
                return False

    print(f"[DENY] {ip}: {iso_country} ({iso_subdiv})")
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
    return Response('OK')


@app.route('/clear_cache')
async def clear_cache(request):
    _is_allowed.cache_clear()

if __name__ == "__main__":
    uvicorn.run(app, host='0.0.0.0', port=8000, proxy_headers=True, forwarded_allow_ips="*")
