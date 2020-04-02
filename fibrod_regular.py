#encoding: utf-8
# скінченно-елементна модель з'єднання з прямокутною регулярною сіткою
from __future__ import division
import os
import numpy as np
import matplotlib.pyplot as plt
from math import pi,sin

class RodConnector:
    """Параметри з'єднання"""
    r0=11.0 # радіус штанги
    r1=18.0 # радіус ніпеля
    l0=150.0 # довжина штанги
    l1=150.0 # довжина ніпеля
    l3=1.875 # зміщення штанги відносно ніпеля вверх
    # рекомендується l3=(l1/n1[1])/2
    n0=3,40 # кількість елементів штанги по x,y
    n1=2,40 # кількість елементів ніпеля по x,y
    y1,y2=10.0, 140.0 # границі вертикальної зони деформування
    args=[0.12, 1.0, 1.0] # параметри деформування для функції dx()
    def dx(self,y):
        """Закон деформування - залежність зміщень (в напрямку до осі)
        точок внутрішньої поверхні ніпеля від ординати точки y"""
        a,b,c=self.args
        #0.1 # рівномірне
        #0.01*y # клинопідібне
        #0.2+0.01*y # рівномірне+клинопідібне
        #1.-0.0005*(y-70)**2 # параболічне
        #1.0+0.5*sin(2*pi*y/30.0+0.0) # гармонічне
        #1.0+0.01*y*sin(2*pi*y/30.0+0.0) # гармонічне зі змінною амплітудою 
        #0.1+(0.2-0.001*y)*sin(2*pi*y/30.0+0.0) # гармонічне зі змінною амплітудою (обернене)
        return self.args[0]
    
