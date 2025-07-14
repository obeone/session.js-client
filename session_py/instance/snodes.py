# -*- coding: utf-8 -*-

"""
This module handles the retrieval of service nodes (snodes) for the Session network.
"""

import logging
from typing import TYPE_CHECKING, List
from session_py.network.base import Request
from session_py.network.request import RequestType
from session_py.types.snode import Snode

if TYPE_CHECKING:
    from session_py.instance.session import Session

logger = logging.getLogger(__name__)

async def get_snodes(self: 'Session') -> List[Snode]:
    """
    Retrieves the list of service nodes (snodes) from the network using the JSON-RPC bootstrap mechanism.

    This method first checks if the snode list is already cached. If so, it
    returns the cached list. Otherwise, it calls get_snodes_rpc to fetch
    the list of snodes from the seed nodes, caches the result, and then returns it.
    """
    logger.debug("get_snodes called")
    if self.snodes is None:
        logger.info("Snode list not cached, fetching from network...")
        self.snodes = await get_snodes_rpc(self)
    else:
        logger.debug("Returning cached snode list.")
    return self.snodes if self.snodes is not None else []
# --- Bootstrap seeds for Session network (adapted from bun-network) ---
SEED1_CERT = """-----BEGIN CERTIFICATE-----
MIIEDTCCAvWgAwIBAgIUWk96HLAovn4uFSI057KhnMxqosowDQYJKoZIhvcNAQEL
BQAwejELMAkGA1UEBhMCQVUxETAPBgNVBAgMCFZpY3RvcmlhMRIwEAYDVQQHDAlN
ZWxib3VybmUxJTAjBgNVBAoMHE94ZW4gUHJpdmFjeSBUZWNoIEZvdW5kYXRpb24x
HTAbBgNVBAMMFHNlZWQxLmdldHNlc3Npb24ub3JnMB4XDTIzMDQwNTAxMjQzNVoX
DTMzMDQwNTAxMjQzNVowejELMAkGA1UEBhMCQVUxETAPBgNVBAgMCFZpY3Rvcmlh
MRIwEAYDVQQHDAlNZWxib3VybmUxJTAjBgNVBAoMHE94ZW4gUHJpdmFjeSBUZWNo
IEZvdW5kYXRpb24xHTAbBgNVBAMMFHNlZWQxLmdldHNlc3Npb24ub3JnMIIBIjAN
BgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA2wlGkR2aDOHoizik4mqvWEwDPOQG
o/Afd/6VqKzo4BpNerVZQNgdMgdLTedZE4FRfetubonYu6iSYALK2iKoGsIlru1u
Q9dUl0abA9v+yg6duh1aHw8oS16JPL0zdq8QevJaTxd0MeDnx4eXfFjtv8L0xO4r
CRFH+H6ATcJy+zhVBcWLjiNPe6mGSHM4trx3hwJY6OuuWX5FkO0tMqj9aKJtJ+l0
NArra0BZ9MaMwAFE7AxWwyD0jWIcSvwK06eap+6jBcZIr+cr7fPO5mAlT+CoGB68
yUFwh1wglcVdNPoa1mbFQssCsCRa3MWgpzbMq+KregVzjVEtilwLFjx7FQIDAQAB
o4GKMIGHMB0GA1UdDgQWBBQ1XAjGKhyIU22mYdUEIlzlktogNzAfBgNVHSMEGDAW
gBQ1XAjGKhyIU22mYdUEIlzlktogNzAPBgNVHRMBAf8EBTADAQH/MB8GA1UdEQQY
MBaCFHNlZWQxLmdldHNlc3Npb24ub3JnMBMGA1UdJQQMMAoGCCsGAQUFBwMBMA0G
CSqGSIb3DQEBCwUAA4IBAQC4PRiu4LyxK71Gk+f3dDvjinuE9F0XtAamKfRlLMEo
KxK8dtLrT8p62rME7QiigSv15AmSNyqAp751N/j0th1prOnxBoG38BXKLBDDClri
u91MR4h034G6LIYCiM99ldc8Q5a5WCKu9/9z6CtVxZcNlfe477d6lKHSwb3mQ581
1Ui3RnpkkU1n4XULI+TW2n/Hb8gN6IyTHFB9y2jb4kdg7N7PZIN8FS3n3XGiup9r
b/Rujkuy7rFW78Q1BuHWrQPbJ3RU2CKh1j5o6mtcJFRqP1PfqWmbuaomam48s5hU
4JEiR9tyxP+ewl/bToFcet+5Lp9wRLxn0afm/3V00WyP
-----END CERTIFICATE-----
"""

