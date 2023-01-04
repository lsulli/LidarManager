## LidarManager Qgis Plugin

Qgis Plugin to manage small and large LIDAR dataset. 
Useful to GIS user with intensive job in LIDAR analysis.

Requires LIDAR file(s) in readable directory and user with read and write privilege for QGIS user directory.
Utility tools for TIL and VRT are active only in Windows with OSGeo4w shell is present in default installation directory (point to system OSGEO4W_ROOT variable) and there isn't user limitation to cmd console.

Tested with QGIS 3.10 and later in Windows 8 and later.

## Summary
1. [Author](#autore)
2. [Main features](#fun_princ)
3. [Start](#start)
4. [Tile Index Layer Setting](#til_setting)
5. [Hillshading setting](#hlsd_setting)
6. [Add lidar to project](#add_lidar)
7. [Utility](#utility)

## Main features <a name="fun_princ"></a>

Add file(s) LIDAR and/or single virtual raster file directly from selected features in Tile Index Layer (**TIL**) with valid field path (you can create TIL with dedicate tool - see below). 
Set on the fly hillshading parameter and CRS. 
Change LIDAR hillshading setting in TOC.
Other Tools: 
  - copy LIDAR selected in TIL to destination directory
  - create Tile Index Layer from directory (with subdirectory) and populate valid field path (very fast: use OSGeo4W shell with gdaltileindex command)
  - create virtual raster file from LIDAR active in TOC
  - check path field in Tile Index Layer to control valid path for raster
  - interactive help string and log message

## AUTHOR <a name="autore"></a>

Lorenzo Sulli - Autorità di bacino distrettuale Appennino settentrionale - Florence (Italy)

www.appenninosettentrionale.it

l.sulli@appenninosettentrionale.it - lorenzo.sulli@gmail.com

## START <a name="start"></a>

 When Lidar Manager Plugin is load you should see a button like this ![alt text](./readme_image/fig4.JPG) in Plugins Toolbar and a submenu in Raster menu.
 The Lidar Manager Window is always on the top also when Qgis is minimize,it's useful to work with other application like window explorer. 
 On start Lidar Manager Window is put in the right bottom side of the screen.
 User can switch from Qgis Main Window to Lidar Manager Window and work with both.
 
##  Tile Index Layer Setting <a name="til_setting"></a>

Lidar Manager reads layers in Table of Content (TOC) and gets **only** polygon vector layer to populate "**Tile Index Layer LIDAR**" combo box list. Gets the first one in TOC. The list is empty if there aren't polygon layer. 

With dedicate button ![alt text](./readme_image/fig2.JPG) you can get the active polygon layer in TOC.

Choose your the TIL with LIDAR reference if exist, if not you can create it with dedicate tool "**Create TIL from DIR**" in the **Utility** section

![alt text](./readme_image/fig1.JPG)


In "**Field path file**" combo box are listing all the string type field present in the TIL, choose one with a file valid path (NB: it work with all file type). 

With dedicate button ![alt text](./readme_image/fig5.JPG) you can check path validity and report it in log box:

![alt text](./readme_image/fig6.JPG)

You can set the EPSG code for CRS from a dedicate field ("**Field EPSG Code**" combo box) or from Qgis combo box for EPSG code list ("**Qgis Epsg code"**).

Whenever you load or open Lidar Manager by default it gets EPSG code from current Qgis project.

NB: EPSG setting is used by TIL and VRT tools. Remember it.

With "**lock as default**" checkbox user can lock input variable in "**Tile Index Setting"**  to preserve change. 


![alt text](./readme_image/fig3.JPG)

##  Hillshading Setting <a name="hlsd_setting"></a>

##  Add Lidar to Project <a name="add_lidar"></a>

![alt text](./readme_image/fig7.JPG)

##  Utility <a name="Utility"></a>

