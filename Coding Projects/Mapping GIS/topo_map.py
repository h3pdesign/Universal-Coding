import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import rasterio
from matplotlib.colors import LightSource

# Load DEM
with rasterio.open("/Users/h3p/Coding/3DMapProject/N00E000.tif") as src:
    dem = src.read(1)
    extent = [src.bounds.left, src.bounds.right, src.bounds.bottom, src.bounds.top]

fig = plt.figure(figsize=(12, 8))
ax = plt.axes(projection=ccrs.PlateCarree())
ax.set_extent(extent)

# Hillshade for 3D effect
ls = LightSource(azdeg=315, altdeg=45)
shaded = ls.hillshade(dem, vert_exag=5)
ax.imshow(shaded, cmap='gray', extent=extent, transform=ccrs.PlateCarree(), alpha=0.7)

# Add land and ocean
ax.add_feature(cfeature.LAND, facecolor='0.8', edgecolor='none')
ax.add_feature(cfeature.OCEAN, facecolor='lightblue', alpha=0.6)

ax.coastlines()
ax.add_feature(cfeature.BORDERS)
plt.title('3D-Like Topographic Map of North America')
plt.savefig('/Users/h3p/Coding/3DMapProject/north_america_topo.png', dpi=300, bbox_inches='tight')
plt.show()π