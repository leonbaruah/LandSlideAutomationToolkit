from osgeo import gdal # Essential for geospatial data manipulation: r, w and transform raster and vector data formats

# Blueprint
class RasterUpsampler:
    # Constructor: used to initialise a new instance of the class
    # self refers to the new instance, while lower, higher and output are arguments
    def __init__(self, lower_res_path, higher_res_path, output_path):
        self.lower_res_path = lower_res_path # Path to lower resolution raster
        self.higher_res_path = higher_res_path # Path to higher resolution raster
        self.output_path = output_path # Output raster upsampled
    
    # Uses self to access the instance variables and methods
    def calculate_target_resolution(self):
        # This method tries to open the higher resolution raster
        dataset = gdal.Open(self.higher_res_path)
        if dataset is None: # if not
            raise FileNotFoundError(f"Could not open {self.higher_res_path}") # None
        
        geotransform = dataset.GetGeoTransform() # Retrieves geotransformation info: pixel width and height
        pixel_width = geotransform[1] # Second item in the tuple
        pixel_height = abs(geotransform[5])  # In case the raster is flipped, also is made positive with abs as it can be negative

        return (pixel_width, pixel_height) # Returns the tuple calculated pixel w and h

    # To perform raster upsampling
    def run_warp_tool(self):
        # Open lower resoltuon raster
        input_dataset = gdal.Open(self.lower_res_path)
        if input_dataset is None:
            raise FileNotFoundError(f"Could not open {self.lower_res_path}") # IF None

        # Retrieve the projection info from input dataset
        input_srs = input_dataset.GetProjection()
        # Get target pixel width and height
        target_resolution = self.calculate_target_resolution()
        # Unpuck the tuple in seperate variables 
        target_pixel_width, target_pixel_height = target_resolution

        # Specify format, target res ,  target spatial reference system and resampling algorithm
        warp_options = gdal.WarpOptions(format='GTiff',
                                        xRes=target_pixel_width, yRes=target_pixel_height,
                                        dstSRS=input_srs,
                                        resampleAlg=gdal.GRA_NearestNeighbour) # nearest neighbour

        gdal.Warp(self.output_path, input_dataset, options=warp_options) # performs the actual upsampling (warping) operation, taking the output path, input dataset, and warp options as arguments 
        # The upsampled raster is saved to self.output_path
        print(f"Upsampling completed. The upsampled raster is saved at: {self.output_path}")
