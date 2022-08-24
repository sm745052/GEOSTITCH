import rasterio
from rasterio.warp import reproject
from rasterio.io import MemoryFile
import matplotlib.pyplot as plt
import numpy as np
from rasterio.features import sieve
import shutil
import cv2
import os
import sys
import whitebox





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
  with rasterio.Env():
      profile = src.profile
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



# im1.nodata = 0
# im2.nodata = 0



# msk1 = im1.read_masks()
# new_msk1 = (msk1[0] & msk1[1] & msk1[2])
# sieved_msk1 = sieve(new_msk1, size=10**6)
# im1.write_mask(sieved_msk1)



# msk2 = im2.read_masks()
# new_msk2 = (msk2[0] & msk2[1] & msk2[2])
# sieved_msk2 = sieve(new_msk2, size=10**6)
# im2.write_mask(sieved_msk2)


# for i in range(3):
#   save_raster(im1, '/tmp/A'+str(i)+'.tif', i)
#   save_raster(im2, '/tmp/B'+str(i)+'.tif', i)

# # for i in range(3):
# #   os.system('whitebox_tools -r=HistogramMatchingTwoImages -v --wd="/tmp/" --i1=A{}.tif --i2=B{}.tif -o=hm{}.tif'.format(i, i, i))

# # hm0 = rasterio.open('/tmp/hm0.tif')
# # hm1 = rasterio.open('/tmp/hm1.tif')
# # hm2 = rasterio.open('/tmp/hm2.tif')

# # im1 = multibander([hm0, hm1, hm2])

# im2_reproj, im2_reproj_trans = reproject(
#     source=rasterio.band(im2, [1, 2, 3]),
#     dst_crs=im1.profile["crs"],
#     dst_resolution=(30, 30),
# )

# im2_reproj_ds = create_dataset(im2_reproj, im1.profile["crs"], im2_reproj_trans)



# for i in range(3):
#   save_raster(im1, 'A'+str(i)+'.tif', i)
#   save_raster(im2_reproj_ds, 'B'+str(i)+'.tif', i)




# import os
# for i in range(3):
#   os.system('whitebox_tools -r=MosaicWithFeathering -v --wd="." --input1=./A{}.tif --input2=./B{}.tif -o=out{}.tif --method=cc --weight=4.0'.format(i, i, i))
#   print(i, "done")



# o0 = rasterio.open('./out0.tif')
# o1 = rasterio.open('./out1.tif')
# o2 = rasterio.open('./out2.tif')




# o = multibander([o0, o1, o2])


# save_raster(o, './final.tif')


def correct_dtype(x):
    ob = rasterio.open(x)
    save_raster(ob, input)



if __name__ == '__main__':
    wbt = whitebox.WhiteboxTools()
    os.system('mkdir tmp')
    image_files = sys.argv[1:]
    raw_names = [i.split('/')[-1][:-4] for i in image_files]
    print("copying images to ./tmp/")
    tmps = [shutil.copy(i, os.path.join('./tmp', i.split('/')[-1])) for i in image_files]
    rasters = [rasterio.open(i, "r+") for i in tmps]
    print("setting nodata values")
    for i in rasters:
        i.nodata = 0
    print("seiving masks")
    for i in rasters:
        msk = i.read_masks()
        new_msk = (msk[0] & msk[1] & msk[2])
        sieved_msk1 = sieve(new_msk, size=10**6)
        i.write_mask(sieved_msk1)
    print("reprojecting and saving rasters")
    for ind, i in enumerate(rasters[1:]):
        im_reproj, im_reproj_trans = reproject(
            source=rasterio.band(i, [1, 2, 3]),
            dst_crs=rasters[0].profile["crs"],
            dst_resolution=(30, 30),
        )
        im_reproj_ds = create_dataset(im_reproj, i.profile["crs"], im_reproj_trans)
        for j in range(3):
            save_raster(im_reproj_ds,  tmps[1:][ind][:-4]+'___'+str(j)+'.tif', j)
    for j in range(3):
        save_raster(rasters[0],  tmps[0][:-4]+'___'+str(j)+'.tif', j)
    done = {raw_names[0]}
    for i in raw_names[1:]:
        for j in range(3):
            input1 = './tmp/' + raw_names[0] + '___' + str(j) + '.tif'
            input2 = './tmp/' + i + '___' + str(j) + '.tif'
            r = os.system('whitebox_tools --run="MosaicWithFeathering" --input1={} --input2={} --output={} --method=cc --weight=4.0'.format(input1, input2, input1))
            correct_dtype(input1)
            if(r==0):
                done.add(i)
            else:
                print("error in {}, band = {}".format(i, j))


    o = multibander([rasterio.open('./tmp/' + raw_names[0] + '___' + str(j)+'.tif') for j in range(3)])
    save_raster(o, './final.tif')
    print("successfully appended", done)