from functools import partial

import numpy as np

from mantidimaging.core.filters.base_filter import BaseFilter
from mantidimaging.core.tools import importer
from mantidimaging.core.utility.progress_reporting import Progress
from mantidimaging.gui.utility import add_property_to_form

OUTLIERS_DARK = 'dark'
OUTLIERS_BRIGHT = 'bright'
_default_radius = 3
_default_mode = OUTLIERS_BRIGHT


class OutliersFilter(BaseFilter):
    filter_name = "Remove Outliers"

    def _filter_func(self, data, diff=None, radius=_default_radius, mode=_default_mode,
                     cores=None, progress=None):
        """
        Requires tomopy to be available.

        :param data: Input data as a 3D numpy.ndarray
        :param diff: Pixel value difference above which to crop bright pixels
        :param radius: Size of the median filter to apply
        :param mode: Spot brightness to remove.
                     Either 'bright' or 'dark'.
        :param cores: The number of cores that will be used to process the data.

        :return: The processed 3D numpy.ndarray
        """
        progress = Progress.ensure_instance(progress,
                                            task_name='Outliers')

        if diff and radius and diff > 0 and radius > 0:
            with progress:
                progress.update(msg="Applying outliers with threshold: {0} and "
                                    "radius {1}".format(diff, radius))

                # we flip the histogram horizontally, this makes the darkest pixels
                # the brightest
                if mode == OUTLIERS_DARK:
                    np.negative(data, out=data)

                tomopy = importer.do_importing('tomopy')

                data = tomopy.misc.corr.remove_outlier(
                    data, diff, radius, ncore=cores)

                # reverse the inversion
                if mode == OUTLIERS_DARK:
                    np.negative(data, out=data)

        return data

    def register_gui(self, form, on_change):
        _, diff_field = add_property_to_form(
            'Difference', 'int', 1, (-1000000, 1000000),
            form=form, on_change=on_change)

        _, size_field = add_property_to_form(
            'Size', 'int', 3, (0, 1000),
            form=form, on_change=on_change)

        _, mode_field = add_property_to_form(
            'Mode', 'choice', valid_values=modes(),
            form=form, on_change=on_change)

        return {
            'diff_field': diff_field,
            'size_field': size_field,
            'mode_field': mode_field
        }

    def execute_wrapper(self, diff_field=None, size_field=None, mode_field=None):
        return partial(self._filter_func,
                       diff=diff_field.value(),
                       radius=size_field.value(),
                       mode=mode_field.currentText())


def _cli_register(parser):
    parser.add_argument(
        "--outliers",
        required=False,
        type=float,
        help="Pixel difference above which to crop bright pixels.")

    parser.add_argument(
        "--outliers-radius",
        default=_default_radius,
        required=False,
        type=int,
        help="Default: %(default)s. "
             "Radius for the median filter to determine the outlier.")

    parser.add_argument(
        "--outliers-mode",
        default=_default_mode,
        required=False,
        type=str,
        help="Default: %(default)s. "
             "Crop bright or dark pixels.\n"
             "Cropping dark pixels is more expensive. "
             "It will invert the image before and after removing the outliers")

    return parser


def modes():
    return [OUTLIERS_BRIGHT, OUTLIERS_DARK]
