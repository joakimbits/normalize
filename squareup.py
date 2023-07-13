"""Move objects into square crops of an image

This will make the objects trainable on square detector with as much of its natural environment as possible.

Notes:
Tests only work on Poltergeist due to a jpg test file dependency - see Dependencies below.
That specific file is write-protected to not accidentally remove it.

Dependencies:
numpy
Pillow
$ python3 -c "from PIL import Image; Image.new('RGB', (640, 360)).save('blank.jpg')"
$ mv blank.jpg bottle-top_has_bottle_and_also_its_box_slot.jpg
"""

import os
import xml.etree.ElementTree as ET

import makemake
import numpy as np
from PIL import Image


class BndBox(np.ndarray):
    """ndarray with coords and corners properties

    >>> bndbox = BndBox(1, 2, 30, 40); bndbox
    BndBox(1, 2, 30, 40)
    >>> bndbox.coords.xmax
    30
    >>> tuple(bndbox)
    (1, 2, 30, 40)
    >>> bndbox.corners[0] += (10, 20); bndbox
    BndBox(11, 22, 30, 40)
    >>> BndBox([1, 2], [3, 4], [50, 60], [70, 80])
    BndBox(* [[ 1  2]
     [ 3  4]
     [50 60]
     [70 80]])
    >>> _.coords
    rec.array([[(1, 3, 50, 70)],
               [(2, 4, 60, 80)]],
              dtype=[('xmin', '<i8'), ('ymin', '<i8'), ('xmax', '<i8'), ('ymax', '<i8')])
    """

    COORDS = 'xmin', 'ymin', 'xmax', 'ymax'
    DTYPE = np.dtype(list(zip(COORDS, [int] * 4)))
    XY_DTYPE = np.dtype(list(zip("xy", [int] * 2)))

    def __new__(cls, xmin=0, ymin=448, xmax=0, ymax=448):
        xmin, ymin, xmax, ymax = map(np.array, (xmin, ymin, xmax, ymax))
        if xmin.shape == ():
            return np.array((xmin, ymin, xmax, ymax), dtype=int).view(cls)

        return np.array(np.stack((xmin, ymin, xmax, ymax), axis=-1), dtype=int).view(cls)

    def __repr__(self):
        return self.__str__(self.__class__.__name__)

    def __str__(self, class_name=""):
        if self.shape == (4,):
            return class_name + repr(tuple(self))

        n = len(self.shape)
        return f"{class_name}(* {self.transpose([-1] + list(range(len(self.shape) - 1))).view(np.ndarray)})"

    @property
    def coords(self):
        if self.shape in ((4,), (1, 4)):
            return self.view(self.DTYPE).view(np.recarray)[0]

        return self.view(self.DTYPE).view(np.recarray)

    @property
    def corners(self):
        if self.shape in ((4,), (1, 4)):
            return self.reshape((2, 2)).view(np.ndarray)

        return self.reshape((-1, 2, 2)).view(np.ndarray)

class Crop(BndBox):
    """bndbox ndarray with offset and dims properties

    >>> crop = Crop(); crop
    Crop((0, 0), (448, 448))
    >>> crop.offset = (1, 2); crop
    Crop((1, 2), (448, 448))
    >>> crop.dimensions -= (8, 8); crop
    Crop((1, 2), (440, 440))
    >>> crop.corners[0] += 40; crop
    Crop((41, 42), (400, 400))
    >>> crop.coords
    (41, 42, 441, 442)
    >>> crop.pixels()
    160000
    """

    DIMS = 'width', 'height'
    DIMS_DTYPE = np.dtype(list(zip(DIMS, [int] * 2)))

    def __new__(cls, offset=(0, 0), dimensions=(448, 448)):
        offset = np.array(offset, dtype=int)
        dimensions = np.array(dimensions, dtype=int)

        return np.hstack((offset, offset + dimensions)).view(cls)

    def __repr__(self):
        return self.__str__(self.__class__.__name__)

    def __str__(self, class_name=""):
        if self.shape == (4,):
            return class_name + repr(tuple(map(tuple, (self.offset, self.dimensions))))

        return class_name + repr((self.offset, self.dimensions))

    @property
    def offset(self):
        if self.shape == (4,):
            return self[:2].view(np.ndarray)
        elif self.shape == (1, 4):
            return self[0, :2].view(np.ndarray)

        return self[..., :2].view(np.ndarray)

    @offset.setter
    def offset(self, xy):
        self.corners[:] -= self[..., :2] - np.array(xy)

    @property
    def dimensions(self):
        if self.shape == (4,):
            return (self[2:] - self[:2]).view(np.ndarray)
        elif self.shape == (1, 4):
            return (self[0, 2:] - self[0, :2]).view(np.ndarray)

        return (self[..., 2:] - self[..., :2]).view(np.ndarray)

    @dimensions.setter
    def dimensions(self, dims):
        self[..., 2:] = self[..., :2] + np.array(dims)

    def pixels(self):
        if not self.size:
            return np.array([], dtype=int)

        dimensions = self.dimensions
        return dimensions[..., 0] * dimensions[..., 1]


