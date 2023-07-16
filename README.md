# Object-in-object detector
Detect many small objects inside their parent objects

This is a suite of tools for detecting objects in two stages: first large and easy-to-detect objects, and then smaller objects inside them.

It focuses on what was most difficult to detect: Small capsules of bottles visible within cardboard insets inside cardboard boxes.

The previously trained object detector was used only to detect parent objects reliably, and the new object-in-object 
detector was used to detect what was inside them reliably also.

Contribution observed by each tool:
1. Focus training on frequent but difficult-to-detect objects: Increased worst-case mAP from 30% to 35%.
2. Zoom into each parent object: Increased worst-case mAP from 35% to 70%.
3. Include the natural surrounding: Increased worst-case mAP from 70% to 73%.

The zooming into each parent object made small objects much easier to detect. It increased the number of pixels in each
small object by an order of magnitude and made overtraining on (pixel) noise in them less likely.

This detector turned a product from unreliable and laggy due to need for post-processing to reduce effect of noise,
to reliable and instant. Also it allowed much smaller networks to be used, which was important since the old model
used only a single Coral edgeTPU on a single Raspberry Pi 4.

## Tool for generating build dependencies: makemake.py
Any python module that imports makemake (and makemake itself) can print a Makefile for handling its dependencies and
tests. It can also print a generic Makefile for handling all source code in its directory, including .py, .c, cpp, .s.

Example: 
$ python3 makemake.py --makemake --generic > Makefile && make

The generic Makefile builds exactly the same targets also when included in a parent Makefile, and will not cause
conflict with the existing python environment since it creates its own python venv from it. 

Python version 3.9 or later is required.

## Many items in multiple boxes: bottle-top_has_bottle_and_also_its_box_slot.xml
A template with precise labelling of object sizes within a complex image.

All object sizes here include also some pixel-width of their local natural environment - a box slot wall, for example.

The labels here are for a set of bottles inside slots inside a set of boxes.

Originally all bottle-top objects here were the size of their capsules only.

## List only existing object classes: classes.py
A tool to generate a list of object class names in order of frequency.

## Focus training on frequent but difficult-to-detect objects: unbalance.py
A tool to remove all image augmentations.

This is useful when most objects in the images are significantly more difficult to detect than some others, but the 
augmentation used did not care about that.

## Zoom into each parent object: squareup.py
A tool to move objects into square crops of an image that only includes one parent object each.

The result of this operation can be used for a dedicated object-in-object detector at much higher resolution.

This step must be performed from the output of a very accurate parent-object-detector. 

Note: Parents objects such as boxes are both large and typically extremely uniform, so a parent-object-detector is 
typically the first step anyway since it is so easy. It is better to not train it to also detect the objects inside 
them unless the object-in-object detector is meant to be co-located with it.

## Various boxes: empty_box.xml no_pixel_box.xml no_pixel_box_and_empty_box.xml single_bottle-top_capsule_in_single_box.xml
Examples of one or more boxes with originally sized objects in them.

The size of a bottle_top here is the size of its capsule only.

## Include the natural surrounding: shapeup.py
A tool to increase the size of the smallest objects to also include its natural surrounding.

This made the previously capsule-sized bottle-top objects less similar to other object classes (confusions with can-top
in particular) and also less similar to bottle-top glares (double detections).