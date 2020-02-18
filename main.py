# -*- coding: cp1251 -*-
'''Макрос Abaqus CAE для розрахунку з'єднання полімерного стержня з сталевою оболонкою'''
from part import *
from material import *
from section import *
from assembly import *
from step import *
from interaction import *
from load import *
from mesh import *
from job import *
from sketch import *
from visualization import *
from connectorBehavior import *

class Material:
    '''Клас описує поняття матеріалу
    В Abaqus задається істинна діаграма деформування (див.Stress and strain measures)
    E - модуль пружності, Па
    mu - коефіцієнт Пуассона
    st - границя текучості, Па
    et - деформація для st
    sb - істинна границя міцності, Па (sv - умовна границя)
    eb - істинна деформація, яка відповідає границі міцності
    delta - відносне видовження
    psi - відносне звуження
    '''
    def __init__(self,E,mu,st,sv,delta,psi):
        '''конструктор'''
        self.E=E#модуль пружності
        self.mu=mu#коефіцієнт Пуассона
        self.st=st#границя текучості
        self.et=st/E#деформація для st
        self.delta=delta/100.0#відносне видовження після розриву
        self.psi=psi/100.0#відносне звуження після розриву
        k=0.4#коефіцієнт(eb=(0.1...0.4,0.2...0.8)delta)
        self.sv=sv#границя міцності
        self.sb=sv*(1+k*self.delta)#істинна границя міцності 
        self.eb=log(1+k*self.delta)#істинна деформація, яка відповідає границі міцності
        #істинне напруження і деформація в момент руйнування
        self.sk=0.8*self.sv/(1-self.psi)#0.8-коефіцієнт руйнуючого навантаження
        #self.sk=self.sv*(1+1.35*self.psi)
        self.ek=log(1/(1-self.psi))
    def bilinear(self):
        '''Повертає словник елестичних і пластичних властивостей'''
        return {'el':((self.E,self.mu),),
                'pl':((self.st,0.0),#білінійна залежність
                (self.sb,self.eb))}#або (self.sk,self.ek)
    def e(self,s,n):
        '''Степенева залежність e(s)
        n - степінь
        '''
        return self.et*(s/self.st)**n
    def power(self,k):
        '''Повертає словник елестичних і пластичних властивостей
        k - кількість ліній для апроксимації пластичної ділянки (2,4,8...)
        '''
        #n визначається з умови проходження через точку (eb+et,sb), n=6...10
        n=log((self.eb+self.et)/self.et)/log(self.sb/self.st)
        ds=self.sb-self.st
        #степенева залежність
        k_=float(k)
        s_e=[(self.st+i/k_*ds,self.e(self.st+i/k_*ds,n)-self.et) for i in range(0,k+1)]
        #s_e=[(self.st+i*ds,self.e(self.st+i*ds,n)-self.et) for i in [0.0,0.25,0.5,0.75,1.0]]
        s_e.append((self.sk,self.ek))#добавити точку руйнування
        return {'el':((self.E,self.mu),),
                'pl':tuple(s_e)}

def set_values(part,feature,par):
    '''
    Присвоює значення параметрам
    Приклад:
    par={'h1':0.0002,'h2':0.00004}
    set_values(part='Al',feature='Shell planar-1',par=par)
    '''
    p=model.parts[part] #деталь
    f=p.features[feature] #елемент
    s=model.ConstrainedSketch(name='__edit__', objectToCopy=f.sketch) #тимчасовий ескіз
    p.projectReferencesOntoSketch(filter=COPLANAR_EDGES, sketch=s, upToFeature=f) #спроектувати
    for k,v in par.iteritems(): #для всіх параметрів
        s.parameters[k].setValues(expression=str(v)) #установити значення
    f.setValues(sketch=s) #установити ескіз
    del s #знищити
    p.regenerate() #регенерувати деталь

def mesh_all():
    '''Будує сітку скінченних елементів'''
    ra=model.rootAssembly #зборка
    #елементи зборки
    reg=(ra.instances['Nipple-1'],ra.instances['Rod-1'],ra.instances['Tool-1']) #!!!!!!!!!!
    ra.deleteMesh(regions=reg) #знищити сітку
    ra.generateMesh(regions=reg) #створити сітку

def JobSubmit():
    '''Виконує задачу'''
    myJob = mdb.jobs['Model-1'] #задача
    myJob.submit() #виконати задачу
    # Чекати поки задача не буде розв'язана
    myJob.waitForCompletion()

