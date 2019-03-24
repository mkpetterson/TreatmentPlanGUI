# -*- coding: utf-8 -*-
"""
Created on Thu Nov  1 14:27:51 2018

Functions separated into:
    1. Pull out data from current phantom dicom set
    2. (Optional) pulls data from new csv and generates patient rtip and rtbdi 
    3. Generate new treatment planning set and upload to virtual machines


@author: mpetterson
"""

import os
import dicom as pd
import numpy as np


def dose_calc(energy):
    dose_per_Gp = energy*(.0001602)
    return dose_per_Gp

def ellipse_vol(a,b,c):
    a = int(a)
    b = int(b)
    c = int(c)
    return 4.18*a*b*c

def dE_dx(E0):
    dEdx = 205.4*np.power(E0,-0.722) #initial value in MeV/cm
    return dEdx


def csv_check(file):
    
    #Import data and exclude empty rows
    data = np.genfromtxt(file, delimiter=',', filling_values=np.nan)
    data = data[~np.isnan(data).any(axis=1)]
    rows,cols = data.shape
    
    if cols != 9:
        csv_msg = 'CSV doesn\'t have 9 columns. Please check'
    else:
        csv_msg = "CSV looks ok! It has %s rows." % rows
   
    return csv_msg   

#Change to use data frame?
def E_depth(E0):
    """Returns array of energy of proton and energy deposited vs depth of penetration for a given initial energy, E0"""
    
    #Initiate lists starting at depth = 0
    E_vs_depth = [E0]
    depth_list = [0]
    dose_list = [0]
    step = 0.25 #cm
    depth = step    
    
    #Create energy loss vs depth 
    for i in range(500):
        E_next = E_vs_depth[-1] - dE_dx(E_vs_depth[-1])*step
        
        # Append lists of proton energy, depth, and dose deposited
        if E_next > 0:    
            dose_list.append(dE_dx(E_vs_depth[-1])*step)
            E_vs_depth.append(E_next)
            depth_list.append(depth)
            depth += step
            
        # Add final values to end of list and break loop    
        else:
            dose_list.extend((E_vs_depth[-1],0))
            E_vs_depth.extend((0,0))
            depth_list.extend((depth, depth+step))
            break
        
    #Turn into numpy arrays    
    depth_list = np.asarray(depth_list)
    E_vs_depth = np.asarray(E_vs_depth)
    dose_list = np.asarray(dose_list)
        
    energy_vs_depth = np.column_stack((depth_list,E_vs_depth,dose_list))
                
    return energy_vs_depth
      
#Need to clean up and make more robust
def dose_estimator(file):
    """Estimates the dose deposited from a given treatment spot map"""
   
    #Open file and replace empty rows with 'nan' values 
    data = np.genfromtxt(file, delimiter=',', filling_values=np.nan, usecols=(1,4,5,6))
    data = data[~np.isnan(data).any(axis=1)] 
    name = os.path.basename(file)

    #Initiate Values    
    energy_current = data[0,0]
    num_spots,foo = data.shape
    dose_Gp = 0
    num_layers = 1
    dose_array = [] #2 column array of proton energy and proton dose
        
    #loop through files and calculate cumulative dose
    for i in range(num_spots):
        energy = data[i,0]
            
       #if we are in new layer
        if energy != energy_current:
            num_layers += 1
            dose_array.append([data[i-1,0],dose_Gp])
            dose_Gp = data[i,3] 
            energy_current = energy
            
        #if we are at last spot
        elif i == (num_spots-1): 
            dose_Gp += data[i,3]
            dose_array.append([data[i-1,0],dose_Gp])
            
        else:
            dose_Gp += data[i,3]
   
    #Organize dose array, total protons, energies
    dose_array = np.asarray(dose_array)
    tot_p = np.sum(dose_array[:,1])
    energies = np.unique(dose_array[:,0])

    #Make strings for output
    str1 = 'Num Spots = ' + str(num_spots)
    str2 = 'Num Layers = ' + str(num_layers)
    str3 = 'Total Gp = ' + str(tot_p)
    str4 = "Unique energies = " + str(energies)
    
    #save ALL THE DATA!!
    f = open(name+'.txt', 'wb') 
    np.savetxt(f,(str1, str2, str3, str4), fmt='%s', delimiter=' ')
    f.close()

    return name, data, dose_array        


def gen_rtip(csv_filename, phantom_dir,setup=False):
    
    #Make clincial dicom set of spot map
    os.system("python csv2xml_Clinical_py36.py " + csv_filename)
    
    #Find the generated rtip 
    rtip = [f for f in os.listdir() if 'RTIP.dcm' in f][0]
    ct_dir = phantom_dir + '/'

    #Extract Fraction Group Sequence and Ion Beam Sequence
    data_copyinfo = pd.read_file(rtip)
    fgs = data_copyinfo.FractionGroupSequence
    ibs = data_copyinfo.IonBeamSequence
    
    #Make beam 0 the setup beam
    if setup:
        ibs[0].TreatmentDeliveryType = 'SETUP'
        ibs[0].IonControlPointSequence[0].PatientSupportAngle = '90'
                
    #Delete extra dicom/xml files from the working directory
    [os.remove(f) for f in os.listdir() if '.dcm' in f.lower()]
    [os.remove(f) for f in os.listdir() if '.xml' in f.lower()]
    
    return ct_dir, fgs, ibs
