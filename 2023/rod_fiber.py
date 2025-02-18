# -*- coding: utf-8 -*-
'''модель пресово-адгезійного з'єднання'''
openMdb(pathName='rod_fiber.cae')
model=mdb.models['Model-1']

class D: pass
d=D() # розміри

d.rn=x1#10.5 # внутрішній радіус ніпеля
d.r1n=17. # зовнішній радіус ніпеля
d.ln=100. # глибина отвору ніпеля

d.rb=11. # радіус тіла
d.lb=d.ln+50. # довжина тіла

d.r1a=d.rn # нижній радіус адгезиву
d.r2a=d.r1a # верхній радіус адгезиву
d.ta=1. # глибина адгезиву
d.pa=30.+x2 # крок адгезиву
d.l1a=10.+x2 # довжина циліндричної (пресової) частини
d.l2a=x3#15. # довжина робочої сторони адгезиву


#================точки характерних кромок моделі========================
class P: pass
p=P() # розміри
p.p1=(d.r1n, d.ln/2, 0) # зовнішній циліндр
p.p2=(d.r1n/2, -30, 0) # нижній торець ніпеля
p.p3=(0, -30/2, 0) # вісь ніпеля
p.p4=(d.rb/2, d.lb, 0) # верхній торець тіла
p.p5=(0, d.lb/2, 0) # вісь тіла
p.p6=(5.0, -10.0, 0.0) # сталева поверхня ніпеля

def createPartition():
    model.ConstrainedSketch(gridSpacing=10.78, name='__profile__',
        sheetSize=431.34, transform=
        model.parts['Nipple'].MakeSketchTransform(
        sketchPlane=model.parts['Nipple'].faces[0],
        sketchPlaneSide=SIDE1, sketchOrientation=RIGHT, origin=(12.224735,
        52.962025, 0.0)))
    model.parts['Nipple'].projectReferencesOntoSketch(filter=
        COPLANAR_EDGES, sketch=model.sketches['__profile__'])
    model.sketches['__profile__'].retrieveSketch(sketch=
        model.sketches['Sketch-3'])
    model.parts['Nipple'].PartitionFaceBySketch(faces=
        model.parts['Nipple'].faces.getSequenceFromMask(('[#1 ]',
        ), ), sketch=model.sketches['__profile__'])


def createProfile(XY):
    '''Створює профіль різьби'''
    for x,y,z in XY:
        s=model.ConstrainedSketch(name='__profile__',sheetSize=200.)
        model.parts['Nipple'].projectReferencesOntoSketch(filter=COPLANAR_EDGES, sketch=s)
        s.ConstructionLine(point1=(0.0,0.0), point2=(0.0, 10.0))
        s.retrieveSketch(sketch=model.sketches['Sketch-3'])
        par={'r1':x, 'dy':y, 'r2':z}
        for k,v in par.iteritems():
            s.parameters[k].setValues(expression=str(v))
        s.delete(objectList=(s.vertices.findAt((0.0,0.0),), ))
        #s.move(objectList=s.geometry.values(),vector=(x,y))
        #model.parts['Nipple'].Cut(sketch=s)
        #model.parts['Nipple'].PartitionFaceBySketch(faces=model.parts['Nipple'].faces.getSequenceFromMask(('[#1 ]',), ), sketch=s) #?
        model.parts['Nipple'].PartitionFaceBySketch(faces=model.parts['Nipple'].faces.findAt(p.p6), sketch=s)

#параметри заготовки ніпеля
set_values(sketch='Sketch-1', p={'r':d.rn, 'r1':d.r1n, 'l':d.ln})
#параметри тіла
set_values(sketch='Sketch-2', p={'r':d.rb, 'l':d.lb})
#параметри профілю різьби ніпеля
set_values(sketch='Sketch-3', p={'r1':d.r1a,'r2':d.r2a,'t':d.ta,'p':d.pa,'l1':d.l1a,'l2':d.l2a})

createPart(n='Nipple',s='Sketch-1')
createPart(n='Rod',s='Sketch-2')

XY=[]; i=0
while i<d.ln:
    XY+=[(d.r1a, i, d.r2a)]
    i+=d.pa
    #d.r1a+=0.04
    #d.r2a+=0.04
#XY=[(d.r1a, 0*d.pa),(d.r1a, 1*d.pa),(d.r1a, 2*d.pa)]
createProfile(XY)

