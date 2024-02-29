"""
2024-01-31 MY




RUN:

python 01-yield-grids-and-maps.py -c 1310 \
-i /Users/myliheik/Documents/GISdata/satotutkimus/SATO_VUODET_2015_2023.csv \
-o /Users/myliheik/Documents/myCROPYIELD/griddedYields/ \
-s /Users/myliheik/Documents/GISdata/Kasvulohkot2020/kasvulohkot2020-mod.shp

WHERE:
-i: inputpath to predictions
-c: crop type(s)
-o: outputpath to yield files and images
-s: shapefile of annual parcel data, year info included

"""

import pandas as pd 
import geopandas as gpd
import matplotlib.pyplot as plt
import seaborn as sns
import os
import matplotlib.colors as mcolors

import matplotlib.cm as cm

from matplotlib.lines import Line2D

import numpy as np
import shapely

from mpl_toolkits.axes_grid1 import make_axes_locatable
import matplotlib.patches as mpatches

from matplotlib.colors import ListedColormap, LinearSegmentedColormap, TwoSlopeNorm

from pathlib import Path
import argparse
import textwrap
import math

#def round_up(n, decimals=0):
#    multiplier = 10 ** decimals
#    return math.ceil(n * multiplier) / multiplier

def round_down(n, decimals=0):
    multiplier = 10 ** decimals
    return math.floor(n * multiplier) / multiplier

# EDIT: 
#Europe borders:
fpeuropa = '/Users/myliheik/Documents/GISdata/EU-countries/Europe_borders.shp'


    
def readShapefile(shapefp):
        gdf = gpd.read_file(shapefp)
        gdf['parcelID'] = gdf['MAATILA_TU'].astype(str) + '_' + gdf['PLVUOSI_PE'].astype(str) + '_' + gdf['KLILM_TUNN'].astype(str)
        gdf['keskipiste'] = gdf.centroid
        year = gdf['VUOSI'][0]
        
        return gdf, year


def readYields(inputfile, croptype, year):
        df0 = pd.read_csv(inputfile)
        df = df0[df0['VUOSI'] == year]
        
        if croptype == '1310': harvested = 'rehuohra_ala'; cropname = 'Feed-barley'; totalyield = 'rehuohra_sato'
        elif croptype == '1320': harvested = 'mallasohra_ala'; cropname = 'Malting-barley'; totalyield = 'mallasohra_sato'
        elif croptype == '1400': harvested = 'kaura_ala'; cropname = 'Oats'; totalyield = 'kaura_sato'
        elif croptype == '1110': harvested = 'syysvehna_ala'; cropname = 'Winter-wheat'; totalyield = 'syysvehna_sato'
        elif croptype == '1120': harvested = 'kevatvehna_ala'; cropname = 'Spring-wheat'; totalyield = 'kevatvehna_sato'
        elif croptype == '4210': harvested = 'rapsi_ala'; cropname = 'Oil-seed-rape'; totalyield = 'rapsi_sato'
        elif croptype == '3100': harvested = 'peruna_ala_yht'; cropname = 'Potato'; totalyield = 'peruna_sato_yht'
        elif croptype == '': harvested = 'kuivaheina_ala'; cropname = 'kuivaheina_ala'; totalyield = 'kuivaheina_sato'
        elif croptype == '': harvested = 'sailorehu_tuore_ala'; cropname = 'sailorehu_tuore_ala'; totalyield = 'sailorehu_tuore_sato'
        elif croptype == '': harvested = 'sailorehu_esik_ala'; cropname = 'sailorehu_esik_ala'; totalyield = 'sailorehu_esik_sato'
        elif croptype == '': harvested = 'niittorehu_ala'; cropname = 'niittorehu_ala'; totalyield = 'niittorehu_sato'
        else:
            print(f'Crop type {croptype} not found! Should be either 1310, 1320, 1400, 1110, 1120, 4210, or 3000.')
            
        print(f'Crop type is {cropname}')

        df2 = df.dropna(subset = [harvested, totalyield])     
        
        df2['yield'] = round(df2[totalyield] / (df2[harvested]/100),0) # kg / (a/100 -> ha)

        return df2, cropname
    

