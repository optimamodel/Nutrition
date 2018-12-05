import geopandas
import matplotlib.pyplot as plt

raw_shapes = geopandas.read_file("shapefiles/gadm36_COD_1.shp")
drc = raw_shapes[['NAME_1', 'geometry']]
drc.rename(columns={'NAME_1': 'province'}, inplace=True)

# Index by row/column names (: means the whole thing)
#drc.loc[:, 'province']
# Index by row and column number
#drc.iloc[3, 1]
#drc.shape

# read_data = geopandas.read_csv('shapefiles\data.csv')
fig = plt.figure()
ax = fig.subplots()
ax.set_axis_off()
ax.set_aspect('equal')

drc.plot(ax=ax, column='province', cmap='Greens', facecolor='white')
#ax.annotate('Current\nutilization\nof existing\nmachines', ha='center', va='bottom', color='black',
           #xy=(100, 45), xytext=(100, 40), arrowprops=dict(facecolor='black', shrink=0.05))
#ax.set_ylabel('Average % capacity to run new machines')
#ax.set_xlabel('Number of machines deployed')
ax.set_title('Under 5 mortality')
fig.savefig('drc.png', transparent=True, bbox_inches='tight', pad_inches=0)
