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
def build(n):
    name='Tool-1-rad-'+str(n)
    model.SurfaceToSurfaceContactStd(adjustMethod=NONE, 
        clearanceRegion=None, contactControls='ContCtrl-1', createStepName='Step-1'
        , datumAxis=None, initialClearance=OMIT, interactionProperty='IntProp-1', 
        master=
        model.rootAssembly.instances[name].surfaces['in']
        , name='Int-'+str(n), slave=
        model.rootAssembly.instances['Nipple-1'].surfaces['out'], 
        sliding=FINITE, thickness=ON)
    model.RigidBody(bodyRegion=
        model.rootAssembly.instances[name].sets['in'],
        name='Constraint-'+str(n), refPointRegion=
        model.rootAssembly.instances[name].sets['rp'])
    model.DisplacementBC(amplitude='Amp-1', createStepName='Step-1'
        , distributionType=UNIFORM, fieldName='', fixed=OFF, localCsys=
        model.rootAssembly.instances[name].datums[8],
        name='BC-'+str(n), region=
        model.rootAssembly.instances[name].sets['rp'],
        u1=-3.5, u2=0.0, u3=0.0, ur1=0.0, ur2=0.0, ur3=0.0)
    model.boundaryConditions['BC-'+str(n)].deactivate('Step-2')

model=mdb.models['Model-1']
model.rootAssembly.RadialInstancePattern(axis=(0.0, 1.0, 0.0),
    instanceList=('Tool-1', ), number=12, point=(0.0, 0.0, 0.0), totalAngle=
    360.0)
for n in [2,3,4,5,6,7,8,9,10,11,12]:
    build(n)
