# LidarManagerPlugin

Qgis Plugin to manage small and large LIDAR dataset. 
Useful to GIS user with intensive job in LIDAR analysis.

Request LIDAR file(s) in readable directory and user with read and write privilege for QGIS user directory.
Utility tools for tIL and VRT are active only in Windows with OSGeo4w shell is present in default installation directory (point to system OSGEO4W_ROOT variable)
Tested with QGIS 3.10 and later in Windows 8 and later.

Add file(s) LIDAR and/or single virtual raster file directly from selected features in Tile Index Layer with valid field path (you can create TIL with dedicate tool - see below). 
Set on the fly hillshading parameter and CRS. 
Change LIDAR hillshading setting in TOC.
Other Tools: 
  - copy LIDAR selected in Tile Index Layer to destination directory
  - create Tile Index Layer from directory (with subdirectory) and populate valid field path (very fast: use OSGeo4W shell with gdaltileindex command)
  - create virtual raster file from LIDAR active in TOC
  - check path field in Tile Index Layer to control valid path for raster
  - interactive help string and log message
 
##  Tile Index Layer Setting
 
![alt text](./readme_image/fig1.JPG)

When Lidar Manager Plugin is load reads layers in Table of Content (TOC) and get only polygon vector layer to populate combo box list. Get the first one in TOC. The list is empty if there aren't polygon layer. 
With dedicate button ![alt text](./readme_image/fig2.JPG) you can get the active layer in TOC.

![alt text](./readme_image/fig3.JPG)


