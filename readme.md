
# Quick setup

Clone the repository : 

```bash
git clone https://forge-osuc.cnrs-orleans.fr/git/plasmag
```

# Installation


Get sure to have conda installed : https://conda.io/projects/conda/en/latest/user-guide/install/index.html

Create a new conda environment from the environment.yml file

```bash
conda env create -f environment.yml
```

Activate the environment

```bash
conda activate PLASMAG
```

Run the application

```bash
python -m plasmag
```



# Documentation

Require Sphinx

```bash
pip install sphinx
```

```bash
cd docs
make html
```
