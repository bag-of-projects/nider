import math
import os
import unittest

from unittest import mock

from PIL import Image as PIL_Image
from PIL import ImageDraw
from PIL import ImageEnhance
from PIL import ImageFilter

from nider.core import MultilineTextUnit

from nider.models import Content
from nider.models import FacebookLandscapePost
from nider.models import FacebookSquarePost
from nider.models import Header
from nider.models import Image
from nider.models import InstagramLandscapePost
from nider.models import InstagramPortraitPost
from nider.models import InstagramSquarePost
from nider.models import Linkback
from nider.models import Paragraph
from nider.models import TwitterLargeCard
from nider.models import TwitterPost


from nider.utils import create_test_image
from nider.utils import get_random_texture

from nider.exceptions import ImageSizeFixedWarning


class TestLinkback(unittest.TestCase):

    def setUp(self):
        self.linkback = Linkback(text='foo', fontfullpath=None)

    def test_set_height(self):
        self.assertEqual(self.linkback.height, 31)


class TestContent(unittest.TestCase):

    def setUp(self):
        header = Header(text='foo', fontfullpath=None)
        linkback = Linkback(text='bar', fontfullpath=None)
        para = Paragraph(text='foo bar', fontfullpath=None)
        self.content = Content(para, header=header, linkback=linkback)

    def test_content_height(self):
        self.assertIsNotNone(self.content.height)


class TestImageInitializationMethods(unittest.TestCase):

    def setUp(self):
        self.image_mock = mock.Mock()

    def test_set_content(self):
        para = Paragraph(text='foo bar', fontfullpath=None)
        content = Content(para)
        Image._set_content(self.image_mock, content)
        self.assertEqual(self.image_mock.content, content)

    def test_set_fullpath_with_valid_path(self):
        fullpath = 'test.png'
        Image._set_fullpath(self.image_mock, fullpath)
        self.assertEqual(self.image_mock.fullpath, fullpath)

    def test_set_fullpath_with_invalid_path(self):
        fullpath = 'non/existent/directory/test.png'
        with self.assertRaises(AttributeError):
            Image._set_fullpath(self.image_mock, fullpath)
        self.assertNotEqual(self.image_mock.fullpath, fullpath)

    def test_set_image_size(self):
        w, h = 500, 500
        Image._set_image_size(self.image_mock, w, h)
        self.assertEqual(self.image_mock.width, w)
        self.assertEqual(self.image_mock.height, h)

    def test_invalid_params_to_set_image_size(self):
        invalid_sizes = [(-1, -2), (-1.5, -5.5)]
        for invalid_size in invalid_sizes:
            with self.subTest():
                with self.assertRaises(AttributeError):
                    Image._set_image_size(self.image_mock, invalid_size[
                        0], invalid_size[1])


