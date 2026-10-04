# Many-Logic Modal Structure Editor

An open-source Python tool for constructing, visualising and verifying properties of **Many-Logic Modal Logic (MLML)** models, over a many lattice and a signature.

## Overview

In MLML, a single Kripke-style model may combine states governed by different logics: each state is assigned its own truth space (a complete sublattice of a common base lattice), so that, for example, a Boolean state, a three-valued state and a paraconsistent state can coexist in the same transition structure. Modalities then relate states across these different logics.

The **MLML Editor** is a graphical application that makes the MLML institution operational. It supports the main institutional ingredients (signatures, signature morphisms, frames, models, model morphisms and reducts), their visualisation, and the evaluation of modal formulas at a state or globally.

The tool is split into two parts:

- a **computational core**, a Python library implementing the MLML semantics;
- a **graphical interface**, built with PyQt6. Hasse diagrams, frames and models are drawn with NetworkX and Matplotlib.

Every object (lattices, signatures, frames, models, morphisms) is stored as JSON, so a workspace can be saved and restored across sessions without loss of information.

## Features

### 1. Truth Spaces

- **Finite Lattices:** Create a lattice by typing its elements, selecting the pairs that belong to the order relation, and defining the **implication** and **negation** operations in dedicated tabs. The tool checks that the order defines a lattice before saving it.
- **Filtered Lattices:** Choose a base lattice and select a filter (the set of designated values). The tool checks that the selection is upward closed. From then on, every computed value is reported together with whether it belongs to the filter (_In Filter_).
- **Many Lattices:** Choose a base filtered lattice and an interpretation mode (see below). The tool lists all subsets that form complete sublattices of the base lattice; select the ones to include and optionally rename them (the name of the base lattice itself is fixed).
- **Down / Up interpretation:** The mode determines how the negation and implication of each complete sublattice are obtained from the base lattice. _Down_ is the conservative interpretation and _Up_ the liberal one.
- **Hasse Diagrams:** Visualise the order of any lattice or sublattice with **Show Hasse Diagram**.

### 2. Institutional Ingredients

Each ingredient has an entry in the **New** menu and a category in the project explorer. Creation windows only offer objects that already exist (for instance, a model can only be built from an existing frame and many lattice).

- **Signatures:** A name, a comma-separated list of propositions and a comma-separated list of actions.
- **Signature Morphisms:** Select a source and a target signature and map each proposition and each action.
- **Kripke Frames:** Over a signature, define the states (each with a long name and a short name of at most five characters), the initial state, and one accessibility relation per action, ticked in a relation matrix. **Show Frame** draws the frame, with the initial state in red.
- **Models:** Equip a frame with a complete sublattice for each state and a valuation for each proposition. Only values in the sublattice of the state are offered, so the valuation is consistent by construction.
- **Frame Morphisms and Model Morphisms:** Choose source and target, and define the function on states. The tool checks preservation of the initial state and of the transitions and, for models, that each state keeps its sublattice. **Show Structure Morphism** draws the source and the target with the mapping between them.
- **Reducts:** Given a signature morphism and a model over its target signature, compute the reduct model over the source signature.

### 3. Local and Global Satisfaction

The formula interpreter is in the lower-right panel. Formulas are typed or composed with the symbol buttons, and malformed input is reported.

1. Select a **model** and a **state**.
2. Choose the **Down** or **Up** interpretation.
3. Compute either:
   - **Local Satisfaction:** the value of the formula at the selected state;
   - **Global Satisfaction:** the meet of the values of the formula in all states (the value at every state is also listed).

Supported constructs:

- **Propositions** of the model's signature.
- **Modal:** Box (`[a]`) and Diamond (`<a>`), where `a` is an action of the signature.
- **Lattice connectives:** Meet (`&`), Join (`|`), Implication (`->`), Negation (`~`).
- **Constants:** Top and Bottom.

The result is shown as a value of the lattice, together with whether it is a designated value (_In Filter_).

### 4. User Interface

The main window has three areas that follow the workflow of model development, from abstract structures (lattices, signatures) to concrete models and formula verification:

- **Project Explorer (left):** lists the objects by category (Signatures, Signature Morphisms, Lattices, Filtered Lattices, Many Lattices, Kripke Frames, Models, Kripke Frame Morphisms, Model Morphisms).
- **Object Details (upper right):** shows the details of the selected object and offers its visualisations (**Show Hasse Diagram**, **Show Frame**, **Show Structure Morphism**).
- **Formula Interpreter (lower right):** see above.

