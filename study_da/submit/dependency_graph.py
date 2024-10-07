"""Dependency graph class to manage the dependencies between jobs"""

# ==================================================================================================
# --- Imports
# ==================================================================================================
# Standard library imports
# Third party imports
# Local imports
from study_da.utils import nested_get


# ==================================================================================================
# --- Class
# ==================================================================================================
class DependencyGraph:
    """
    A class to manage the dependencies between jobs.

    Attributes:
        dic_tree (dict): The dictionary representing the job tree.
        dic_all_jobs (dict): The dictionary containing all jobs and their details.
        dependency_graph (dict): The dictionary representing the dependency graph.

    Methods:
        __init__(dic_tree, dic_all_jobs): Initializes the DependencyGraph class.
        build_full_dependency_graph(): Builds the full dependency graph.
        get_unfinished_dependency(job): Gets the list of unfinished dependencies for a given job.
    """

    def __init__(self, dic_tree: dict, dic_all_jobs: dict):
        """
        Initializes the DependencyGraph class.

        Args:
            dic_tree (dict): The dictionary representing the job tree.
            dic_all_jobs (dict): The dictionary containing all jobs and their details.
        """
        self.dic_tree = dic_tree
        self.dic_all_jobs = dic_all_jobs
        self.dependency_graph = {}

    def build_full_dependency_graph(self) -> dict:
        """
        Builds the full dependency graph.

        Returns:
            dict: The full dependency graph.
        """
        self.set_l_keys = {
            tuple(self.dic_all_jobs[job]["l_keys"][:-1]) for job in self.dic_all_jobs
        }
        for job in self.dic_all_jobs:
            l_keys = self.dic_all_jobs[job]["l_keys"]
            self.dependency_graph[job] = set()
            # Add all parents to the dependency graph
            for i in range(len(l_keys) - 1):
                l_keys_parent = l_keys[:i]
                if tuple(l_keys_parent) in self.set_l_keys:
                    parent = nested_get(self.dic_tree, l_keys_parent)
                    # Look for all the jobs in the parent (but not the generations below)
                    for name_parent, sub_dict in parent.items():
                        if "file" in sub_dict:
                            self.dependency_graph[job].add(sub_dict["file"])
        return self.dependency_graph

    def get_unfinished_dependency(self, job: str) -> list:
        """
        Gets the list of unfinished dependencies for a given job.

        Args:
            job (str): The name of the job.

        Returns:
            list: The list of unfinished dependencies.
        """
        # Ensure the dependency graph is built
        if self.dependency_graph == {}:
            self.build_full_dependency_graph()

        # Get the list of dependencies
        l_dependencies = self.dependency_graph[job]

        # Get the corresponding list of l_keys
        ll_keys = [self.dic_all_jobs[dep]["l_keys"] for dep in l_dependencies]

        return [
            dep
            for dep, l_keys in zip(l_dependencies, ll_keys)
            if nested_get(self.dic_tree, l_keys + ["status"]) != "finished"
        ]
