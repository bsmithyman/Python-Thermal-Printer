#!/usr/bin/env python

import numpy as np

import matplotlib
matplotlib.use('agg')
from matplotlib.figure import Figure
from matplotlib.backends.backend_agg import FigureCanvasAgg

import Image

from Adafruit_Thermal import Adafruit_Thermal

from pygeo.segyread import SEGYFile

dpi = 100

figkwargs = {
	'facecolor':	'w',
	'figsize':	(15,4.8),
}

sf = SEGYFile('line05.src')
src = sf[:]
ns = sf.ns

trh = sf.trhead[0]

dt = trh['dt'] / 1000.
tmin = trh['lagb']
tmax = dt*ns + tmin

x = np.linspace(tmin, tmax, sf.ns)

fig = Figure(**figkwargs)

ax = fig.add_subplot(1,1,1)
pl = ax.plot(x, src)

ax.set_title('Source signature for Line 05')
ax.set_xlabel('Time (ms)')
ax.set_ylabel('Amplitude')

canvas = FigureCanvasAgg(fig)
renderer = canvas.get_renderer()
renderer.dpi = dpi
canvas.draw()

l,b,w,h = [int(item) for item in canvas.figure.bbox.bounds]
im = Image.fromstring("RGB", (w,h), canvas.tostring_rgb()).rotate(90)

printer = Adafruit_Thermal("/dev/tty.NoZAP-PL2303-00005014", 19200, timeout=5)
printer.begin()
printer.printImage(im, True)
printer.feed(2)
