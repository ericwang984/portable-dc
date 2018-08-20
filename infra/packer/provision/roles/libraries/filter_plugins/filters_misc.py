import math

from ansible import errors
from ansible.module_utils.six import string_types
from ansible.parsing.yaml.objects import AnsibleVaultEncryptedUnicode
from jinja2.runtime import Undefined

# import boolean converter
try:
    from ansible.module_utils.parsing.convert_bool import boolean
except ImportError:
    from ansible import constants as C

    boolean = C.mk_boolean


def append_if_exists(a, astr):
    """
    Return the input string with the argument appended.
    Return empty string if the input string is undefined/falsey.
    """

    if isinstance(a, Undefined) or not a:
        return ''
    else:
        return str(a) + str(astr)


def default_if_true(a, dval, enabled):
    """
    Return the default value if the input string is undefined/falsey and `enabled` is true.
    `enabled` can be an undefined variable, in which case it defaults to 'false'.
    Otherwise, return the input string.
    """

    if isinstance(enabled, Undefined):
        enabled = False

    if isinstance(a, Undefined) or not a:
        # input string is Undefined or falsey
        if boolean(enabled):
            return dval
        else:
            raise errors.AnsibleFilterError('default_if_true: enabled flag is `false` for value')
    else:
        # input string is valid, no default needed
        return a


def escape_newlines(a):
    """
    Return the original value with carriage returns and new lines escaped
    """

    # workaround for Ansible #24425
    if isinstance(a, AnsibleVaultEncryptedUnicode):
        a = str(a)

    if not isinstance(a, string_types):
        raise errors.AnsibleFilterError('escape_newlines: can only operate on text (got {})'.format(type(a)))

    # input string is valid, no default needed
    return a.replace("\r", "\\r").replace("\n", "\\n").strip()


def literal_newlines(a):
    """
    Return the original value with carriage returns and new lines expanded
    to literal control characters.
    """

    # workaround for Ansible #24425
    if isinstance(a, AnsibleVaultEncryptedUnicode):
        a = str(a)

    if not isinstance(a, string_types):
        raise errors.AnsibleFilterError('literal_newlines: can only operate on text (got {})'.format(type(a)))

    # input string is valid, no default needed
    return a.replace("\\r", "\r").replace("\\n", "\n").strip()


def split(a, char, index=None):
    """
    Split a string on every occurence of 'char',
    return the `index`th element from the list if index is given.
    Strips empty items from the list.
    """

    if isinstance(a, Undefined):
        raise errors.AnsibleFilterError('split: input variable is undefined')

    if not (isinstance(a, string_types) or isinstance(a, str)):
        raise errors.AnsibleFilterError('split: cannot split type {}'.format(type(a)))

    al = a.split(char)

    # Remove empty items from the list
    al = list(filter(None, al))

    if index is not None:
        try:
            return al[index]
        except IndexError as e:
            raise errors.AnsibleFilterError('split: element {} not found in list - {}'.format(index, e))

    return al


def select_keys(a, wanted):
    """
    Filter a dictionary's keys according to a list of wanted keys.
    Returns the input value if 'wanted' is Undefined.
    """

    if not isinstance(a, dict):
        raise errors.AnsibleFilterError('select_keys: filter operand `{}` is not a dict'.format(a))

    if isinstance(wanted, Undefined):
        return a

    if not isinstance(wanted, list):
        raise errors.AnsibleFilterError('select_keys: filter argument `{}` is not a list'.format(wanted))

    return dict((k, a[k]) for k in wanted if k in a)


def connection_string(a, schema=None, port=None, delim=','):
    """
    Generates a 'delim'-separated connection string
    from a list of addresses, a schema and a port number.
    """

    out = []

    for addr in a:
        s, p = '', ''

        if schema is not None:
            s = str(schema) + '://'

        if port is not None:
            p = ':' + str(port)

        out.append(s + addr + p)

    return delim.join(out)


def quorum(a):
    """
    Return a minimum quorum threshold by calculating argument / 2 + 1.
    """
    if not isinstance(a, int) or (a % 2 == 0):
        raise errors.AnsibleFilterError('quorum: filter argument `{}` is not an odd integer'.format(a))

    return int(math.floor(a / 2) + 1)


class FilterModule(object):
    """ Miscellaneous Filters """

    def filters(self):
        filters = {
            # strings
            'append_if_exists': append_if_exists,
            'split': split,

            # general variable manipulation
            'default_if_true': default_if_true,
            'escape_newlines': escape_newlines,
            'literal_newlines': literal_newlines,

            # dict operations
            'select_keys': select_keys,

            # generation / concatenation
            'connection_string': connection_string,

            # math
            'quorum': quorum
        }

        return filters