class Model:
    """Скінченно-елементна модель з'єднання з прямокутною регулярною сіткою
    Увага! Тут нумерація індексів з 0, а у inp-файлі з 1"""
    def __init__(self):
        self.ccx=r"c:\CalculiXLauncher-03.1-beta_Windows-32bit\bin\ccx\ccx212.exe" # повний шлях до розв'язувача
        self.dirccx=os.path.dirname(self.ccx)
        os.chdir(self.dirccx)
        self.filename='fiber' # назва файлу моделі
        self.reset()
    
    def reset(self): # очистити сітку
        self.N=[] # вузли
        self.E=[] # елементи
        self.indE={} # індекси елементів деталей
    
    def indN(self,part):
        """Індекси вузлів деталі part"""
        s=set()
        for i in self.indE[part]:
            s.update(set(self.E[i]))
        return list(s)
        
    def mesh(self,x,y,lx,ly,nx,ny):
        """Будує регулярну сітку на прямокутній області
        x,y # лівий нижній кут
        lx,ly # ширина, висота
        nx,ny - кількість елементів в ширину і висоту"""
        newE=[] # індекси нових елементів
        dx, dy = lx/nx, ly/ny # ширина, висота елемента
        for j in range(ny):
            for i in range(nx):
                #print i,j
                e=[] # елемент
                for dn in [(0,0),(dx,0),(dx,dy),(0,dy)]: # додати 4 вузли (проти годинникової стрілки)
                    n=[i*dx+dn[0]+x, j*dy+dn[1]+y] # вузол
                    if n not in self.N: # якщо такого вузла ще немає
                        self.N.append(n) # додати вузол
                    e.append(self.N.index(n)) # додати номер вузла в елемент
                self.E.append(e) # додати елемент
                newE.append(len(self.E)-1) # додати індекс елемента
        return newE

    def getVLineNodes(self,part,x,y1,y2):
        """Повертає індекси вузлів вертикальної лінії"""
        L=[] # вузли однієї лінії
        for i in self.indN(part): # для індексів вузлів деталі part
            n=self.N[i] # вузол
            if n[0]==x and n[1]>=y1 and n[1]<=y2: # якщо належить лінії
                L.append([i,n])
        L.sort(key=lambda x: x[1][1]) # сортувати по y
        L=[i[0] for i in L] # тільки індекси
        return L
        
    def getHLineNodes(self,part,y,x1,x2):
        """Повертає індекси вузлів горизонтальної лінії"""
        L=[] # вузли однієї лінії
        for i in self.indN(part): # для індексів вузлів деталі part
            n=self.N[i] # вузол
            if n[1]==y and n[0]>=x1 and n[0]<=x2: # якщо належить лінії
                L.append([i,n])
        L.sort(key=lambda x: x[1][0]) # сортувати по x
        L=[i[0] for i in L] # тільки індекси
        return L
    
    def getElements(self,Nodes):
        """Повертає список елементів і їх граней за впорядкованим списком вузлів лінії"""
        n=0
        E=[] # список елементів
        P={(0,1):'S1',(1,2):'S2',(2,3):'S3',(0,3):'S4'} # грані елемента
        while n<len(Nodes)-1: # кожний вузол крім останнього
            n1,n2=Nodes[n],Nodes[n+1] # пара сусідніх вузлів
            # шукаємо цю пару серед усіх елементів
            for i,e in enumerate(self.E): 
                if n1 in e and n2 in e:
                    p=sorted((e.index(n1),e.index(n2))) # вузли грані
                    E.append((i,P[tuple(p)]))
            n+=1
        return E
    
    def deform(self):
        """Деформування сітки лінії
        Увага! Величина деформування повинна бути меншою розміру елемента
        Увага! Деформувати сітку тільки після визначення потрібних вузлів функціями getHLineNodes, getVLineNodes"""
        L=self.getVLineNodes(part='nipple',x=rc.r0,y1=0,y2=rc.l1)
        for i in L: # для кожного вузла лінії
            x,y=self.N[i]
            if y>=rc.y1 and y<=rc.y2: # межі деформування
                self.N[i][0]=x-rc.dx(y) # змістити вузол вліво на величину dx

    def draw(self):
        """Рисує сітку"""
        N=self.N
        for i,e in enumerate(self.E):# [:4]
            X=[N[e[0]][0],N[e[1]][0],N[e[2]][0],N[e[3]][0],N[e[0]][0]]
            Y=[N[e[0]][1],N[e[1]][1],N[e[2]][1],N[e[3]][1],N[e[0]][1]]
            if i in self.indE['nipple']:
                plt.plot(X, Y,'ko-')
            else:
                plt.plot(X, Y,'ro-')
        plt.axes().set_aspect('equal')
        plt.show()
                
    def writeINP(self,Lines): 
        """Створює inp-файл для CalculiX
        Увага! Нумерація індексів у файлі з 1, тому усі індекси збільшуємо на 1"""
        Line1,Line2,Line3,Line4,Line5=Lines # списки вузлів потрібних ліній
        
        s="*NODE, NSET=NALL\n"
        for i,n in enumerate(self.N):
            x,y=n
            s+="%d, %f,%f\n"%(i+1,x,y)
        
        s+="*NSET, NSET=Line1\n"
        for i in Line1:
            s+="%d\n"%(i+1)
        
        s+="*NSET, NSET=Line2\n"
        for i in Line2:
            s+="%d\n"%(i+1)
        
        s+="*NSET, NSET=Line3\n"
        for i in Line3:
            s+="%d\n"%(i+1)
        
        s+="*NSET, NSET=Line4\n"
        for i in Line4:
            s+="%d\n"%(i+1)
            
        s+="*NSET, NSET=Line5\n"
        for i in Line5:
            s+="%d\n"%(i+1)
            
        s+="*ELEMENT, type=CAX4, ELSET=Rod\n" # або CAX4R
        for i,e in enumerate(self.E):
            if i==self.indE['nipple'][0]:
                s+="*ELEMENT, type=CAX4, ELSET=Nipple\n"
            s+="%d, %d,%d,%d,%d\n"%(i+1,e[0]+1,e[1]+1,e[2]+1,e[3]+1)
        
        s+="*SURFACE, NAME = Line2, TYPE = ELEMENT\n"
        for i,j in self.getElements(Line2):
            s+="%d, %s\n"%(i+1, j)
        
        s+="*SURFACE, NAME = Line4, TYPE = ELEMENT\n"
        for i,j in self.getElements(Line4):
            s+="%d, %s\n"%(i+1, j)
        
        Elset1=set() # елементи, де потрібні будуть результати
        for i,j in self.getElements(Line3)+self.getElements(Line4):
            Elset1.add(i)
        s+="*ELSET,ELSET=Elset1\n"
        for i in Elset1:
            s+="%d\n"%(i+1)
        
        s+="""
*MATERIAL, NAME=mat1
*ELASTIC,TYPE=ENGINEERING CONSTANTS
10000.0,50000.0,10000.0,0.22,0.22,0.22,4000.0,4000.0
20000.0,295.0
*MATERIAL, NAME=mat2
*ELASTIC
210000.0, 0.3 
*SOLID SECTION, ELSET=Rod, MATERIAL=mat1
1.
*SOLID SECTION, ELSET=Nipple, MATERIAL=mat2
1.
*SURFACE INTERACTION, NAME=Int1
*SURFACE BEHAVIOR, PRESSURE-OVERCLOSURE=LINEAR
1.E7, 3.
*FRICTION
0.2, 47000 
*CONTACT PAIR, INTERACTION=Int1, ADJUST=Line4, TYPE=SURFACE TO SURFACE
Line4, Line2
*BOUNDARY
Line5,1,1,0.0
*BOUNDARY
Line1,1,2,0.0
*AMPLITUDE,NAME=A1
0.0,0.0,0.1,0.1,0.2,0.2,0.3,0.3, 
0.4,0.4,0.5,0.5,0.6,0.6,0.7,0.7,
0.8,0.8,0.9,0.9,1.0,1.0
*STEP,NLGEOM
*STATIC
1E-4,1.0
*NODE FILE 
U,
*EL FILE
S,
*END STEP

*STEP,NLGEOM
*STATIC,DIRECT
0.01,1.0
*BOUNDARY
**BOUNDARY,AMPLITUDE=A1
Line3,2,2,5.0
*NODE FILE 
U,
*EL FILE
S,
** *NODE PRINT,NSET=Line3
** RF
*EL PRINT,ELSET=Elset1
S
*END STEP
"""
        
        f=open(self.dirccx+"\\"+self.filename+".inp", 'w')
        f.write(s)
        f.close()

    def runCCX(self):
        """Розраховує задачу в CalculiX"""
        import subprocess
        s=subprocess.check_output([self.ccx, "-i", self.dirccx+ "\\" +self.filename], shell=True)
        L=[ln.strip() for ln in s.splitlines()[-10:]] # останні рядки виведення
        if "Job finished" in L:
            return 1 # якщо розрахунок успішний
        return 0 # якщо розрахунок не успішний
        
    def readResult1(self, Nodes):
        """Читає результати для елементів штанги в місці контакту"""
        elset=[str(i+1) for i,j in self.getElements(Nodes)]
        f=open(self.dirccx+"\\"+self.filename+".dat",'r')
        L=f.readlines()
        f.close()
        Y=[] # значення
        inc1=True
        for s in L: # для кожного рядка
            w=s.strip().split(' ') # слова
            w=[i for i in w if i.strip()!=''] # без пустих слів
            if w==[]: continue # пропустити пусті рядки
            if w[0]=='stresses':
                if not inc1: break # тільки для першого інкремента
                inc1=False
            if w[0] in elset: # якщо елемент у списку
                if w[1]=='3': # integration point (1 для CAX4R)
                    Y.append(float(w[2])) # !!! напруження sxx
        return min(Y) # бо зі знаком -
            
    def readResult2(self, Nodes):
        """Читає результати для елементів штанги в місці верхнього торця"""
        elset=[str(i+1) for i,j in self.getElements(Nodes)]
        f=open(self.dirccx+"\\"+self.filename+".dat", 'r')
        L=f.readlines()
        f.close()
        T=[] # час
        Y=[] # значення
        n=len(elset) # кількість елементів
        for s in L: # для кожного рядка
            w=s.strip().split(' ') # слова
            w=[i for i in w if i.strip()!=''] # без пустих слів
            if w==[]: continue # пропустити пусті рядки
            #print w
            if w[0]=='stresses': #'forces'
                T.append(float(w[-1]))
            if w[0]==elset[0]: # якщо перший елемент списку
                if w[1]=='3': # integration point (1 для CAX4R)
                    Y.append(float(w[3])/n)
            if w[0] in elset[1:]: # якщо не перший елемент списку
                if w[1]=='3': # integration point
                    Y[-1]=Y[-1]+float(w[3])/n # середнє по елементам
        plt.plot(T,Y,'ko-')
        plt.show()
        
        # D=[(b-a)/(T[1]-T[0]) for a,b in zip(Y[:-1],Y[1:])] # похідна dy/dt
        # print D
        # dmin=200 # мінімальне допустиме (малий наклон дотичної на рис. означає руйнування з'єднання)
        # for i,d in enumerate(D): # для усіх значень dy/dt
        #     if d<dmin: # якщо менше допустимого
        #         return T[i],Y[i] # то це точка руйнування
        Ymax=max(Y)
        t=T[Y.index(Ymax)]
        if t==T[-1]: print "Увага! Можливо знайдено максимальне напруження. Збільшіть величину осьової деформації"
        return t, Ymax
                
    def run(self, runCCX=True):
        """Створює модель і виконує задачу"""
        self.reset() # очистити
        # створити сітку
        self.indE['rod']=self.mesh(x=0.0, y=rc.l3, lx=rc.r0, ly=rc.l0, nx=rc.n0[0], ny=rc.n0[1])
        print len(self.N),len(self.E)
        self.indE['nipple']=self.mesh(x=rc.r0, y=0.0, lx=rc.r1-rc.r0, ly=rc.l1, nx=rc.n1[0], ny=rc.n1[1])

        Line1=self.getHLineNodes('nipple', y=0, x1=0, x2=rc.r1) # низ
        Line2=self.getVLineNodes('nipple', x=rc.r0, y1=0, y2=rc.l1) # контакт
        Line3=self.getHLineNodes('rod', y=rc.l0+rc.l3, x1=0, x2=rc.r0) # верх
        Line4=self.getVLineNodes('rod', x=rc.r0, y1=rc.l3, y2=rc.l0+rc.l3) # контакт
        Line5=self.getVLineNodes('rod', x=0, y1=rc.l3, y2=rc.l0+rc.l3) # вісь
        self.deform() # !!! деформувати сітку тільки після визначення потрібних вузлів функціями getHLineNodes, getVLineNodes
        self.writeINP([Line1,Line2,Line3,Line4,Line5])
        if runCCX==False:
            self.draw() # тільки нарисувати сітку і вийти
            return
        if self.runCCX(): # розрахувати і повернути результати
            sxx=self.readResult1(Nodes=Line4)
            t,syy=self.readResult2(Nodes=Line3)
            print sxx,t,syy
            return sxx,t,syy
                
    def optimize(self):
        """Виконує послідовність задач для оптимізації"""
        open('result.csv', 'w').close() # створити файл результатів
        for x in [0.10,0.11,0.12,0.13,0.14,0.15]: # значення параметрів моделі
            rc.args[0]=x # змінити значення параметрів моделі
            sxx,t,syy=self.run() # розрахувати і отримати результати
            with open('result.csv', 'a') as f: # додати результати у файл
                f.write("%f;%f;%f;%f\n"%(x,sxx,t,syy))

##            
rc=RodConnector()
mr=Model()
#mr.run(False) # тільки створити модель і показати сітку
mr.run() # виконати задачу
#mr.optimize() # виконати послідовність задач
