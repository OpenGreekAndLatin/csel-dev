import glob
import os
import xml.etree.ElementTree as ET

# globs are the unixy wildcard for command like ls
# so */* will get all the files. [!_] mean not an underscore
for path_and_name in glob.glob('*/[!_]*'):
    # get the name for the file without the extension, 
    # so for '/one/one-lump.xml' filename will be 'one-lump'
    filename = os.path.basename(path_and_name).split('.')[0]
    print(path_and_name, filename)

    # ET. parse does the heavy lifting. The entire XML file is
    # parsed in one shot and root is a reference to the root element of the
    # XML document.
    root = ET.parse(path_and_name)

    # findall is a method that the root object has. It searches the entire
    # tree and finds all the <title> objects and returns a list of them.
    title = root.findall('title')

    # if we found more than one we are in trouble, so assert that there was
    # only one
    assert(len(title) == 1)

    # change the text of the element
    title[0].text = filename

    # write the file to disk
    ET.dump(root)
    # root.write(path_and_name)
