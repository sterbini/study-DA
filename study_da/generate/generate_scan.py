"""This class is used to generate a study (along with the corresponding tree) from a parameter file,
and potentially a set of template files."""

# ==================================================================================================
# --- Imports
# ==================================================================================================

# Import standard library modules
import inspect
import itertools
import os
import shutil
from typing import Any

# Import third-party modules
import numpy as np
import ruamel.yaml as yaml
from jinja2 import Environment, FileSystemLoader

# Import user-defined modules
from study_da.utils import find_item_in_dict, load_dic_from_path, nested_set


# ==================================================================================================
# --- Class definition
# ==================================================================================================
class GenerateScan:
    def __init__(self, path_config: str):
        # Load configuration
        self.config, self.ryaml = load_dic_from_path(path_config)

        # Parameters common across all generations (e.g. for parallelization)
        self.dic_common_parameters: dict[str, Any] = {}

    def render(
        self,
        str_parameters: str,
        template_path: str,
        template_name: str,
        dependencies: dict[str, str] = {},
    ) -> str:
        """
        Renders the study file using a template.

        Args:
            str_parameters (str): The string representation of parameters to declare/mutate.
            template_path (str): The path to the template file.
            template_name (str): The name of the template file.
            dependencies (dict[str, str], optional): The dictionary of dependencies. Defaults to {}.

        Returns:
            str: The rendered study file.
        """
        # Generate generations from template
        environment = Environment(loader=FileSystemLoader(template_path))
        template = environment.get_template(template_name)

        return template.render(parameters=str_parameters, **dependencies)

    def write(self, study_str: str, file_path: str):
        """
        Writes the study file to disk.

        Args:
            study_str (str): The study file string.
            file_path (str): The path to write the study file.
        """

        # Make folder if it doesn't exist
        folder = os.path.dirname(file_path)
        if folder != "":
            os.makedirs(folder, exist_ok=True)

        with open(file_path, mode="w", encoding="utf-8") as file:
            file.write(study_str)

    def generate_render_write(
        self,
        gen_name: str,
        study_path: str,
        template_name: str,
        template_path: str,
        dic_mutated_parameters: dict[str, Any] = {},
    ) -> list[str]:  # sourcery skip: default-mutable-arg
        """
        Generates, renders, and writes the study file.

        Args:
            gen_name (str): The name of the generation.
            study_path (str): The path to the study folder.
            template_name (str): The name of the template file.
            template_path (str): The path to the template folder.
            dic_mutated_parameters (dict[str, Any], optional): The dictionary of mutated parameters. Defaults to {}.

        Returns:
            tuple[str, list[str]]: The study file string and the list of study paths.
        """
        directory_path_gen = f"{study_path}"
        if not directory_path_gen.endswith("/"):
            directory_path_gen += "/"
        file_path_gen = f"{directory_path_gen}{gen_name}.py"

        # Generate the string of parameters
        str_parameters = "{"
        for key, value in dic_mutated_parameters.items():
            if isinstance(value, str):
                str_parameters += f"'{key}' : '{value}', "
            else:
                str_parameters += f"'{key}' : {value}, "
        str_parameters += "}"

        # Adapt the dict of dependencies to the current generation
        dic_dependencies = self.config["dependencies"] if "dependencies" in self.config else {}
        # Always load configuration from above generation
        depth_gen = 1
        # Initial dependencies are always copied at the root of the study (hence value.split("/")[-1])
        dic_dependencies = {
            key: "../" * depth_gen + value.split("/")[-1] for key, value in dic_dependencies.items()
        }

        # Render and write the study file
        study_str = self.render(
            str_parameters,
            template_name=template_name,
            template_path=template_path,
            dependencies=dic_dependencies,
        )

        self.write(study_str, file_path_gen)
        return [directory_path_gen]

    def get_dic_parametric_scans(self, generation) -> tuple[dict[str, Any], dict[str, Any]]:
        """
        Retrieves dictionaries of parametric scan values.

        Args:
            generation: The generation name.

        Returns:
            tuple[dict[str, Any], dict[str, Any]]: The dictionaries of parametric scan values.
        """

        if generation == "base":
            raise ValueError("Generation 'base' should not have scans.")

        def test_convert_for_subvariables(parameter_dict: dict, parameter_list: list) -> list:
            if "subvariables" in parameter_dict:
                subvariables = self.config["structure"][generation]["scans"][parameter][
                    "subvariables"
                ]
                parameter_list = [
                    {subvar: value for subvar in subvariables} for value in parameter_list
                ]
            return parameter_list

        dic_parameter_lists = {}
        dic_parameter_lists_for_naming = {}
        for parameter in self.config["structure"][generation]["scans"]:
            if "linspace" in self.config["structure"][generation]["scans"][parameter]:
                l_values_linspace = self.config["structure"][generation]["scans"][parameter][
                    "linspace"
                ]
                parameter_list = np.round(
                    np.linspace(
                        l_values_linspace[0],
                        l_values_linspace[1],
                        l_values_linspace[2],
                        endpoint=True,
                    ),
                    5,
                )
                dic_parameter_lists_for_naming[parameter] = parameter_list
            elif "logspace" in self.config["structure"][generation]["scans"][parameter]:
                l_values_logspace = self.config["structure"][generation]["scans"][parameter][
                    "logspace"
                ]
                parameter_list = np.round(
                    np.logspace(
                        l_values_logspace[0],
                        l_values_logspace[1],
                        l_values_logspace[2],
                        endpoint=True,
                    ),
                    5,
                )
                dic_parameter_lists_for_naming[parameter] = parameter_list
            elif "path_list" in self.config["structure"][generation]["scans"][parameter]:
                l_values_path_list = self.config["structure"][generation]["scans"][parameter][
                    "path_list"
                ]
                n_path_arg = l_values_path_list[1]
                n_path = find_item_in_dict(self.dic_common_parameters, n_path_arg)
                if n_path is None:
                    raise ValueError(
                        f"Parameter {n_path_arg} is not defined in the scan configuration."
                    )
                parameter_list = [
                    l_values_path_list[0].replace("____", f"{n:02d}") for n in range(n_path)
                ]
                dic_parameter_lists_for_naming[parameter] = [f"{n:02d}" for n in range(n_path)]
            elif "list" in self.config["structure"][generation]["scans"][parameter]:
                parameter_list = self.config["structure"][generation]["scans"][parameter]["list"]
                dic_parameter_lists_for_naming[parameter] = parameter_list
            else:
                raise ValueError(f"Scanning method for parameter {parameter} is not recognized.")

            # Ensure that all values are not numpy types (to avoid serialization issues)
            parameter_list = [x.item() if isinstance(x, np.generic) else x for x in parameter_list]

            # Handle nested parameters
            parameter_list_updated = test_convert_for_subvariables(
                self.config["structure"][generation]["scans"][parameter], parameter_list
            )
            dic_parameter_lists[parameter] = parameter_list_updated

        # Remember common parameters as they might be used across generations
        if "common_parameters" in self.config["structure"][generation]:
            self.dic_common_parameters[generation] = {}
            for parameter in self.config["structure"][generation]["common_parameters"]:
                self.dic_common_parameters[generation][parameter] = self.config["structure"][
                    generation
                ]["common_parameters"][parameter]

        return dic_parameter_lists, dic_parameter_lists_for_naming

    def create_scans(
        self,
        generation: str,
        generation_path: str,
        template_name: str,
        template_path: str,
    ) -> list[str]:
        """
        Creates study files for parametric scans.

        Args:
            generation (str): The generation name.
            generation_path (str): The path to the layer folder.
            template_name (str): The name of the template file.
            template_path (str): The path to the template folder.

        Returns:
            tuple[list[str], list[str]]: The list of study file strings and the list of study paths.
        """
        # Get dictionnary of parametric values being scanned
        dic_parameter_lists, dic_parameter_lists_for_naming = self.get_dic_parametric_scans(
            generation
        )
        # Generate render write for cartesian product of all parameters
        l_study_path = []
        for l_values, l_values_for_naming in zip(
            itertools.product(*dic_parameter_lists.values()),
            itertools.product(*dic_parameter_lists_for_naming.values()),
        ):
            dic_mutated_parameters = dict(zip(dic_parameter_lists.keys(), l_values))
            dic_mutated_parameters_for_naming = dict(
                zip(dic_parameter_lists.keys(), l_values_for_naming)
            )
            path = (
                generation_path
                + "_".join(
                    [
                        f"{parameter}_{value}"
                        for parameter, value in dic_mutated_parameters_for_naming.items()
                    ]
                )
                + "/"
            )

            # Add common parameters
            if generation in self.dic_common_parameters:
                dic_mutated_parameters |= self.dic_common_parameters[generation]

            # Generate the study for current generation
            self.generate_render_write(
                generation,
                path,
                template_name,
                template_path,
                dic_mutated_parameters=dic_mutated_parameters,
            )

            # Append the list of study paths to build the tree later on
            l_study_path.append(path)

        return l_study_path

    def complete_tree(
        self, dictionary_tree: dict, l_study_path_next_gen: list[str], gen: str
    ) -> dict:
        """
        Completes the tree structure of the study dictionary.

        Args:
            dictionary_tree (dict): The dictionary representing the study tree structure.
            l_study_path_next_gen (list[str]): The list of study paths for the next gen.
            gen (str): The generation name.

        Returns:
            dict: The updated dictionary representing the study tree structure.
        """
        for path_next in l_study_path_next_gen:
            nested_set(
                dictionary_tree,
                path_next.split("/")[1:-1] + [gen],
                {"file": f"{path_next}{gen}.py"},
            )

        return dictionary_tree

    def write_tree(self, dictionary_tree: dict):
        """
        Writes the study tree structure to a YAML file.

        Args:
            dictionary_tree (dict): The dictionary representing the study tree structure.
        """
        ryaml = yaml.YAML()
        with open(self.config["name"] + "/" + "tree.yaml", "w") as yaml_file:
            ryaml.indent(sequence=4, offset=2)
            ryaml.dump(dictionary_tree, yaml_file)

    def create_study_for_current_gen(self, generation: str, study_path: str) -> list[str]:
        """
        Creates study files for the current generation.

        Args:
            generation (str): The name of the current generation.
            study_path (str): The path to the study folder.
            dictionary_tree (dict): The dictionary representing the study tree structure.

        Returns:
            tuple[list[str], list[str]]: The list of study file strings and the list of study paths.
        """
        executable_name = self.config["structure"][generation]["executable"]["name"]
        template = self.config["structure"][generation]["executable"]["template"]
        if template:
            executable_path = f"{os.path.dirname(inspect.getfile(GenerateScan))}/template_scripts/"
        else:
            raise ValueError("Executables that are not templates are not implemented yet.")

        return (
            self.create_scans(generation, study_path, executable_name, executable_path)
            if "scans" in self.config["structure"][generation]
            else self.generate_render_write(
                self.config["structure"][generation],
                study_path,
                executable_name,
                executable_path,
            )
        )

    def create_study(
        self,
        tree_file: bool = True,
        force_overwrite: bool = False,
    ) -> None:
        l_study_path = [self.config["name"] + "/"]
        dictionary_tree = {}
        """
        Creates study files for the entire study.

        Args:
            tree_file (bool, optional): Whether to write the study tree structure to a YAML file. Defaults to True.
            force_overwrite (bool, optional): Whether to overwrite existing study files. Defaults to False.

        Returns:
            list[str]: The list of study file strings.
        """
        # Remove existing study if force_overwrite
        if os.path.exists(self.config["name"]):
            if not force_overwrite:
                answer = input(
                    "The folder already exists. You might delete an existing study. "
                    "Do you want to overwrite it? [y/n]"
                )
                if answer != "y":
                    print("Aborting...")
                    exit()
            shutil.rmtree(self.config["name"])

        # Browse through the generations
        l_generations = list(self.config["structure"].keys())
        for idx, generation in enumerate(l_generations):
            l_study_path_all_next_generation = []
            for study_path in l_study_path:
                # Get list of paths for the children of the current study
                l_study_path_next_generation = self.create_study_for_current_gen(
                    generation, study_path
                )
                # Update tree
                dictionary_tree = self.complete_tree(
                    dictionary_tree, l_study_path_next_generation, generation
                )
                # Complete list of paths for the children of all studies (of the current generation)
                l_study_path_all_next_generation.extend(l_study_path_next_generation)

            # Update study path for next later
            l_study_path = l_study_path_all_next_generation

        # Add dependencies to the study
        if "dependencies" in self.config:
            for dependency, path in self.config["dependencies"].items():
                shutil.copy2(path, self.config["name"])

        if tree_file:
            self.write_tree(dictionary_tree)
