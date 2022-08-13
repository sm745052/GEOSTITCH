import numpy as np
import rasterio
from rasterio.warp import reproject
from rasterio.io import MemoryFile
from rasterio.merge import merge
from utils import custom_merge


im1 = rasterio.open("./images/fcc_R2_AW_20220405_091_047_B_01.tif")
im2 = rasterio.open("./images/fcc_R2A_AW_20220404_098_048_A_01.tif")


im2_reproj, im2_reproj_trans = reproject(
    source=rasterio.band(im2, [1, 2, 3]),
    dst_crs=im1.profile["crs"],
    dst_resolution=(30, 30),
)


def create_dataset(data, crs, transform):
    memfile = MemoryFile()
    dataset = memfile.open(
        driver="GTiff",
        height=data.shape[1],
        width=data.shape[2],
        count=3,
        crs=crs,
        transform=transform,
        dtype=data.dtype,
    )
    dataset.write(data, [1, 2, 3])
    return dataset


im2_reproj_ds = create_dataset(im2_reproj, im1.profile["crs"], im2_reproj_trans)

merged, transf = merge([im2_reproj_ds, im1], method=custom_merge)