#!/usr/bin/env python

# ========================================================================
# Written by Brendan Smithyman <brendan@bitsmithy.net>, May 2013

# This is a Python/Flask-based HTTP server that uses the Adafruit Thermal
# Printer library to communicate with a thermal receipt printer.
# The server accepts formatted XML by HTTP POST, and parses it to extract
# commands for the printer.  This makes it possible to "push" content to
# the printer (e.g., running on a Raspberry Pi), which opens up a number
# of cloud-based automation options.  If you choose to use this code on an
# externally-accessible machine, you should familiarize yourself with the
# security implications and possibly proxy the server.

# TODO
# - Add code for image processing
# - Improve error handling (esp. for malformed inputs)
# - Add symantec markup processing at alternate URLs?

# ========================================================================
# MIT LICENSE 

# Copyright (c) 2013 Brendan Smithyman

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

# ========================================================================
# Initialization / imports

import xml.dom.minidom
from Adafruit_Thermal import Adafruit_Thermal
from flask import Flask, request

# Options for Flask server
appkwargs = {
    'debug':	True,
    'host':	'0.0.0.0',
}

# Options for thermal printer
printerargs = ['/dev/ttyAMA0', 19200]

# The form that is returned in response to an HTTP GET
htmlform = '''\
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html>
<head>
<title>XML Printer</title>
</head>
<body>
<p>This interface is accessible via HTTP POST to /xml, and expects formatted XML.</p>
</body>
</html>
'''

# Initialize the printer
printer = Adafruit_Thermal(*printerargs)

# Create the server app
app = Flask(__name__)


# ========================================================================
# HTTP routing and views

# Routing for the server root
@app.route("/", methods=['GET', 'POST'])
def index ():

    return htmlform

# Routing for the XML post URL
@app.route('/xml', methods=['GET', 'POST'])
def processxml ():
    '''
    Processes the XML post method and passes information to the node handlers.
    '''

    # Return usage instructions
    if (request.method == 'GET'):
        return htmlform

    # Process POST data as XML
    # TODO: Error handling for malformed input
    # TODO: Check on Content-Type: text/xml
    elif (request.method == 'POST'):
        if (not request.data):
            data = ''.join(request.environ['wsgi.input'].readlines())
        else:
            data = request.data

        # Parse the XML using minidom
        doc = xml.dom.minidom.parseString(data)
        startnode = doc.childNodes[0]

        # Begin hierarchical processing of XML
        processNode(startnode)

        return 'Ok'

# ========================================================================
# XML Element Handlers

# This is the root element for the XML schema
def elementPrintout (node, state):
    '''
    Initialization and teardown of the printer.
    '''

    if (state):
        printer.online()
    else:
        # Feed enough paper to allow tearing
        printer.feed(4)
        printer.offline()

# This can (in principle) be used to reset printer settings if needed, but
# seems to cause odd behaviour on my unit
def elementNormal (node, state):
    if (state):
        printer.normal()

# ------------------------------------------------------------------------
# Alignment elements
# We default to left justification

def elementLeft (node, state):
    if (state):
        printer.justify("L")

def elementCenter (node, state):
    if (state):
        printer.justify("C")
    else:
        printer.justify("L")

def elementRight (node, state):
    if (state):
        printer.justify("R")
    else:
        printer.justify("L")

# ------------------------------------------------------------------------
# Feed elements

def elementFeed (node, state):
    if (state):
        if ('lines' in node.attributes.keys()):
            printer.feed(int(node.attributes['lines'].value))
        else:
            printer.feed(1)

def elementFeedRows (node, state):
    if (state):
        if ('rows' in node.attributes.keys()):
            printer.feedRows(int(node.attributes['rows'].value))
        else:
            printer.feedRows(1)

# ------------------------------------------------------------------------
# Formatting elements

def elementInverse (node, state):
    if (state):
        printer.inverseOn()
    else:
        printer.inverseOff()

def elementBold (node, state):
    if (state):
        printer.boldOn()
    else:
        printer.boldOff()

