"""Use more relevant bounding box sizes

Defaults to shaping up the bottle-top bounding boxes that include only the capsules
to use a larger and more bottle-including size.

This will make it less similar to can-top (missed detections) or bottle-top glare
(double detections).

The normalized file is output into a subdirectory normalized/ next to the file.

Dependencies:
numpy
"""

import os
import xml.etree.ElementTree as ET

import makemake
from numpy import median


def ceiling_division(numerator, denominator):
    return -(-numerator // denominator)


class Norm:
    """Normalize (increase) the size around its centre if too small

    >>> norm = Norm(); norm
    Norm('bottle-top_has_bottle_and_also_its_box_slot.xml', ['can-top', 'bottle-top'], (37.0, 35.5), (29, 20))
    >>> sloppy_bottle = 'single_bottle-top_capsule_in_single_box.xml'
    >>> Norm(sloppy_bottle)
    Norm('single_bottle-top_capsule_in_single_box.xml', ['can-top', 'bottle-top'], (21.0, 33.0), (21, 33))
    >>> norm(sloppy_bottle)
    Shapeup bottle-top size (21, 33) to (37.0, 35.5)
    Norm('normalized/single_bottle-top_capsule_in_single_box.xml', ['bottle-top'], (37.0, 36.0), (37, 36))
    >>> ET.parse(f'normalized/{sloppy_bottle}').getroot().findall('object')[-1].findtext('difficult')
    '1'
    >>> norm(sloppy_bottle, difficult=False)
    Shapeup bottle-top size (21, 33) to (37.0, 35.5)
    Norm('normalized/single_bottle-top_capsule_in_single_box.xml', ['bottle-top'], (37.0, 36.0), (37, 36))
    >>> ET.parse(f'normalized/{sloppy_bottle}').getroot().findall('object')[-1].findtext('difficult')
    '0'
    >>> norm(norm.template).template
    'bottle-top_has_bottle_and_also_its_box_slot.xml'
    >>> norm(norm.template, copy=True).template
    'normalized/bottle-top_has_bottle_and_also_its_box_slot.xml'
    """  # noqa: E501

    def __repr__(self):
        return self.__class__.__name__ + repr(
            (self.template, self.objects, self.normal, self.small))

    def __init__(self, template='bottle-top_has_bottle_and_also_its_box_slot.xml',
                 objects=['can-top', 'bottle-top'],
                 normal=None, small=None):
        """Normal and small bndbox size for objects in template matching these names"""
        self.template = template
        self.objects = objects
        if normal and small:
            self.normal, self.small = normal, small
            return

        matches = (o for o in ET.parse(template).getroot().iter('object')
                   if o.findtext('name') in objects)
        bndboxes = [o.find('bndbox') for o in matches]
        if not bndboxes:
            self.normal = self.small = None
            return

        dX = [int(bndbox.findtext('xmax')) - int(bndbox.findtext('xmin'))
              for bndbox in bndboxes]
        dY = [int(bndbox.findtext('ymax')) - int(bndbox.findtext('ymin'))
              for bndbox in bndboxes]

        self.normal = (median(dX), median(dY))
        self.small = (min(dX), min(dY))

    def __call__(self, sloppy, names=['bottle-top'], difficult=True, copy=False,
                 normalized_dir='normalized'):
        """Shapeup the bndbox of objects matching these names"""
        voc = ET.parse(sloppy)
        root = voc.getroot()

        modified = False
        coords = 'xmin', 'xmax', 'ymin', 'ymax'
        for o in root.iter('object'):
            name = o.findtext('name')
            if name in names:
                bndbox = o.find('bndbox')
                xmin, xmax, ymin, ymax = map(int, map(bndbox.findtext, coords))
                size = (xmax - xmin, ymax - ymin)
                if size[0] < self.small[0] or size[1] < self.small[1]:
                    print(f"Shapeup {name} size {size} to {self.normal}")

                    if difficult:
                        o.find('difficult').text = '1'

                    x = (xmin + xmax) / 2
                    y = (ymin + ymax) / 2
                    dx, dy = self.normal

                    xminc, xmaxc, yminc, ymaxc = map(bndbox.find, coords)
                    xminc.text = str(int(2 * x - dx) // 2)
                    yminc.text = str(int(2 * y - dy) // 2)
                    xmaxc.text = str(ceiling_division(int(2 * x + dx), 2))
                    ymaxc.text = str(ceiling_division(int(2 * y + dy), 2))

                    modified = True

        if copy or modified:
            here, filename = os.path.split(sloppy)
            there = os.path.join(here, normalized_dir)
            not_sloppy = os.path.join(there, filename)

            if not os.path.isdir(there):
                os.makedirs(there)

            voc.write(not_sloppy)
        else:
            not_sloppy = sloppy

        return self.__class__(not_sloppy, names)


if __name__ == '__main__':
    import argparse

    argparser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=__doc__,
        epilog="""Examples:
$ rm -rf normalized
$ venv/bin/python shapeup.py *bottle*.xml
bottle-top_has_bottle_and_also_its_box_slot.xml
single_bottle-top_capsule_in_single_box.xml
Shapeup bottle-top size (21, 33) to (37.0, 35.5)

$ ls normalized/
single_bottle-top_capsule_in_single_box.xml

$ venv/bin/python shapeup.py -c *bottle*.xml > normalized/log.txt
$ ls normalized/
bottle-top_has_bottle_and_also_its_box_slot.xml
log.txt
single_bottle-top_capsule_in_single_box.xml
""")
    makemake.add_arguments(argparser)
    argparser.add_argument(
        '-t', '--template', action='store',
        default=os.path.join(
            makemake.module_dir, 'bottle-top_has_bottle_and_also_its_box_slot.xml'),
        help=(
            "Template pascal voc xml file for defining normal and smallest bndbox sizes"
            " (bottle-top_has_bottle_and_also_its_box_slot.xml)"))
    argparser.add_argument(
        '-to', '--template_object', action='store',
        default=['can-top', 'bottle-top'], nargs='+', help=(
            "Template object(s) for defining normal and smallest bndbox sizes"
            " (can-top bottle-top)"))
    argparser.add_argument(
        '-o', '--object', action='store',
        default=['bottle-top'], nargs='+', help="Object(s) to shape-up (bottle-top)")
    argparser.add_argument(
        '-d', '--difficult', action='store', default=1,
        type=int, help="Mark shaped-up objects difficult (1)")
    argparser.add_argument(
        '-c', '--copy', action='store_true',
        help="Create a copy even if not modified")
    argparser.add_argument(
        '-n', '--normalized_dir', action='store',
        default='normalized', help="Target directory for normalized files")
    argparser.add_argument(
        'voc_file', action='store',
        nargs='+', help="Pascal voc xml file to shape-up (*.xml)")
    args = argparser.parse_args()

    voc_files = args.voc_file

    norm = Norm(args.template, args.template_object)

    for voc_file in args.voc_file:
        print(voc_file)
        norm(voc_file, args.object, args.difficult, args.copy, args.normalized_dir)
