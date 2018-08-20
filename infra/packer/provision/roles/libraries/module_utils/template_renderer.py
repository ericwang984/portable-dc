import json
import os

import yaml
from ansible.module_utils._text import to_text
from ansible.plugins.action import ActionBase
from ansible.template import generate_ansible_template_vars


class TemplateRenderer(ActionBase):
    """
    Action plugin mixin class for convenient template rendering with variable injection.
    """

    def run(self, tmp=None, task_vars=None):
        return super(TemplateRenderer, self).run(tmp, task_vars)

    def _get_working_path(self):
        """
        Get the 'work directory' of the execution context.
        :return: the current 'work dir' relative to role or playbook
        :rtype: str
        """
        cwd = self._loader.get_basedir()

        if self._task._role is not None:
            cwd = self._task._role._role_path

        return cwd

    def _find_template(self, topdir=None, subdir='', filename=None, default_ext='json'):
        """
        Look for a template file relative to the execution context.
        Uses three components, 'topdir', 'subdir' and 'filename', to build a path on disk.
        This allows the implementing tool to flexibly enforce a directory structure with
        at least one fixed top-level directory.

        :param topdir: top-level directory to search in, adjacent to the workdir
        :type topdir: str
        :param subdir: intermediate nested directory that is scanned first, before the top level (optional)
        :type subdir: str
        :param filename: name of the file to look for - can have an extension that overrides 'default_ext'
        :type filename: str
        :param default_ext: default extension to look for if omitted in 'src'
        :type default_ext: str
        :return: absolute path of the first-matched template
        :rtype: str
        :raise ValueError: when 'topdir' or 'filename' are empty or not specified
        :raise ValueError: when no template found on disk
        """

        if not topdir:
            raise ValueError("parameter 'topdir' empty or not specified")

        # Need a non-empty value
        if not filename:
            raise ValueError("parameter 'filename' empty or not specified")

        working_path = self._get_working_path()
        playbook_dir = self._loader.get_basedir()

        # append default extension if it cannot be inferred
        _, ext = os.path.splitext(filename)
        if not ext:
            filename = '{}.{}'.format(filename, default_ext)

        # look for files in the 'directory' directory unless an absolute path is given
        searched_paths = []
        if os.path.isabs(filename):
            srcpath = filename
        else:
            # look inside <topdir>/<subdir> directory
            srcpath = self._loader.path_dwim_relative(working_path, os.path.join(topdir, subdir), filename)
            searched_paths.append(os.path.join(working_path, topdir, subdir, filename))

            # indicate that the root of the Ansible repo is also scanned
            if working_path != playbook_dir:
                searched_paths.append(os.path.join(playbook_dir, topdir, subdir, filename))

            # if empty, look inside <topdir> directory
            if not os.path.exists(srcpath):
                srcpath = self._loader.path_dwim_relative(working_path, topdir, filename)
                searched_paths.append(os.path.join(working_path, topdir, filename))

                # indicate that the root of the Ansible repo is also scanned
                if working_path != playbook_dir:
                    searched_paths.append(os.path.join(playbook_dir, topdir, filename))

        if not os.path.exists(srcpath):
            raise ValueError('{} {} template {} not found in any of {}'
                             .format(topdir, subdir, filename, searched_paths))

        return srcpath

    def _render_template(self, task_vars=None, extra_vars=None, srcfile=None, parser='json'):
        """
        Renders the template, interprets the output using the specified parser
        and returns a dictionary with the result.

        :param task_vars: the global Ansible task_vars dictionary
        :type task_vars: dict
        :param extra_vars: extra variables to inject into template context
        :type extra_vars: dict
        :param srcfile: the absolute path on disk to read for the template from
        :type srcfile: str
        :param parser: the parser to interpret the template result with (default json)
        :type parser: str
        :return: the interpreted app definition
        :rtype: dict
        """

        # make a copy of task_vars so we can manipulate them freely
        temp_vars = task_vars.copy()

        # save template engine's vars to restore later
        old_vars = self._templar._available_variables

        # generate template-specific vars (ansible_managed, etc.)
        temp_vars.update(generate_ansible_template_vars(srcfile))

        # add our own custom variables to the template context
        if extra_vars:
            temp_vars.update(extra_vars)

        # swap temp_vars into template context
        self._templar.set_available_variables(temp_vars)

        # open the template file
        try:
            with open(srcfile, 'r') as f:
                template_data = to_text(f.read())
        except IOError:
            raise ValueError('unable to load src file {}'.format(srcfile))

        # render the template
        # convert_data=False disables the interpretation of the resulting json blob
        # we do this explicitly below, since we'll need to support both json and yaml (later).
        result = self._templar.template(template_data, preserve_trailing_newlines=True,
                                        escape_backslashes=False, convert_data=False)

        # parse the result according to the value in 'parser'
        if parser == 'json':
            out = json.loads(result)
        elif parser == 'yml' or parser == 'yaml':
            out = yaml.load(result)
            if not out:
                raise ValueError("'{}' does not contain a valid YAML document".format(srcfile))
        else:
            raise NotImplementedError("unknown parser {}".format(parser))

        # restore old task_vars back into template engine context
        self._templar.set_available_variables(old_vars)

        return out