SEED2_CERT = """-----BEGIN CERTIFICATE-----
MIIEDTCCAvWgAwIBAgIUXkVaUNO/G727mNeaiso9MjvBEm4wDQYJKoZIhvcNAQEL
BQAwejELMAkGA1UEBhMCQVUxETAPBgNVBAgMCFZpY3RvcmlhMRIwEAYDVQQHDAlN
ZWxib3VybmUxJTAjBgNVBAoMHE94ZW4gUHJpdmFjeSBUZWNoIEZvdW5kYXRpb24x
HTAbBgNVBAMMFHNlZWQyLmdldHNlc3Npb24ub3JnMB4XDTIzMDQwNTAxMjI0MloX
DTMzMDQwNTAxMjI0MlowejELMAkGA1UEBhMCQVUxETAPBgNVBAgMCFZpY3Rvcmlh
MRIwEAYDVQQHDAlNZWxib3VybmUxJTAjBgNVBAoMHE94ZW4gUHJpdmFjeSBUZWNo
IEZvdW5kYXRpb24xHTAbBgNVBAMMFHNlZWQyLmdldHNlc3Npb24ub3JnMIIBIjAN
BgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAvT493tt1EWdyIa++X59ffrQt+ghK
+3Hv/guCPmR0FxPUeVnayoLbeKgbe8dduThh7nlmlYnpwbulvDnMF/rRpX51AZiT
A8UGktBzGXi17/D/X71EXGqlM41QZfVm5MCdQcghvbwO8MP0nWmbV4DdiNYAwSNh
fpGMEiblCvKtGN71clTkOW+8Moq4eOxT9tKIlOv97uvkUS21NgmSzsj453hrb6oj
XR3rtW264zn99+Gv83rDE1jk0qfDjxCkaUb0BvRDREc+1q3p8GZ6euEFBM3AcXe7
Yl0qbJgIXd5I+W5nMJJCyJHPTxQNvS+uJqL4kLvdwQRFAkwEM+t9GCH1PQIDAQAB
o4GKMIGHMB0GA1UdDgQWBBQOdqxllTHj+fmGjmdgIXBl+k0PRDAfBgNVHSMEGDAW
gBQOdqxllTHj+fmGjmdgIXBl+k0PRDAPBgNVHRMBAf8EBTADAQH/MB8GA1UdEQQY
MBaCFHNlZWQyLmdldHNlc3Npb24ub3JnMBMGA1UdJQQMMAoGCCsGAQUFBwMBMA0G
CSqGSIb3DQEBCwUAA4IBAQBkmmX+mopdnhzQC5b5rgbU7wVhlDaG7eJCRgUvqkYm
Pbv6XFfvtshykhw2BjSyQetofJaBh5KOR7g0MGRSn3AqRPBeEpXfkBI9urhqFwBF
F5atmp1rTCeHuAS6w4mL6rmj7wHl2CRSom7czRdUCNM+Tu1iK6xOrtOLwQ1H1ps1
KK3siJb3W0eKykHnheQPn77RulVBNLz1yedEUTVkkuVhzSUj5yc8tiwrcagwWX6m
BlfVCJgsBbrJ754rg0AJ0k59wriRamimcUIBvKIo3g3UhJHDI8bt4+SvsRYkSmbi
rzVthAlJjSlRA28X/OLnknWcgEdkGhu0F1tkBtVjIQXd
-----END CERTIFICATE-----
"""

