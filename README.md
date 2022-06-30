# LidarManagerPlugin
Qgis Plugin to manage small and large LIDAR dataset. 
Useful to GIS user with intensive job in LIDAR analysis.

Request LIDAR file(s) in readable directory and user with read and write privilege for user directory.
Tested with Qgis 3.10 and following

Add file(s) lidar and/or single virtual raster file directly from Tile Index Layer with valid field path. 
Set on the fly hillshading parameter and CRS. 
Change hillshading setting to LIDAR in TOC.
Other Tools: 
  - copy LIDAR selected in Tile Index Layer to destination directory
  - create Tile Index Layer from directory/subdirectory or frome LIDAR in TOC and populate valid field path (use gdal:tileindex process)
  - create virtual raster file from LIDAR active in TOC
  - check path field in Tile Index Layer to control valid path for raster
  - interactive help string and log message
