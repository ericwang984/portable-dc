def join_list(inlist):
    """
    Return a string representation of a list of arbitrary items,
    joined by newlines. Adds a trailing newline.

    :param inlist: list of arbitrary objects
    :type inlist: list
    :return: newline-joined string
    :rtype: str
    """

    # Return empty string to avoid returning unnecessary newlines
    if not inlist:
        return ''

    # Get individual string representation of all DiffEntries
    diffstr = [str(x) for x in inlist]

    # Join the entries with newlines and wrap in newlines
    return '\n'.join(diffstr) + '\n'


def prepared_diff(inlist):
    """
    Render a list of diff entries from ansible-dotdiff and wraps it
    in an Ansible diff structure.

    :param inlist: The input list
    :type inlist: list
    :return: dict with a single `prepared` key
    :rtype: dict
    """

    diffstr = join_list(inlist)

    # Wrap in a list of dicts with a single 'prepared' key
    return dict(prepared='{}\n'.format(diffstr))