mat1=Material(E=210000.0,mu=0.28,st=400.0,sv=600.0,delta=21.0,psi=56.0).power(8)
createMaterial('Material-1',et=mat1['el'],pt=mat1['pl'])
model.Material(name='Material-2')
model.materials['Material-2'].Elastic(table=((0.1e5, 0.5e5, 0.1e5, 0.22, 0.22, 0.22, 0.04e5, 0.04e5, 0.2e5), ), type=ENGINEERING_CONSTANTS)
model.Material(name='Material-3')
model.materials['Material-3'].Elastic(table=((5000.0, 0.22), ))
model.materials['Material-3'].Plastic(table=((2.0, 0.0, 100.0),
    (8.0, 0.1, 100.0), (20.0, 0.0, 0.0), (80.0, 0.1, 0.0)),
    temperatureDependency=ON)

createSectionAssign(n='Section-1',m='Material-1',p='Nipple')
createSectionAssign(n='Section-2',m='Material-2',p='Rod')
model.parts['Rod'].MaterialOrientation(additionalRotationType=ROTATION_NONE, axis=AXIS_3, fieldName='', localCsys=None, orientationType=GLOBAL, region=Region(faces=model.parts['Rod'].faces), stackDirection=STACK_3)
model.HomogeneousSolidSection(material='Material-3', name='Section-3', thickness=None)
#model.parts['Nipple'].Set(faces=model.parts['Nipple'].faces[1:], name='Adhesive')
faces=model.parts['Nipple'].faces
i=faces.findAt(p.p6).index
model.parts['Nipple'].Set(faces=faces[:i]+faces[i+1:], name='Adhesive')
model.parts['Nipple'].SectionAssignment(region=model.parts['Nipple'].sets['Adhesive'], sectionName='Section-3') # після Section-1!!!

#.getSequenceFromMask(mask=('[#1 ]', ), ))
createAssemblyInstance(n='Nipple-1',p='Nipple')
createAssemblyInstance(n='Rod-1',p='Rod')
ra=model.rootAssembly
model.StaticStep(initialInc=0.05, maxInc=0.05, name='Step-1', previous='Initial')
#createStep(n='Step-1',pr='Initial')
model.StaticStep(initialInc=0.05, maxInc=0.05, name='Step-2', previous='Step-1')

model.TabularAmplitude(data=((0.0, 1.0), (1.0, 1.0)), name='Amp-1', smooth=SOLVER_DEFAULT, timeSpan=STEP)
model.TabularAmplitude(data=((0.0, 1.0), (1.0, 1.0)), name='Amp-2', smooth=SOLVER_DEFAULT, timeSpan=STEP)
model.Temperature(createStepName='Step-1',
    crossSectionDistribution=CONSTANT_THROUGH_THICKNESS, distributionType=
    UNIFORM, magnitudes=(100.0, ), amplitude='Amp-1', name='Predefined Field-1', region=
    model.rootAssembly.instances['Nipple-1'].sets['Adhesive'])
model.predefinedFields['Predefined Field-1'].setValuesInStep(
    magnitudes=(0.0, ), amplitude='Amp-2', stepName='Step-2')

def createContactSet2(n,i,x,ymin,ymax,dy):
    '''Створює набір для контакту
    n - ім'я
    i - елемент зборки
    x, ymin, ymax, dy - параметри пошуку
    '''
    model.rootAssembly.regenerate()
    ae=model.rootAssembly.instances[i].edges
    p=[] # точки для пошуку
    y=ymin
    while y<ymax:
        p.append(((x,y,0.0), ))
        y+=dy
    model.rootAssembly.Set(name=n,edges=ae.findAt(*p))

createContactSet2('Master', 'Nipple-1', d.rn, 0.0, d.ln, 1.0)
#createContactSet(n='Master',i='Nipple-1',ep=((p.p1, ), (p.p2, ), (p.p3, ), ))
createContactSet(n='Slave',i='Rod-1',ep=((p.p4, ), (p.p5, ), ))
model.ContactProperty('IntProp-1')
model.interactionProperties['IntProp-1'].TangentialBehavior(
    dependencies=0, directionality=ISOTROPIC, elasticSlipStiffness=None,
    formulation=PENALTY, fraction=0.005, maximumElasticSlip=FRACTION,
    pressureDependency=OFF, shearStressLimit=None, slipRateDependency=OFF,
    table=((0.1, ), ), temperatureDependency=OFF)
model.interactionProperties['IntProp-1'].NormalBehavior(
    allowSeparation=ON, constraintEnforcementMethod=DEFAULT,
    pressureOverclosure=HARD)
