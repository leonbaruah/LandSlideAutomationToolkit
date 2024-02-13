import geopandas as gpd
import rasterio
from rasterio.mask import mask as rasterio_mask
import numpy as np
import pandas as pd

# Defining class to encapsulate the logic for analysing population in areas at risk of landslide
class LandslidePopulationAnalysis:
    def __init__(self, shp_path, landslide_raster_path, population_raster_path): # Constructor for initisialising instances of class
        self.shp_path = shp_path # Path to AOI
        self.landslide_raster_path = landslide_raster_path # Path to landslide risk raster
        self.population_raster_path = population_raster_path # Path to the population raster

    # Methof for masking a raster dataset with a given geometry, used to focus on specific areas
    def mask_raster(self, raster_path, geometry):
        try:
            with rasterio.open(raster_path) as src: # Open raster file for reading
                # Apply the mask function to crop the raster to the provided geometry 
                out_image, out_transform = rasterio_mask(src, [geometry], crop=True)
                out_meta = src.meta.copy()
            return out_image, out_transform, out_meta
        except Exception as e:
            print(f"Error masking raster {raster_path}: {e}") # Print any errors
            return None, None, None # Return none values indicating the operation failed

    def calculate_population_in_risk_areas(self): # Method to calculate the population in areas designated as high risk for landslide
        try:
            gdf = gpd.read_file(self.shp_path) # Load the shapefile
        except Exception as e:
            print(f"Error reading shapefile {self.shp_path}: {e}") # If there is error loading the shape print it
            return pd.DataFrame()

        results = []

        for _, row in gdf.iterrows(): # Iterate over each row in the gdf
            geometry = row['geometry'] # Extract geometry for the current row
            # Mask the landslide and population rasters with the current geometry
            landslide_image, _, landslide_meta = self.mask_raster(self.landslide_raster_path, geometry)
            population_image, _, population_meta = self.mask_raster(self.population_raster_path, geometry)

            # Skip if there was an error masking the raster
            if landslide_image is None or population_image is None:
                continue

            # Resize images to have the same shape
            # Determine the max dimensions to standardise the size of both rasters
            max_rows = max(landslide_image.shape[1], population_image.shape[1])
            max_cols = max(landslide_image.shape[2], population_image.shape[2])

            # Create padded versions of both rasters filled with their respective nodata values:
            # Create a new array filled with the NoData value from the landslide raster's metadata.
            # This array will have one layer (1 in the shape tuple) and dimensions specified by max_rows and max_cols.
            # The dimensions are calculated to ensure it can hold either the landslide or the population data,
            # whichever is larger, thereby standardising the size for comparison.
            # np.full() creates an array of the given shape and fills it with the specified value, in this case, the NoData value,
            # which is used to indicate missing data within a raster. The dtype (data type) is matched to that of the original landslide image
            # to ensure consistency in data representation.
            landslide_padded = np.full((1, max_rows, max_cols), landslide_meta['nodata'], dtype=landslide_image.dtype)
            # Now, insert the original landslide image data into the padded array.
            # This step involves copying the data from the landslide_image into the appropriate section of the landslide_padded array.
            # The slicing [:, :landslide_image.shape[1], :landslide_image.shape[2]] specifies where the original data should be placed:
            # - The first colon (:) indicates that this operation applies to all bands of the raster (in this case, there's only one).
            # - The second part (:landslide_image.shape[1]) specifies that the rows of the original image data should fill the rows from the start up to its own row count.
            # - Similarly, the third part (:landslide_image.shape[2]) specifies that the columns of the original image data should fill the columns from the start up to its own column count.
            # This effectively overlays the original landslide raster data onto the top-left corner of the new, larger padded array,
            # leaving the remainder of the array filled with the NoData value. This is crucial for maintaining the original data's integrity
            # while standardizing the array size for subsequent analysis, allowing direct comparison or mathematical operations with another similarly padded array.
            #landslide_padded[:, :landslide_image.shape[1], :landslide_image.shape[2]] = landslide_image
            landslide_padded[:, :landslide_image.shape[1], :landslide_image.shape[2]] = landslide_image

            # same logic
            population_padded = np.full((1, max_rows, max_cols), population_meta['nodata'], dtype=population_image.dtype)
            population_padded[:, :population_image.shape[1], :population_image.shape[2]] = population_image

            # Use the padded arrays for further analysis
            # subsequent analysis
            landslide_image = landslide_padded
            population_image = population_padded

            # Extract the NoData value from the population raster's metadata
            # Replace with NaN for numerical operations
            population_nodata = population_meta.get('nodata', np.nan)

            # Mask out the NoData values from the population raster
            population_image = np.where(population_image == population_nodata, np.nan, population_image)

            # Identify high-risk areas (3, 4 are high-risk)
            high_risk_mask = np.isin(landslide_image, [3, 4], assume_unique=True)

            # Calculate population at risk, ignoring NoData values
            # by applying the high-risk mask to the population raster
            population_at_risk = np.where(high_risk_mask, population_image, np.nan)
            total_population_at_risk = np.nansum(population_at_risk) # Sum the population at risk, ignoring nan

            total_population_at_risk = np.round(total_population_at_risk) # Round the total pop at risk t eliminate decimal, if any

            # Handle potential negative values caused by incorrect data or calculations
            if total_population_at_risk < 0:
                print(f"Negative population at risk for {row['ADM2_EN']}. Setting to zero, check your data.")
                total_population_at_risk = 0

            # Append the results for the current area to the results list
            results.append({
                "admin_boundary": row['ADM2_EN'],
                "total_population_at_risk": total_population_at_risk
            })

        return pd.DataFrame(results) # Convert list to gdf and return it


    # Export to csv
    def export_to_csv(self, output_path):
        df = self.calculate_population_in_risk_areas()
        if not df.empty:
            df.to_csv(output_path, index=False)
            print(f"Data exported to {output_path}")
        else:
            print("No data to export.")
