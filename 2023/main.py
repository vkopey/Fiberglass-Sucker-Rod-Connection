# -*- coding: utf-8 -*-
import csv
execfile('tools.py')
csv_file=open("results.csv", "wb")
writer = csv.writer(csv_file,delimiter = ';')
#writer.writerow(['x','s'])
x1=10.5
x2=0.0
x3=15.0
#for x1 in [10.1,10.2,10.3,10.4,10.5,10.6,10.7,10.8,10.9]: # rn
#for x2 in [-9,-8,-7,-6,-5,-4,-3,-2,-1,0,1,2,3,4,5,6,7,8,9]: # інкр l1a, pa
#for x3 in [9,10,11,12,13,14,15,16,17,18,19,20]: # вел. l2a
for x4 in [0,1,2,3,4,5,6,7,8,9]: # декр l1a та інкр l2a
    execfile('rod_fiber.py')
    print 'x=',x1
    #Mdb()
    #session.viewports['Viewport: 1'].setValues(displayedObject=None)
csv_file.close()
