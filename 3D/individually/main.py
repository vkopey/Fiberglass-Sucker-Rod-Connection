# -*- coding: cp1251 -*-
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
def build(np):
    n=np[0]
    p=np[1]
    if n==1:
        model.StaticStep(initialInc=0.1, maxInc=0.1, name='Step-'+str(n), previous='Initial')
    else:
        model.StaticStep(initialInc=0.1, maxInc=0.1, name='Step-'+str(n), previous='Step-'+str(n-1))
        model.boundaryConditions['BC-'+str(n-1)].deactivate('Step-'+str(n))
        model.interactions['Int-'+str(n-1)].deactivate('Step-'+str(n))
        model.boundaryConditions['BC-'+str(p-1)].deactivate('Step-'+str(n))
        model.interactions['Int-'+str(p-1)].deactivate('Step-'+str(n))
    for i in np:
        model.SurfaceToSurfaceContactStd(adjustMethod=NONE,
            clearanceRegion=None, contactControls='ContCtrl-1', createStepName='Step-'+str(n)
            , datumAxis=None, initialClearance=OMIT, interactionProperty='IntProp-1', 
            master=model.rootAssembly.instances['Tool-1-rad-'+str(i)].surfaces['in']
            , name='Int-'+str(i), slave=
            model.rootAssembly.instances['Nipple-1'].surfaces['out'], 
            sliding=FINITE, thickness=ON)
        model.RigidBody(bodyRegion=
            model.rootAssembly.instances['Tool-1-rad-'+str(i)].sets['in'],
            name='Constraint-'+str(i), refPointRegion=
            model.rootAssembly.instances['Tool-1-rad-'+str(i)].sets['rp'])
        model.DisplacementBC(amplitude='Amp-1', createStepName='Step-'+str(n)
            , distributionType=UNIFORM, fieldName='', fixed=OFF, localCsys=
            model.rootAssembly.instances['Tool-1-rad-'+str(i)].datums[8],
            name='BC-'+str(i), region=
            model.rootAssembly.instances['Tool-1-rad-'+str(i)].sets['rp'],
            u1=-3.5, u2=0.0, u3=0.0, ur1=0.0, ur2=0.0, ur3=0.0)

model=mdb.models['Model-1']
model.rootAssembly.RadialInstancePattern(axis=(0.0, 1.0, 0.0),
    instanceList=('Tool-1', ), number=12, point=(0.0, 0.0, 0.0), totalAngle=360.0)
model.rootAssembly.features.changeKey(fromName='Tool-1', toName='Tool-1-rad-1') 
for np in [(1,7),(2,8),(3,9),(4,10),(5,11),(6,12)]:
    build(np)

model.StaticStep(initialInc=0.1, maxInc=0.1, name='Step-7', previous='Step-6')
model.boundaryConditions['BC-12'].deactivate('Step-7')
model.boundaryConditions['BC-6'].deactivate('Step-7')
model.interactions['Int-12'].deactivate('Step-7')
model.interactions['Int-6'].deactivate('Step-7')
model.DisplacementBC(amplitude=UNSET, createStepName='Initial', 
    distributionType=UNIFORM, fieldName='', localCsys=None, name='up', 
    region=model.rootAssembly.instances['Rod-1'].sets['up'], 
    u1=SET, u2=SET, u3=SET, ur1=SET, ur2=SET, ur3=SET) 
model.boundaryConditions['up'].setValuesInStep(stepName='Step-7', u2=7.0) 
