import errno
import operator as py_operator
import os

from distutils.version import LooseVersion, StrictVersion


def semver_spec(versions_iter, operator, version):
    """
    Filter a list of strings with semantic versions according to a single comparison tuple, eg.
    'lt' and '1.0.0'. This will yield all versions of the list below 1.0.0.

    :param versions_iter: Iterable of versions to filter
    :type versions_iter: list
    :param operator: the Python operator to apply to the operation (ge, gt, lt, le, ..)
    :type operator: str
    :param version: the version to compare against
    :type version: str
    :return: list of versions that comply with the version and operator
    :rtype: list
    """

    v = LooseVersion(str(version))

    vl = []

    for i in versions_iter:
        try:
            # versions need to comply with StrictVersion, which doesn't render a trailing .0 to string
            # use LooseVersion to run comparisons and pass them around
            StrictVersion(i)
            vl.append(LooseVersion(i))
        except ValueError:
            # ignore non-semver entries
            pass

    # get python operator method with the given name
    method = getattr(py_operator, operator)

    return [x for x in vl if method(x, v)]


def find_semver(path, version, extension='.yml'):
    """
    For all entries in a given path, find the file with the highest semantic version
    below or equals to the given semantic version.

    :param path: path to the directory to scan for semantically-versioned files
    :type path: str
    :param version: version to use in the semver lookup
    :type version: str
    :param extension: limit search to files with this extension
    :type extension: str
    :return: path to the file that matches the criteria
    :rtype: str
    :raises OSError: when the input path does not exist, no files are matched or cannot be accessed
    :raises ValueError: when the input version is not SemVer
    """

    if not os.path.isdir(path):
        raise OSError("path '{}' is not a directory".format(path))

    try:
        StrictVersion(version)
    except ValueError:
        raise ValueError("string '{}' is not a semantic version".format(version))

    # list all files with a certain extension with the extension removed
    dir_entries = [x[:-len(extension)] for x in os.listdir(path) if x.endswith(extension)]

    # return a list of comparable version objects adhering to specification
    versions = semver_spec(dir_entries, 'le', version)

    if not versions:
        raise OSError("no files matching spec '(<={}){}' found in path '{}'".format(version, extension, path))

    # select the highest-available remaining version
    selected_ver = max(versions)

    # rebuild the path to the file
    out_file = os.path.join(path, str(selected_ver) + extension)

    if not os.path.isfile(out_file):
        raise OSError(errno.ENOENT, "error opening file '{}'".format(out_file))

    return out_file
