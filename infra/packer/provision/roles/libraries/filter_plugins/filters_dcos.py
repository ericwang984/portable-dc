import base64
import hashlib
import json

from ansible import errors
from ansible.module_utils.six import text_type

# import boolean converter
try:
    from ansible.module_utils.parsing.convert_bool import boolean
except ImportError:
    from ansible import constants as C

    boolean = C.mk_boolean


def get_network(a, tenant):
    """
    Given a dictionary of tenants, look up the 'network' subkey
    under the given 'tenant' key. Otherwise, use the name of the tenant.
    """
    if not isinstance(a, dict):
        raise errors.AnsibleFilterError('get_network({}): filter operand "{}" is not a dict'.format(tenant, a))

    try:
        network = a[tenant].get('network', tenant)
    except KeyError as e:
        # Return the name of the tenant if it's missing in the dictionary
        return tenant
    except AttributeError as e:
        raise errors.AnsibleFilterError('get_network({}): {}'.format(tenant, e))

    return network


def get_enclave(tenant):
    """
    Given a tenant name, return the name of the tenant's enclave network name.
    """
    if not isinstance(tenant, text_type):
        raise errors.AnsibleFilterError('get_enclave({}): filter operand "{}" is not a string'.format(tenant, tenant))

    return tenant + '-enc'


def get_vpn_password(a, tenant):
    """
    Given a dictionary of tenants, look up the 'vpn.password' subkey
    under the given 'tenant' key.
    """
    if not isinstance(a, dict):
        raise errors.AnsibleFilterError('get_vpn_password({}): filter operand "{}" is not a dict'.format(tenant, a))

    try:
        pw = a[tenant]['vpn']['password']
    except KeyError as e:
        raise errors.AnsibleFilterError('get_vpn_password({}): error looking up key {}'.format(tenant, e))

    return pw


def get_vpn_port(a, tenant):
    """
    Given a dictionary of tenants, look up the 'vpn.port' subkey
    under the given 'tenant' key.
    """
    if not isinstance(a, dict):
        raise errors.AnsibleFilterError('get_vpn_port({}): filter operand "{}" is not a dict'.format(tenant, a))

    try:
        port = int(a[tenant]['vpn']['port'])

    except KeyError as e:
        raise errors.AnsibleFilterError('get_vpn_port({}): error looking up key {}'.format(tenant, e))
    except ValueError as e:
        raise errors.AnsibleFilterError('get_vpn_port({}): port is not an int - {}'.format(tenant, e))

    return port


def marathon_url(a, url_base='.marathon.mesos'):
    """
    Converts an app name into a valid Marathon URL.
    """

    if isinstance(a, list):
        p = a
    else:
        p = a.split('/')

    # Filter empty items from list (caused by duplicate slashes)
    l = list(filter(None, reversed(p)))

    return ".".join(l) + url_base


def vrack_id(a, vracks=5):
    """
    Determine a virtual 'rack ID' based on the hostname of the machine.
    Attempts to extract integers from a dash-separated (-) hostname, eg.
    iot-private-slave-3. In case the string contains multiple integers,
    the last one is used.

    The vrack_id is calculated by performing a modulo operation on the
    base integer. The amount of vracks can be altered using the 'vracks'
    kwarg.

    In case the base integer (by splitting the string) cannot be derived,
    the SHA2 hash of the hostname is used as the base for the modulo.
    This may lead to an uneven distribution in some circumstances.
    """

    # Extract all integers from the base string
    n = [int(s) for s in a.split('-') if s.isdigit()]

    # Return the last integer mod the amount of vracks
    if n:
        return int(n[-1] % vracks)

    # Base integer(s) could not be derived, fall back to SHA2
    h = hashlib.sha256(a).hexdigest()
    return int(int(h, 16) % vracks)


def image_metadata(a):
    """
    Generate DC/OS Universe Metadata from an image URL.
    Only icon-small is used by the UI; icon-medium and icon-large need to be
    present for validation purposes. Otherwise, the icon will not display.

    :return: base64-encoded JSON for DC/OS metadata
    :rtype: str
    """

    md = {'images': {'icon-small': a, 'icon-medium': '_', 'icon-large': '_'}}

    # sort keys to get deterministic results across py2/py3
    jd = json.dumps(md, sort_keys=True)

    # py3 accepts and returns bytes from b64encode
    # all base64 input and payload should fit in ascii
    return base64.b64encode(jd.encode('ascii')).decode('ascii')


class FilterModule(object):
    """
    DC/OS-related filters
    """

    def filters(self):
        filters = {
            # tenant-related operations
            'get_network': get_network,
            'get_enclave': get_enclave,
            'get_vpn_password': get_vpn_password,
            'get_vpn_port': get_vpn_port,
            'marathon_url': marathon_url,

            # infrastructure helpers
            'vrack_id': vrack_id,

            # misc
            'image_metadata': image_metadata,
        }

        return filters
