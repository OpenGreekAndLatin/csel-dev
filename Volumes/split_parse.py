import xml.etree.ElementTree as ET
import re
import os
from os import listdir
from os.path import isfile, join


INPUT_CHARSET="utf-8"

########## Function ##############################################

def getfileName(n):
    i=1
    name=n
    if os.path.exists(n+".xml"):
        name=n+"_"+str(i)
        while os.path.exists(name+".xml"):
            i+=1
            name=n+"_"+str(i)
    
    return name+".xml"


def saveFile(OutputFolder,OutputHeader,name,content):
    filename=getfileName(OutputFolder+"/"+name)
    outputFooter='</div>\n</body>\n</text>\n</TEI>'
    foutput=open(filename,"w",encoding=INPUT_CHARSET)
    foutput.write(OutputHeader.replace("\\n","\r"))
    foutput.write(content.replace("\\n","\r")[2:-1])
    foutput.write(outputFooter)
    foutput.close()

def saveFileWITHOUTHEADER(OutputFolder,name,content):
    filename=getfileName(OutputFolder+"/"+name)
    foutput=open(filename,"w",encoding=INPUT_CHARSET)
    #foutput.write(OutputHeader.replace("\\n","\r"))
    foutput.write(content.replace("\\n","\r")[2:-1])
    #foutput.write(outputFooter)
    foutput.close()



def listallFilesinFolder(mypath,extension):
	extension="."+extension.lower()
	onlyfiles = [ f for f in listdir(mypath) if isfile(join(mypath,f)) and f.lower().endswith(extension) ]
	return onlyfiles

def ParseFile(OutputFolder,path):
    ET.register_namespace('', "http://www.tei-c.org/ns/1.0")
    tree = ET.parse(path)
    root = tree.getroot()
    header=root[0] # Header
    OutputHeader='<TEI xmlns="http://www.tei-c.org/ns/1.0">\n'
    OutputHeader+=str(ET.tostring(header))[2:-1]
    OutputHeader+='<text>\n<body>\n<div type="edition">\n'
    outputFooter='</div>\n</body>\n</text>\n</TEI>'
    index=0
    unknown=0
    mms=0
    addenda=0
    toc=0
    fragmenta=0
    dedication=0
    # [create new counter for the new subtyope] e.g.  tbl=0
    for child in root[1][0][0]:
        print(child.attrib)
        if str(child.tag)=="{http://www.tei-c.org/ns/1.0}div" and 'subtype' in child.attrib:
            att=child.attrib;
            if att['subtype']=="preface": # Introduction
                saveFile(OutputFolder,OutputHeader,"Introduction",str(ET.tostring(child)))
            elif att['subtype']=="work":  # Work
                title=""
                if 'n' in child.attrib:
                    title=att['n']
                else:
                    unknown+=1
                    title="UNKNOWN"+str(unknown)
                saveFile(OutputFolder,OutputHeader,title,str(ET.tostring(child)))
            elif att['subtype']=="index":  # Index
                index+=1
                saveFile(OutputFolder,OutputHeader,"INDEX"+str(index),str(ET.tostring(child)))
            elif att['subtype']=="mss":  # Index
                mms+=1
                saveFileWITHOUTHEADER(OutputFolder,"MMS"+str(mms),str(ET.tostring(child)))
            elif att['subtype']=="addenda":  # Add
                addenda+=1
                saveFile(OutputFolder,OutputHeader,"ADDENDA"+str(addenda),str(ET.tostring(child)))
            elif att['subtype']=="toc":  # toc
                toc+=1
                saveFile(OutputFolder,OutputHeader,"TOC"+str(toc),str(ET.tostring(child)))
            elif att['subtype']=="fragmenta":  # fragm
                fragmenta+=1
                saveFile(OutputFolder,OutputHeader,"FRAGMENTA"+str(fragmenta),str(ET.tostring(child)))
            elif att['subtype']=="dedication":  # dedication
                dedication+=1
                saveFileWITHOUTHEADER(OutputFolder,"Dedication"+str(dedication),str(ET.tostring(child)))




##################################################################

####################### Code starts here #########################

folderPath= "files/"#"/u/stoyanova/Desktop/csel-dev" # path of the folder where CSEL XML file exist

# 1- List all files in the folder
files=listallFilesinFolder(folderPath,"xml")
for f in files:
    print(f)
    OutputFolder=folderPath+"/"+f+"_Output"
    filepath=folderPath+"/"+f
    if not os.path.exists(OutputFolder):
        os.makedirs(OutputFolder)
    ParseFile(OutputFolder,filepath)
