
# Quick setup

Clone the repository : 

```bash
git clone https://forge-osuc.cnrs-orleans.fr/git/plasmag
```

# Installation


Get sure to have conda installed : https://conda.io/projects/conda/en/latest/user-guide/install/index.html

### Linux conda installation

You can try to install conda with the following command

```bash
mkdir -p ~/miniconda3
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O ~/miniconda3/miniconda.sh
bash ~/miniconda3/miniconda.sh -b -u -p ~/miniconda3
rm -rf ~/miniconda3/miniconda.sh
```

Add conda to your PATH

```bash
~/miniconda3/bin/conda init bash
~/miniconda3/bin/conda init zsh
```
Restart your terminal and try to run conda

```bash
conda --version
```

### Install

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
python PLASMAG.py
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
