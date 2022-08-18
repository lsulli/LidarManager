# -*- coding: utf-8 -*-
"""
/***************************************************************************
 LidarManager
                                 A QGIS plugin
Manage LIDAR dataset in map canvas
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                              -------------------
        begin                : 2022-04-13
        git sha              : $Format:%H$
        copyright            : (C) 2022 by Lorenzo Sulli
        email                : lorenzo.sulli@gmail.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

import os
import time
import shutil
import webbrowser

from qgis import processing
from osgeo import gdal

from PyQt5 import uic
from PyQt5 import QtWidgets
from PyQt5 import QtCore
from PyQt5.QtWidgets import QMainWindow, QLabel
from PyQt5.QtWidgets import QGridLayout, QWidget, QApplication, QDesktopWidget

from qgis.core import QgsMapLayerProxyModel, QgsSettings, QgsCoordinateReferenceSystem, QgsProcessingFeedback
from qgis.core import QgsHillshadeRenderer, QgsMapLayer, QgsRasterLayer, QgsApplication, QgsMapLayerType, QgsProject

from qgis.gui import QgsEncodingFileDialog

# constant variable
USER_DIRECTORY = QgsApplication.qgisSettingsDirPath()  # save vrt file in user directory without user selection
MY_DEFAULT_DESTDIR = os.path.join(USER_DIRECTORY, 'processing/outputs/').replace("\\", "/")
MY_README_LINK = r'https://github.com/lsulli/LidarManagerPlugin/blob/main/README.md'

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'lidar_manager_dialog_base.ui'))

class LidarManagerDialog(QtWidgets.QDialog,FORM_CLASS):
    """ dialog class for LidarPlugin QGIS3 plugin """
    def __init__(self, iface, parent=None):
        """Constructor."""
        super(LidarManagerDialog, self).__init__(parent)
        self.iface = iface
        self.setupUi(self)
        self.encoding = None
        # move near top right of desktop screen
        qtRectangle = self.frameGeometry()
        TopRightPoint = QDesktopWidget().availableGeometry().topRight()
        qtRectangle.moveTopRight(TopRightPoint)
        qtRectangle.translate(-30,15)
        self.move(qtRectangle.topLeft())
        # constructor for LayerBox control
        self.LayerBox.setFilters(QgsMapLayerProxyModel.PolygonLayer)
        self.LayerBox.currentIndexChanged.connect(self.sel_epsg)
        self.LayerBox.currentIndexChanged.connect(self.field_select)
        # constructor for button
        self.loadactivelayer_btn.setText("<<") # some GUI variable not set in QT Designer
        self.loadactivelayer_btn.setToolTip("Load active layer")
        self.loadactivelayer_btn.clicked.connect(self.sel_active_layer)
        self.loadactivelayer_btn.clicked.connect(self.field_select)
        self.btn_addlidar.clicked.connect(self.load_lidar_from_til)
        self.btn_applytoselect.setToolTip("Apply hlsd to select")
        self.btn_applytoselect.clicked.connect(self.apply_az_elev_zfactor)
        self.btn_default_value_hlsd.clicked.connect(self.default_value_hlsd)
        self.btn_browse_dir.clicked.connect(lambda: self.browse_dir('copy_lidar'))
        self.btn_copy_lidar.clicked.connect(self.copy_lidar_from_layer)
        self.btn_vrt_from_toc.clicked.connect(self.vrt_from_toc)
        self.btn_create_tileindex.clicked.connect(self.create_til)
        self.btn_clean_log.clicked.connect(self.clear_log)
        self.cancelBtn.clicked.connect(self.reject)
        self.btn_chk_field.clicked.connect(self.check_path)
        self.btn_open_user_folder.clicked.connect(self.open_user_folder)
        self.btn_help.clicked.connect(self.open_readme_md)
        # constructor for check box
        self.epsgfield_ckb.stateChanged.connect(self.sel_epsg)
        self.ckb_setdefault.stateChanged.connect(self.initialize_widgets)
        # constructor for Dial, Slider and SPinBox for elevatione and azimut
        self.AzimutDial.valueChanged.connect(self.changeAzimutSpinBox)
        self.AzimutSpinBox.valueChanged.connect(self.changeAzimutDial)
        self.ElevationSlider.valueChanged.connect(self.changeElevationSpinBox)
        self.ElevationSpinBox.valueChanged.connect(self.changeElevationSlider)
        # constructor for QlineEdit
        self.destination_copy_dir.textChanged.connect(self.check_directory)

    def initialize_widgets(self, event):
        """Lock as default value the user input for Tile Index Layer 
        --------------------------"""
        self.textdisplay.clear()
        if self.chk_help.isChecked():
            self.textdisplay.setText('Help: ' + self.initialize_widgets.__doc__)
        
        if self.ckb_setdefault.isChecked():
            self.LayerBox.setEnabled(False)
            self.FieldPath_CBox.setEnabled(False)
            self.FieldEPSG_CBox.setEnabled(False)
            self.mQgsProjectionSelectionWidget.setEnabled(False)
            self.FieldEPSG_CBox.setEnabled(False)
            self.loadactivelayer_btn.setEnabled(False)
            self.epsgfield_ckb.setEnabled(False)
        else:
            self.LayerBox.setEnabled(True)
            self.FieldPath_CBox.setEnabled(True)
            self.FieldEPSG_CBox.setEnabled(True)
            self.LayerBox.setFilters(QgsMapLayerProxyModel.PolygonLayer)
            # self.sel_active_layer()
            self.mQgsProjectionSelectionWidget.setEnabled(True)
            self.FieldEPSG_CBox.setEnabled(False)
            self.loadactivelayer_btn.setEnabled(True)
            self.epsgfield_ckb.setEnabled(True)
            self.sel_epsg()
    
    def check_directory(self):
        if os.path.exists(self.destination_copy_dir.text()):
            self.btn_copy_lidar.setEnabled(True)
        else:
            self.btn_copy_lidar.setEnabled(False)
        
    def sel_active_layer(self):
        """Get active layer in TOC, if it is a polygon layer pass to tile index layer combo box and populate fields combo box
        --------------------------"""
        self.textdisplay.clear()
        if self.chk_help.isChecked():
            self.textdisplay.setText('Help: ' + self.sel_active_layer.__doc__)
        if self.ckb_setdefault.isChecked() == False:
            try:
                if self.iface.activeLayer():
                    my_active_toc_layer=self.iface.activeLayer()
                    my_name_toc_layer = my_active_toc_layer.name()
                    
                    # if active layer is a polygon layer set active layer in ComboBox, else get first one polygon layer 
                    if (my_active_toc_layer.type() == QgsMapLayer.VectorLayer):
                        if (my_active_toc_layer.geometryType() == 2):
                            # get index in ComboBox by name layer 
                            my_cb_index = self.LayerBox.findText(my_name_toc_layer)
                            # set active layer in TOC in ComboBox 
                            self.LayerBox.setCurrentIndex(my_cb_index)
                            self.textdisplay.append('Get polygon layer ' + self.set_text_color(my_name_toc_layer, 2, 600) )                        
                        else:
                            self.LayerBox.setCurrentIndex(0)
                            self.textdisplay.append('Layer ' + self.set_text_color(my_name_toc_layer, 1, 600)  + ' is not a polygon layer. Get the first one in TOC' )                        
                    else:
                        self.LayerBox.setCurrentIndex(0)
                        self.textdisplay.append('Layer ' + self.set_text_color(my_name_toc_layer, 1, 600) + ' is not a vector polygon layer. Get the first one in TOC' )                        
                else:
                    self.textdisplay.append('No active Layer in TOC')
            except:
                self.LayerBox.setCurrentIndex(0)
                self.textdisplay.append('Error getting layer from TOC')

    def field_select(self, event):
        """Populate field combo box from tile index layer
        --------------------------"""
        if self.ckb_setdefault.isChecked() == False and self.get_user_input()[0] is not None:
            self.FieldPath_CBox.clear()
            self.FieldEPSG_CBox.clear()
            mylist_field1 = []
            mylist_field2 = []

            for field in self.get_user_input()[0].fields():
                mylist_field1.append(field.name())
            
            mylist_field2 =[field.name() for field in self.get_user_input()[0].fields()]

                    
            self.FieldPath_CBox.addItems(mylist_field1)
            self.FieldEPSG_CBox.addItems(mylist_field2)

    def sel_epsg(self):
        """ check/uncheck selectBox if epsg input mode changed """
        if self.epsgfield_ckb.isChecked():
            self.mQgsProjectionSelectionWidget.setEnabled(False)
            self.FieldEPSG_CBox.setEnabled(True)
        else:
            self.mQgsProjectionSelectionWidget.setEnabled(True)
            self.FieldEPSG_CBox.setEnabled(False)
            

    def get_user_input(self):
        """ get list of user input """
        try:
            vlayer = self.LayerBox.currentLayer()# get input Tile Index layer from LayerBox -Index 0
        except:
            vlayer = None
        try:
            my_path_fld = self.FieldPath_CBox.currentText()# get input field with path for LIDAR file - Index 1
        except:
            my_path_fld= None
        my_zfactorset = self.ZfactorSpinBox.value() # get z factor value - Index 2
        my_Azimut = self.AzimutSpinBox.value()# get azimut value - Index 3
        my_Elevation = self. ElevationSpinBox.value()# get elevation value - Index 4
        my_crs = None
        my_crs_field = None

        # get CRS (EPSG code) from cbox - Index 5
        try:
            if self.epsgfield_ckb.isChecked():
                my_crs_field = self.FieldEPSG_CBox.currentText()
                print ('my_crs_field: ', my_crs_field)
                return vlayer, my_path_fld, my_zfactorset, my_Azimut, my_Elevation, my_crs_field
            else:
                my_crs = self.mQgsProjectionSelectionWidget.crs()
                print ('my_crs: ', my_crs.EpsgCrsId())
                return vlayer, my_path_fld, my_zfactorset, my_Azimut, my_Elevation, my_crs
        except:
            pass
            return vlayer, my_path_fld, my_zfactorset, my_Azimut, my_Elevation, my_crs

    def changeAzimutSpinBox(self):
        myDialValue= self.AzimutDial.value()
        if (myDialValue >= 0 and myDialValue <= 180):
            self.AzimutSpinBox.setValue(myDialValue+180)
        else:
            self.AzimutSpinBox.setValue(myDialValue-180)

    def changeAzimutDial(self):
        mySpinBoxValue= self.AzimutSpinBox.value()
        if (mySpinBoxValue >= 0 and mySpinBoxValue <= 180):
            self.AzimutDial.setValue(mySpinBoxValue+180)
        else:
            self.AzimutDial.setValue(mySpinBoxValue-180)
            
    def changeElevationSpinBox(self):
        mySliderValue= self.ElevationSlider.value()
        self.ElevationSpinBox.setValue(mySliderValue)
        
    def changeElevationSlider(self):
        myElevationSpinBoxValue= self.ElevationSpinBox.value()
        self.ElevationSlider.setValue(myElevationSpinBoxValue)

    def browse_file(self):
        """ Open save layer dialog 
        --------------------------"""
        self.textdisplay.clear()
        if self.chk_help.isChecked():
            self.textdisplay.setText('Help: ' + self.browse_file.__doc__)
        settings = QgsSettings()
        dirName = settings.value("/UI/lastShapefileDir")
        encode = settings.value("/UI/encoding")
        # DirDialog = QtWidgets.QFileDialog.getExistingDirectory(self,"Choose Directory",dirName)
        fileDialog = QgsEncodingFileDialog(self, "Output virtual file", dirName,
                                           "Virtual file (*.vrt)", encode)
        fileDialog.setDefaultSuffix("vrt")
        fileDialog.setFileMode(QtWidgets.QFileDialog.AnyFile)
        fileDialog.setAcceptMode(QtWidgets.QFileDialog.AcceptSave)
        if not fileDialog.exec_() == QtWidgets.QDialog.Accepted:
            return
        files = fileDialog.selectedFiles()
        self.VirtualFileEdit.setText(files[0])
        self.encoding = fileDialog.encoding()

    def browse_dir(self, dir_type):
        """Select directory to copy the lidar file(s) selected in tile index layer
        --------------------------"""
        # self.textdisplay.clear()
        if dir_type == 'copy_lidar':
            my_dir_tile = 'Choose Directory to Copy LIDAR'
            if self.chk_help.isChecked():
                self.textdisplay.clear()
                self.textdisplay.setText('Help: ' + self.browse_dir.__doc__)
        elif dir_type == 'til_dir':
            my_dir_tile = 'Choose Directory source to create Tile Index Layer'
            if self.chk_help.isChecked():
                self.textdisplay.clear()
                self.textdisplay.setText('Help: Create Tile Index Layer from lidar files in a directory (read also subdirectory)\n  --------------------------')
        settings = QgsSettings()
        dirName = settings.value("/UI/lastShapefileDir")
        my_dir = QtWidgets.QFileDialog.getExistingDirectory(self, my_dir_tile, dirName, QtWidgets.QFileDialog.ShowDirsOnly)
        if dir_type == 'copy_lidar':
            self.destination_copy_dir.setText(my_dir)
        return my_dir
    
    def load_lidar_from_til(self):
        """Load Lidar as file or Virtual Raster from feature selection in tile index layer and apply hillshading setting.
        ------------------------- """
        self.textdisplay.clear()
        my_dtm_list_vrt = []
        if self.chk_help.isChecked():
            self.textdisplay.append('Help: ' + self.load_lidar_from_til.__doc__)

        if not self.chk_vrtraster.isChecked()and not self.chk_addfile.isChecked():
            self.textdisplay.append("No option add lidar/add vrt selected.")
            time.sleep(0.5)
            self.progress_bar.setValue(0)
        else:
            my_selection=self.get_user_input()[0].selectedFeatures()# get selection from input layer
            mytot_selection=len(my_selection) # count selection to manage output message
            
            if mytot_selection > 12:
                self.textdisplay.append(str(mytot_selection) + ' tile features selected. Process may take long time')
                
            #set name for vrt if checked
                
            my_count = 0
            my_count_none = 0
            
            if mytot_selection == 0:
                self.textdisplay.append("No feature selection in Layer: " + self.get_user_input()[0].name()+ ' - exit')
            else: 
                if self.chk_addfile.isChecked():
                    self.textdisplay.append("Start load LIDAR file")
                # add lidar from path field in features selection
                for feature in my_selection:
                    my_count=my_count+1
                    #check if file exist and is a QgsRasterLayer (return None if is invalid)
                    try:
                        rlyr=QgsRasterLayer(feature[self.get_user_input()[1]], os.path.basename(feature[self.get_user_input()[1]]))
                    except:
                        rlyr=QgsRasterLayer('invalid_path', 'invalid_raster') #when error occur from selected feature create an invalid raster type to pass next one and manage the invalid one
                    
                    if not rlyr.isValid():
                        my_count_none = my_count_none+1
                    else:
                        if self.chk_vrtraster.isChecked():
                            my_dtm_list_vrt.append(feature[self.get_user_input()[1]])
                        if self.chk_addfile.isChecked():
                            # add MapLayer to Project
                            mlyr = QgsProject.instance().addMapLayer(rlyr)
                        # manage raster projection by input user
                            if self.FieldEPSG_CBox.isEnabled():
                                mlyr.setCrs(QgsCoordinateReferenceSystem(feature[self.get_user_input()[5]], QgsCoordinateReferenceSystem.EpsgCrsId))
                            else:
                                if self.get_user_input()[5].isValid():
                                    mlyr.setCrs(QgsCoordinateReferenceSystem(self.get_user_input()[5]))
                                else: 
                                    pass
                            #set hillshading by input user
                            r = QgsHillshadeRenderer (mlyr.dataProvider(), 1, self.get_user_input()[3], self.get_user_input()[4])
                            r.setZFactor (self.get_user_input()[2])
                            mlyr.setRenderer(r)
                            # set progressbar and textdisplay when process is in progress
                            self.progress_bar.setValue(1+int(my_count/mytot_selection*100))
                            self.textdisplay.append(self.set_text_color(mlyr.name(), 2, 600))
                            self.textdisplay.append(" add to project")
                # create vrt file from path field in Tile Index File
                if self.chk_vrtraster.isChecked()and len(my_dtm_list_vrt)>0:
                    self.add_vrt_from_til(my_dtm_list_vrt)
                # set progressbar and textdisplay when all processes have done
                self.progress_bar.setValue(100)
                if my_count_none>0:
                    self.textdisplay.append('Path field "' + self.get_user_input()[1]+'" return no raster type for ' +str(my_count_none) 
                    + ' record(s) of '+ str(len(my_selection))+ ' record(s) selected.')
                    if my_count_none == len(my_selection):
                        self.textdisplay.append('Check type and attributes of selected field.')# display when all record are invalid
                time.sleep(0.5)
                self.progress_bar.setValue(0)
                self.iface.setActiveLayer(self.get_user_input()[0])

    def apply_az_elev_zfactor(self):
        """Apply azimut, elevation and z factor user input value to selected file/vrt lidar(s) 
        -------------------------"""
        self.textdisplay.clear()
        if self.chk_help.isChecked():
            self.textdisplay.append('Help: ' + self.apply_az_elev_zfactor.__doc__)
        my_err_layers = 0
        my_ok_layers = 0
        mylayers = self.iface.layerTreeView().selectedLayersRecursive()
        mylayers_count = len(mylayers)
        my_zfactorset = self.ZfactorSpinBox.value() 
        my_azimut = self.AzimutSpinBox.value()
        my_elevation = self.ElevationSpinBox.value()

        for my_raster in mylayers:
            if type(my_raster) is QgsRasterLayer:
                r = QgsHillshadeRenderer(my_raster.dataProvider(), 1, my_azimut, my_elevation)
                r.setZFactor(my_zfactorset)
                my_raster.setRenderer(r)
                my_ok_layers = my_ok_layers +1
                self.progress_bar.setValue(1+int(my_ok_layers/mylayers_count*100))
                self.textdisplay.append("Processing " + str(my_ok_layers) + " raster layer(s)")
            else:
                my_err_layers = my_err_layers+1

        time.sleep(0.5)
        self.progress_bar.setValue(100)
        self.iface.mapCanvas().refreshAllLayers()
        if my_err_layers >0:
            self.textdisplay.append(str(my_ok_layers) + " layers processing. Selection counts " + str(my_err_layers)
            + " no grid o raster layers")
        else:
            self.textdisplay.append("Done. " + str(my_ok_layers) + " layer(s) processing.")
        time.sleep(0.5)
        self.progress_bar.setValue(0)
    # function to test connect
    def def_test(self):
        QtWidgets.QMessageBox.warning(self, "Lidar_manager","funziona")
        
        
    def check_path(self):
        """Check field selected in combo box to verify and report valid path file for all record
        -------------------------"""
        self.textdisplay.clear()
        if self.chk_help.isChecked():
            self.textdisplay.append('Help: ' + self.check_path.__doc__)
        if self.get_user_input()[0]:
            my_field_list = self.get_user_input()[0].fields()
            my_field_index = my_field_list.indexFromName(self.get_user_input()[1])
            my_field_object = my_field_list[my_field_index]
            start_time = time.time()
            count_true=0
            count_raster=0
            count_false=0
            count_null=0
            count_tot = self.get_user_input()[0].featureCount()
            if my_field_object.typeName() == 'String':
                self.textdisplay.append('Check path file. Field: "' + self.get_user_input()[1]+'" - ' +my_field_object.typeName()+' - Valid type....')
                for f in self.get_user_input()[0].getFeatures():
                    count_prog = count_true+count_false+count_null
                    self.progress_bar.setValue(1+int(count_prog/count_tot*100))
                    try:
                        if not (f[self.get_user_input()[1]]):
                            count_null = count_null+1
                            pass
                        else:
                            if os.path.isfile(f[self.get_user_input()[1]]):
                                count_true=count_true+1
                            else:
                                count_false=count_false+1
                    except:
                        count_false=count_false+1
                tot_time = round ((time.time() - start_time),2)
                self.textdisplay.append('Record with valid file path:' + self.set_text_color(str(count_true), 2, 600)) 
                self.textdisplay.append('Record with invalid file path:' + self.set_text_color(str(count_false), 1, 600))
                self.textdisplay.append('Record with null value:' + self.set_text_color(str(count_null), 1, 600))
                self.progress_bar.setValue(0)
                return count_true, count_false, count_null, tot_time
            else:
                self.textdisplay.append('Check path file. Field: "' + self.get_user_input()[1]+ '" - ' +my_field_object.typeName()+' - Invalid type')
        else:
            self.textdisplay.append('No field selected')

    def copy_lidar_from_layer(self):
        """Copy lidar file(s) from selected tile(s) in tile index layer to destination directory
        --------------------------"""
        # manage log information
        self.textdisplay.clear()
        if self.chk_help.isChecked():
            self.textdisplay.append('Help: ' + self.copy_lidar_from_layer.__doc__)
        
        # start of time measurement
        start_time = time.time()
        self.textdisplay.append("Start to copy file")
        
        my_destdir = self.destination_copy_dir.text()
        
        # create a directory from input in widget, useful only by direct user input
        if len(my_destdir) > 0:
            if os.path.exists(my_destdir)==False: 
                os.mkdir(my_destdir)

        # get input user
        my_selection=self.get_user_input()[0].selectedFeatures()# get selection from input layer
        vprovider=self.get_user_input()[0].dataProvider()
        
        # count selection to manage output message
        mytot_selection=len(my_selection) 
        # counter to check file existing
        my_file_exist=0
        my_file_nonexist=0
        my_tot_file=my_file_exist+my_file_nonexist
        
        if len(my_selection) == 0:
            self.textdisplay.append ('Non feature selected in layer '+ self.get_user_input()[0].name())
        else:
            for feature in my_selection:
                my_tot_file=my_tot_file+1
                if os.path.exists(feature[self.get_user_input()[1]]):
                    try:
                        shutil.copyfile(feature[self.get_user_input()[1]],my_destdir+'/'+os.path.basename(feature[self.get_user_input()[1]]))
                        self.progress_bar.setValue(1+int(my_tot_file/len(my_selection)*100))
                        self.textdisplay.append ('copied file n. '+ str(my_file_exist+1)+' of ' + str(len(my_selection)))
                        my_file_exist = my_file_exist+1
                    except:
                        self.textdisplay.append('Error in copying file')
                else:
                    # self.progress_bar.setValue(1+int(my_tot_file/len(my_selection)*100))
                    # self.textdisplay.append ('file '+ feature[self.get_user_input()[1]]+ ' non trovato')
                    my_file_nonexist = my_file_nonexist+1
            if len(my_selection) == my_file_nonexist:
                self.textdisplay.append ('Invalid file in input field of layer ' + self.get_user_input()[0].name())
            self.textdisplay.append ('File selected: ' +str(len(my_selection)))
            self.textdisplay.append ('File copied: '+ self.set_text_color(str(my_file_exist), 2, 600) +' in '+self.set_text_color(my_destdir, 2, 600))
            self.textdisplay.append ('File not find: '+self.set_text_color(str(my_file_nonexist), 1, 600))
            self.textdisplay.append ('Time process: ' + str(round ((time.time() - start_time),2)) + ' second(s)')
            self.progress_bar.setValue(100)
            self.textdisplay.append("Done")
            time.sleep(0.5)
            self.progress_bar.setValue(0)

    def vrt_from_toc(self):
        """Create virtual raster file from lidar active in TOC
        --------------------------"""
        self.textdisplay.clear()

        if self.chk_help.isChecked():
            self.textdisplay.append('Help: ' + self.vrt_from_toc.__doc__)
        # start of time measurement
        start_time = time.time()
        self.textdisplay.append("Start create virtual raster")

        # get list of raster active in TOC
        my_raster_toc = self.iface.layerTreeView().selectedLayersRecursive()

       # counter for raster file

        my_raster_count_none = 0
        my_raster_count_ok = 0
        my_dtm_list_vrt = []

        # populate list of Raster Layer and count
        for rst in my_raster_toc:
            if rst.type() == QgsMapLayerType.RasterLayer:
                my_dtm_list_vrt.append(rst.publicSource())
                my_raster_count_ok = my_raster_count_ok +1
            else:
                my_raster_count_none = my_raster_count_none+1
        
        if len(my_dtm_list_vrt) == 0:
            self.textdisplay.append('No raster layer (s) active in TOC')
        else:
            self.progress_bar.setValue(25)
            my_date_time_str = time.strftime("%Y_%m_%d_%H_%M_%S")
            my_vrt = 'Vrt_'+my_date_time_str+'.vrt'
            vrt_path = os.path.join(MY_DEFAULT_DESTDIR, my_vrt)

            try:
                my_vrt_built = gdal.BuildVRT(vrt_path, my_dtm_list_vrt)
                my_vrt_built = None
                my_new_vrt = self.iface.addRasterLayer(vrt_path, my_vrt)
            except:
                pass
            self.progress_bar.setValue(50)
            time.sleep(0.5)
            # manage raster projection by input user
            try:
                if self.epsgfield_ckb.isChecked():
                    pass
                else:
                    if self.get_user_input()[5].isValid():
                        my_new_vrt.setCrs(self.get_user_input()[5])
                    else:
                        pass
            except:
                pass

            try:
                vrt_r = QgsHillshadeRenderer(my_new_vrt.dataProvider(), 1, self.get_user_input()[3],
                                         self.get_user_input()[4])
                vrt_r.setZFactor(self.get_user_input()[2])
                my_new_vrt.setRenderer(vrt_r)
                self.progress_bar.setValue(90)
                time.sleep(0.5)
                self.textdisplay.append("Create vrt file in default user folder: \n" + vrt_path)
                if my_raster_count_none > 0:
                    self.textdisplay.append('Return no raster type for ' + str(
                        my_raster_count_none) + ' layer(s)')
            except:
                self.textdisplay.append("Error to create Virtual Raster check input")

        # set progressbar and textdisplay when all processes have done
        self.progress_bar.setValue(100)
        self.textdisplay.append("Virtual Raster done")
        time.sleep(0.5)
        self.progress_bar.setValue(0)
        self.iface.setActiveLayer(self.get_user_input()[0])
        
    def create_til(self):
        """Create a Tile Index Layer from active layers in TOC or from directory source
        --------------------------"""
        # manage log information
        self.textdisplay.clear()
        if self.chk_help.isChecked():
            self.textdisplay.setText('Help: ' + self.create_til.__doc__)
        
        self.textdisplay.append('Start to create Tile Index Layer')
        self.progress_bar.setValue(5)
        
        my_list_path_dtm=[]
        my_count_files = 0
        my_raster_count_none = 0
        my_tot_raster_file=0
        # tile index from selected lidar in TOC   
        if self.radiobtn_til_from_activelayers.isChecked():
            mylayers = self.iface.layerTreeView().selectedLayersRecursive()
            for r in mylayers:
                if r.type() == QgsMapLayerType.RasterLayer:
                    my_list_path_dtm.append(r.publicSource())
                else:
                    my_raster_count_none = my_raster_count_none+1
            my_text = 'No raster layer(s) active in TOC'
        # tile index from lidar files in directory
        else:
            my_til_dir=self.browse_dir('til_dir')
            # to manage color text in QTextEdit
            dirText =  self.set_text_color(my_til_dir, 2, 600)
            self.textdisplay.append('Read file to get tile from: ' + dirText + ' wait...')
            #count file in directory and subdirectory
            for folderName, subFolders, fileNames in os.walk(my_til_dir):
                for f in fileNames:
                    my_count_files=my_count_files+1
            # check if is valid path for QgsRasterLayer and populate list to use in gdal:tileindex
            for folderName, subFolders, fileNames in os.walk(my_til_dir):
                for f in fileNames:
                    rlyr=QgsRasterLayer(os.path.join(folderName,f), f)
                    my_tot_raster_file=my_tot_raster_file+1
                    if not rlyr.isValid():
                        self.progress_bar.setValue(1+int(my_tot_raster_file/my_count_files*100))
                        my_raster_count_none = my_raster_count_none+1 # useful to manage invalid raster file
                    else:
                        self.progress_bar.setValue(1+int(my_tot_raster_file/my_count_files*100))
                        my_list_path_dtm.append(os.path.join(folderName,f))
            my_text = 'No raster layer(s) in source directory'       
        
        if len (my_list_path_dtm)>5:
            self.textdisplay.append("Read "+ str(len(my_list_path_dtm)) + " valid path in directory/subdirectory. Process may take long time...")
            self.progress_bar.setValue(50)
            time.sleep(0.5)
        
        if len (my_list_path_dtm)>0:
            # use specific name and location to manage name output
            my_date_time_str = time.strftime("%Y_%m_%d_%H_%M_%S")
            my_til = 'TIL_'+my_date_time_str+'.shp'
            til_path = os.path.join(MY_DEFAULT_DESTDIR, my_til)
            #Core process
            processing.runAndLoadResults('gdal:tileindex', {'LAYERS': my_list_path_dtm,
            'PATH_FIELD_NAME': 'PATH', 'ABSOLUTE_PATH':False,'OUTPUT':til_path})#'TEMPORARY_OUTPUT' to create a default temporary file
            self.progress_bar.setValue(75)
            #when load tile layer it is active, it faster to use it. Processing return a dict: need to get QgsVectorLayer from path
            my_til_layer=self.iface.activeLayer()
            
            if self.epsgfield_ckb.isChecked():
                my_text_prj = 'No EPSG set'
            else:
                if self.get_user_input()[5].isValid():
                    my_til_layer.setCrs(QgsCoordinateReferenceSystem(self.get_user_input()[5]))
                    my_text_prj=''
                else:
                    my_text_prj = 'No EPSG set'
            
            my_file_path_text = self.set_text_color(til_path, 2, 600)
            self.textdisplay.append("Create Tile Index Layer in default user folder: " + my_file_path_text)
            self.textdisplay.append(my_text_prj)
            
            if my_raster_count_none > 0:
                self.textdisplay.append("Skip n. " + str(my_raster_count_none)+ " no raster layer(s)")
        else:
            self.textdisplay.append(my_text)
            
        self.progress_bar.setValue(100)
        self.textdisplay.append('Done - Create Tile Index Layer')
        time.sleep(0.5)
        self.progress_bar.setValue(0)
    
    def clear_log(self):
        """Clean all message log
        --------------------------"""
        # manage log information
        self.textdisplay.clear()
        if self.chk_help.isChecked():
            self.textdisplay.append('Help: ' + self.clear_log.__doc__)
            
    def set_text_color(self, mytext, mycolor, mybold, myitalic = 'normal'):
        """Set html code to color string in QTextEdit
        --------------------------"""
        # input index match color
        my_color_list = ["#000000", "#ff0000", "#008000"]
        
        outputText = "<span style=\" font-size:8pt; font-weight:"
        # input mybold integer (600) match bold/no bold 
        outputText += str(mybold)
        outputText += "; font-style:"
        outputText += myitalic
        outputText += "; color:"
        outputText += my_color_list[mycolor]
        outputText += ";\" >"
        outputText += mytext
        outputText += "</span>"
        return outputText
    
    def default_value_hlsd (self):
        """Set artificial NW middle latitudine sun position as default value to azimut, elevation and z factor for hillshading
        --------------------------"""
        self.textdisplay.clear()
        if self.chk_help.isChecked():
            self.textdisplay.append('Help: ' + self.default_value_hlsd.__doc__)
        self.AzimutSpinBox.setValue(315)
        self.ElevationSpinBox.setValue(45)
        self.ZfactorSpinBox.setValue(1)
        
    def test_layer(self):
        """ function just to do something """
        self.textdisplay.append('write somenthing to test')
        
    def add_vrt_from_til (self, mylist):
        self.textdisplay.append('Start create Virtual Raster file')
        #create vrt path file name 
        my_date_time_str = time.strftime("%Y_%m_%d_%H_%M_%S")
        my_vrt = 'Vrt_'+my_date_time_str+'.vrt'
        vrt_path = os.path.join(MY_DEFAULT_DESTDIR, my_vrt)
        #built vrt file
        my_vrt_built = gdal.BuildVRT(vrt_path, mylist)
        self.progress_bar.setValue(25)
        my_vrt_built = None
        my_new_vrt = self.iface.addRasterLayer(vrt_path, my_vrt)
        self.progress_bar.setValue(50)
        time.sleep(0.5)
        # manage raster projection by input user
        if self.FieldEPSG_CBox.isEnabled():
            try:
                my_new_vrt.setCrs(QgsCoordinateReferenceSystem(feature[self.get_user_input()[5]], QgsCoordinateReferenceSystem.EpsgCrsId))
            except:
                self.textdisplay.append("Error reading EPSG input. EPSG code not set")
        else:
            try:
                if self.get_user_input()[5].isValid():
                    my_new_vrt.setCrs(QgsCoordinateReferenceSystem(self.get_user_input()[5]))
                else: 
                    self.textdisplay.append("Invalid EPSG input. EPSG code not set")
            except:
                self.textdisplay.append("Error reading EPSG input. EPSG code not set")
        
        self.progress_bar.setValue(50)
        time.sleep(0.5)
        vrt_r = QgsHillshadeRenderer (my_new_vrt.dataProvider(), 1, self.get_user_input()[3], self.get_user_input()[4])
        vrt_r.setZFactor (self.get_user_input()[2])
        my_new_vrt.setRenderer(vrt_r)
        self.progress_bar.setValue(90)
        time.sleep(0.5)
        self.textdisplay.append("Create vrt file in default user folder: ")
        self.textdisplay.append(self.set_text_color(vrt_path, 2, 600))

    def open_user_folder(self):
        """Open user folder directory in default OS file manager
        --------------------------"""
        self.textdisplay.clear()
        if self.chk_help.isChecked():
            self.textdisplay.setText('Help: ' + self.open_user_folder.__doc__)
        try:
            os.startfile(MY_DEFAULT_DESTDIR)
        except:
            self.textdisplay.append(MY_DEFAULT_DESTDIR + ' not exist')
    
    def open_readme_md(self):
        """Open readme file in github plugin repository
        --------------------------"""
        self.textdisplay.clear()
        if self.chk_help.isChecked():
            self.textdisplay.setText('Help: ' + self.open_readme_md.__doc__)
        try:
            webbrowser.open(MY_README_LINK)
            self.textdisplay.append('For complete help contents read readme.md file in github repository:')
            self.textdisplay.append(self.set_text_color(MY_README_LINK, 0, 600))
            self.textdisplay.append('it is opening in default OS web broswer')
        except:
            self.textdisplay.append(MY_README_LINK + ' not exist')
            