The menu bar covers the whole lifecycle of an object:

- **New:** create objects.
- **Load / Delete:** manage saved objects.
- **See:** show available objects.
- **View:** switch between Light and Dark themes.
- **Help:** definitions, a notation reference and diagnostic logs.

## Installation

### Requirements

- Python 3.11.2 or higher
- PyQt6 version 6.10.2 or higher (see Install Dependencies)
- NetworkX and Matplotlib (see Install Dependencies)

### Install Dependencies

Choose one of the following to install the dependencies:

#### Windows (pip)

Run the following command to install the required libraries:

```bash
pip install PyQt6 networkx matplotlib
```

Navigate to the project directory and execute the main application script:

```bash
python app.py
```

#### Windows (scripts to configure the environment, install python, if needed, create venv and install all dependencies):

Run the following command to install the required libraries:

```bash
setup.bat:
@echo off
setlocal

:: Verifies if python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python not found. Trying to install Python 3.12 via winget...
    winget install -e --id Python.Python.3.12
    echo Please, close the terminal and open it again to update the PATH.
    pause
    exit
)

echo Creating virtual environment...
python -m venv .venv

echo Activating virtual environment...
call .venv\Scripts\activate

echo Installing dependencies...
python -m pip install --upgrade pip
pip install PyQt6 networkx matplotlib

echo.
echo Done! To run the app, use: python app.py
pause
```

#### Linux (scripts to configure the environment, install python, if needed, create venv and install all dependencies):

Run the following command to install the required libraries:

```bash
setup.sh:

#!/bin/bash

detect_distro() {
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        echo $ID
    else
        echo "unknown"
    fi
}

DISTRO=$(detect_distro)
echo "Distribution detected: $DISTRO"

case $DISTRO in
    ubuntu|debian|pop|linuxmint|kali)
        echo "Configuring to Debian/Ubuntu..."
        sudo apt update
        sudo apt install -y python3.12 python3.12-venv python3-pip \
        libxcb-cursor0 libxkbcommon-x11-0 libxcb-icccm4 libxcb-image0 \
        libxcb-keysyms1 libxcb-render-util0 libxcb-xinerama0 libxcb-xinput0
        PYTHON_BIN="python3.12"
        ;;

    fedora)
        echo "Configuring to Fedora..."
        sudo dnf install -y python3.12 python3-pip \
        libxcb libxkbcommon-x11 qt6-qtbase-gui
        PYTHON_BIN="python3.12"
        ;;

    arch|manjaro)
        echo "Configuring to Arch Linux..."
        sudo pacman -Syu --noconfirm python python-pip \
        libxcb libxkbcommon-x11
        PYTHON_BIN="python"
        ;;

    alpine)
        echo "Configurando para Alpine..."
        # Note: PyQt6 in Alpine could be hard due to musl library
        sudo apk add python3 py3-pip libxcb libxkbcommon
        PYTHON_BIN="python3"
        ;;

    *)
        echo "Distribution not suported automatically."
        echo "Please, install the Python 3.12 and the XCB libraries manually."
        exit 1
        ;;
esac

if [ ! -d ".venv" ]; then
    echo "Creating virtual environment with $PYTHON_BIN..."
    $PYTHON_BIN -m venv .venv
else
    echo "Virtual environment already exists."
fi

echo "Activating virtual environment and installing Python dependencies ..."
source .venv/bin/activate

pip install --upgrade pip
pip install PyQt6 networkx matplotlib

echo -e "\n===================================================="
echo "Done!"
echo "To run the app:"
echo "1. Activate the venv: source .venv/bin/activate"
echo "2. Execute: python app.py"
echo "===================================================="
```

#### MacOs (pip)

Run the following command to install the required libraries:

```bash
python3 -m venv .venv

source .venv/bin/activate

python3 -m pip install --upgrade pip

python3 -m pip install PyQt6 networkx matplotlib
```

Navigate to the project directory and execute the main application script:

```bash
python3 app.py
```

#### If the previous steps failed to install PyQt6, follow the instructions in:

[Link to PythonGUIs website](https://www.pythonguis.com/pyqt6/)

## Contact

Created by [Rodrigo Alves](mailto:rodrigoalves@ua.pt), [Manuel Martins](mailto:martins@ua.pt), [Alexandre Madeira](mailto:madeira@ua.pt)
Feel free to reach out with questions or suggestions.
