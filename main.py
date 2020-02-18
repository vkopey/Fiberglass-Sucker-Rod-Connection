# -*- coding: cp1251 -*-
'''������ Abaqus CAE ��� ���������� �'������� ���������� ������� � �������� ���������'''
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
    '''���� ����� ������� ��������
    � Abaqus �������� ������� ������� ������������ (���.Stress and strain measures)
    E - ������ ��������, ��
    mu - ���������� ��������
    st - ������� ��������, ��
    et - ���������� ��� st
    sb - ������� ������� ������, �� (sv - ������ �������)
    eb - ������� ����������, ��� ������� ������� ������
    delta - ������� ����������
    psi - ������� ��������
    '''
    def __init__(self,E,mu,st,sv,delta,psi):
        '''�����������'''
        self.E=E#������ ��������
        self.mu=mu#���������� ��������
        self.st=st#������� ��������
        self.et=st/E#���������� ��� st
        self.delta=delta/100.0#������� ���������� ���� �������
        self.psi=psi/100.0#������� �������� ���� �������
        k=0.4#����������(eb=(0.1...0.4,0.2...0.8)delta)
        self.sv=sv#������� ������
        self.sb=sv*(1+k*self.delta)#������� ������� ������ 
        self.eb=log(1+k*self.delta)#������� ����������, ��� ������� ������� ������
        #������� ���������� � ���������� � ������ ����������
        self.sk=0.8*self.sv/(1-self.psi)#0.8-���������� ���������� ������������
        #self.sk=self.sv*(1+1.35*self.psi)
        self.ek=log(1/(1-self.psi))
    def bilinear(self):
        '''������� ������� ���������� � ���������� ������������'''
        return {'el':((self.E,self.mu),),
                'pl':((self.st,0.0),#������ ���������
                (self.sb,self.eb))}#��� (self.sk,self.ek)
    def e(self,s,n):
        '''��������� ��������� e(s)
        n - ������
        '''
        return self.et*(s/self.st)**n
    def power(self,k):
        '''������� ������� ���������� � ���������� ������������
        k - ������� ��� ��� ������������ ��������� ������ (2,4,8...)
        '''
        #n ����������� � ����� ����������� ����� ����� (eb+et,sb), n=6...10
        n=log((self.eb+self.et)/self.et)/log(self.sb/self.st)
        ds=self.sb-self.st
        #��������� ���������
        k_=float(k)
        s_e=[(self.st+i/k_*ds,self.e(self.st+i/k_*ds,n)-self.et) for i in range(0,k+1)]
        #s_e=[(self.st+i*ds,self.e(self.st+i*ds,n)-self.et) for i in [0.0,0.25,0.5,0.75,1.0]]
        s_e.append((self.sk,self.ek))#�������� ����� ����������
        return {'el':((self.E,self.mu),),
                'pl':tuple(s_e)}

def set_values(part,feature,par):
    '''
    �������� �������� ����������
    �������:
    par={'h1':0.0002,'h2':0.00004}
    set_values(part='Al',feature='Shell planar-1',par=par)
    '''
    p=model.parts[part] #������
    f=p.features[feature] #�������
    s=model.ConstrainedSketch(name='__edit__', objectToCopy=f.sketch) #���������� ����
    p.projectReferencesOntoSketch(filter=COPLANAR_EDGES, sketch=s, upToFeature=f) #������������
    for k,v in par.iteritems(): #��� ��� ���������
        s.parameters[k].setValues(expression=str(v)) #���������� ��������
    f.setValues(sketch=s) #���������� ����
    del s #�������
    p.regenerate() #������������ ������

def mesh_all():
    '''���� ���� ��������� ��������'''
    ra=model.rootAssembly #������
    #�������� ������
    reg=(ra.instances['Nipple-1'],ra.instances['Rod-1'],ra.instances['Tool-1']) #!!!!!!!!!!
    ra.deleteMesh(regions=reg) #������� ����
    ra.generateMesh(regions=reg) #�������� ����

def JobSubmit():
    '''������ ������'''
    myJob = mdb.jobs['Model-1'] #������
    myJob.submit() #�������� ������
    # ������ ���� ������ �� ���� ����'�����
    myJob.waitForCompletion()

def readODB_set(set,step,var,pos=NODAL):
    '''������� ������ ���������� � ������ ������ ������� ��������� �����
    set - �������
    step - ����� �����
    var - �����:
    (('S', INTEGRATION_POINT, ((INVARIANT, 'Mises'), )), )
    (('U', NODAL, ((COMPONENT, 'U2'), )), )
    pos - �������: NODAL - ��� �����,INTEGRATION_POINT - ��� ��������
    �������: readODB_set(set='Set-1',step='Step-1',var=var)
    '''
    #�������� ���
    if pos==NODAL:    
        dat=session.xyDataListFromField(odb=myOdb, outputPosition=NODAL, variable=var, nodeSets=(set.upper(),)) #���
    if pos==INTEGRATION_POINT:
        dat=session.xyDataListFromField(odb=myOdb, outputPosition=INTEGRATION_POINT, variable=var, elementSets=(set.upper(),)) #���
    
    step_number=myOdb.steps[step].number #����� �����
    
    nframes=[] #������ ������� ������ � ������� �����
    for k in myOdb.steps.keys(): #��� ��� �����
        nframes.append(len(myOdb.steps[k].frames))
                      
    nstart_frame=nframes[step_number-2] #����� ����������� ������ �����
    nend_frame=int(sum(nframes[step_number-2:step_number])) #����� �������� ������ �����
    res=[] #������ ����������
    for x in dat: #��� ��� �����
        #x.data �� ((���,��������),(���,��������)...)
        res.append(x.data[nstart_frame:nend_frame]) #��� ����� � ��������� �����
                            
    #�������� �������� ���
    for k in session.xyDataObjects.keys():
        del session.xyDataObjects[k] 
    return res #�������� ������ �������

