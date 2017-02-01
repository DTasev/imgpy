from __future__ import (absolute_import, division, print_function)
from recon.helper import Helper

from recon.data.loader import get_file_names, nxsread, parallel_move_data, do_stack_load_par, do_stack_load_seq, load_stack


def execute(input_path, img_format, data_dtype, cores, chunksize, parallel_load, h):
    h = Helper.empty_init() if h is None else h

    return _do_nxs_load(input_path, img_format, data_dtype, cores, chunksize, parallel_load, h)


def _do_nxs_load(input_path, img_format, data_dtype, cores, chunksize, parallel_load, h):
    """
    Do loading from NEXUS .nxs file, this requires special handling of the data, because flat and dark images are
    appended to the array.

    :param input_path: Path for the input data folder
    :param img_format: format for the input images
    :param data_dtype: Default:np.float32, data type for the input images
    :param cores: Default:1, cores to be used if parallel_load is True
    :param chunksize: chunk of work per worker
    :param parallel_load: Default: False, if set to true the loading of the data will be done in parallel.
            This could be faster depending on the IO system. For local HDD runs the recommended setting is False
    :param h: Optional helper class. If not provided an empty one will be initialised.
    :returns :: stack of images as a 3-elements tuple: numpy array with sample images, white image, and dark image.
    """
    data_file = get_file_names(input_path, img_format)

    data = load_stack(nxsread, data_file[0], data_dtype, "NXS Load", cores, chunksize, parallel_load, h)

    return data[:-2, :, :], data[-2, :, :], data[-1, :, :]


def _do_stack_move_seq(data, new_data, img_shape, name, h):
    """
    Sequential version of loading the data.
    This performs faster locally, but parallel performs faster on SCARF

    :param data: shared array of data
    :param load_func:
    :param file_name: the name of the stack file
    :param img_shape:
    :param name:
    :param h:
    :return:
    """
    # this will open the file but not read all of it in
    h.prog_init(img_shape[0], name)
    for i in range(img_shape[0]):
        data[i] = new_data[i]
        h.prog_update()
    h.prog_close()
    return data


def _do_stack_move_par(data, new_data, cores, chunksize, name, h):
    # this runs faster on SCARF
    from parallel import two_shared_mem as ptsm
    f = ptsm.create_partial(parallel_move_data, fwd_function=ptsm.inplace_fwd_func)
    ptsm.execute(new_data, data, f, cores, chunksize, name, h=h)
    return data