class TestImageBaseMethods(unittest.TestCase):

    def setUp(self):
        header = Header(text='foo', fontfullpath=None)
        linkback = Linkback(text='bar', fontfullpath=None)
        para = Paragraph(text='foo bar', fontfullpath=None)
        content = Content(para, header=header, linkback=linkback)
        fullpath = 'test.png'
        self.img = Image(content, fullpath)

    def test_fix_img_size(self):
        self.img.content.height = 101
        self.img.height = 100
        with self.assertWarns(ImageSizeFixedWarning):
            self.img._fix_image_size()
        self.assertFalse(self.img.content.fits)
        self.assertEqual(self.img.height, self.img.content.height)

    def test_no_need_for_fix_img_size(self):
        self.img.content.height = 100
        self.img.height = 101
        self.img._fix_image_size()
        self.assertTrue(self.img.content.fits)
        self.assertNotEqual(self.img.height, self.img.content.height)

    def test_create_img(self):
        self.img._create_image()
        self.assertIsInstance(self.img.image, PIL_Image.Image)

    def test_create_draw_object(self):
        self.img._create_image()
        self.img._create_draw_object()
        self.assertIsInstance(self.img.draw, ImageDraw.ImageDraw)

    @mock.patch('nider.models.Image._save')
    @mock.patch('nider.models.Image._draw_content')
    def test_draw_on_texture(self,
                             _draw_content_mock,
                             _save):
        self.img.draw_on_texture()
        self.assertTrue(_draw_content_mock.called)

    def test_draw_on_texture_with_invalid_texturepath(self):
        with self.assertRaises(FileNotFoundError):
            self.img.draw_on_texture(texture_path='foo/bar.png')

    @mock.patch('nider.models.Image._save')
    @mock.patch('nider.models.Image._draw_content')
    def test_draw_on_bg(self,
                        _draw_content_mock,
                        _save):
        self.img.draw_on_bg()
        self.assertTrue(_draw_content_mock.called)

    @mock.patch('nider.models.Image._save')
    @mock.patch('nider.models.Image._draw_content')
    def test_draw_on_image(self,
                           _draw_content_mock,
                           _save):
        with create_test_image():
            self.img.draw_on_image(
                image_path=os.path.abspath('test.png'))
        self.assertTrue(_draw_content_mock.called)

    @mock.patch('PIL.ImageEnhance._Enhance.enhance')
    @mock.patch('nider.models.Image._save')
    @mock.patch('nider.models.Image._draw_content')
    def test_draw_on_image_with_enhancements(self,
                                             _draw_content_mock,
                                             _save,
                                             enhance_mock):
        with create_test_image():
            enhance_mock.return_value = PIL_Image.open('test.png')
            self.img.draw_on_image(
                image_path=os.path.abspath('test.png'),
                image_enhancements=((ImageEnhance.Sharpness, 0.5),
                                    (ImageEnhance.Brightness, 0.5)))
        self.assertTrue(enhance_mock.called)
        self.assertTrue(_draw_content_mock.called)

    @mock.patch('PIL.Image.Image.filter')
    @mock.patch('nider.models.Image._save')
    @mock.patch('nider.models.Image._draw_content')
    def test_draw_on_image_with_filters(self,
                                        _draw_content_mock,
                                        _save,
                                        filter_mock):
        filters = (ImageFilter.BLUR, ImageFilter.GaussianBlur(2))
        with create_test_image():
            filter_mock.return_value = PIL_Image.open('test.png')
            self.img.draw_on_image(
                image_path=os.path.abspath('test.png'),
                image_filters=filters)
        self.assertTrue(filter_mock.called)
        self.assertTrue(_draw_content_mock.called)

    def test_draw_on_image_with_invalid_imagepath(self):
        with self.assertRaises(FileNotFoundError):
            self.img.draw_on_image('foo/bar.png')


class TestImageMethodsThatRequireImageAndDraw(unittest.TestCase):

    def setUp(self):
        header = Header(text='foo', fontfullpath=None)
        linkback = Linkback(text='bar', fontfullpath=None)
        para = Paragraph(text='foo bar', fontfullpath=None)
        content = Content(para, header=header, linkback=linkback, padding=45)
        self.fullpath = 'test.png'
        self.img = Image(content, self.fullpath)
        self.img._create_image()
        self.img._create_draw_object()

    @classmethod
    def tearDownClass(self):
        fullpath = 'test.png'
        os.remove(fullpath)

    @mock.patch('PIL.Image.Image.paste')
    def test_fill_img_with_texture(self, mock):
        texture = get_random_texture()
        self.img._fill_image_with_texture(texture)
        self.assertTrue(mock.called)

    @mock.patch('PIL.ImageDraw.ImageDraw.rectangle')
    def test_fill_img_with_color(self, mock):
        bgcolor = (0, 0, 0)
        self.img.bgcolor = (0, 0, 0)
        self.img._fill_image_with_color()
        mock.assert_called_once_with(
            [(0, 0), self.img.image.size], fill=bgcolor)

    @mock.patch('nider.models.Image._draw_unit')
    def test_draw_header(self, mock):
        self.img._draw_header()
        mock.assert_called_once_with(45,
                                     self.img.header)

    @mock.patch('nider.models.Image._draw_unit')
    def test_draw_para_with_content_that_fits(self, mock):
        self.img._draw_para()
        current_h = math.floor(
            (self.img.height - self.img.para.height) / 2)
        mock.assert_called_once_with(current_h, self.img.para)

    @mock.patch('nider.models.Image._draw_unit')
    def test_draw_para_content_with_header_that_does_not_fit(self, mock):
        self.img.content.fits = False
        self.img._draw_para()
        header_with_padding_height = 2 * \
            self.img.content.padding + self.img.header.height
        current_h = header_with_padding_height
        mock.assert_called_once_with(current_h, self.img.para)

    @mock.patch('nider.models.Image._draw_unit')
    def test_draw_para_content_without_header_that_does_not_fit(self, mock):
        self.img.content.fits = False
        self.img.header = None
        self.img._draw_para()
        current_h = self.img.content.padding
        mock.assert_called_once_with(current_h, self.img.para)

    @mock.patch('PIL.ImageDraw.ImageDraw.text')
    def test_draw_linkback(self, mock):
        self.img.color = (0, 0, 0)
        aligns = ['center', 'right', 'left']
        for align in aligns:
            with self.subTest():
                self.img.linkback.align = align
                self.img._draw_linkback()
                self.assertTrue(mock.called)

    @mock.patch('nider.models.Image._draw_linkback')
    @mock.patch('nider.models.Image._draw_para')
    @mock.patch('nider.models.Image._draw_header')
    def test_draw_content(self, _draw_header_mock,
                          _draw_para_mock, _draw_linkback_mock):
        self.img._draw_content()
        self.assertTrue(_draw_header_mock.called)
        self.assertTrue(_draw_para_mock.called)
        self.assertTrue(_draw_linkback_mock.called)

    @mock.patch('PIL.ImageDraw.ImageDraw.text')
    def test_draw_unit(self, text_mock):
        drop_shadow_options = [True, False]
        self.img.color = (0, 0, 0)
        start_height = 0
        aligns = ['center', 'right', 'left']
        for align in aligns:
            for drop_shadow_option in drop_shadow_options:
                self.img.drop_shadow = drop_shadow_option
                if drop_shadow_option:
                    self.img.shadowcolor = (0, 0, 0)
                with self.subTest():
                    unit = MultilineTextUnit(
                        text='foo', fontfullpath=None, drop_shadow=drop_shadow_option,
                        align=align)
                    self.img._draw_unit(start_height, unit)
                    self.assertTrue(text_mock.called)

    def test_save(self):
        self.img._save()
        self.assertTrue(os.path.isfile(self.fullpath))


