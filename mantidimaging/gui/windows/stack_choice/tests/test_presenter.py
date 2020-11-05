import unittest
from unittest import mock
from uuid import uuid4

import mantidimaging.test_helpers.unit_test_helper as th
from mantidimaging.gui.windows.stack_choice.view import Notification
from mantidimaging.gui.windows.stack_choice.presenter import StackChoicePresenter


class StackChoicePresenterTest(unittest.TestCase):
    def setUp(self):
        self.original_stack = th.generate_images()
        self.new_stack = th.generate_images()
        self.v = mock.MagicMock()
        self.op_p = mock.MagicMock()
        self.uuid = uuid4()
        self.p = StackChoicePresenter(original_stack=self.original_stack,
                                      new_stack=self.new_stack,
                                      operations_presenter=self.op_p,
                                      stack_uuid=self.uuid,
                                      view=self.v)

    def test_presenter_doesnt_raise_lists_for_original_stack(self):
        single_stack_uuid = uuid4()
        original_stack = [(th.generate_images(), single_stack_uuid), (th.generate_images(), uuid4())]
        StackChoicePresenter(original_stack, mock.MagicMock(), mock.MagicMock(), single_stack_uuid, mock.MagicMock())

    def test_presenter_throws_list_if_uuid_is_not_in_stack(self):
        single_stack_uuid = uuid4()
        original_stack = [(th.generate_images(), single_stack_uuid), (th.generate_images(), uuid4())]
        self.assertRaises(expected_exception=RuntimeError,
                          callable=StackChoicePresenter,
                          args=(original_stack, mock.MagicMock(), mock.MagicMock(), single_stack_uuid,
                                mock.MagicMock()))

    def test_show_calls_show_in_the_view(self):
        self.p.show()

        self.v.show.assert_called_once()

    def test_notify_choose_original(self):
        self.p.do_reapply_original_data = mock.MagicMock()

        self.p.notify(Notification.CHOOSE_ORIGINAL)

        self.p.do_reapply_original_data.assert_called_once()

    def test_notify_handles_exceptions(self):
        self.p.do_reapply_original_data = mock.MagicMock()
        self.p.do_reapply_original_data.side_effect = RuntimeError

        self.p.notify(Notification.CHOOSE_ORIGINAL)

        self.p.operations_presenter.show_error.assert_called_once()

    def test_notify_choose_new_data(self):
        self.p.do_clean_up_original_data = mock.MagicMock()

        self.p.notify(Notification.CHOOSE_NEW_DATA)

        self.p.do_clean_up_original_data.assert_called_once()

    def test_clean_up_original_images_stack(self):
        self.op_p.original_images_stack = [(1, self.uuid), (2, uuid4())]

        self.p._clean_up_original_images_stack()

        self.assertEqual(1, len(self.op_p.original_images_stack))
        self.assertEqual(2, self.op_p.original_images_stack[0][0])

        self.p._clean_up_original_images_stack()

        self.assertEqual(None, self.op_p.original_images_stack)

    def test_do_reapply_original_data(self):
        self.p._clean_up_original_images_stack = mock.MagicMock()
        self.p.close_view = mock.MagicMock()
        self.p.stack = 1

        self.p.do_reapply_original_data()

        self.op_p.main_window.presenter.model.set_images_in_stack.assert_called_once_with(self.uuid, 1)
        self.p._clean_up_original_images_stack.assert_called_once()
        self.assertTrue(self.v.choice_made)
        self.p.close_view.assert_called_once()

    def test_do_clean_up_original_data(self):
        self.p.stack = mock.MagicMock()
        self.p._clean_up_original_images_stack = mock.MagicMock()
        self.p.close_view = mock.MagicMock()

        self.p.do_clean_up_original_data()

        self.p._clean_up_original_images_stack.assert_called_once()
        self.p.stack.free_memory.assert_called_once()
        self.assertTrue(self.v.choice_made)
        self.p.close_view.assert_called_once()

    def test_close_view_calls_close_on_view(self):
        self.p.close_view()

        self.v.close.assert_called_once()

    def test_close_view_sets_done_true(self):
        self.p.close_view()

        self.assertTrue(self.p.done)