def readODB_set(set,step,var,pos=NODAL):
    '''Повертає список результатів в вузлах заданої множини вказаного кроку
    set - множина
    step - номер кроку
    var - змінна:
    (('S', INTEGRATION_POINT, ((INVARIANT, 'Mises'), )), )
    (('U', NODAL, ((COMPONENT, 'U2'), )), )
    pos - позиція: NODAL - для вузлів,INTEGRATION_POINT - для елементів
    Приклад: readODB_set(set='Set-1',step='Step-1',var=var)
    '''
    #отримати дані
    if pos==NODAL:    
        dat=session.xyDataListFromField(odb=myOdb, outputPosition=NODAL, variable=var, nodeSets=(set.upper(),)) #дані
    if pos==INTEGRATION_POINT:
        dat=session.xyDataListFromField(odb=myOdb, outputPosition=INTEGRATION_POINT, variable=var, elementSets=(set.upper(),)) #дані
    
    step_number=myOdb.steps[step].number #номер кроку
    
    nframes=[] #містить кількість фреймів в кожному кроці
    for k in myOdb.steps.keys(): #для всіх кроків
        nframes.append(len(myOdb.steps[k].frames))
                      
    nstart_frame=nframes[step_number-2] #номер початкового фрейма кроку
    nend_frame=int(sum(nframes[step_number-2:step_number])) #номер кінцевого фрейма кроку
    res=[] #список результатів
    for x in dat: #для всіх вузлів
        #x.data це ((час,значення),(час,значення)...)
        res.append(x.data[nstart_frame:nend_frame]) #дані тільки з вказаного кроку
                            
    #видалити тимчасові дані
    for k in session.xyDataObjects.keys():
        del session.xyDataObjects[k] 
    return res #повертае список значень

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
    max=(0,0)
    for x in data:
        if x[1]>max[1]:
            max=x
    return max

import csv
csv_file=open("results.csv", "wb") #відкрити csv файл
writer = csv.writer(csv_file,delimiter = ';') #установити розділювач
writer.writerow(['deltax','st','lc','step_time','S22','step_time','cpress']) #записати рядок
model=mdb.models['Model-1'] #модель

for deltax in [0.1,0.15,0.2,0.25,0.3]: #цикл для зміни глибини переміщення штампів
    for lc in [100.0,140.0,180.0]: #цикл для зміни довжини обтискання 
        for st in [300.0,400.0,500.0]: #цикл для зміни границі текучості сталі
            #установити значення геометричних параметрів
            set_values(part='Nipple',feature='Shell planar-1',par={'l1':lc+20,'r1':17})
            set_values(part='Tool',feature='Wire-1',par={'l1':lc,'l2':lc+10})
            set_values(part='Rod',feature='Shell planar-1',par={'l1':lc+70})
            model.rootAssembly.regenerate() #обновити
            #створити матеріал
            mat_steel=Material(E=210000.0,mu=0.28,st=st,sv=600.0,delta=21.0,psi=56.0)
            #задати матеріали
            model.materials['Material-1'].elastic.setValues(table=((mat_steel.E, mat_steel.mu), ))
            model.materials['Material-1'].plastic.setValues(table=mat_steel.power(8)['pl'])
            model.materials['Material-2'].elastic.setValues(table=((0.1e5, 0.5e5, 0.1e5, 0.22, 0.22, 0.22, 0.04e5, 0.04e5, 0.2e5), )) 
            mesh_all() #створити сітку
            model.boundaryConditions['BC-4'].setValues(u1=-deltax) #гранична умова
            #model.loads['Load-1'].setValues(magnitude=press)
            JobSubmit() #виконати задачу
            myOdb = openOdb(path=model.name + '.odb') #відкрити базу даних результатів
            session.viewports['Viewport: 1'].setValues(displayedObject=myOdb)
            
            #отримати напруження
            x1=readODB_set2(set='Up',step='Step-2',var=('S','S22'),pos=INTEGRATION_POINT)
            x1max=findmax(x1)#знайти максимальне з усіх фреймів
            
            #отримати контактний тиск
            x2=readODB_set2(set='Nip',step='Step-1',var=('CPRESS',''))
            x2max=findmax(x2)#знайти максимальне з усіх фреймів
            
            #отримати вертикальне переміщення
            #x3=readODB_set2(set='Bot',step='Step-2',var=('U','U2'))
            
            ##отримати напруження
            #var=(('S', INTEGRATION_POINT, ((INVARIANT, 'Mises'), )), )
            #print readODB_set(set='Up',step='Step-2',var=var)
            ##отримати вертикальне переміщення
            #var=(('U', NODAL, ((COMPONENT, 'U2'), )), )
            #print readODB_set(set='Bot',step='Step-2',var=var)
            
            #записати дані у файл
            writer.writerow([deltax, st, lc, x1max[0], x1max[1], x2max[0], x2max[1]])
            myOdb.close() #закрити базу даних результатів 
csv_file.close() #закрити файл csv