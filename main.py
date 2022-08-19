import numpy as np
import rasterio
from rasterio.warp import reproject
from rasterio.io import MemoryFile
from rasterio.merge import merge
import matplotlib.pyplot as plt
import cv2

import numpy as np

def custom_merge(merged_data, new_data, merged_data_mask, new_data_mask, index=None, roff=None, coff=None):
    '''
    Edit this function to change the merging algorithm.
    '''
    merged_image = np.rollaxis(merged_data, 0, 3)
    new_image = np.rollaxis(new_data, 0, 3)
    merged_mask1 = np.all(merged_image != [0, 0, 0], axis = -1)
    merged_mask2 = np.all(merged_image != [255, 255, 255], axis = -1)
    merged_mask = merged_mask1 & merged_mask2
    merged_image[:] = cv2.bitwise_and(merged_image, merged_image, mask = merged_mask.astype(np.uint8))
    merged_mask = np.all(merged_image != [0, 0, 0], axis = -1)
    merged_image = cv2.cvtColor(merged_image, cv2.COLOR_RGB2RGBA)
    merged_image[:, :, 3] = merged_mask
    new_mask1 = np.all(new_image != [0, 0, 0], axis = -1)
    new_mask2 = np.all(new_image != [255, 255, 255], axis = -1)
    new_mask = new_mask1 & new_mask2
    new_image[:] = cv2.bitwise_and(new_image, new_image, mask = new_mask.astype(np.uint8))
    new_mask = np.all(new_image != [0, 0, 0], axis = -1)
    new_image = cv2.cvtColor(new_image, cv2.COLOR_RGB2RGBA)
    new_image[:, :, 3] = new_mask
    merged_image_float = merged_image.astype(float)
    new_image_float = new_image.astype(float)
    opacity = 0.7
    blended_img = soft_light(merged_image_float, new_image_float, opacity).astype(np.uint8)
    merged_data[:] = np.rollaxis(blended_img, 2, 0)




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

merged, transf = merge([im2_reproj_ds, im1], method = custom_merge)