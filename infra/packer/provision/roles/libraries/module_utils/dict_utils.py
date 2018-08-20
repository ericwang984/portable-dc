def dict_path(d, path, default=None):
    """
    Traverse the path in the dictionary and return the element.
    Returns an empty dict if one of the elements does not exist.

    :param d: the dictionary to traverse
    :type d: dict
    :param path: the dot-separated path
    :type path: str
    :return: element at path
    """

    keys = path.split('.')
    rv = d

    try:
        for key in keys:
            rv = rv.get(key)
    except AttributeError:
        return default

    return rv


def filter_dict(fdict, mask):
    """
    Filters a dictionary based on an overlay mask.

    :param fdict: the base dictionary to filter
    :type fdict: dict
    :param mask: mask to overlay the dictionary with
    :type mask: list
    :return: filtered dictionary
    :rtype: dict
    """

    if fdict is None:
        fdict = dict()

    if mask is None:
        mask = []

    return {k: v for (k, v) in fdict.items() if k in mask}
