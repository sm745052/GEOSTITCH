import numpy as np


def custom_merge_works(merged_data, new_data, merged_data_mask, new_data_mask, index=None, roff=None, coff=None):
    '''
    Edit this function to change the merging algorithm.
    '''
    merged_data[:] = np.maximum(merged_data, new_data)