SEED3_CERT = """-----BEGIN CERTIFICATE-----
MIIEDTCCAvWgAwIBAgIUTz5rHKUe+VA9IM6vY6QACc0ORFkwDQYJKoZIhvcNAQEL
BQAwejELMAkGA1UEBhMCQVUxETAPBgNVBAgMCFZpY3RvcmlhMRIwEAYDVQQHDAlN
ZWxib3VybmUxJTAjBgNVBAoMHE94ZW4gUHJpdmFjeSBUZWNoIEZvdW5kYXRpb24x
HTAbBgNVBAMMFHNlZWQzLmdldHNlc3Npb24ub3JnMB4XDTIzMDQwNTAxMjYzMVoX
DTMzMDQwNTAxMjYzMVowejELMAkGA1UEBhMCQVUxETAPBgNVBAgMCFZpY3Rvcmlh
MRIwEAYDVQQHDAlNZWxib3VybmUxJTAjBgNVBAoMHE94ZW4gUHJpdmFjeSBUZWNo
IEZvdW5kYXRpb24xHTAbBgNVBAMMFHNlZWQzLmdldHNlc3Npb24ub3JnMIIBIjAN
BgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA6FgxIk9KmYISL5fk7BLaGAW6lBx8
b4VL3DjlyrFMz7ZhSbcUcavWyyYB+iJxBRhfQGJ7vbwJZ1AwVJisjDFdiLcWzTF8
gzZ7LVXH8qlVnqcx0gksrWYFnG3Y2WJrxEBFdD29lP7LVN3xLQdplMitOciqg5jN
oRjtwGo+wzaMW6WNPzgTvxLzPce9Rl3oN4tSK7qlA9VtsyHwOWBMcogv9LC9IUFZ
2yu0RdcxPdlwLwywYtSRt/W87KbAWTcYY1DfN2VA68p9Cip7/dPOokRduMh1peux
swmIybpC/wz/Ql6J6scSOjDUp/2UsIdYIvyP/Dibi4nHRmD+oz9kb+J3AQIDAQAB
o4GKMIGHMB0GA1UdDgQWBBSQAFetDPIzVg9rfgOI7bfaeEHd8TAfBgNVHSMEGDAW
gBSQAFetDPIzVg9rfgOI7bfaeEHd8TAPBgNVHRMBAf8EBTADAQH/MB8GA1UdEQQY
MBaCFHNlZWQzLmdldHNlc3Npb24ub3JnMBMGA1UdJQQMMAoGCCsGAQUFBwMBMA0G
CSqGSIb3DQEBCwUAA4IBAQCiBNdbKNSHyCZJKvC/V+pHy9E/igwvih2GQ5bNZJFA
daOiKBgaADxaxB4lhtzasr2LdgZdLrn0oONw+wYaui9Z12Yfdr9oWuOgktn8HKLY
oKkJc5EcMYFsd00FnnFcO2U8lQoL6PB/tdcEmpOfqtvShpNhp8SbadSNiqlttvtV
1dqvqSBiRdQm1kz2b8hA6GR6SPzSKlSuwI0J+ZcXEi232EJFbgJ3ESHFVHrhUZro
8A16/WDvZOMWCjOqJsFBw15WzosW9kyNwBtZinXVO3LW/7tVl08PDcarpH4IWjd0
LDpU7zGjcD/A19tfdfMFTOmETuq40I8xxtlR2NENFOAL
-----END CERTIFICATE-----
"""

SEEDS = [
    {
        "url": "seed1.getsession.org",
        "pubkey256": "mlYTXvkmIEYcpswANTpnBwlz9Cswi0py/RQKkbdQOZQ=",
        "cert256": "36:EA:0B:25:35:37:98:85:51:EE:85:6E:4F:D2:0D:55:01:1E:9C:8B:27:EA:A2:F3:4B:8F:32:A0:BD:F0:4F:2D",
        "cert_content": SEED1_CERT,
    },
    {
        "url": "seed2.getsession.org",
        "pubkey256": "ZuUxe4wopBR83Yy5fePPNX0c00BnkQCu/49oapFpB0k=",
        "cert256": "C5:90:8D:D4:13:9A:CD:96:AE:DD:1E:45:57:65:97:65:08:09:C8:A5:EA:02:AF:55:6D:48:53:D4:53:96:E0:E7",
        "cert_content": SEED2_CERT,
    },
    {
        "url": "seed3.getsession.org",
        "pubkey256": "4xe+8k1NjxerVTjUsWlZJNKt3PA7Y31pUls2tHYippA=",
        "cert256": "8A:0A:F2:C7:12:34:2F:22:CE:00:E5:3C:16:01:41:0E:F8:D8:41:56:AE:E0:A9:80:9C:32:F6:F7:EF:BE:55:6E",
        "cert_content": SEED3_CERT,
    },
]

