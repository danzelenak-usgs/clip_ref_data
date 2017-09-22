from collections import namedtuple
import numpy as np


class GetExtents:

    GeoExtent = namedtuple('GeoExtent', ['x_min', 'y_max', 'x_max', 'y_min'])
    GeoAffine = namedtuple('GeoAffine', ['ul_x', 'x_res', 'rot_1', 'ul_y', 'rot_2', 'y_res'])
    GeoCoordinate = namedtuple('GeoCoordinate', ['x', 'y'])
    RowColumn = namedtuple('RowColumn', ['row', 'column'])
    RowColumnExtent = namedtuple('RowColumnExtent', ['start_row', 'start_col', 'end_row', 'end_col'])

    CONUS_EXTENT = GeoExtent(x_min=-2565585,
                             y_min=14805,
                             x_max=2384415,
                             y_max=3314805)

    def __init__(self, h, v):
        """
        
        :param h: 
        :param v: 
        """

        self.H = h

        self.V = v

        self.TILE_EXTENT, self.PIXEL_AFFINE = self.geospatial_hv(self.H, self.V)

        self.chip_ulx_coords = [x for x in range(self.TILE_EXTENT.x_min, self.TILE_EXTENT.x_max, 3000)]
        self.chip_uly_coords = [y for y in range(self.TILE_EXTENT.y_max, self.TILE_EXTENT.y_min, -3000)]

        self.CHIP_UL = [self.GeoCoordinate(x=i, y=j) for j in self.chip_uly_coords for i in self.chip_ulx_coords]

        self.CHIP_EXTENTS = {ind + 1: self.get_chip_extent(chip_coord[0], chip_coord[1]) for ind, chip_coord in
                        enumerate(self.CHIP_UL)}

    def geo_to_rowcol(self, affine, coord):
        """
        Transform geo-coordinate to row/col given a reference affine.
        
        Yline = (Ygeo - GT(3) - Xpixel*GT(4)) / GT(5)
        Xpixel = (Xgeo - GT(0) - Yline*GT(2)) / GT(1)
    
        :param affine: 
        :param coord: 
        :return: 
        """

        row = (coord.y - affine.ul_y - affine.ul_x * affine.rot_2) / affine.y_res
        col = (coord.x - affine.ul_x - affine.ul_y * affine.rot_1) / affine.x_res

        return self.RowColumn(row=int(row),
                         column=int(col))

    def rowcol_to_geo(self, affine, rowcol):
        """
        Transform a row/col into a geospatial coordinate given reference affine.
        
        Xgeo = GT(0) + Xpixel*GT(1) + Yline*GT(2)
        Ygeo = GT(3) + Xpixel*GT(4) + Yline*GT(5)
        
        :param affine: 
        :param rowcol: 
        :return: 
        """

        x = affine.ul_x + rowcol.column * affine.x_res + rowcol.row * affine.rot_1
        y = affine.ul_y + rowcol.column * affine.rot_2 + rowcol.row * affine.y_res

        return self.GeoCoordinate(x=x, y=y)


    def geospatial_hv(self, h, v, loc=CONUS_EXTENT):
        """
        Geospatial extent and 30m affine for a given ARD grid location.
        
        :param h: 
        :param v: 
        :param loc: 
        :return: 
        """

        xmin = loc.x_min + h * 5000 * 30
        xmax = loc.x_min + h * 5000 * 30 + 5000 * 30
        ymax = loc.y_max - v * 5000 * 30
        ymin = loc.y_max - v * 5000 * 30 - 5000 * 30

        return (self.GeoExtent(x_min=xmin, x_max=xmax, y_max=ymax, y_min=ymin),
                self.GeoAffine(ul_x=xmin, x_res=30, rot_1=0, ul_y=ymax, rot_2=0, y_res=-30))


    def get_chip_extent(self, chip_ulx, chip_uly):
        """
        
        :param chip_ulx: 
        :param chip_uly: 
        :return: 
        """

        return self.GeoExtent(x_min=chip_ulx, x_max=chip_ulx + 3000,
                         y_min=chip_uly - 3000, y_max=chip_uly)

    def get_pixel_coords(self, chip_extent):
        """
        Generate the pixel ul coordinates
        :param chip_ul: 
        :return: 
        """

        chip_array = np.zeros((100,100))

        coord_keys = [(i, j) for i in range(100) for j in range(100)]

        pixel_x0 = chip_extent.x_min # + 15
        pixel_y0 = chip_extent.y_max # - 15

        pixel_x_coords = [pixel_x0 + (i * 30) for i in range(100)]
        pixel_y_coords = [pixel_y0 - (i * 30) for i in range(100)]

        pixel_dict = {coord_keys[ind_x + ind_y * 100] : self.GeoCoordinate(x=x, y=y)
                        for ind_y, y in enumerate(pixel_y_coords)
                        for ind_x, x in enumerate(pixel_x_coords)}

        return {coord_keys[ind_x + ind_y * 100] : self.GeoCoordinate(x=x, y=y)
                for ind_y, y in enumerate(pixel_y_coords)
                for ind_x, x in enumerate(pixel_x_coords)}
