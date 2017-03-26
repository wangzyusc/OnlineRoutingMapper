# -*- coding: utf-8 -*-
"""
/***************************************************************************
 OnlineRoutingMapper
                                 A QGIS plugin
 Generate routes by using online services (Google Directions etc.)
                              -------------------

        copyright            : (C) 2015 by Mehmet Selim BILGIN
        email                : mselimbilgin@yahoo.com
        web                  : cbsuygulama.wordpress.com
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

from PyQt4.QtCore import *
from PyQt4.QtGui import *

from routeprovider import RouteProvider

from qgis.gui import QgsMapToolEmitPoint
from qgis.core import *

import resources

from onlineroutingmapper_dialog import OnlineRoutingMapperDialog

import os,urllib2

class OnlineRoutingMapper(object):
    def __init__(self, iface):
        self.iface = iface
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&Online Routing Mapper')
        # TODO: We are going to let the user set this up in a future iteration
        self.toolbar = self.iface.addToolBar(u'OnlineRoutingMapper')
        self.toolbar.setObjectName(u'OnlineRoutingMapper')

    def tr(self, message):
        return QCoreApplication.translate('OnlineRoutingMapper', message)

    def add_action(
        self,
        icon_path,
        text,
        callback,
        enabled_flag=True,
        add_to_menu=True,
        add_to_toolbar=True,
        status_tip=None,
        whats_this=None,
        parent=None):
   

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            self.toolbar.addAction(action)

        if add_to_menu:
            self.iface.addPluginToMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

    def initGui(self):
        icon_path = self.plugin_dir + os.sep + 'icon.png'

        self.add_action(
            icon_path,
            text=self.tr(u'Online Routing Mapper'),
            callback=self.run,
            parent=self.iface.mainWindow())

    def clickHandler(self, QgsPoint):
        whichTextBox.setText(str(QgsPoint.x()) + ',' +str(QgsPoint.y()))
        self.dlg.showNormal()
        self.canvas.unsetMapTool(self.clickTool) #I dont need it no more. Let it free

    def toolActivator(self, QLineEdit):
        self.dlg.showMinimized()
        global whichTextBox
        whichTextBox = QLineEdit #I find this way to control it
        self.clickTool.canvasClicked.connect(self.clickHandler)
        self.canvas.setMapTool(self.clickTool) #clickTool is activated

    def crsTransform(self, inputPointStr):
        sourceCRS = self.canvas.mapSettings().destinationCrs() #getting the project CRS
        destinationCRS = QgsCoordinateReferenceSystem(4326) #google uses this CRS
        transformer = QgsCoordinateTransform(sourceCRS,destinationCRS) #defining a CRS transformer
        inputQgsPoint = QgsPoint(float(inputPointStr.split(',')[0]), float(inputPointStr.split(',')[1]))
        outputQgsPoint = transformer.transform(inputQgsPoint)

        return str(outputQgsPoint.y()) + ',' + str(outputQgsPoint.x())

    def checkNetConnection(self):
        try:
            urllib2.urlopen('http://www.google.com',timeout=7)
            return True
        except urllib2.URLError as err:
            pass
        return False

    def routeMaker(self, wktLineString):
        feature = QgsFeature()
        feature.setGeometry(QgsGeometry.fromWkt(wktLineString))
        vectorLayer = QgsVectorLayer('LineString?crs=epsg:4326', 'Routing Result', 'memory')
        layerProvider = vectorLayer.dataProvider()
        vectorLayer.startEditing()
        layerProvider.addFeatures([feature])
        vectorLayer.commitChanges()
        vectorLayer.updateExtents()
        vectorLayer.loadNamedStyle(self.plugin_dir + os.sep + 'OnlineRoutingMapper.qml')
        QgsMapLayerRegistry.instance().addMapLayer(vectorLayer)
        destinationCRS = self.canvas.mapSettings().destinationCrs() #getting the project CRS
        sourceCRS = QgsCoordinateReferenceSystem(4326)
        transformer = QgsCoordinateTransform(sourceCRS,destinationCRS)
        extentForZoom = transformer.transform(vectorLayer.extent())
        self.canvas.setExtent(extentForZoom)
        self.canvas.zoomScale(self.canvas.scale()*1.03) #zoom out a little bit.
        # QMessageBox.information(self.dlg, 'Information' ,'The analysis result was added to the canvas.')

    
    def _getPorts(self):
        """
            Extract all the co-ordinates from a layer containing morocco_ports
        """
        for lyr in QgsMapLayerRegistry.instance().mapLayers().values():
            if lyr.name() == "PortByType OGRGeoJSON Point":
                layer = lyr
                break

        if layer:
            # We managed to get the layer
            iter = layer.getFeatures()
            ports = []
            for feature in iter:
                # x = long, y = lat
                print feature['LAT_DEG'], feature['LONG_DEG']
                port = str(feature['LAT_DEG']) + "," + str(feature['LONG_DEG'])
                ports.append(port)
            print 'length of port list is '+ len(ports)
            return ports
        else:
            print 'The port list is empty'
            return None

    def runAnalysis(self):
        if len(self.dlg.startTxt.text())>0 and len(self.dlg.stopTxt.text())>0:
            
            # Test
            # load co-ordinates of two ports
            # find distances against few postal co-ordinates
           
            ports = self._getPorts()

            # Ouarzazate: 30.916667, -6.916667
            loc1_x = -6.916667
            loc2_x = -5.224722
            loc1_y = 30.916667
            loc2_y = 33.441667

            loc1 = str(loc1_y) + "," + str(loc1_x)
            loc2 = str(loc2_y) + "," + str(loc2_x)
            # locs = [loc1, loc2]
            locs = [loc1]

            paths = []
            # iterate over the ports, find the distance and draw the line
            for port in ports:
                # iterate over the locations
                for loc in locs:
                    startPoint = port
                    stopPoint = loc
                    print str(startPoint) + ', ' + str(stopPoint)
        
                    wkt, url = self.routeEngine.google(startPoint, stopPoint)
                    paths.append({'wkt': wkt, 'url': url})
                    # self.routeMaker(wkt)
           
            for route in paths:
                self.routeMaker(route['wkt'])
            # else:
            #   QMessageBox.warning(self.dlg, 'Network Error!', 'There is no internet connection.')
        else:
            QMessageBox.information(self.dlg,'Warning', 'Please choose Start Location and Stop Location.')

    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginMenu(
                self.tr(u'&Online Routing Mapper'),
                action)
            self.iface.removeToolBarIcon(action)
        # remove the toolbar
        del self.toolbar

    def run(self):
        self.routeEngine = RouteProvider()
        self.canvas = self.iface.mapCanvas()
        self.dlg = OnlineRoutingMapperDialog()
        self.dlg.setFixedSize(self.dlg.size())
        self.clickTool = QgsMapToolEmitPoint(self.canvas) #clicktool instance generated in here.
        self.dlg.startBtn.clicked.connect(lambda : self.toolActivator(self.dlg.startTxt))
        self.dlg.stopBtn.clicked.connect(lambda : self.toolActivator(self.dlg.stopTxt))
        self.dlg.runBtn.clicked.connect(self.runAnalysis)

        self.dlg.show()