def mergeData(gdf, df2, croptype, yieldpath, cropname, year):
        if croptype == '3100': # potatoes
            gdf2 = gdf[gdf['KVI_KASVIK'].str.startswith('31')]
        else: 
            gdf2 = gdf[gdf['KVI_KASVIK'] == croptype]       
            
        # Choose only farms in survey data:

        gdf2.MAATILA_TU = gdf2.MAATILA_TU.astype('int').copy()
        row_mask = gdf2.MAATILA_TU.isin(df2['tiltu'].unique().tolist())
        filtered = gdf2[row_mask].copy()   
            
        ####### Discard farms having fields further than 30km apart:
        
        dataByFarm = filtered[['MAATILA_TU', 'KVI_KASVIK', 'geometry']].dissolve(by=['MAATILA_TU', 'KVI_KASVIK'], aggfunc='sum')
        farms0 = len(dataByFarm)

        distanceWithin = dataByFarm.geometry.bounds
        distanceWithin['distancex'] = distanceWithin.maxx - distanceWithin.minx
        distanceWithin['distancey'] = distanceWithin.maxy - distanceWithin.miny
        distanceWithin['maxdistance'] = distanceWithin[['distancex', 'distancey']].apply(max, axis=1)
        distanceWithin['maxdistance'].describe() # keskim. 3.9km, max 136km
        dataByFarm2 = dataByFarm[distanceWithin['maxdistance'] < 30000].reset_index()
        farms1 = len(dataByFarm2)        
        
        row_mask = filtered.MAATILA_TU.isin(dataByFarm2['MAATILA_TU'])
        filtered1 = filtered[row_mask].copy()
        
        print(f'{(farms1-farms0)} farms filtered out because their fields were > 30km apart.') 
        
        ##############################################################

        filtered2 = filtered1.merge(df2[['tiltu', 'yield']], how = 'left', left_on = 'MAATILA_TU', right_on = 'tiltu')
        filtered3 = filtered2.dropna(subset = ['yield'])
        filtered3['lon'] = filtered3.keskipiste.x
        filtered3['lat'] = filtered3.keskipiste.y
                
        for index, row in filtered3[['lon', 'lat']].iterrows(): 
            x = round_down(row['lon'], -4)
            y = round_down(row['lat'], -4)
            filtered3.loc[index, 'EOFORIGIN10km'] = x
            filtered3.loc[index, 'NOFORIGIN10km'] = y

            #x = round_down(row['lon'], -3)
            #y = round_down(row['lat'], -3)
            #filtered3.loc[index, 'EOFORIGIN1km'] = x
            #filtered3.loc[index, 'NOFORIGIN1km'] = y    

            #x = round(row['lon']/5000) * 5000
            #y = round(row['lat']/5000) * 5000
            #filtered3.loc[index, 'EOFORIGIN5km'] = x
            #filtered3.loc[index, 'NOFORIGIN5km'] = y        


        #filtered3['5kmCELLCODE'] = "5kmN" + (filtered3["NOFORIGIN5km"]/1000).astype(int).map(lambda x: f'{x:0>4}') + "E" (filtered3['EOFORIGIN5km']/1000).astype(int).map(lambda x: f'{x:0>4}') # vähemmän kuin 4 digits
        #filtered3['1kmCELLCODE'] = "1kmN" + (filtered3["NOFORIGIN1km"]/1000).astype(int).map(lambda x: f'{x:0>4}') + "E" + (filtered3['EOFORIGIN1km']/1000).astype(int).map(lambda x: f'{x:0>4}')
        filtered3['10kmCELLCODE'] = "10kmN" + (filtered3["NOFORIGIN10km"]/1000).astype(int).map(lambda x: f'{x:0>4}') + "E" + (filtered3['EOFORIGIN10km']/1000).astype(int).map(lambda x: f'{x:0>4}')

        # more than 5 observations from a grid
        filtered3['count'] = filtered3[['EOFORIGIN10km', 'NOFORIGIN10km', '10kmCELLCODE', 'yield', 'lon', 'lat']].groupby('10kmCELLCODE')['yield'].transform('count')
        filtered4 = filtered3[filtered3['count'] > 5]   

        filtered5 = filtered4[['EOFORIGIN10km', 'NOFORIGIN10km', '10kmCELLCODE', 'yield', 'lon', 'lat']].groupby('10kmCELLCODE').agg('mean').reset_index()
        
        
        filtered5['geometry4326'] = gpd.points_from_xy(filtered5['lon'], filtered5['lat'])
        filtered6 = filtered5[['EOFORIGIN10km', 'NOFORIGIN10km', '10kmCELLCODE', 'yield', 'geometry4326']].set_geometry('geometry4326')
        filtered6.crs = filtered2.crs  
        filtered7 = filtered6.to_crs('epsg:4326')
        filtered7['EOFORIGIN4326'] = filtered7.geometry4326.x
        filtered7['NOFORIGIN4326'] = filtered7.geometry4326.y

        filtered7['yield'] = round(filtered7['yield'],0)

        if type(year) is not int: # check
            year = int(year)  
            
        outputfile = os.path.join(yieldpath, 'Yields-' + croptype + '-' + cropname + '-' + str(year) + '.csv')
        print(f"Saving yields in {outputfile}")
        filtered7[['EOFORIGIN10km', 'NOFORIGIN10km', '10kmCELLCODE', 'yield', 'EOFORIGIN4326', 'NOFORIGIN4326']].to_csv(outputfile, index = False)
        
        return filtered7
    
    