import aiohttp
import json

from session_py.errors import SessionFetchError, SessionFetchErrorCode

async def get_snodes_rpc(self: 'Session') -> List[Snode]:
    """
    Retrieves the list of service nodes (snodes) using a JSON-RPC call to the /json_rpc endpoint of each bootstrap seed node.

    The function implements a sequential fallback mechanism: it iterates through all statically configured seed nodes
    (seed1.getsession.org, seed2.getsession.org, seed3.getsession.org) on port 80 (HTTP standard, no explicit port in URL).
    Each seed is expected to have an embedded X.509 certificate and public keys for security. For each seed, it sends a JSON-RPC 2.0 POST request
    with the method 'get_n_service_nodes', requesting the fields: public_ip, storage_port, pubkey_x25519, pubkey_ed25519.

    Only snodes with a valid public_ip (not '0.0.0.0') are returned. If all seeds fail to respond or return invalid data,
    a SessionFetchError is raised.

    :return: A list of Snode objects.
    :raises SessionFetchError: If all seeds fail to respond or return invalid data.

    Example:
        snodes = await session.get_snodes_rpc()
    """
    logger.info("Attempting to fetch snodes from JSON-RPC endpoints...")
    for seed in SEEDS:
        url = f"http://{seed['url']}/json_rpc"  # Port 80 implicit, as in bun-network
        logger.debug(f"Trying seed: {url}")
        # cert_content, pubkey256, cert256 are available in seed for future use (e.g. HTTPS, verification)
        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    "User-Agent": "WhatsApp",
                    "Accept": "*/*",
                    "Connection": "close",
                    "Content-Type": "application/json"
                }
                body = {
                    "jsonrpc": "2.0",
                    "id": 0,
                    "method": "get_n_service_nodes",
                    "params": {
                        "fields": {
                            "public_ip": True,
                            "storage_port": True,
                            "pubkey_x25519": True,
                            "pubkey_ed25519": True
                        }
                    }
                }

                async def body_generator(json_body):
                    yield json.dumps(json_body).encode('utf-8')

                proxy = getattr(self.network, 'proxy', None)
                async with session.post(url, data=body_generator(body), headers=headers, timeout=10, proxy=proxy, ssl=False) as resp:
                    if resp.status != 200:
                        logger.warning(f"Request to {url} failed with status {resp.status}")
                        continue
                    data = await resp.json()
                    snodes_raw = data.get("result", {}).get("service_node_states", [])
                    snodes = [
                        Snode(
                            host=snode["public_ip"],
                            port=int(snode["storage_port"]),
                            pubkey_x25519=snode["pubkey_x25519"],
                            pubkey_ed25519=snode["pubkey_ed25519"]
                        )
                        for snode in snodes_raw
                        if snode.get("public_ip") and snode["public_ip"] != "0.0.0.0"
                    ]
                    if snodes:
                        logger.info(f"Successfully fetched {len(snodes)} snodes from {url}")
                        self.snodes = snodes
                        return snodes
                    else:
                        logger.warning(f"No valid snodes found from {url}")
        except Exception as e:
            logger.warning(f"Failed to fetch snodes from {url}: {e}", exc_info=True)
            continue
    logger.error("Failed to fetch snodes from all seeds. Raising SessionFetchError.")
    raise SessionFetchError(
        code=SessionFetchErrorCode.SNODE_ERROR,
        message="Failed to fetch snodes from all seeds using JSON-RPC."
    )
