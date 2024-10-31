# Doing an octupole scan along the tune superdiagonal

Octupole scans are an other type of scans that are frequently requested. Just like tune scan, they are usually done in second generation: the first one allows to convert the Mad sequence to a Xsuite collider (single job), while the second one enables to configure the collider and do the scan for various octupoles and tune values (tune values being on the superdiagonal). Let's give an example with the ```config_runIII.yaml``` configuration template.

???+ warning "TODO"

    As you can see in the script, parameter are accessed only with their names. No key is provided, while the corresponding yaml file might have a nested structure. This is because the `set_item_in_dic` function is used to set the value of the parameter. This function will look for the parameter in the configuration file (everywhere) and set its value. Now, if two parameters have the same name, but are in different parts of the configuration file, the script will not work as expected. This is the price of making the package as simple as possible. If you happen to have two parameters with the same name, you will have to modify one of them in the configuration file.

## Study configuration