def elementUpsideDown (node, state):
    if (state):
        printer.upsideDownOn()
    else:
        printer.upsideDownOff()

def elementStrike (node, state):
    if (state):
        printer.strikeOn()
    else:
        printer.strikeOff()

def elementUnderline (node, state):
    if (state):
        if ('thickness' in node.attributes.keys()):
            printer.underlineOn(int(node.attributes['thickness'].value))
        else:
            printer.underlineOn()
    else:
        printer.underlineOff()

# ------------------------------------------------------------------------
# Spacing elements

def elementDoubleHeight (node, state):
    if (state):
        printer.doubleHeightOn()
    else:
        printer.doubleHeightOff()

def elementDoubleWidth (node, state):
    if (state):
        printer.doubleWidthOn()
    else:
        printer.doubleWidthOff()

def elementLineHeight (node, state):
    if (state):
        if ('thickness' in node.attributes.keys()):
            printer.setLineHeight(int(node.attributes['height'].value))
        else:
            printer.setLineHeight()

# ------------------------------------------------------------------------
# Font elements
# Default to small text (i.e., 32 characters per line)

def elementLarge (node, state):
    if (state):
        printer.setSize('L')
    else:
        printer.setSize('S')

def elementMedium (node, state):
    if (state):
        printer.setSize('M')
    else:
        printer.setSize('S')

def elementSmall (node, state):
    if (state):
        printer.setSize('S')

# ========================================================================
# XML handling code

# Dictionary to map tagnames to processing functions
elementDict = {
    'printout':		elementPrintout,
#    'normal':		elementNormal,
    'left':		elementLeft,
    'center':		elementCenter,
    'right':		elementRight,
    'br':		elementFeed,
    'feed':		elementFeed,
    'feedrows':		elementFeedRows,
    'inverse':		elementInverse,
    'bold':		elementBold,
    'upsidedown':	elementUpsideDown,
    'strikethrough':	elementStrike,
    'underline':	elementUnderline,
    'doubleheight':	elementDoubleHeight,
    'doublewidth':	elementDoubleWidth,
    'lineheight':	elementLineHeight,
    'large':		elementLarge,
    'medium':		elementMedium,
    'small':		elementSmall,
}

def processElement (node):
    '''
    Processes minidom nodes that correspond to elements in the XML
    schema.  If the tag is recognized as a supported formatting option
    then the corresponding function is called for the opening of the tag.
    The child nodes are processed, and then the closing tag is handled.

    Depending on the type of behaviour desired, the element handling
    function could choose to ignore either the beginning or end tag.
    '''

    tagkey = node.tagName.lower()

    # If the element is recognized, process the tag opening...
    try:
        elementDict[tagkey](node, True)
    except KeyError:
        pass

    # ...then handle any children (if they exist)... 
    for childnode in node.childNodes:
        processNode(childnode)

    # ...and process the close of the tag.
    try:
        elementDict[tagkey](node, False)
    except KeyError:
        pass

def processText (node):
    '''
    Processes text nodes in the XML.  By ignoring nodes that consist of
    only whitespace the behaviour is a bit closer to HTML/etc.
    Whitespace (including leading and following spaces, tabs, etc.) is
    relevant inside the innermost tag groups that contain the text, but
    is a bit looser otherwise.  This makes it possible to write XML code
    that is a bit closer to human-readable.
    '''

    if (not node.wholeText.isspace()):
        printer.write(node.wholeText)

# Dictionary to map minidom nodes to handling functions
nodeDict = {
    xml.dom.minidom.Node.ELEMENT_NODE:	processElement,
    xml.dom.minidom.Node.TEXT_NODE:	processText,
}

def processNode (node):
    '''
    Processes minidom nodes and maps to element- or text-handling code.
    This is called recursively from processElement to handle child nodes.
    '''

    try:
        nodeDict[node.nodeType](node)
    except KeyError:
        pass

# Main program execution (starts the Flask server)
if (__name__ == '__main__'):
    app.run(**appkwargs)
