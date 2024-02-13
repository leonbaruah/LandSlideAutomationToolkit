import geopandas as gpd # For handling geographic data
import rasterio # For reading and writing raster datasets
from rasterio.mask import mask # For masking raster datasets with geometric shapes
import json # For parsin json format data

# Blueprint
class RasterMasker:
    def __init__(self, raster_path, shp_path, output_path):
        # Constructor method to initialise the class object
        self.raster_path = raster_path # Path to the input raster dataset
        self.shp_path = shp_path # Path to the shapefile 
        self.output_path = output_path # Path to where the masked_raster will be saved

    @staticmethod
    def get_features(gdf):
        """Convert geodataframe to JSON features."""
        # This method converts a GDF to a list of geometry features in json format
        # GDF: loaded from a shapefile
        # The method uses list to iterate over each feature in the gdf
        # Converts to json format and extracts the geometry part of each feature
        return [json.loads(gdf.to_json())['features'][i]['geometry'] for i in range(len(gdf))]

    def mask_raster_with_shp(self):
        """Mask raster with Shapefile boundaries and save as new TIFF."""
        # This method performs the main functionality of masking a raster dataset using a shp
        try:
            gdf = gpd.read_file(self.shp_path) # To load shp as gdf
            with rasterio.open(self.raster_path) as src:
                # Open input
                geoms = self.get_features(gdf) # Convert gdf to json features
                out_image, out_transform = mask(src, geoms, crop=True) # Mask application
                out_meta = src.meta.copy() # Copy metadata of the source raster
            
            # Update metadata
            out_meta.update({
                "driver": "GTiff", # Set the format of the output raster to TIFF
                "height": out_image.shape[1], # Update height from the output image dimensions
                "width": out_image.shape[2], # Update the width from the output image dimensions
                # The affine transformation parameters are encapsulated in the "transform" attribute in the script. 
                # When the script updates the "transform" with out_transform, 
                # it is effectively updating these parameters to match the new coordinates and orientation of the masked raster dataset. 
                "transform": out_transform
            })

            with rasterio.open(self.output_path, "w", **out_meta) as dest:
                # Open a new tiff file for writing the masked dataset
                dest.write(out_image) # Write to the file

            print(f"Masked raster saved to {self.output_path}")
            return self.output_path  # Return the path of the masked output
        except Exception as e:
            print(f"An error occurred: {e}")
            return None
