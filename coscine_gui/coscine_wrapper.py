class CoscineWrapper:
    def __init__(self, project):
        """
        project(coscine.project/coscine.client):
        """
        if hasattr(project, 'client'):
            self._project = project
            self._client = project.client
        else:
            self._project = None
            self._client = project

        if self._client.verbose:
            print("Silenced client!")
            self._client.verbose = False

    @property
    def verbose(self):
        return self._client.verbose

    @verbose.setter
    def verbose(self, val):
        self._client.verbose = val

    def list_groups(self):
        if self._project is None:
            return [pr.name for pr in self._client.projects()]
        else:
            return [pr.name for pr in self._project.subprojects()]

    def list_nodes(self):
        if self._project is None:
            return []
        else:
            return [res.name for res in self._project.resources()]

    def __getitem__(self, key):
        if key in self.list_nodes():  # This implies project is not None
            return self._project.resource(key)
        self.get_group(key)

    def get_node(self, key):
        if key in self.list_nodes():
            return self._project.resource(key)
        else:
            return KeyError(key)

    def get_group(self, key):
        if key in self.list_groups() and self._project is not None:
            return self.__class__(self._project.subprojects(displayName=key)[0])
        elif key in self.list_groups():
            return self.__class__(self._client.project(key))
        else:
            raise KeyError(key)