createContact()
createBCSet(n='Encastre',i='Nipple-1',ep=(p.p2, )) # закріплення
createBCSet(n='Axis',i='Rod-1',ep=(p.p5, )) # вісь
createBCSet(n='Load',i='Rod-1',ep=(p.p4, )) # навантаження
createBC_Encastre()
model.DisplacementBC(amplitude=UNSET, createStepName='Step-1',
    distributionType=UNIFORM, fieldName='', fixed=OFF, localCsys=None, name=
    'BC-2', region=ra.sets['Axis'], u1=0.0, u2=UNSET, ur3=0.0)
model.DisplacementBC(amplitude=UNSET, createStepName='Step-2',
    distributionType=UNIFORM, fieldName='', fixed=OFF, localCsys=None, name=
    'BC-3', region=ra.sets['Load'], u1=UNSET, u2=5.0, ur3=UNSET)
ra.seedEdgeBySize(constraint=FINER, deviationFactor=0.1, edges=ra.sets['Master'].edges, minSizeFactor=0.1, size=0.5)
ra.seedEdgeBySize(constraint=FINER, deviationFactor=0.1, edges=ra.sets['Slave'].edges, minSizeFactor=0.1, size=0.5)
ra.seedPartInstance(deviationFactor=0.1, minSizeFactor=0.1, regions=(ra.instances['Rod-1'], ra.instances['Nipple-1']), size=1.)
ra.setMeshControls(allowMapped=False, regions=ra.instances['Rod-1'].faces)

ra.generateMesh(regions=(ra.instances['Rod-1'], ra.instances['Nipple-1']))
createJobSubmit()

def readODB_set2(set,step,var,pos=NODAL):
    '''Повертає список середніх результатів в вузлах заданої множини вказаного кроку
    (менш універсальна альтернатива readODB_set())
    set - множина
    step - крок
    var - змінна:
    ('S','Mises')
    ('S','Pressure')
    ('U','Magnitude')
    ('U','U1')
    ('CPRESS','')
    ('D','') #коефіцієнт запасу втомної міцності
    pos - позиція: NODAL - для вузлів,INTEGRATION_POINT - для елементів
    Приклад: readODB_set2(set='Cont',step='Step-1',var=('S','Mises'))
    '''
    if pos==NODAL:
        s=myOdb.rootAssembly.nodeSets[set.upper()] #множина вузлів
    if pos==INTEGRATION_POINT:
        s=myOdb.rootAssembly.elementSets[set.upper()] #множина елементів
    m=[] #список середніх результатів з усіх вузлів множини
    for f in myOdb.steps[step].frames: #для кожного фрейму
        fo=f.fieldOutputs[var[0]].getSubset(region=s,position=pos) #дані
        #openOdb(r'C:/Temp/Model-1.odb').steps['Step-1'].frames[4].fieldOutputs['CPRESS'].getSubset(position=NODAL, region=openOdb(r'C:/Temp/Model-1.odb').rootAssembly.nodeSets['CONT']).values[0].data
        res=[] #список результатів
        for v in fo.values: #для кожного вузла/елемента
            if var[1]=='Mises': res.append(v.mises)#додати до списку результатів
            if var[1]=='S11': res.append(v.data.tolist()[0])
            if var[1]=='S22': res.append(v.data.tolist()[1])
            if var[1]=='S33': res.append(v.data.tolist()[2])
            if var[1]=='S12': res.append(v.data.tolist()[3])
            if var[1]=='Pressure': res.append(v.press)
            if var[0]=='U' and var[1]=='Magnitude': res.append(v.magnitude)
            if var[1]=='U1': res.append(v.data.tolist()[0])
            if var[1]=='U2': res.append(v.data.tolist()[1])
            if var[0]=='CPRESS': res.append(v.data)
        m.append((f.frameValue, sum(res)/len(res)))  #додати середнє з усіх вузлів
    return m #повертае список значень


def findmax(data):
    '''Повертає максимальне значення в форматі (час, значення)'''
    maxx=(0,0)
    for x in data:
        if x[1]>maxx[1]:
            maxx=x
    return maxx

def createResults():
    session.viewports['Viewport: 1'].setValues(displayedObject=myOdb)
    res=readODB_set2(set='Slave',step='Step-1',var=('S','Mises'),pos=INTEGRATION_POINT)
    s1max=findmax(res) #знайти максимальне з усіх фреймів
    res=readODB_set2(set='Load',step='Step-2',var=('S','S22'),pos=INTEGRATION_POINT)
    s2max=findmax(res)
    writer.writerow([x1, s1max[0], s1max[1], s2max[0], s2max[1]])

myOdb = openOdb(path=model.name + '.odb')
createResults()
myOdb.close()
