import os

def find_executable(cmd):
    """
    Return first-found executable in the environment's PATH.
    If no executable is found, returns None. Mainly for use in action plugins,
    for modules, use get_bin_path().

    :param cmd: name of the executable
    :type cmd: str
    :return: absolute path of the executable, or None
    :rtype: str
    """

    p = (os.path.join(path, cmd)
         for path in os.environ["PATH"].split(os.pathsep)
         if os.access(os.path.join(path, cmd), os.X_OK))

    return next(p, None)
