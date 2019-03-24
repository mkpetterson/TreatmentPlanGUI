# -*- coding: utf-8 -*-
"""
Created on Thu Jan  3 14:35:01 2019

@author: mpetterson
"""


import os
import paramiko
from ftplib import FTP


def upload(pdir):
    """Uploads entire treatment session to both PACS and server. Must be onsite to work"""
    
    #Select folder to copy over
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