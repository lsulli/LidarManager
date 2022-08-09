# LidarManagerPlugin
Qgis Plugin to manage small and large LIDAR dataset. 
Useful to GIS user with intensive job in LIDAR analysis.

Request LIDAR file(s) in readable directory and user with read and write privilege for QGIS user directory.
Tested with QGIS 3.10 and later.

Add file(s) LIDAR and/or single virtual raster file directly from selected features in Tile Index Layer with valid field path (you can create TIL with dedicate tool - see below). 
Set on the fly hillshading parameter and CRS. 
Change LIDAR hillshading setting in TOC.
Other Tools: 
  - copy LIDAR selected in Tile Index Layer to destination directory
  - create Tile Index Layer from directory (with subdirectory) or from active LIDAR in TOC and populate valid field path (use gdal:tileindex process)
  - create virtual raster file from LIDAR active in TOC
  - check path field in Tile Index Layer to control valid path for raster
  - interactive help string and log message


