"""
Module containing helper functions relating to PyQt.
"""

from __future__ import absolute_import, division, print_function

import os

from PyQt5 import Qt, uic

from mantidimaging.core.utility import finder


class BlockQtSignals(object):
    """
    Used to block Qt signals from a selection of QWidgets within a context.
    """

    def __init__(self, q_objects):
        from PyQt5 import Qt
        for obj in q_objects:
            assert isinstance(obj, Qt.QObject), \
                "This class must be used with QObjects"

        self.q_objects = q_objects
        self.previous_values = None

    def __enter__(self):
        self.previous_values = \
            [obj.blockSignals(True) for obj in self.q_objects]

    def __exit__(self, *args):
        for obj, prev in zip(self.q_objects, self.previous_values):
            obj.blockSignals(prev)


def compile_ui(ui_file, qt_obj=None):
    base_path = os.path.join(
        finder.get_external_location(__file__), finder.ROOT_PACKAGE)
    return uic.loadUi(os.path.join(base_path, ui_file), qt_obj)


def select_file(field, caption):
    """
    :param field: The field in which the result will be saved
    :param caption: Title of the file browser window that will be opened
    :return: True: If a file has been selected, False otherwise
    """
    assert isinstance(field, Qt.QLineEdit), (
            "The passed object is of type {0}. This function only works with "
            "QLineEdit".format(type(field)))

    selected_file = Qt.QFileDialog.getOpenFileName(caption=caption)[0]
    # open file dialogue and set the text if file is selected
    if selected_file:
        field.setText(selected_file)
        return True

    # no file has been selected
    return False


def select_directory(field, caption):
    assert isinstance(field, Qt.QLineEdit), (
            "The passed object is of type {0}. This function only works with "
            "QLineEdit".format(type(field)))

    # open file dialogue and set the text if file is selected
    field.setText(Qt.QFileDialog.getExistingDirectory(caption=caption))


def add_property_to_form(label,
                         dtype,
                         default_value=None,
                         valid_values=None,
                         tooltip=None,
                         on_change=None,
                         form=None):
    """
    Adds a property to the algorithm dialog.

    Handles adding basic data options to the UI.

    :param label: Label that describes the option
    :param dtype: Option data type (any of: file, int, float, bool, list)
    :param default_value: Optionally select the default value
    :param valid_values: Optionally provide the range or selection of valid
                         values
    :param tooltip: Optional tooltip text to show on property
    :param on_change: Function to be called when the property changes
    :param form: Form layout to optionally add the new widgets to
    """
    # By default assume the left hand side widget will be a label
    left_widget = Qt.QLabel(label)
    right_widget = None

    def set_spin_box(box):
        """
        Helper function to set default options on a spin box.
        """
        if valid_values:
            box.setMinimum(valid_values[0])
            box.setMaximum(valid_values[1])
        if default_value:
            box.setValue(default_value)

    def assign_tooltip(widgets):
        """
        Helper function to assign tooltips to widgets.
        """
        if tooltip:
            for w in widgets:
                w.setToolTip(tooltip)

    # Set up data type dependant widgets
    if dtype == 'file':
        left_widget = Qt.QLineEdit()
        right_widget = Qt.QPushButton(label)
        assign_tooltip([left_widget, right_widget])
        right_widget.clicked.connect(
                lambda: select_file(left_widget, label))
        if on_change is not None:
            left_widget.textChanged.connect(lambda: on_change())

    elif dtype == 'int':
        right_widget = Qt.QSpinBox()
        assign_tooltip([right_widget])
        set_spin_box(right_widget)
        if on_change is not None:
            right_widget.valueChanged[int].connect(lambda: on_change())

    elif dtype == 'float':
        right_widget = Qt.QDoubleSpinBox()
        assign_tooltip([right_widget])
        set_spin_box(right_widget)
        if on_change is not None:
            right_widget.valueChanged[float].connect(lambda: on_change())

    elif dtype == 'bool':
        left_widget = None
        right_widget = Qt.QCheckBox(label)
        assign_tooltip([right_widget])
        if isinstance(default_value, bool):
            right_widget.setChecked(default_value)
        if on_change is not None:
            right_widget.stateChanged[int].connect(lambda: on_change())

    elif dtype == 'list':
        right_widget = Qt.QComboBox()
        assign_tooltip([right_widget])
        if valid_values:
            right_widget.addItems(valid_values)
        if on_change is not None:
            right_widget.currentIndexChanged[int].connect(lambda: on_change())

    elif dtype == 'label':
        pass

    else:
        raise ValueError("Unknown data type")

    # Add to form layout
    if form is not None:
        form.addRow(left_widget, right_widget)

    return (left_widget, right_widget)


def delete_all_widgets_from_layout(lo):
    """
    Removes and deletes all child widgets form a layout.

    :param lo: Layout to clean
    """
    # For each item in the layout (removed as iterated)
    while lo.count() > 0:
        item = lo.takeAt(0)

        # Recurse for child layouts
        if isinstance(item, Qt.QLayout):
            delete_all_widgets_from_layout(item)

        # Orphan child widgets (seting a None parent removes them from the
        # layout and marks them for deletion)
        elif item.widget() is not None:
            item.widget().setParent(None)