def plotMaps(FIyields, croptype, cropname, year, imagepath, dfeuropaFIN):

    miny = 6632470
    maxy = 7400000
    
    plt.rcParams['text.usetex'] = True

    if type(year) is not int: # check
        year = int(year)
 
    # define min and max values and colormap for the plots
    if croptype == '3100':
        value_min = 10000
        value_max = 30000       
    else:
        value_min = 1000
        value_max = 5000
    cmap = 'YlGn'
    norm = mcolors.Normalize(vmin = value_min, vmax = value_max)
    
    fig = plt.figure(figsize = (6,10))
    ax_map = fig.add_axes([0, 0, 1, 1])
    dfeuropaFIN.plot(ax = ax_map, color = 'lightgray')#, color=colors) #['#C62828', '#283593', '#283593', '#FF9800'])
    ax_map.set_axis_off()

    gdf = gpd.GeoDataFrame(FIyields, geometry = gpd.points_from_xy(FIyields['EOFORIGIN10km'], FIyields['NOFORIGIN10km']), crs = 'EPSG:3067')

    gdf.plot(ax = ax_map, column = 'yield', marker = 's', markersize = 25, # marker = 'o' for bullet
                       vmin = value_min, vmax = value_max, cmap = cmap, norm = norm, edgecolor = None)

    ax_map.axis('off')
    #ax_map.set(title = cropname + ' ' + year)

    ax_map.annotate('Mean yield: ' + str(round(FIyields['yield'].mean())) + ' kg/ha',
        xy=(596327, 6823806),  xycoords='data', weight='bold',
    xytext=(0.35, 0.55), textcoords='axes fraction', # xytext=(0.95, 0.55)
    #arrowprops=dict(facecolor='black', shrink=0.05),
    horizontalalignment='right', verticalalignment='top',
    )


    # define a mappable based on which the colorbar will be drawn
    mappable = cm.ScalarMappable(
        norm = mcolors.Normalize(vmin = value_min, vmax = value_max),
        cmap = cmap
    )

    # define position and extent of colorbar
    #cb_ax = fig.add_axes([0.1, 0.1, 0.8, 0.05]) # horizontal
    cb_ax = fig.add_axes([1, .1, 0.025, 0.85])

    ax_map.set_title('Yields of ' + cropname + ' (' + str(year) + ') in 10km grid')
    # draw colorbar
    cbar = fig.colorbar(mappable, cax = cb_ax, orientation='vertical', label =  'Yield (kg/ha)')

    outfile = os.path.join(imagepath, 'Yields-' + croptype + '-' + cropname + '-' + str(year) + '.png')
    plt.savefig(outfile, dpi=300, bbox_inches='tight')
    print(f"Saving image in {outfile}")


    
    

    
    

# MAIN:
def main(args):
    try:
        if not args.inputfile or not args.crops or not args.shapefile:
            raise Exception('Missing input filepath or crop type argument. Try --help .')

        print(f'\n01-yield-grids-and-maps.py')
        
        
        imagepath = Path(os.path.expanduser(args.outputpath), 'img')
        imagepath.mkdir(parents=True, exist_ok=True)

        yieldpath = Path(os.path.expanduser(args.outputpath), 'yields')
        yieldpath.mkdir(parents=True, exist_ok=True)
        
        dfeuropa = gpd.read_file(fpeuropa)
        dfeuropaFIN = dfeuropa[(dfeuropa['TZID'] == 'Europe/Helsinki') | (dfeuropa['TZID'] == 'Europe/Mariehamn')].to_crs('epsg:3067')           
        
        gdf, year = readShapefile(args.shapefile)
        
        for croptype in args.crops:
            
            df2, cropname = readYields(args.inputfile, croptype, year)
            
            FIyields = mergeData(gdf, df2, croptype, yieldpath, cropname, year) 
                        
            print(f'Do a map of {cropname}')
            plotMaps(FIyields, croptype, cropname, year, imagepath, dfeuropaFIN)
        
        print(f'\nDone.')

    except Exception as e:
        print('\n\nUnable to read input or write output. Check prerequisites and see exception output below.')
        parser.print_help()
        raise e


if __name__ == '__main__':
    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
                                     epilog=textwrap.dedent(__doc__))

    parser.add_argument('-i', '--inputfile',
                        help='Filepath of raw yields.',
                        type=str)  
    parser.add_argument('-s', '--shapefile',
                        help='Filepath of shapefile containing parcel geometries.',
                        type=str)  
    parser.add_argument('-o', '--outputpath',
                        help='Filepath of outputs.',
                        type=str)  
    parser.add_argument('-c', '--crop', action='store', dest='crops',
                         type=str, nargs='*', default=['1310', '1320', '1400'],
                         help='Crop type(s). E.g. -c 1310 1320')    


    args = parser.parse_args()
    main(args)
