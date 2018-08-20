from ansible.errors import AnsibleFilterError
from ansible.module_utils.six import text_type, string_types


def extend(a, b):
    """
    Call Python's extend() on the input list and return the result.
    Parameters cannot be strings.
    """

    if isinstance(a, (string_types, text_type)):
        raise AnsibleFilterError('extend() input "{}" cannot be a string'.format(a))
    if isinstance(b, (string_types, text_type)):
        raise AnsibleFilterError('extend() parameter "{}" cannot be a string'.format(b))

    try:
        iter(a)
    except TypeError:
        raise AnsibleFilterError('extend() input is not iterable')
    try:
        iter(b)
    except TypeError:
        raise AnsibleFilterError('extend() parameter is not iterable')

    return list(a) + list(b)


class FilterModule(object):
    """ Iterator Filters """

    def filters(self):
        filters = {
            'extend': extend,
        }

        return filters
