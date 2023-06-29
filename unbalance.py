"""Symlink only non-augmented files

This will make training faster, more focussed on what is normal, therefore more relevant for what we
have problems with now: bottle-top.

The symlinks are output into a subdirectory normalized/.

Note that not even the original is kept when there are augmentations of it. This is because it seems most of the
augmentations are of weird originals, and that the original is not immediately identifiable.

Dependencies:
numpy
"""

import os

import makemake
import numpy as np


if __name__ == '__main__':
    import argparse

    argparser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
                                        description=__doc__,
                                        epilog="""Examples:
$ rm -rf normalized/ other_dir/ keep_aug_* dummy_aug_*
$ touch keep_aug_0.jpg dummy_aug_0.jpg dummy_aug_1.jpg
$ python3 unbalance.py *_aug_?.jpg
normalized/keep_aug_0.jpg -> ../keep_aug_0.jpg

$ python3 unbalance.py normalized/*_aug_?.jpg -o other_dir
other_dir/keep_aug_0.jpg -> ../normalized/keep_aug_0.jpg
""")
    makemake.add_arguments(argparser)

    argparser.add_argument('aug_file', action='store',
                           nargs='+', help="Files to unbalance (*_aug_?.*)")
    argparser.add_argument('-o', '--output_dir', action='store', default="normalized",
                           help="Output directory for unbalanced images (normalized)")
    args = argparser.parse_args()

    files, exts = np.array(tuple(zip(* map(os.path.splitext, args.aug_file))), dtype=str)
    filebases, augs = np.array([file.split('_aug_')[-2:] for file in files], dtype=str).T

    for filebase, aug, ext, aug_file in zip(filebases, augs, exts, args.aug_file):
        if aug == "0" and not ((filebases == filebase) & (augs == "1") & (exts == ext)).any():
            if not os.path.isdir(args.output_dir):
                os.makedirs(args.output_dir)

            aug_dir, aug_filename = os.path.split(aug_file)
            path = os.path.join(args.output_dir, aug_filename)
            reverse_path = os.path.relpath(os.path.abspath(aug_file), os.path.abspath(args.output_dir or "."))
            if os.path.exists(path):
                os.remove(path)

            os.symlink(reverse_path, path, False)
            print(path, "->", reverse_path)
