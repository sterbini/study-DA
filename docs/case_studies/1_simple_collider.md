# Working with a single collider

The special function ```create_single_job()``` can be used to build and configure a collider without having to manually configure an irrelevant configuration scan.

Assuming you'd like to work with the template [`hllhc16` configuration](../template_files/configurations/config_hllhc16.md), but save the collider from the 2nd generation and only track for 1000 turns, you could proceed as follows:

```py title="file.py" linenums="1"
print('test')
```

Your directory structure must be identical to the provided templates one:

```bash
📁 root/
├─╴📁 children/
│   ├── 📁 job/
│   └── 📁 job/
└── 📁 children/
    ├── 📁 job/
    └── 📁 job/
```
