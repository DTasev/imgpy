# Copyright (C) 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later

from typing import TYPE_CHECKING

import numpy as np
from PyQt5 import Qt
from PyQt5.QtWidgets import (QAction, QApplication, QCheckBox, QComboBox, QLabel, QMainWindow, QMenu, QMessageBox,
                             QPushButton, QSizePolicy, QSplitter, QStyle, QVBoxLayout)
from pyqtgraph import ImageItem

from mantidimaging.core.net.help_pages import open_api_webpage
from mantidimaging.gui.mvp_base import BaseMainWindowView
from mantidimaging.gui.utility import delete_all_widgets_from_layout
from mantidimaging.gui.widgets.mi_image_view.view import MIImageView
from mantidimaging.gui.widgets.stack_selector import StackSelectorWidgetView

from .filter_previews import FilterPreviews
from .presenter import FiltersWindowPresenter
from .presenter import Notification as PresNotification

if TYPE_CHECKING:
    from mantidimaging.gui.windows.main import MainWindowView  # noqa:F401  # pragma: no cover


class FiltersWindowView(BaseMainWindowView):
    auto_update_triggered = Qt.pyqtSignal()

    splitter: QSplitter
    collapseToggleButton: QPushButton

    linkImages: QCheckBox
    showHistogramLegend: QCheckBox
    combinedHistograms: QCheckBox
    invertDifference: QCheckBox
    overlayDifference: QCheckBox

    previewsLayout: QVBoxLayout
    previews: FilterPreviews
    stackSelector: StackSelectorWidgetView

    notification_icon: QLabel
    notification_text: QLabel

    presenter: FiltersWindowPresenter

    applyButton: QPushButton
    applyToAllButton: QPushButton
    filterSelector: QComboBox

    def __init__(self, main_window: 'MainWindowView'):
        super(FiltersWindowView, self).__init__(main_window, 'gui/ui/filters_window.ui')

        self.main_window = main_window
        self.presenter = FiltersWindowPresenter(self, main_window)
        self.roi_view = None
        self.roi_view_averaged = False
        self.splitter.setSizes([200, 9999])
        self.splitter.setStretchFactor(0, 1)

        # Populate list of operations and handle filter selection
        self.filterSelector.addItems(self.presenter.model.filter_names)
        self.filterSelector.currentTextChanged.connect(self.handle_filter_selection)
        self.filterSelector.currentTextChanged.connect(self._update_apply_all_button)
        self.handle_filter_selection("")

        # Handle stack selection
        self.stackSelector.stack_selected_uuid.connect(self.presenter.set_stack_uuid)
        self.stackSelector.stack_selected_uuid.connect(self.auto_update_triggered.emit)

        # Handle apply filter
        self.applyButton.clicked.connect(lambda: self.presenter.notify(PresNotification.APPLY_FILTER))
        self.applyToAllButton.clicked.connect(lambda: self.presenter.notify(PresNotification.APPLY_FILTER_TO_ALL))

        self.previews = FilterPreviews(self)
        self.previews.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.previewsLayout.addWidget(self.previews)
        self.clear_previews()

        self.combinedHistograms.stateChanged.connect(self.histogram_mode_changed)
        self.showHistogramLegend.stateChanged.connect(self.histogram_legend_is_changed)
        # set here to trigger the changed event
        self.showHistogramLegend.setChecked(True)

        self.linkImages.stateChanged.connect(self.link_images_changed)
        # set here to trigger the changed event
        self.linkImages.setChecked(True)
        self.invertDifference.stateChanged.connect(lambda: self.presenter.notify(PresNotification.UPDATE_PREVIEWS))
        self.overlayDifference.stateChanged.connect(lambda: self.presenter.notify(PresNotification.UPDATE_PREVIEWS))

        # Handle preview index selection
        self.previewImageIndex.valueChanged[int].connect(self.presenter.set_preview_image_index)

        # Preview update triggers
        self.auto_update_triggered.connect(self.on_auto_update_triggered)
        self.updatePreviewButton.clicked.connect(lambda: self.presenter.notify(PresNotification.UPDATE_PREVIEWS))

        self.stackSelector.subscribe_to_main_window(main_window)
        self.stackSelector.select_eligible_stack()

        # Handle help button pressed
        self.filterHelpButton.pressed.connect(self.open_help_webpage)
        self.collapseToggleButton.pressed.connect(self.toggle_filters_section)

    def cleanup(self):
        self.stackSelector.unsubscribe_from_main_window()
        if self.roi_view is not None:
            self.roi_view.close()
            self.roi_view = None
        self.auto_update_triggered.disconnect()
        self.main_window.filters = None
        self.presenter = None

    def show(self):
        super(FiltersWindowView, self).show()
        self.auto_update_triggered.emit()

    def handle_filter_selection(self, filter_name: str):
        """
        Handle selection of a filter from the drop down list.
        """
        # If a divider select the one below the divider.
        if filter_name == self.presenter.divider:
            self.filterSelector.setCurrentIndex(self.filterSelector.currentIndex() + 1)

        # Remove all existing items from the properties layout
        delete_all_widgets_from_layout(self.filterPropertiesLayout)

        # Do registration of new filter
        self.presenter.notify(PresNotification.REGISTER_ACTIVE_FILTER)

        # Update preview on filter selection (on the off chance the default
        # options are valid)
        self.auto_update_triggered.emit()

    def on_auto_update_triggered(self):
        """
        Called when the signal indicating the filter, filter properties or data
        has changed such that the previews are now out of date.
        """
        self.clear_notification_dialog()
        if self.previewAutoUpdate.isChecked() and self.isVisible():
            self.presenter.notify(PresNotification.UPDATE_PREVIEWS)

    def clear_previews(self):
        self.previews.clear_items()

    def histogram_mode_changed(self):
        combined_histograms = self.combinedHistograms.isChecked()
        self.previews.combined_histograms = combined_histograms

        # Clear old histogram bits
        self.previews.delete_histograms()
        self.previews.delete_histogram_labels()

        # Init the correct histograms
        if combined_histograms:
            self.previews.init_histogram()
        else:
            self.previews.init_separate_histograms()
        self.previews.update_histogram_data()

    def histogram_legend_is_changed(self):
        self.previews.histogram_legend_visible = self.showHistogramLegend.isChecked()
        legend = self.previews.histogram_legend
        if legend:
            if self.showHistogramLegend.isChecked():
                legend.show()
            else:
                legend.hide()

    def link_images_changed(self):
        if self.linkImages.isChecked():
            self.previews.link_all_views()
        else:
            self.previews.unlink_all_views()

    @property
    def preview_image_before(self) -> ImageItem:
        return self.previews.image_before

    @property
    def preview_image_after(self) -> ImageItem:
        return self.previews.image_after

    @property
    def preview_image_difference(self) -> ImageItem:
        return self.previews.image_difference

    def show_error_dialog(self, msg=""):
        self.notification_text.show()
        self.notification_icon.setPixmap(QApplication.style().standardPixmap(QStyle.SP_MessageBoxCritical))
        self.notification_text.setText(str(msg))

    def clear_notification_dialog(self):
        self.notification_icon.clear()
        self.notification_text.clear()
        self.notification_text.hide()

    def show_operation_completed(self, operation_name):
        self.notification_text.show()
        self.notification_icon.setPixmap(QApplication.style().standardPixmap(QStyle.SP_DialogYesButton))
        self.notification_text.setText(f"{operation_name} completed successfully!")

    def open_help_webpage(self):
        filter_id = self.presenter.model._find_filter_index_from_filter_name(self.filterSelector.currentText())
        filter_module_path = self.presenter.get_filter_module_name(filter_id)

        try:
            open_api_webpage(filter_module_path)
        except RuntimeError as err:
            self.show_error_dialog(str(err))

    def ask_confirmation(self, msg: str):
        response = QMessageBox.question(self, "Confirm action", msg, QMessageBox.Ok | QMessageBox.Cancel)  # type:ignore
        return response == QMessageBox.Ok

    def _update_apply_all_button(self, filter_name):
        list_of_apply_single_stack = ["ROI Normalisation", "Flat-fielding"]
        if filter_name in list_of_apply_single_stack:
            self.applyToAllButton.setEnabled(False)
        else:
            self.applyToAllButton.setEnabled(True)

    def roi_visualiser(self, roi_field):
        # Start the stack visualiser and ensure that it uses the ROI from here in the rest of this
        try:
            images = self.presenter.stack.presenter.get_image(self.presenter.model.preview_image_idx)
        except Exception:
            # Happens if nothing has been loaded, so do nothing as nothing can't be visualised
            return

        window = QMainWindow(self)
        window.setWindowTitle("Select ROI")
        window.setMinimumHeight(600)
        window.setMinimumWidth(600)
        self.roi_view = MIImageView(window)
        window.setCentralWidget(self.roi_view)
        self.roi_view.setWindowTitle("Select ROI for operation")

        def toggle_average_images(images_):
            if self.roi_view_averaged:
                self.roi_view.setImage(images_.data)
                self.roi_view_averaged = False
            else:
                averaged_images = np.sum(self.presenter.stack.presenter.images.data, axis=0)
                self.roi_view.setImage(averaged_images)
                self.roi_view_averaged = True
            self.roi_view.roi.show()
            self.roi_view.ui.roiPlot.hide()

        # Add context menu bits:
        menu = QMenu(self.roi_view)
        toggle_show_averaged_image = QAction("Toggle show averaged image", menu)
        toggle_show_averaged_image.triggered.connect(lambda: toggle_average_images(images))
        menu.addAction(toggle_show_averaged_image)
        menu.addSeparator()
        self.roi_view.imageItem.menu = menu

        self.roi_view.setImage(images.data)

        def roi_changed_callback(callback):
            roi_field.setText(callback.to_list_string())
            roi_field.editingFinished.emit()

        self.roi_view.roi_changed_callback = lambda callback: roi_changed_callback(callback)

        # prep the MIImageView to display in this context
        self.roi_view.ui.roiBtn.hide()
        self.roi_view.ui.histogram.hide()
        self.roi_view.ui.menuBtn.hide()
        self.roi_view.ui.roiPlot.hide()
        self.roi_view.roi.show()
        self.roi_view.ui.gridLayout.setRowStretch(1, 5)
        self.roi_view.ui.gridLayout.setRowStretch(0, 95)
        self.roi_view.button_stack_right.hide()
        self.roi_view.button_stack_left.hide()
        button = QPushButton("OK", window)
        button.clicked.connect(lambda: window.close())
        self.roi_view.ui.gridLayout.addWidget(button)

        window.show()

    def toggle_filters_section(self):
        if self.collapseToggleButton.text() == "<<":
            self.splitter.setSizes([0, 9999])
            self.collapseToggleButton.setText(">>")
        else:
            self.splitter.setSizes([200, 9999])
            self.collapseToggleButton.setText("<<")
