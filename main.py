import rasterio
from rasterio.warp import reproject
from rasterio.io import MemoryFile
import matplotlib.pyplot as plt
import numpy as np
from rasterio.features import sieve
import shutil
import cv2
import os



tmpA = shutil.copy("/content/GEOSTITCH/images/C01.tif", "/tmp/A.tif")
tmpB = shutil.copy("/content/GEOSTITCH/images/D01.tif", "/tmp/B.tif")


im1 = rasterio.open(tmpA, 'r+')
im2 = rasterio.open(tmpB, 'r+')


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



def save_raster(src, file, band = None):
  n=1
  if band is None:
    n = 3
  array = src.read()
  # black = np.all(np.rollaxis(array, 0, 3)==[0, 0, 0], axis=-1)
  # notblack = ~black
  # array = np.rollaxis(cv2.bitwise_and(np.rollaxis(array, 0, 3), np.rollaxis(array, 0, 3), mask = notblack.astype(np.uint8)), 2, 0)
  # array += (black * 255).astype(np.uint16)
  with rasterio.Env():

      # Write an array as a raster band to a new 8-bit file. For
      # the new file's profile, we start with the profile of the source
      profile = src.profile

      # And then change the band count to 1, set the
      # dtype to uint8, and specify LZW compression.
      profile.update(
          dtype=rasterio.uint8,
          count=n,
          compress='lzw')
  if n==3:
      with rasterio.open(file, 'w', **profile) as dst:
          dst.write(array.astype(rasterio.uint8))
  else:
      with rasterio.open(file, 'w', **profile) as dst:
          dst.write(array[band].astype(rasterio.uint8), 1)



def multibander(ls):
  n = len(ls)
  arr = np.array([i.read()[0] for i in ls]).astype(np.uint8)
  return create_dataset(arr, ls[0].profile['crs'], ls[0].transform)



im1.nodata = 0
im2.nodata = 0



msk1 = im1.read_masks()
new_msk1 = (msk1[0] & msk1[1] & msk1[2])
sieved_msk1 = sieve(new_msk1, size=10**6)
im1.write_mask(sieved_msk1)



msk2 = im2.read_masks()
new_msk2 = (msk2[0] & msk2[1] & msk2[2])
sieved_msk2 = sieve(new_msk2, size=10**6)
im2.write_mask(sieved_msk2)


for i in range(3):
  save_raster(im1, '/tmp/A'+str(i)+'.tif', i)
  save_raster(im2, '/tmp/B'+str(i)+'.tif', i)

# for i in range(3):
#   os.system('whitebox_tools -r=HistogramMatchingTwoImages -v --wd="/tmp/" --i1=A{}.tif --i2=B{}.tif -o=hm{}.tif'.format(i, i, i))

# hm0 = rasterio.open('/tmp/hm0.tif')
# hm1 = rasterio.open('/tmp/hm1.tif')
# hm2 = rasterio.open('/tmp/hm2.tif')

# im1 = multibander([hm0, hm1, hm2])

im2_reproj, im2_reproj_trans = reproject(
    source=rasterio.band(im2, [1, 2, 3]),
    dst_crs=im1.profile["crs"],
    dst_resolution=(30, 30),
)

im2_reproj_ds = create_dataset(im2_reproj, im1.profile["crs"], im2_reproj_trans)



for i in range(3):
  save_raster(im1, 'A'+str(i)+'.tif', i)
  save_raster(im2_reproj_ds, 'B'+str(i)+'.tif', i)




import os
for i in range(3):
  os.system('whitebox_tools -r=MosaicWithFeathering -v --wd="." --input1=./A{}.tif --input2=./B{}.tif -o=out{}.tif --method=cc --weight=4.0'.format(i, i, i))
  print(i, "done")



o0 = rasterio.open('./out0.tif')
o1 = rasterio.open('./out1.tif')
o2 = rasterio.open('./out2.tif')




o = multibander([o0, o1, o2])


save_raster(o, './final.tif')