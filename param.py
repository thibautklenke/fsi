import xml.etree.ElementTree as ET

import subprocess
import time
import os

import numpy as np
import pandas as pd

from itertools import product

def run_program(exec_path: str, n_procs: int = 4) -> None:
    """Executes the dealii program
    
    Parameters
    ----------
    exec_path : str
        Path of the program to execute
    n_procs : int, Default = 4
        Number of ranks to use.
    """
    subprocess.run(["mpirun", "-np", str(n_procs), exec_path], stdout=subprocess.DEVNULL)

def update_xml_params(xml_path: str, alpha: float, beta: float, mesh: int, tmax: int) -> None:
    """Updates a given xml file.

    Parameters
    ----------
    xml_path : str
        Path of the xml file to update.
    alpha : float
        alpha parameter to update.
    beta : float
        beta parameter to update.
    mesh : int
        How many mesh refinements to use.
    tmax : int
        If the problem is time-dependent: Maximum number of time steps
    """
    tree = ET.parse(xml_path)
    root = tree.getroot()

    # Update preconditioner
    precond_list = root.find(".//ParameterList[@name='Preconditioner List']")
    if precond_list is not None:
        geo_op = precond_list.find("ParameterList[@name='GeometricOverlappingOperator']")
        if geo_op is not None:
            update_scalar = geo_op.find("ParameterList[@name='Update Scalar Multipliers']")
            if update_scalar is not None:
                for param in update_scalar.findall("Parameter"):
                    if param.attrib.get('name') == "Alpha":
                        param.set('value', str(alpha))
                    elif param.attrib.get('name') == "Beta":
                        param.set('value', str(beta))
    
    # Update mesh
    mesh_list = root.find(".//ParameterList[@name='Mesh and Geometry']")
    if mesh_list is not None:
        for param in mesh_list.findall("Parameter"):
            if param.attrib.get('name') == "Number of refinements":
                param.set('value', str(mesh))
    
    # Update tmax
    time_list = root.find(".//ParameterList[@name='Timestepping schemes']")
    if time_list is not None:
        for param in time_list.findall("Parameter"):
            if param.attrib.get('name') == "max no timesteps":
                param.set('value', str(tmax))
        
    
    tree.write(xml_path)

def grid_search(
    xml_path: str,
    csv_path: str,
    exec_path: str,
    alpha_vals: np.ndarray,
    beta_vals: np.ndarray,
    grid: int,
) -> tuple[float, float]:
    """Perform a grid search over alpha and beta, return best parameters.

    Parameters
    ----------
    xml_path : str
        Path to the XML configuration file.
    csv_path : str
        Path to the CSV file where iteration counts are written.
    exec_path : str
        Path of the program to execute
    alpha_vals : np.ndarray
        Sequence of alpha values to test.
    beta_vals : np.ndarray
        Sequence of beta values to test.
    grid : int
        Number of mesh refinements to use during grid search.

    Returns
    -------
    tuple[float, float]
        The best (alpha, beta) parameters that minimize the iteration count.
    """
    for alpha, beta in product(alpha_vals, beta_vals):
        update_xml_params(xml_path, alpha, beta, grid, -1)
        run_program(exec_path)

    print("Finished grid search")

    df = pd.read_csv(csv_path).drop_duplicates()
    min_entry = df.iloc[df["iter"].argmin()]

    best_alpha = float(min_entry["alpha"])
    best_beta = float(min_entry["beta"])
    print(f"Found alpha = {best_alpha}, beta = {best_beta}")

    return best_alpha, best_beta

def main() -> None:
    # Parameter ranges
    alpha_vals = np.linspace(-10, 10, 10)
    beta_vals = np.linspace(-10, 10, 10)

    # Paths
    xml_path = "step-fsi.xml"
    csv_path = "iters.csv"
    exec_path = "build/step-fsi"

    # Create csv
    if os.path.exists(csv_path):
        os.remove(csv_path)

    with open(csv_path, "w") as f:
        f.write("alpha,beta,iter\n")

    # Grid search on coarse grid
    best_alpha, best_beta = grid_search(xml_path, csv_path, exec_path, alpha_vals, beta_vals, grid=3)

    # Run final simulation with best params on fine grid
    update_xml_params(xml_path, best_alpha, best_beta, mesh=7, tmax=-1)
    run_program(exec_path)
    print("Final run completed")


if __name__ == "__main__":
    main()