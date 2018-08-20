from ansible.errors import AnsibleFilterError
from ansible.module_utils.parsing.convert_bool import boolean
from ansible.module_utils.six import iteritems, text_type, string_types
from jinja2 import StrictUndefined


def dict_query(a, attr=None, value=None, default=False):
    """
    Given a dictionary, return a list of its keys that has a given attribute
    set to a specified value.

    `value` is always attempted to be interpreted as a boolean the Ansible way.
    'yes', 'no', 'y', 'n' are valid options.

    :param attr: Attribute of the object to compare
    :type attr: str
    :param value: Value of the object to look for. Attempts to be cast to boolean.
    :type value: str
    :param default: Value to use as a default in case the key is missing from object.
    :type default: str | bool
    :returns: list of dict keys that match the criteria
    :rtype: list
    """

    if attr is None:
        raise AnsibleFilterError('dict_query: filter parameter `attr` is mandatory')

    if not isinstance(a, dict):
        raise AnsibleFilterError('dict_query({}, {}): filter operand "{}" is not a dict'.format(attr, value, a))

    out = []

    for k, v in iteritems(a):

        # Default the attribute to False if non-existent
        if v.get(attr) is None:
            iv = default
        else:
            try:
                iv = boolean(v[attr])
            except TypeError:
                iv = v[attr]

        if iv == value:
            out.append(k)

    return out


def dict_lookup(*args, **kwargs):
    """
    Makes nested dictionary access in Python much less painless.
    Access arbitrarily-nested dictionary keys. Uses explicit dictionary access,
    NOT __getattr__(). All traversed objects MUST be dictionaries.

    :param *args: variable length arguments with members of the dict to access
    :param error: fails filter when member is not found, default: False
    :type error: bool
    :return: the value at the given location in the dict
    :raises AnsibleFilterError: upon invalid input, or when the lookup fails (when error=True)
    """

    error = kwargs.pop('error', False)

    # convert args to list so it can be mutated
    args = list(args)

    if len(args) < 2:
        raise AnsibleFilterError('dict_lookup: need at least 1 operand and 1 parameter')

    # pop off the leftmost element of the list, the operand (the jinja2 variable piped to this filter)
    d = args.pop(0)

    if not isinstance(d, dict):
        raise AnsibleFilterError('dict_lookup: operand needs to be a dict')

    # list of accessed members throughout the tree
    accessed = []

    # tree pointer, overwritten on every access
    ptr = d

    # iterate over all positional args and try to use them to access dict keys
    for a in args:

        # only support accessing dict entries with string keys
        if not isinstance(a, (string_types, text_type)):
            raise AnsibleFilterError("dict_lookup: dict key parameter '{}' is not a string".format(a))

        # make sure we only attempt lookups in dictionaries
        if not isinstance(ptr, dict):
            raise AnsibleFilterError(
                "dict_lookup: trying to access member '{}' of non-dictionary value at '.{}'"
                    .format(a, '.'.join(accessed)))

        try:
            # keep a list of traversed members for error reporting
            accessed.append(a)

            # step into the requested member
            ptr = ptr[a]

        except KeyError:
            if error:
                raise AnsibleFilterError("dict_lookup: dict member '.{}' does not exist".format('.'.join(accessed)))

            # if the lookup fails at any point and error reporting is disabled, return StrictUndefined
            return StrictUndefined(name="dict_lookup: '.{}'".format('.'.join(accessed)))

    return ptr


class FilterModule(object):
    """ Iterator Filters """

    def filters(self):
        filters = {
            'dict_select': dict_query,
            'dict_query': dict_query,
            'dict_lookup': dict_lookup
        }

        return filters
