# SC2Blend
A Blender plugin script for importing saves and scenarios from the awesome 1993 game, SimCity 2000.

## How to use it

- You'll need to decompress sc2_blocks.zip, and relocate it to the directory you'll be working from (while keeping the individual blocks contained within the directory called 'sc2_blocks'). Right now, it's best to keep import_sc2.py, the sc2_blocks directory, and your .sc2 file in the same directory.
- Then, open Blender, and import the script. You can do this by either, locating the files to Blender's plugin directory, or loading it into Blender's text editor and clicking "Run Script"
- If you didn't see any errors, go to File > Import > SimCity2000(.sc2), and select a file.

## Texturing
Once imported, your level is UV wrapped to the sc2_blocks_texture.png