class FileStructure:
    """Locations for original and normalized image and voc files"""

    def __init__(self, image_file, normalized_image_dir='normalized', voc_dir=None, normalized_voc_dir=None):
        assert os.path.exists(image_file), f"{image_file} not found in {os.getcwd()}"

        image_dir, image_filename = os.path.split(image_file)
        name, image_ext = os.path.splitext(image_filename)

        if voc_dir == None:
            voc_dir = image_dir

        if normalized_voc_dir == None:
            normalized_voc_dir = normalized_image_dir

        voc_file = os.path.join(voc_dir, name + ".xml")

        self.image_file = image_file
        self.name = name
        self.image_ext = image_ext
        self.image_dir = image_dir
        self.normalized_image_dir = normalized_image_dir

        self.voc_file = voc_file
        self.voc_dir = voc_dir
        self.normalized_voc_dir = normalized_voc_dir


class Norm(Crop):
    """bndbox ndarray for cropping an image

    >>> crop = Norm(); crop
    Norm('bottle-top_has_bottle_and_also_its_box_slot.xml', ['box'], array([179, 132]), array([171, 110]), array([134, 137]))
    >>> crop.coords
    rec.array([[(339, 116, 518, 248)],
               [(157,   2, 322, 118)],
               [(346, 248, 512, 360)],
               [( 32,   7, 166, 144)],
               [(177, 249, 348, 359)],
               [(320,   1, 500, 119)]],
              dtype=[('xmin', '<i8'), ('ymin', '<i8'), ('xmax', '<i8'), ('ymax', '<i8')])
    >>> for norm in crop(): print(Image.open(norm.image).size, norm.dimensions)
    (179, 179) [[ 38  47]
     [ 38  34]
     [ 38  40]
     [ 40  36]
     [ 36  39]
     [ 35  40]
     [ 45  34]
     [ 38  38]
     [ 41  37]
     [ 40  36]
     [ 38  37]
     [ 40  37]
     [179 132]]
    (165, 165) [[ 38  32]
     [ 29  31]
     [ 41  39]
     [ 41  26]
     [ 30  27]
     [ 35  34]
     [ 37  25]
     [ 36  21]
     [ 31  23]
     [165 116]
     [ 32  32]]
    (166, 166) [[ 37  34]
     [ 36  21]
     [ 37  37]
     [ 38  22]
     [ 36  20]
     [ 36  38]
     [ 37  38]
     [ 37  33]
     [166 112]]
    (137, 137) [134 137]
    (171, 171) [[ 35  22]
     [ 36  39]
     [ 38  37]
     [ 39  37]
     [171 110]]
    (180, 180) [[ 39  35]
     [ 40  36]
     [ 37  32]
     [ 40  44]
     [ 33  38]
     [ 82  37]
     [ 45  82]
     [ 36  29]
     [180 118]]
    >>> Norm("single_bottle-top_capsule_in_single_box.xml")
    Norm('single_bottle-top_capsule_in_single_box.xml', ['box'], array([168, 138]), array([168, 138]), array([168, 138]))
    >>> Image.open("bottle-top_has_bottle_and_also_its_box_slot.jpg").save("single_bottle-top_capsule_in_single_box.jpg")
    >>> for norm in _(): print(Image.open(norm.image).size, repr(norm))
    (168, 168) Norm('normalized/single_bottle-top_capsule_in_single_box_0.xml', None, array([168, 138]), array([21, 33]), array([21, 33]))
    >>> Norm("empty_box.xml")
    Norm('empty_box.xml', ['box'], array([168, 138]), array([168, 138]), array([168, 138]))
    >>> Image.open("bottle-top_has_bottle_and_also_its_box_slot.jpg").save("empty_box.jpg")
    >>> for norm in _(): print(Image.open(norm.image).size, repr(norm))
    (168, 168) Norm('normalized/empty_box_0.xml', None, array([168, 138]), array([168, 138]), array([168, 138]))
    >>> Norm("no_pixel_box.xml")
    Ignoring box at [563 142]: No pixels!
    Norm('no_pixel_box.xml', ['box'], None, None, None)
    >>> for norm in _(): print(Image.open(norm.image).size, repr(norm))
    >>> Norm("no_pixel_box_and_empty_box.xml")
    Ignoring box at [563 142]: No pixels!
    Norm('no_pixel_box_and_empty_box.xml', ['box'], array([168, 138]), array([168, 138]), array([168, 138]))
    >>> Image.open("bottle-top_has_bottle_and_also_its_box_slot.jpg").save("no_pixel_box_and_empty_box.jpg")
    >>> for norm in _(): print(Image.open(norm.image).size, repr(norm))
    Ignoring box at [563 142]: No pixels!
    (168, 168) Norm('normalized/no_pixel_box_and_empty_box_0.xml', None, array([168, 138]), array([168, 138]), array([168, 138]))
    """

    class EfficientDet:
        """The input layer is a square"""
        L1 = (384, 384)
        L2 = (448, 448)
        L3 = (512, 512)
        L4 = (640, 640)

    def __repr__(self):
        return self.__class__.__name__ + repr((self.template, self.objects_filter, self.large, self.normal, self.small))

    def __new__(cls, template='bottle-top_has_bottle_and_also_its_box_slot.xml', objects_filter=['box'],
                large=None, normal=None, small=None, image=None):
        """
        Grab bndboxes for all matching objects in a VOC .xml file.
        Find their most normal and small sized bndbox.
        """
        voc = ET.parse(template).getroot()

        if objects_filter != None:
            objects = [o for o in voc.iter('object') if o.findtext('name') in objects_filter]
        else:
            objects = voc.findall('object')

        bndboxes = np.array([[o.find('bndbox').findtext(c) for c in BndBox.COORDS] for o in objects], dtype=int)
        self = bndboxes.view(cls)

        pixels = np.atleast_1d(self.pixels())
        waste = (pixels == 0).nonzero()[0]
        for i in waste:
            print(f"Ignoring {objects[i].findtext('name')} at {self[i].offset}: No pixels!")

        if waste.size:
            ok = pixels.nonzero()[0]
            objects = [objects[i] for i in ok]
            if not ok.size:
                ok = slice(0, 0)

            pixels = pixels[ok]
            self = self[ok]

        if pixels.size:
            indices = np.argsort(-pixels)
            large = self[indices[0]].dimensions
            normal = self[indices[len(indices) // 2]].dimensions
            small = self[indices[-1]].dimensions

        self.template = template
        self.objects_filter = objects_filter
        self.voc = voc
        self.objects = objects
        self.large = large
        self.normal = normal
        self.small = small
        self.image = image

        return self

    def __call__(self, image_file=None, normalized_image_dir='normalized', voc_dir=None, normalized_voc_dir=None,
                 square=True):
        """
        Crop an image and move each object into the crop where it is most embedded.
        """
        if not self.size:
            return

        if image_file == None:
            image_file = os.path.splitext(self.template)[0] + ".jpg"

        fs = FileStructure(image_file, normalized_image_dir, voc_dir, normalized_voc_dir)

        image = Image.open(image_file)
        items = Norm(fs.voc_file, None)
        bndboxes_crops_inner_margins = items.corners[..., np.newaxis, 0, :] - self.corners[..., 0, :]
        bndboxes_crops_outer_margins = self.corners[..., 1, :] - items.corners[..., np.newaxis, 1, :]
        bndboxes_crops_margins = np.concatenate((bndboxes_crops_inner_margins, bndboxes_crops_outer_margins), axis=-1)
        bndboxes_crops_worst_margin = np.min(bndboxes_crops_margins, axis=-1)
        bndboxes_cropindex = np.atleast_1d(bndboxes_crops_worst_margin.argmax(axis=-1))

        if not os.path.isdir(fs.normalized_image_dir):
            os.makedirs(fs.normalized_image_dir)

        if not os.path.isdir(fs.normalized_voc_dir):
            os.makedirs(fs.normalized_voc_dir)

        image_file_for_crop = os.path.join(fs.normalized_image_dir, fs.name + "_%s" + fs.image_ext)
        voc_file_for_crop = os.path.join(fs.normalized_voc_dir, fs.name + "_%s.xml")
        filename = items.voc.find('filename')
        width, height = map(items.voc.find('size').find, ('width', 'height'))
        for i, crop in enumerate(self):
            offset = crop.offset
            dimensions = crop.dimensions
            if square:
                margin = dimensions[0] - dimensions[1]
                if margin < 0:
                    margin = -margin
                    if offset[0] > margin // 2:
                        offset = (offset[0] - margin // 2, offset[1])
                    else:
                        offset = (0, offset[1])

                    dimensions = (dimensions[1], dimensions[1])
                elif margin > 0:
                    if offset[1] > margin // 2:
                        offset = (offset[0], offset[1] - margin // 2)
                    else:
                        offset = (offset[0], 0)

                    dimensions = (dimensions[0], dimensions[0])

                if margin:
                    crop = Crop(offset, dimensions)

            image_file = image_file_for_crop % i
            image.crop(crop.coords).save(image_file)
            filename.text = image_file
            width.text, height.text = map(str, dimensions)
            for o in items.voc.findall('object'):
                items.voc.remove(o)

            for o, bndbox, cropindex in zip(items.objects, items, bndboxes_cropindex):
                if cropindex == i:
                    items.voc.append(o)
                    for j, c in enumerate(map(o.find('bndbox').find, self.COORDS)):
                        c.text = str(bndbox[j] - offset[j % 2])

            ET.ElementTree(items.voc).write(voc_file_for_crop % i)

        # Possibly import the cropped files
        for i in range(len(self)):
            yield Norm(voc_file_for_crop % i, None, image=image_file_for_crop % i)


if __name__ == '__main__':
    import argparse

    argparser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
                                        description=__doc__,
                                        epilog="""Examples:
$ rm -rf normalized/
$ python3 squareup.py bottle-top_has_bottle_and_also_its_box_slot.jpg
bottle-top_has_bottle_and_also_its_box_slot.jpg
[179 132] ['box'] normalized/bottle-top_has_bottle_and_also_its_box_slot_0.xml in (179, 179) normalized/bottle-top_has_bottle_and_also_its_box_slot_0.jpg
[165 116] ['box'] normalized/bottle-top_has_bottle_and_also_its_box_slot_1.xml in (165, 165) normalized/bottle-top_has_bottle_and_also_its_box_slot_1.jpg
[166 112] ['box'] normalized/bottle-top_has_bottle_and_also_its_box_slot_2.xml in (166, 166) normalized/bottle-top_has_bottle_and_also_its_box_slot_2.jpg
[134 137] ['box'] normalized/bottle-top_has_bottle_and_also_its_box_slot_3.xml in (137, 137) normalized/bottle-top_has_bottle_and_also_its_box_slot_3.jpg
[171 110] ['box'] normalized/bottle-top_has_bottle_and_also_its_box_slot_4.xml in (171, 171) normalized/bottle-top_has_bottle_and_also_its_box_slot_4.jpg
[180 118] ['box'] normalized/bottle-top_has_bottle_and_also_its_box_slot_5.xml in (180, 180) normalized/bottle-top_has_bottle_and_also_its_box_slot_5.jpg
""")
    makemake.add_arguments(argparser)

    argparser.add_argument('-o', '--object', action='store', default=['box'],
                           nargs='+', help="Template object(s) for defining normal and smallest crop sizes (box)")
    argparser.add_argument('image_file', action='store',
                           nargs='+', help="Image file to shape-up (*.jpg)")
    argparser.add_argument('-nid', '--normalized_image_dir', action='store', default="normalized",
                           help="Output directory for cropped images (normalized)")
    argparser.add_argument('-vd', '--voc_dir', action='store', default=None,
                           help="Input directory for voc files (directory of IMAGE_FILE)")
    argparser.add_argument('-nvd', '--normalized_voc_dir', action='store', default=None,
                           help="Output directory for cropped voc files (NORMALIZED_IMAGE_DIR)")
    args = argparser.parse_args()

    # template='bottle-top_has_bottle_and_also_its_box_slot.xml', objects=['box'], normal=None, small=None

    for image_file in args.image_file:
        print(image_file)
        fs = FileStructure(image_file, args.normalized_image_dir, args.voc_dir, args.normalized_voc_dir)
        squareup = Norm(fs.voc_file, args.object)
        for norm in squareup(fs.image_file, fs.normalized_image_dir, fs.voc_dir, fs.normalized_voc_dir):
            print(norm.large, args.object, norm.template, "in", Image.open(norm.image).size, norm.image)
