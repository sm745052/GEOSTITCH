import numpy as np
import rasterio
from rasterio.warp import reproject
from rasterio.io import MemoryFile
from rasterio.merge import merge
import matplotlib.pyplot as plt
import cv2
import os
import numpy as np



def edit_raster(src, method, file):
    with rasterio.Env():
        # Write an array as a raster band to a new 8-bit file. For
        # the new file's profile, we start with the profile of the source
        profile = src.profile
        arr = src.read()
        arr = np.rollaxis(arr, 0, 3)
        arr = method(arr)
        arr = np.rollaxis(arr, 2, 0)
        # And then change the band count to 1, set the
        # dtype to uint8, and specify LZW compression.
        profile.update(
            dtype=rasterio.uint8,
            count=3,
            compress='lzw')
        with rasterio.open(file, 'w', **profile) as dst:
            dst.write(arr.astype(rasterio.uint8))








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
    new_mask1 = np.all(new_image != [0, 0, 0], axis = -1)
    new_mask2 = np.all(new_image != [255, 255, 255], axis = -1)
    new_mask = new_mask1 & new_mask2
    new_image[:] = cv2.bitwise_and(new_image, new_image, mask = new_mask.astype(np.uint8))
    # plt.imshow(merged_image)
    # plt.show()
    # plt.imshow(new_image)
    # plt.show()
    # new_image = cv2.bitwise_and(new_image,new_image, mask = new_mask.astype(np.uint8))
    merged_data[:] = np.rollaxis(np.maximum(merged_image, new_image), 2, 0)




im1 = rasterio.open("./images/fcc_R2_AW_20220405_091_047_B_01.tif")
im2 = rasterio.open("./images/fcc_R2A_AW_20220404_098_048_A_01.tif")


print("writing images")
cv2.imwrite('./src.tif', im2)
cv2.imwrite('./ref.tif', im1)
print("correcting colour")
os.system("cd image-statistics-matching && python3 main.py hm -m 1.0 -s rgb -c 0,1,2 -p ../src.tif ../ref.tif ../out.tif")
print("reading new image")
im2[:] = plt.imread('./out.tif')



print("transforming")
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


print("Merging")
merged, transf = merge([im2_reproj_ds, im1], method = custom_merge)