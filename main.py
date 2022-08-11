import numpy as np
import matplotlib.pyplot as plt
import rasterio
from rasterio.warp import reproject
from rasterio.io import MemoryFile
from rasterio.merge import merge

import chainer
from chainer import cuda, serializers
from skimage import img_as_float
from skimage.io import imread, imsave
from gp_gan import gp_gan
from model import EncoderDecoder, DCGAN_G



tds = rasterio.open("./images/11.tif")
sds = rasterio.open("./images/14.tif")
G = EncoderDecoder(64, 64, 3, 4000, image_size=64)
serializers.load_npz('models/blending_gan.npz', G)
try:
    cuda.get_device(0).use()  # Make a specified GPU current
    G.to_gpu()  # Copy the model to the GPU
except:
    print("gpu not found at 0")



im1_reproj, im1_reproj_trans = reproject(
    source=rasterio.band(sds, [1, 2, 3]),
    dst_crs=tds.profile["crs"],
    dst_resolution=(30, 30),
)


def custom_merge_works(old_data, new_data, old_nodata, new_nodata, index=None, roff=None, coff=None):
    print(old_data.shape)
    print(new_data.shape)
    obj = new_data
    bg = old_data
    black_pixels_mask = np.all(new_data == [0, 0, 0], axis=-1)
    mask = ~black_pixels_mask
    with chainer.using_config("train", False):
        blended_im = gp_gan(obj, bg, mask, G, 64, 0, color_weight=1,
                            sigma=0.5,
                            gradient_kernel="normal", smooth_sigma=1,
                            supervised=True,
                            nz=100, n_iteration=1000)
    old_data[:] = np.maximum(old_data, new_data)


def create_dataset(data, crs, transform):
    # Receives a 2D array, a transform and a crs to create a rasterio dataset
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


im1_reproj_ds = create_dataset(im1_reproj, tds.profile["crs"], im1_reproj_trans)

merged, transf = merge([im1_reproj_ds, tds], method=custom_merge_works)