class TestFacebookSquarePost(unittest.TestCase):

    @mock.patch('nider.models.Image._set_fullpath')
    @mock.patch('nider.models.Image._set_content')
    def setUp(self, *mocks):
        self.post = FacebookSquarePost(content=mock.Mock(),
                                       fullpath=mock.Mock())

    def test_size(self):
        self.assertEqual(self.post.width, 470)
        self.assertEqual(self.post.height, 470)


class TestFacebookLandscapePost(unittest.TestCase):

    @mock.patch('nider.models.Image._set_fullpath')
    @mock.patch('nider.models.Image._set_content')
    def setUp(self, *mocks):
        self.post = FacebookLandscapePost(content=mock.Mock(),
                                          fullpath=mock.Mock())

    def test_size(self):
        self.assertEqual(self.post.width, 1024)
        self.assertEqual(self.post.height, 512)


class TestTwitterPost(unittest.TestCase):

    @mock.patch('nider.models.Image._set_fullpath')
    @mock.patch('nider.models.Image._set_content')
    def setUp(self, *mocks):
        self.post = TwitterPost(content=mock.Mock(),
                                fullpath=mock.Mock())

    def test_size(self):
        self.assertEqual(self.post.width, 1024)
        self.assertEqual(self.post.height, 512)


class TestTwitterLargeCard(unittest.TestCase):

    @mock.patch('nider.models.Image._set_fullpath')
    @mock.patch('nider.models.Image._set_content')
    def setUp(self, *mocks):
        self.post = TwitterLargeCard(content=mock.Mock(),
                                     fullpath=mock.Mock())

    def test_size(self):
        self.assertEqual(self.post.width, 506)
        self.assertEqual(self.post.height, 506)


class TestInstagramSquarePost(unittest.TestCase):

    @mock.patch('nider.models.Image._set_fullpath')
    @mock.patch('nider.models.Image._set_content')
    def setUp(self, *mocks):
        self.post = InstagramSquarePost(content=mock.Mock(),
                                        fullpath=mock.Mock())

    def test_size(self):
        self.assertEqual(self.post.width, 1080)
        self.assertEqual(self.post.height, 1080)


class TestInstagramPortraitPost(unittest.TestCase):

    @mock.patch('nider.models.Image._set_fullpath')
    @mock.patch('nider.models.Image._set_content')
    def setUp(self, *mocks):
        self.post = InstagramPortraitPost(content=mock.Mock(),
                                          fullpath=mock.Mock())

    def test_size(self):
        self.assertEqual(self.post.width, 1080)
        self.assertEqual(self.post.height, 1350)


class TestInstagramLandscapePost(unittest.TestCase):

    @mock.patch('nider.models.Image._set_fullpath')
    @mock.patch('nider.models.Image._set_content')
    def setUp(self, *mocks):
        self.post = InstagramLandscapePost(content=mock.Mock(),
                                           fullpath=mock.Mock())

    def test_size(self):
        self.assertEqual(self.post.width, 1080)
        self.assertEqual(self.post.height, 566)


if __name__ == '__main__':
    unittest.main()