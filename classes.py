"""List only existing object names

Using this list during training can make training faster.
"""
import glob
from collections import Counter
import xml.etree.ElementTree as ET

import makemake


if __name__ == '__main__':
    import argparse

    argparser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
                                        description=__doc__,
                                        epilog="""Examples:
$ python3 classes.py bottle-top_has_bottle_and_also_its_box_slot.xml
bottle-top
can-top
box
bottle-bottom
baginbox-top

$ python3 classes.py 'bottle-top_has_bottle_and_*.xml'
bottle-top
can-top
box
bottle-bottom
baginbox-top
""")
    makemake.add_arguments(argparser)
    argparser.add_argument('voc_file', action='store',
                           nargs='+', help="Files to analyze ('*.xml')")
    args = argparser.parse_args()
    names = Counter()
    for voc_file in args.voc_file:
        for voc_file_ in glob.iglob(voc_file):
            voc = ET.parse(voc_file_).getroot()
            names |= Counter(o.findtext('name') for o in voc.iter('object'))

    for name, count in names.most_common():
        print(name)
