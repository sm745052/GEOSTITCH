# AIS

AIS is a software to do image blending of satelite GIS images implemented in python using Rasterio

## Dependencies

Use the package manager [pip](https://pip.pypa.io/en/stable/) to install the requirements.

```bash
pip install -r requirements.txt
```

## TODO

go to utils.py.

edit the custom merge function.

run main.py to see the results of your merging algorithm

Example custom merge:
```python
def custom_merge_works(merged_data, new_data, merged_data_mask, new_data_mask, index=None, roff=None, coff=None):
    '''
    Edit this function to change the merging algorithm.
    '''
    merged_data[:] = np.maximum(merged_data, new_data)
```

## Contributing
Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

Please make sure to update tests as appropriate.

## License
[MIT](https://choosealicense.com/licenses/mit/)