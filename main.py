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





def rearrange(image_files):
    rasters = [rasterio.open(i) for i in image_files]
    bboxes = [i.bounds for i in rasters]
    for i in range(len(rasters)-1):
        for j in range(i+1, len(rasters)):
            if(not rasterio.coords.disjoint_bounds(bboxes[i], bboxes[j])):
                tmp = rasters[j]
                rasters[j] = rasters[i]
                rasters[i] = tmp
                tmp = image_files[j]
                image_files[j] = image_files[i]
                image_files[i] = tmp
                break
    return image_files



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




def correct_dtype(x):
    ob = rasterio.open(x)
    try:
        save_raster(ob, x, 0)
    except:
        save_raster(ob, x)



if __name__ == '__main__':
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
        save_raster(im_reproj_ds, tmps[1:][ind][:-4]+'.tif')
        for j in range(3):
            save_raster(im_reproj_ds,  tmps[1:][ind][:-4]+'___'+str(j)+'.tif', j)
    for j in range(3):
        save_raster(rasters[0],  tmps[0][:-4]+'___'+str(j)+'.tif', j)
    

    image_files = rearrange(image_files)
    raw_names = [i.split('/')[-1][:-4] for i in image_files]
    print(raw_names)

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