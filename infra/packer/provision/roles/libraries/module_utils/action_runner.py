import copy

from ansible.plugins.action import ActionBase


class ActionRunner(ActionBase):
    """
    Action plugin mixin class for an action plugin that calls another action plugin.
    """

    def run(self, tmp=None, task_vars=None):
        return super(ActionRunner, self).run(tmp, task_vars)

    def _run_action_plugin(self, plugin_name, task_vars, module_args=None, check_mode=None):
        """
        Taken from the `win_updates` action plugin. Convenience method to copy the current task,
        clear the args, replace them with our own and run the action plugin.

        :param plugin_name: name of the action plugin to execute
        :param task_vars: task vars passed to the action plugin
        :param module_args: module arguments to pass to the plugin
        :param check_mode: whether or not to override check mode on the callee
        :return: result of module execution
        """

        # Create new task object and reset the args
        new_task = self._task.copy()
        new_task.args = {}

        # clone the play context (contains check mode flag, etc.)
        new_ctx = copy.deepcopy(self._play_context)

        # some action plugins (synchromize..) mutate task_vars, give them a sandbox
        new_task_vars = task_vars.copy()

        if module_args is not None:
            for key, value in module_args.items():
                new_task.args[key] = value

        # force check mode to be in a certain state
        if check_mode is not None:
            new_ctx.check_mode = check_mode

        # run the action plugin and return the results
        action = self._shared_loader_obj.action_loader.get(
            plugin_name,
            task=new_task,
            connection=self._connection,
            play_context=new_ctx,
            loader=self._loader,
            templar=self._templar,
            shared_loader_obj=self._shared_loader_obj
        )

        return action.run(task_vars=new_task_vars)
