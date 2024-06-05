"""This class is used to generate a study (along with the corresponding tree) from a parameter file,
and potentially a set of template files."""

# ==================================================================================================
# --- Imports
# ==================================================================================================

# Import standard library modules
import itertools
import os
import shutil
from typing import Any

import numpy as np

# Import third-party modules
from jinja2 import Environment, FileSystemLoader

# Import user-defined modules
from . import load_configuration_from_path


# ==================================================================================================
# --- Class definition
# ==================================================================================================
class StudyDA:
    def __init__(self, path_config: str):
        # Load configuration
        self.config, self.ryaml = load_configuration_from_path(path_config)

    def render(
        self,
        str_parameters: str,
        template_path: str,
        template_name: str,
    ) -> str:
        """
        Renders the study file using a template.

        Args:
            str_parameters (str): The string representation of parameters to declare/mutate.
            template_path (str): The path to the template file.
            template_name (str): The name of the template file.

        Returns:
            str: The rendered study file.
        """
        # Generate generations from template
        environment = Environment(loader=FileSystemLoader(template_path))
        template = environment.get_template(template_name)

        return template.render(parameters=str_parameters)

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
    ) -> tuple[str, list[str]]:  # sourcery skip: default-mutable-arg
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

        # Get the string of mutated parameters

        # Render and write the study file
        study_str = self.render(
            str_parameters, template_name=template_name, template_path=template_path
        )

        self.write(study_str, file_path_gen)
        return study_str, [directory_path_gen]

    def get_dic_parametric_scans(self, layer) -> tuple[dict[str, Any], dict[str, Any]]:
        """
        Retrieves dictionaries of parametric scan values.

        Args:
            layer: The layer name.

        Returns:
            tuple[dict[str, Any], dict[str, Any]]: The dictionaries of parametric scan values.
        """

        def test_convert_for_each_beam(parameter_dict: dict, parameter_list: list) -> list:
            if "for_each_beam" in parameter_dict and parameter_dict["for_each_beam"]:
                parameter_list = [{"lhcb1": value, "lhcb2": value} for value in parameter_list]
            return parameter_list

        def convert_variables_to_values(l_values: list) -> list:
            for idx, param in enumerate(l_values):
                with contextlib.suppress(ValueError):
                    l_values[idx] = self.get_parameters(param)
            return l_values

        dic_parameter_lists = {}
        dic_parameter_lists_for_naming = {}
        for parameter in self.master["structure"][layer]["scans"]:
            if "linspace" in self.master["structure"][layer]["scans"][parameter]:
                l_values_linspace = self.master["structure"][layer]["scans"][parameter]["linspace"]
                l_values_linspace = convert_variables_to_values(l_values_linspace)
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
            elif "logspace" in self.master["structure"][layer]["scans"][parameter]:
                l_values_logspace = self.master["structure"][layer]["scans"][parameter]["logspace"]
                l_values_logspace = convert_variables_to_values(l_values_logspace)
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
            elif "path_list" in self.master["structure"][layer]["scans"][parameter]:
                l_values_path_list = self.master["structure"][layer]["scans"][parameter][
                    "path_list"
                ]
                l_values_path_list = convert_variables_to_values(l_values_path_list)
                parameter_list = [
                    l_values_path_list[0].replace("____", f"{n:02d}")
                    for n in range(l_values_path_list[1], l_values_path_list[2])
                ]
                dic_parameter_lists_for_naming[parameter] = [
                    f"{n:02d}" for n in range(l_values_path_list[1], l_values_path_list[2])
                ]
            elif "list" in self.master["structure"][layer]["scans"][parameter]:
                parameter_list = self.master["structure"][layer]["scans"][parameter]["list"]
                parameter_list = convert_variables_to_values(parameter_list)
                dic_parameter_lists_for_naming[parameter] = parameter_list
            else:
                raise ValueError(f"Scanning method for parameter {parameter} is not recognized.")

            parameter_list_updated = test_convert_for_each_beam(
                self.master["structure"][layer]["scans"][parameter], parameter_list
            )
            dic_parameter_lists[parameter] = parameter_list_updated

        return dic_parameter_lists, dic_parameter_lists_for_naming

    def create_scans(
        self,
        gen: str,
        layer: str,
        layer_path: str,
        template_name: str,
        template_path: str,
    ) -> tuple[list[str], list[str]]:
        """
        Creates study files for parametric scans.

        Args:
            gen (str): The generation name.
            layer (str): The layer name.
            layer_path (str): The path to the layer folder.
            template_name (str): The name of the template file.
            template_path (str): The path to the template folder.

        Returns:
            tuple[list[str], list[str]]: The list of study file strings and the list of study paths.
        """
        # Get dictionnary of parametric values being scanned
        dic_parameter_lists, dic_parameter_lists_for_naming = self.get_dic_parametric_scans(layer)
        # Generate render write for cartesian product of all parameters
        l_study_str = []
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
                layer_path
                + "_".join(
                    [
                        f"{parameter}_{value}"
                        for parameter, value in dic_mutated_parameters_for_naming.items()
                    ]
                )
                + "/"
            )
            l_study_path.append(path)
            l_study_str.append(
                self.generate_render_write(
                    gen,
                    "",
                    path,
                    template_name,
                    template_path,
                    dic_mutated_parameters=dic_mutated_parameters,
                )
            )
        return l_study_str, l_study_path

    def complete_tree(
        self, dictionary_tree: dict, l_study_path_next_layer: list[str], gen: str
    ) -> dict:
        """
        Completes the tree structure of the study dictionary.

        Args:
            dictionary_tree (dict): The dictionary representing the study tree structure.
            l_study_path_next_layer (list[str]): The list of study paths for the next layer.
            gen (str): The generation name.

        Returns:
            dict: The updated dictionary representing the study tree structure.
        """
        for path_next in l_study_path_next_layer:
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
        with open(self.master["name"] + "/" + "tree.yaml", "w") as yaml_file:
            ryaml.indent(sequence=4, offset=2)
            ryaml.dump(dictionary_tree, yaml_file)

    def create_study_for_current_gen(
        self, idx_layer: int, layer: str, gen: str, study_path: str, dictionary_tree: dict
    ) -> tuple[list[str], list[str]]:
        """
        Creates study files for the current generation.

        Args:
            idx_layer (int): The index of the current layer.
            layer (str): The name of the current layer.
            gen (str): The name of the current generation.
            study_path (str): The path to the study folder.
            dictionary_tree (dict): The dictionary representing the study tree structure.

        Returns:
            tuple[list[str], list[str]]: The list of study file strings and the list of study paths.
        """
        template_name = self.master[gen].get("template_name", self.default_template_name)
        template_path = self.master[gen].get("template_path", self.default_template_path)
        if "scans" in self.master["structure"][layer]:
            l_study_scan_str, l_study_path_next_layer = self.create_scans(
                gen, layer, study_path, template_name, template_path
            )
            return l_study_scan_str, l_study_path_next_layer
            # l_study_str.extend(l_study_scan_str)
        else:
            # Always give the layer the name of the first generation file,
            # except if very first layer
            layer_temp = (
                "base" if idx_layer == 0 else self.master["structure"][layer]["generations"][0]
            )
            study_str, l_study_path_next_layer = self.generate_render_write(
                gen,
                layer_temp,
                study_path,
                template_name,
                template_path,
            )
            # l_study_str.append(study_str)
            return [study_str], l_study_path_next_layer

    def create_study(self, tree_file: bool = True, force_overwrite: bool = False) -> list[str]:
        l_study_str = []
        l_study_path = [self.master["name"] + "/"]
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
        if force_overwrite and os.path.exists(self.master["name"]):
            shutil.rmtree(self.master["name"])

        for idx, layer in enumerate(sorted(self.master["structure"].keys())):
            # Each generaration inside of a layer should yield the same l_study_path_next_layer
            l_study_path_next_layer = []
            for study_path in l_study_path:
                for gen in self.master["structure"][layer]["generations"]:
                    l_curr_study_str, l_study_path_next_layer = self.create_study_for_current_gen(
                        idx, layer, gen, study_path, dictionary_tree
                    )
                    l_study_str.extend(l_curr_study_str)
                    dictionary_tree = self.complete_tree(
                        dictionary_tree, l_study_path_next_layer, gen
                    )

            # Update study path for next later
            l_study_path = l_study_path_next_layer

        if tree_file:
            self.write_tree(dictionary_tree)

        return l_study_str
