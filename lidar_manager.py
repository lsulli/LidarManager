# -*- coding: utf-8 -*-
"""
/***************************************************************************
 LidarManager
                                 A QGIS plugin
Manage large LIDAR dataset in map canvas
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
import os.path
from qgis.core import QgsProject
from PyQt5.QtCore import QSettings, QTranslator, qVersion, QCoreApplication, Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QAction, QMessageBox

# Initialize Qt resources from file resources.py
from .resources import *
# Import the code for the dialog
from .lidar_manager_dialog import LidarManagerDialog

class LidarManager:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        # Save reference to the QGIS interface
        self.iface = iface
        # Create the dialog (after translation) and keep reference
        self.dlg = LidarManagerDialog(iface)
        # self.dlg.setModal(True) # delete? work from ui 
        # self.dlg.setParent(self.iface.mainWindow()) # not working: set Qdialog trasparent 
        self.dlg.setWindowFlags(Qt.WindowStaysOnTopHint)# always on top - Problem: hide some qgis standard dialog 

    # add icon and menu item

    def initGui(self):
        # create action
        self.action = QAction(
            QIcon(":/plugins/lidar_manager/icons/LidarManager.ico"), "Lidar Manager", self.iface.mainWindow()
        )
        self.action.setWhatsThis("Manger lidar dataset")
        self.action.triggered.connect(self.show_and_setting_dialog)
        # add toolbar button and menu item
        self.iface.addToolBarIcon(self.action)
        self.iface.addPluginToRasterMenu("&Lidar Manager", self.action)

    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        self.iface.removeToolBarIcon(self.action)
        self.iface.removePluginRasterMenu("&Lidar Manager", self.action)

    def show_and_setting_dialog(self):
        """Run method that performs just show dialog"""
        # if EPSG widget is enabled set to crs project
        if self.dlg.mQgsProjectionSelectionWidget.isEnabled():
            self.dlg.mQgsProjectionSelectionWidget.setCrs(QgsProject.instance().crs())
        # show the dialog if not visible
        if not self.dlg.isVisible():
            self.dlg.show()
            self.dlg.testedit_logdisplay.clear()
            #set CRS as default from project
        # show the dioalog normal if minimized
        if self.dlg.isMinimized():
            self.dlg.showNormal()
        #set focus to add lidar btn
        self.dlg.btn_addlidar_file.setFocus()
   