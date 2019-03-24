# -*- coding: utf-8 -*-
"""
Created on Thu Nov  1 11:55:58 2018

GUI for treatment map modification/creation for different phantom CT sets. 
Roughly organized into three panes:
    
    Pane 1: Select phantom CT set and ammend isocenter/gantry angles
    Pane 2: Show specs for current treatment and allow browsing for new treatment
    Pane 3: Spot maps of current or proposed treatment. Top: spot map. Bottom: Bragg peaks 


@author: mpetterson
"""

import sys, os
import numpy as np
import Generate_RTIP_func1 as gen1
import Generate_RTIP_func2 as gen2
import Generate_RTIP_func3 as gen3

from PyQt5.QtWidgets import QLabel, QTextEdit, QMainWindow, QAction, QLineEdit, qApp, QSlider, QPushButton, QFormLayout
from PyQt5.QtWidgets import QVBoxLayout, QApplication, QWidget, QCheckBox, QRadioButton, QHBoxLayout, QFileDialog, QComboBox
from PyQt5.QtCore import Qt

import matplotlib
matplotlib.use("Qt5Agg")
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure



class Window(QWidget):
    
    def __init__(self):
        super().__init__()
        
        self.init_ui()
        
    def init_ui(self):
 
        mainLayout = QVBoxLayout()
        self.setGeometry(600,200,1000,800)
        self.flag = False
        
        self.done_red = 'font-size: 18px; color: rgb(200,50,50)'
        self.done_blue = 'font-size: 18px; color: rgb(50,50,200)'
        self.done_green = 'font-size: 20px; color: rgb(50,200,100)'

        #H box for vertical panes        
        paneLayout = QHBoxLayout()
        paneWidget = QWidget()
        paneWidget.setLayout(paneLayout)

        doneLayout = QHBoxLayout()
        doneWidget = QWidget()
        doneWidget.setLayout(doneLayout)
        
        #First vertical pane: Input layout
        self.inputLayout = QVBoxLayout()
        self.inputLayout.setAlignment(Qt.AlignTop)
        inputWidget = QWidget()
        inputWidget.setFixedWidth(250)
        inputWidget.setLayout(self.inputLayout)
        
        #Drop down menu for phantom plans
        lbl = QLabel("Select Phantom Plan")   
        lbl.setFixedHeight(20)
        dropdown = QComboBox(self)
        dropdown.setFixedHeight(20)
        self.phantom_path = './MGH_Phantoms/'
        phantoms = gen1.get_phantom_list(self.phantom_path)
        dropdown.addItem('Select Phantom')
        for name in phantoms:           
            dropdown.addItem(name)

        dropdown.activated[str].connect(self.onActivated)
        self.inputLayout.addWidget(lbl)
        self.inputLayout.addWidget(dropdown)
        
        #Text box for patient name
        name_lbl1 = QLabel("Enter Patient First Name (required)")
        name_lbl2 = QLabel("Enter Patient Last Name (required)")
        name_lbl1.setFixedHeight(20)
        name_lbl2.setFixedHeight(20)
        self.patientfirstname = QLineEdit()
        self.patientlastname = QLineEdit()
        
        self.inputLayout.addWidget(name_lbl1)
        self.inputLayout.addWidget(self.patientfirstname)
        self.inputLayout.addWidget(name_lbl2)
        self.inputLayout.addWidget(self.patientlastname)
        
        #Current Isocenter values
        self.currentiso_lbl = QLabel()
        self.currentiso_lbl.setFixedHeight(30)
        
        #Hbox for isocenter
        isoLayout = QHBoxLayout()
        isoWidget = QWidget()
        isoWidget.setFixedWidth(250)
        isoWidget.setLayout(isoLayout)
                        
        #Isocenter parameters
        lbl_iso = QLabel("Enter new isocenter values below")
        lbl_iso.setFixedHeight(20)
        lbl_x = QLabel("X (mm)")
        lbl_y = QLabel("Y (mm)")
        lbl_z = QLabel("Z (mm)")
        self.le_x = QLineEdit()
        self.le_y = QLineEdit()
        self.le_z = QLineEdit()
        
        self.inputLayout.addWidget(self.currentiso_lbl)
        self.inputLayout.addWidget(lbl_iso)
        
        isoLayout.addWidget(lbl_x)
        isoLayout.addWidget(self.le_x)
        isoLayout.addWidget(lbl_y)        
        isoLayout.addWidget(self.le_y)
        isoLayout.addWidget(lbl_z)
        isoLayout.addWidget(self.le_z)
        self.inputLayout.addWidget(isoWidget)
        
        #Gantry Angle
        gantry_lbl = QLabel("Gantry Angle")
        gantry_lbl.setFixedHeight(20)
        self.gantry = QLineEdit()
        self.inputLayout.addWidget(gantry_lbl)
        self.inputLayout.addWidget(self.gantry)
        
        #Generate new set and upload to WB
        new_lbl = QLabel("Click below to generate new phantom set")
        new_lbl.setFixedHeight(30)
        new_btn = QPushButton("Generate")
        new_btn.setFixedHeight(30)
        new_btn.setStyleSheet('font-size: 18px')
        new_btn.clicked.connect(self.generate_dicom)
        self.upload_btn = QPushButton("Upload to WB")
        self.upload_btn.setFixedHeight(30)
        self.upload_btn.setStyleSheet(self.done_red)
        self.upload_btn.clicked.connect(self.upload_to_WB)
        
        self.inputLayout.addWidget(new_lbl)
        self.inputLayout.addWidget(new_btn)
        self.inputLayout.addWidget(self.upload_btn)

                
        #Second vertical pane
        self.rtipLayout = QVBoxLayout()
        self.rtipLayout.setAlignment(Qt.AlignTop)
        rtipWidget = QWidget()
        rtipWidget.adjustSize()
        rtipWidget.setLayout(self.rtipLayout)
        
        #Current spot map
        self.spot_lbl = QLabel("Spot map specs")
        self.spot_lbl.setStyleSheet("font-size : 12px")
        self.spot_lbl.setFixedHeight(20)
        self.spot_stats = QLabel()
        self.spot_stats.setWordWrap(True)
        self.spot_stats.adjustSize()

        # Button to load new spot map        
        spot_lbl2 = QLabel("Click below to browse for new spot map")
        spot_lbl2.setStyleSheet("font-size : 12px")
        spot_lbl2.setFixedHeight(30)
        dataLoadBtn = QPushButton("Browse")
        dataLoadBtn.setFixedHeight(30)
        dataLoadBtn.clicked.connect(self.load_spot_map)        
        self.chkbox = QCheckBox("Check box to use loaded csv file")
        self.chkbox2 = QCheckBox("Check box if the first beam is the setup beam")
       
        self.rtipLayout.addWidget(self.spot_lbl)  
        self.rtipLayout.addWidget(self.spot_stats)
        self.rtipLayout.addWidget(spot_lbl2)
        self.rtipLayout.addWidget(dataLoadBtn)
        self.rtipLayout.addWidget(self.chkbox)
        self.rtipLayout.addWidget(self.chkbox2)
                
        # Add space for spot map statistics
        self.loadstatus = QLabel()
        self.loadstatus.setFixedHeight(40)
        
        self.csv_stats = QLabel()
        self.csv_stats.setAlignment(Qt.AlignTop)
        self.csv_stats.setWordWrap(True)
        
        self.rtipLayout.addWidget(self.loadstatus)
        self.rtipLayout.addWidget(self.csv_stats) 
        
        
        #Third pane
        plotWidget = QWidget()
        plotLayout = QVBoxLayout()
        
        #Make figures and navi toolbar
        self.fig = Figure()
        self.canvas = FigureCanvas(self.fig)
        self.axes11 = self.fig.add_subplot(2,1,1)
        self.axes12 = self.fig.add_subplot(2,1,2)
        self.fig.tight_layout()
        
        navi_toolbar = NavigationToolbar(self.canvas,plotWidget)
        plotLayout.addWidget(navi_toolbar)
        plotLayout.addWidget(self.canvas,Qt.AlignHCenter)

        #Done status        
        self.done_lbl = QLabel()
        self.done_lbl.setStyleSheet(self.done_green)
        self.done_lbl.setAlignment(Qt.AlignHCenter)
        doneLayout.addWidget(self.done_lbl)
        
        #Add widgets to main window
        paneLayout.addWidget(inputWidget)
        paneLayout.addWidget(rtipWidget)
        paneLayout.addLayout(plotLayout)

        mainLayout.addWidget(paneWidget)
        mainLayout.addWidget(doneWidget)
        self.setLayout(mainLayout)
        
        self.show()
                       
                
    def onActivated(self,text):
        
        #Update labels
        string = "Spot Map Specs: %s" % text
        self.spot_lbl.setText(string)
        self.spot_lbl.adjustSize()

        #Pull in RTIP from phantom set
        self.phantom_dir = self.phantom_path + text + '/'
        
        #Get isocenter, gantry, and spot map
        self.isocenter, self.gantry_angle, self.msg = gen1.get_isocenter(self.phantom_dir)
        specs, mapy = gen1.plot_rtip_map(self.phantom_dir)

        self.currentiso_lbl.setText("Current isocenter position: %s" % self.isocenter)
        with open(specs, 'r') as f:
            text = f.read()
            self.spot_stats.setText(text)
            self.spot_stats.setAlignment(Qt.AlignTop)
        f.close()
        
        #Plot spot map 
        self.axes11.clear()
        self.axes12.clear()
        self.axes11.scatter(mapy[:,1], mapy[:,2])
        self.axes11.set_title("Spot Map")
        self.axes11.set_xlabel("X(mm)")
        self.axes11.set_ylabel("Y(mm")
        self.fig.tight_layout()
        self.canvas.draw()
        

    def load_spot_map(self):
        
        #Clear plots
        self.axes11.clear()
        self.axes12.clear()
        
        #Open file location        
        dlg = QFileDialog()
        dlg.setFileMode(QFileDialog.ExistingFile)
        self.spotmap = dlg.getOpenFileName(self, 'Select Spot Map CSV', '~./')
        self.current_wdir = os.path.dirname(self.spotmap[0])
       
        #Get data
        csv_msg = gen2.csv_check(self.spotmap[0])
        self.done_lbl.setText(csv_msg)
        self.name, self.data, dose_array = gen2.dose_estimator(self.spotmap[0])
        self.E_list = dose_array[:,0]
        dose = dose_array[:,1]
                
        #Update text box with statistics
        with open(self.name + '.txt', 'r') as f:
            file_text = f.read()
            self.csv_stats.setText(file_text)
            self.csv_stats.setAlignment(Qt.AlignTop)
        f.close()

        #Plot spot map 
        self.axes11.scatter(self.data[:,1], self.data[:,2])
        self.axes11.set_title("Spot Map")
        self.axes11.set_xlabel("X(mm)")
        self.axes11.set_ylabel("Y(mm")
        
        #Plot Bragg peaks. FIX TO MAKE MORE ROBUST WITH VARYING STEP SIZE
        BP_sum = np.zeros((200))#dose at depth, column for each Bragg peak
        for n,e in enumerate(self.E_list):
            energy_vs_depth = gen2.E_depth(e)
            self.axes12.plot(energy_vs_depth[:,0], energy_vs_depth[:,2]*dose[n], linewidth=1)
            
            # Find max depth for setting x-axis max
            if n==0:
                x_max = energy_vs_depth[-1,0]
            
            #sum bragg peaks
            for m in range(energy_vs_depth.shape[0]):
                BP_sum[m] += energy_vs_depth[m,2]*dose[n]
                

        # Plot data
        self.axes12.plot(np.arange(0,len(BP_sum)/4,0.25), BP_sum, color='black')
        self.axes12.set_xlim(0, x_max+2)
        self.axes12.set_title("Approximate Bragg Peaks (normalized to dose)")
        self.axes12.set_xlabel("Depth/Z (cm)")
        self.axes12.set_ylabel("Dose (arb)")
        self.fig.tight_layout()
        self.canvas.draw()

        #Print values of interest
        self.loadstatus.setText("File loaded:\n%s" % self.name)
        self.loadstatus.setAlignment(Qt.AlignTop)
        
   
    def generate_dicom(self):
     
        #Generate new RTIP from csv
        if self.chkbox.isChecked():
            csv_file = self.spotmap[0]
            if self.chkbox2.isChecked():
                setup = True
            else:
                setup = False
            
            try:
                ct_directory,fgs,ibs = gen2.gen_rtip(csv_file, self.phantom_dir,setup)
                print(ct_directory)

            except:
                self.done_lbl.setText("Could not process csv. Please check that format is correct")
                
        #If no new csv, use old treatment plan
        else:
            try:
                ct_directory = self.phantom_dir
                fgs = None
                ibs = None
            except:
                self.done_lbl.setText("No phantom directory selected!")
                return 0
            
        #Name
        fname = self.patientfirstname.text()
        lname = self.patientlastname.text()
        
        #Create new dicom set and print done message
        try:
            self.new_dir, done_msg = gen3.gen_dicom(fname,lname,ct_directory)
            self.upload_btn.setStyleSheet(self.done_green)
            self.flag = True
        except:
            done_msg = "Could not generate new dicom set. Check Python log"
            
        self.done_lbl.setText(done_msg)
        
        #If text boxes filled, use those values, otherwise copy isocenter only from selected phantom
        if self.le_x.text() or self.gantry.text():
            gen3.replace_iso_gantry_spots(self.new_dir,
                                   self.le_x.text(),self.le_y.text(),self.le_z.text(),
                                   self.gantry.text(),fgs,ibs)
        else:
            self.gantry_angle = None
            gen3.replace_iso_gantry_spots(self.new_dir,
                                   self.isocenter[0],self.isocenter[1],self.isocenter[2],
                                   self.gantry_angle,fgs,ibs)

        
    def upload_to_WB(self):
        if self.flag == False:
            self.done_lbl.setText("Cannot upload to Whiteboard")
        else:
            upload_msg = gen3.upload(self.new_dir)
            self.done_lbl.setText(upload_msg)

        
#This bit to prevent kernal from dying. Taken from stack overflow. Works only part of the time
if __name__ == '__main__':

    if not QApplication.instance():
        app = QApplication(sys.argv)
    else:
        app = QApplication.instance() 
        
        
a_window = Window() #Now create instance of window class
sys.exit(app.exec_())
        
        
                
                
                
                
                