def readODB_set2(set,step,var,pos=NODAL):
    '''������� ������ ������� ���������� � ������ ������ ������� ��������� �����
    (���� ����������� ������������ readODB_set())
    set - �������
    step - ����
    var - �����:
    ('S','Mises')
    ('S','Pressure')
    ('U','Magnitude')
    ('U','U1')
    ('CPRESS','')
    ('D','') #���������� ������ ������ ������
    pos - �������: NODAL - ��� �����,INTEGRATION_POINT - ��� ��������
    �������: readODB_set2(set='Cont',step='Step-1',var=('S','Mises'))
    '''
    if pos==NODAL:    
        s=myOdb.rootAssembly.nodeSets[set.upper()] #������� �����
    if pos==INTEGRATION_POINT:
        s=myOdb.rootAssembly.elementSets[set.upper()] #������� ��������
    m=[] #������ ������� ���������� � ��� ����� �������
    for f in myOdb.steps[step].frames: #��� ������� ������
        fo=f.fieldOutputs[var[0]].getSubset(region=s,position=pos) #���
        #openOdb(r'C:/Temp/Model-1.odb').steps['Step-1'].frames[4].fieldOutputs['CPRESS'].getSubset(position=NODAL, region=openOdb(r'C:/Temp/Model-1.odb').rootAssembly.nodeSets['CONT']).values[0].data
        res=[] #������ ����������
        for v in fo.values: #��� ������� �����/��������
            if var[1]=='Mises': res.append(v.mises)#������ �� ������ ����������
            if var[1]=='S11': res.append(v.data.tolist()[0])
            if var[1]=='S22': res.append(v.data.tolist()[1])
            if var[1]=='S33': res.append(v.data.tolist()[2])
            if var[1]=='S12': res.append(v.data.tolist()[3])
            if var[1]=='Pressure': res.append(v.press)
            if var[0]=='U' and var[1]=='Magnitude': res.append(v.magnitude)
            if var[1]=='U1': res.append(v.data.tolist()[0])
            if var[1]=='U2': res.append(v.data.tolist()[1])
            if var[0]=='CPRESS': res.append(v.data)
        m.append((f.frameValue, sum(res)/len(res)))  #������ ������ � ��� �����
    return m #�������� ������ �������

def findmax(data):
    '''������� ����������� �������� � ������ (���, ��������)'''
    max=(0,0)
    for x in data:
        if x[1]>max[1]:
            max=x
    return max

import csv
csv_file=open("results.csv", "wb") #������� csv ����
writer = csv.writer(csv_file,delimiter = ';') #���������� ���������
writer.writerow(['deltax','st','lc','step_time','S22','step_time','cpress']) #�������� �����
model=mdb.models['Model-1'] #������

for deltax in [0.1,0.15,0.2,0.25,0.3]: #���� ��� ���� ������� ���������� ������
    for lc in [100.0,140.0,180.0]: #���� ��� ���� ������� ���������� 
        for st in [300.0,400.0,500.0]: #���� ��� ���� ������� �������� ����
            #���������� �������� ������������ ���������
            set_values(part='Nipple',feature='Shell planar-1',par={'l1':lc+20,'r1':17})
            set_values(part='Tool',feature='Wire-1',par={'l1':lc,'l2':lc+10})
            set_values(part='Rod',feature='Shell planar-1',par={'l1':lc+70})
            model.rootAssembly.regenerate() #��������
            #�������� �������
            mat_steel=Material(E=210000.0,mu=0.28,st=st,sv=600.0,delta=21.0,psi=56.0)
            #������ ��������
            model.materials['Material-1'].elastic.setValues(table=((mat_steel.E, mat_steel.mu), ))
            model.materials['Material-1'].plastic.setValues(table=mat_steel.power(8)['pl'])
            model.materials['Material-2'].elastic.setValues(table=((0.1e5, 0.5e5, 0.1e5, 0.22, 0.22, 0.22, 0.04e5, 0.04e5, 0.2e5), )) 
            mesh_all() #�������� ����
            model.boundaryConditions['BC-4'].setValues(u1=-deltax) #�������� �����
            #model.loads['Load-1'].setValues(magnitude=press)
            JobSubmit() #�������� ������
            myOdb = openOdb(path=model.name + '.odb') #������� ���� ����� ����������
            session.viewports['Viewport: 1'].setValues(displayedObject=myOdb)
            
            #�������� ����������
            x1=readODB_set2(set='Up',step='Step-2',var=('S','S22'),pos=INTEGRATION_POINT)
            x1max=findmax(x1)#������ ����������� � ��� ������
            
            #�������� ���������� ����
            x2=readODB_set2(set='Nip',step='Step-1',var=('CPRESS',''))
            x2max=findmax(x2)#������ ����������� � ��� ������
            
            #�������� ����������� ����������
            #x3=readODB_set2(set='Bot',step='Step-2',var=('U','U2'))
            
            ##�������� ����������
            #var=(('S', INTEGRATION_POINT, ((INVARIANT, 'Mises'), )), )
            #print readODB_set(set='Up',step='Step-2',var=var)
            ##�������� ����������� ����������
            #var=(('U', NODAL, ((COMPONENT, 'U2'), )), )
            #print readODB_set(set='Bot',step='Step-2',var=var)
            
            #�������� ��� � ����
            writer.writerow([deltax, st, lc, x1max[0], x1max[1], x2max[0], x2max[1]])
            myOdb.close() #������� ���� ����� ���������� 
csv_file.close() #������� ���� csv