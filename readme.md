
# PLASMAG 
**(Python Library for Accurate Space Magnetometer Adjustments with Genetics)**

PLASMAG is a simulation software specifically designed for 
space magnetometers.
At its core, PLASMAG serves as a comprehensive tool for the parameters adjustment.

Currently, PLASMAG is tailored to support search coil type instruments.
However, its architecture is built with flexibility and extensibility in mind. This means PLASMAG is not only limited to current implementations but is also designed to easily accommodate the addition of new instruments and the integration of diverse calculation methods and models. 


## Table of Contents

- [Quick Setup](#quick-setup)
- [Installation](#installation)
  - [Prerequisites](#prerequisites)
  - [Installing Conda](#installing-conda)
  - [Setting Up the Project](#setting-up-the-project)
- [Usage](#usage)
- [Availables Models](#availables-models)
- [Documentation](#documentation)
- [Contributing](#contributing)
- [License](#license)
- [Acknowledgments](#acknowledgments)

## Quick Setup

Clone the repository : 

```bash
git clone https://forge-osuc.cnrs-orleans.fr/git/plasmag
```

## Installation

### Prerequisites


Ensure you have Conda installed. If not, follow the instructions here: https://conda.io/projects/conda/en/latest/user-guide/install/index.html

### Linux conda installation

Linux Conda Installation

Install Conda using the following commands:

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
Restart your terminal and verify the Conda installation:
```bash
conda --version
```

### Setting Up the Project

Create and activate a new Conda environment:

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

## Usage

TODO

## Availables Models

At the moment, the PLASMAG simulation model has only one model implemented: a simple search coil MAGNETOMETER analytic model. 

The simulation was validated by comparing the simulation results with the real data from the JUICE mission. 

The parameters for JUICE's search coil can be found in the data/JUICE.json file."

The implemented simulation model performs quite well, demonstrating high accuracy for low frequency values. This is reflected in the impedance plot, where the plotted curves all maintain consistent levels and shapes. 

However, challenges arise when extending the analysis to higher frequency ranges. 
Specifically, for the NEMI and Closed Loop Transfer Function (CLTF),
the model tends to diverge slightly at high frequencies.
This divergence becomes particularly evident after the resonance frequency. 
At this juncture, analytically describing the 'capacitance' part of the system grows 
increasingly difficult, leading to a slight deviation from expected behaviors. 
This discrepancy underlines a current limitation of the model, spotlighting the 
need for further refinement and development to enhance its accuracy.

## Documentation

To generate project documentation:

```bash
pip install sphinx
cd docs
make html
```

Navigate to docs/_build/html/index.html to view the documentation.

## Contributing

The project is open to contributions. Please refer to the [CONTRIBUTING.md](CONTRIBUTING.md) file for more information.

## Acknowledgments

TODO
