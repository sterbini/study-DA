"""Generate the code reference pages and navigation."""

from pathlib import Path

import mkdocs_gen_files
import ruamel.yaml

##### First update configurations
for filename, header in zip(
    ["config_hllhc16", "config_hllhc13", "config_runIII", "config_runIII_ions"],
    ["HL-LHC v1.6", "HL-LHC v1.3", "Run III", "Run III ions"],
):
    path = f"study_da/generate/template_configurations/{filename}.yaml"
    ryaml = ruamel.yaml.YAML()
    with open(path, "r") as fid:
        dic = ryaml.load(fid)

    with open(f"docs/template_files/configurations/{filename}.md", "w") as fid:
        fid.write(f"# {header} configuration\n\n")
        fid.write(f"""```yaml title="{filename}.yaml"\n""")
        ryaml.dump(dic, fid)
        fid.write("""```\n""")

# Add the dictionnary of parameter names and keys
path = "study_da/postprocess/configs/parameters_lhc.yaml"
ryaml = ruamel.yaml.YAML()
with open(path, "r") as fid:
    dic = ryaml.load(fid)

with open("docs/template_files/mapping/parameters_lhc.md", "w") as fid:
    fid.write("# Parameters mapping \n\n")
    fid.write("""```yaml title="parameters_lhc.yaml"\n""")
    ryaml.dump(dic, fid)
    fid.write("""```\n""")

##### Then update scripts
for filename, header in zip(
    ["generation_1", "generation_2_level_by_nb", "generation_2_level_by_sep"],
    [
        "Generation 1 (generate xsuite collider from mad sequence) template script",
        "Generation 2 (configure and level by bunch intensity, track) template script",
        "Generation 2 (configure and level by separation, track) template script",
    ],
):
    path = f"study_da/generate/template_scripts/{filename}.py"
    with open(path, "r") as f:
        content = f.read()

    with open(f"docs/template_files/scripts/{filename}.md", "w") as f:
        f.write(f"# {header}\n\n")
        f.write(f"""```py title="{filename}.py"\n""")
        f.write(content)
        f.write("""```\n""")


##### Then generate technical documentation
nav = mkdocs_gen_files.Nav()

root = Path(__file__).parent.parent
src = root

for path in sorted(src.rglob("*.py")):
    module_path = path.relative_to(src).with_suffix("")
    if "study_da/" not in path.as_posix():
        continue
    doc_path = path.relative_to(src).with_suffix(".md")
    full_doc_path = Path("reference", doc_path)

    parts = tuple(module_path.parts)

    if parts[-1] == "__init__":
        parts = parts[:-1]
        doc_path = doc_path.with_name("index.md")
        full_doc_path = full_doc_path.with_name("index.md")
    elif parts[-1] == "__main__":
        continue

    nav[parts] = doc_path.as_posix()

    with mkdocs_gen_files.open(full_doc_path, "w") as fd:
        ident = ".".join(parts)
        fd.write(f"::: {ident}")

    mkdocs_gen_files.set_edit_path(full_doc_path, Path("../") / path)

with mkdocs_gen_files.open("reference/SUMMARY.md", "w") as nav_file:
    nav_file.writelines(nav.build_literate_nav())

# Display the generated nav
with mkdocs_gen_files.open("reference/SUMMARY.md", "r") as nav_file:
    for line in nav_file:
        print(line, end="")
