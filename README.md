# Gridded Yields from Finland

- Crop yields from crop production survey are reported on farm-level. E.g. each barley parcel of a farm is set to have the same mean yield.  

- If a farm is having its barley (or crop in question) fields more than 30km apart, it is excluded. Typically fields are within 3km range.

- Center points of fields are mapped in 10km grids. Each grid much have > 5 parcels with reported yields, otherwise excluded. We take the mean yield of all parcels per grid, the unit is kg/ha.

- Projected coordinate system for Finland is epsg:3067. Grids are reported as the North of Origin or East of Origin meaning the bottom left corner of a grid (min x, min y). Grids are reported both in epsg:3067 and in more common WGS 84 (EPSG:4326).

- Parcel geometries are available from year 2016 on, so grids can be produced from 2016 on.
 

The following crops were selected:
1110 Winter wheat
1120 Spring wheat
1400 Oats
1310 Feed Barley
1320 Malting barley
3000 Potatoes (all)
Grasses are difficult. There is farmer reported yield information on these (list below) but I dont know how to map parcels to these categories. Parcel geometry data (LPIS) has all annual and perennial combined into 'annual' and 'perennial' category conserning these:
silage feed fresh
silage feed pre-dried
forage for mowing
dried hay


The csv file looks like this:

EOFORIGIN10km,NOFORIGIN10km,10kmCELLCODE,yield,EOFORIGIN4326,NOFORIGIN4326

310000.0,6650000.0,10kmN6650E0310,3712.0,23.643236974023324,60.01592913467296

270000.0,6660000.0,10kmN6660E0270,5000.0,22.895679855964566,60.10007796086207

290000.0,6660000.0,10kmN6660E0290,2246.0,23.27680861847499,60.04974869380741

320000.0,6660000.0,10kmN6660E0320,3585.0,23.895582125208914,60.078123793347785

330000.0,6660000.0,10kmN6660E0330,2599.0,23.989700644947064,60.1002221064294

 

- 10kmCELLCODE is a unique identifier of a grid cell.
- The cvs file name tells it all: Yields-1310-Feed-barley-2020.csv

![Yields-1400-Oats-2019](https://github.com/myliheik/griddedYields/assets/9526912/3d82cef8-b381-458e-b47d-49d4fc34eab4)
