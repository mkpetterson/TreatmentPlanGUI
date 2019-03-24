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
import random
import dicom as pd

from ftplib import FTP
import paramiko

  
def gen_dicom(fname,lname,ct_dir):
    """Generates a session by cloning phantom selected in GUI"""
    
    #Assign name, ID, and make directory for new session
    p_name = lname + '^' + fname
    p_id = fname + '_' + ''.join(random.choice('1234567890ABCDEF') for i in range(3))
    new_dir = fname+'_'+lname
    os.mkdir(new_dir)
    
    #Do the work
    os.system("python cpydcm2_36_mkp.py -i "+ct_dir+" -o ./"+new_dir+" -cconv -attr \"PatientName : "+p_name+", PatientID : "+ p_id+", PatientBirthDate : 19830104, PatientSex : F\"")
    done_msg = "Data saved to directory: %s " % new_dir
    new_dir = new_dir + '/'
        
    return new_dir, done_msg
    
    
def replace_iso_gantry_spots(pdir,x=None,y=None,z=None,angle=None,fgs=None,ibs=None):
    
    rtip = [f for f in os.listdir(pdir) if 'RTIP' in f and '.dcm' in f.lower()][0]
    data = pd.read_file(pdir+rtip)
    
    num_beams = len(data.IonBeamSequence)
    
    if x and y and z:
        for i in range(num_beams):
            data.IonBeamSequence[i].IonControlPointSequence[0].IsocenterPosition[0] = str(x)
            data.IonBeamSequence[i].IonControlPointSequence[0].IsocenterPosition[1] = str(y)
            data.IonBeamSequence[i].IonControlPointSequence[0].IsocenterPosition[2] = str(z)
    else:
        pass
    
    if angle:
        for i in range(num_beams):
            data.IonBeamSequence[i].IonControlPointSequence[0].GantryAngle = str(angle)
    else:
        pass
    
    #Copy fraction group sequence and ion beam sequence if we are making a new plan
    if fgs and ibs:
        data.FractionGroupSequence = fgs
        data.IonBeamSequence = ibs
    else:
        pass
    
    #Make sure other items are dicom-compliant (labels/names/geometry/)
    data.RTPlanLabel = 'label'
    data.RTPlanName = 'name'
    data.RTPlanGeometry = 'PATIENT'
    data.FractionGroupSequence[0].FractionGroupNumber = '1'
    
    #Check the setup beam
    if data.IonBeamSequence[0].IonControlPointSequence[0].NominalBeamEnergy == '0':
        data.IonBeamSequence[0].TreatmentDeliveryType = 'SETUP'
        data.IonBeamSequence[0].IonControlPointSequence[0].PatientSupportAngle = '90'
    
    #Write data to file
    pd.write_file(pdir+rtip[0],data)
    
    
def upload(pdir):
    """Uploads dicom session (CT set/RTIP/RTSS/PSSR/RTBDI)"""
    
    #Get folder to copy over
    directory_name = pdir
    files = [f for f in os.listdir(path=directory_name)]
    
    #Get environment
    f = open('credentials.txt', 'r')
    credentials = f.readlines()
    pacs = credentials[0].replace('\n','').split(' ')
    wb = credentials[1].split(' ')
    pacs_info = {"address": pacs[0], "username": pacs[1], "password": pacs[2]}
    wb_info = {"address": wb[0], "username": wb[1], "password": wb[2], "port": wb[3]}   
        

    #Connect to host/PACS computer
    try:
        ssh_client_pacs = paramiko.SSHClient()
        ssh_client_pacs.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh_client_pacs.connect(hostname=pacs_info['address'], username=pacs_info['username'], password=pacs_info['password'])
        print("Connected to PACS host")
        
    except:
        msg = "Could not connect to network."
        return msg
        
    #Upload data to host
    try:
        stdin,stdout,stderr = ssh_client_pacs.exec_command('cd sessions; mkdir %s; ls' % directory_name)
        print("Directory created. Starting upload")
    
        #Uploading directory - using recursive file upload
        for f in files:
            ftp_client = ssh_client_pacs.open_sftp()
            ftp_client.put(os.path.join(directory_name,f),'sessions/'+directory_name+f)
            ftp_client.close()
    
    except:
        msg = "Could not upload files"
        return msg
        
    #Transmit to PACS
    print("Transmitting to PACS")
    try:
        stdin,stdout,stderr = ssh_client_pacs.exec_command('./upload_session_data_to_pacs.sh ~/sessions/'+directory_name)
        print(stdout.readlines())
        print(directory_name)
        ssh_client_pacs.close()
    except:
        msg = "Could not transmist files to PACS"
        return msg
    
    #FTP into second VM
    try:    
        print('FTP into WB computer')
        ftp_client = FTP()
        ftp_client.connect(wb_info['address'], wb_info['port'])
        ftp_client.login(wb_info['username'], wb_info['password'])
        #ftp_client.retrlines('LIST')
    except:
        msg = "Could not connect to WB computer"
        return msg
    
    #Copy dicom files over one at a time (only works for dicom. Use storlines for text files)
    try:
        ftp_client.mkd(directory_name)
        print("Copying dicom files to WB server")
        for f in files:
            with open(os.path.join(directory_name,f),'rb') as dcm_file:
                ftp_client.storbinary('STOR %s' % os.path.join(directory_name,f), dcm_file)
        ftp_client.quit()
        print("Finished copying files to remote server")
    except:
        msg = "Could not transmit files to WB computer"
        return msg
    
    msg = "Everything worked, surprisingly"
    return msg