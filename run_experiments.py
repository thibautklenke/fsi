import xml.etree.ElementTree as ET

import subprocess
import time

from itertools import product

def run_program():
    subprocess.run(["mpirun", "-np", "4", "./build/step-fsi"], stdout=subprocess.DEVNULL)

def update_xml_params(xml_path, alpha, beta, mesh, tmax):
    tree = ET.parse(xml_path)
    root = tree.getroot()

    precond_list = root.find(".//ParameterList[@name='Preconditioner List']")
    if precond_list is not None:
        for param in precond_list.findall("Parameter"):
            if param.attrib.get('name') == "Alphalog":
                param.set('value', str(alpha))
            elif param.attrib.get('name') == "Betalog":
                param.set('value', str(beta))

        geo_op = precond_list.find("ParameterList[@name='GeometricOverlappingOperator']")
        if geo_op is not None:
            update_scalar = geo_op.find("ParameterList[@name='Update Scalar Multipliers']")
            if update_scalar is not None:
                for param in update_scalar.findall("Parameter"):
                    if param.attrib.get('name') == "Alpha":
                        param.set('value', str(alpha))
                    elif param.attrib.get('name') == "Beta":
                        param.set('value', str(beta))
    
    mesh_list = root.find(".//ParameterList[@name='Mesh and Geometry']")
    if mesh_list is not None:
        for param in mesh_list.findall("Parameter"):
            if param.attrib.get('name') == "Number of refinements":
                param.set('value', str(mesh))
    
    time_list = root.find(".//ParameterList[@name='Timestepping schemes']")
    if time_list is not None:
        for param in time_list.findall("Parameter"):
            if param.attrib.get('name') == "max no timesteps":
                param.set('value', str(tmax))
        
    
    tree.write(xml_path)

i = 0
n = 1

alpha_vals_10 = [round(x / 10 - 10, 2) for x in range(201)]
alpha_vals = [round(x / 2 - 10, 2) for x in range(41)]
mesh_vals = [round(x, 1) for x in range(3, 8)]


for alpha, beta, mesh in list(product(alpha_vals, alpha_vals, mesh_vals)):

    print(alpha, beta, mesh)

    update_xml_params("step-fsi.xml", alpha, beta, mesh)

    # Run n times for more accurate measurements
    for _ in range(n):
        run_program()
        i += 1
    
    if i % 100 == 0:
        print(f"Finished {i} runs")


