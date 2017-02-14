from __future__ import (absolute_import, division, print_function)
from imgdata.loader import get_folder_names, get_file_names


def execute(config):
    from helper import Helper
    h = Helper(config)
    output_dir = config.func.output_path
    from imgdata.saver import Saver
    s = Saver(config, h)
    # fail early if invalid directory
    s.make_dirs_if_needed()

    from imgdata import loader
    sample, flat, dark = loader.load_data(config, h)
    s.save(
        sample,
        output_dir,
        config.func.convert_prefix,
        flat,
        dark,
        zfill_len=0)
