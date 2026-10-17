"""Independent complex-plane expectations; compare to the author model later."""
import cmath
import json
import math
from pathlib import Path

WORK=Path(__file__).resolve().parent
def rotate(point,centre,degrees):
    p=complex(*point);c=complex(*centre)
    q=c+(p-c)*cmath.exp(1j*math.radians(degrees))
    return [q.real,q.imag]

cases=[]
for centre in [[2,1],[0,0],[-3,2]]:
    for point in [[4,2],centre,[0,-2],[-1.5,3.25]]:
        for angle in [0,30,45,90,180,270,360,-90]:
            result=rotate(point,centre,angle)
            assert abs(math.dist(point,centre)-math.dist(result,centre))<1e-12
            assert math.dist(rotate(result,centre,-angle),point)<1e-12
            cases.append({'point':point,'centre':centre,'degrees':angle,'expected':result})
assert math.dist(rotate([4,2],[2,1],90),[1,3])<1e-12
with (WORK/'math-oracle.json').open('x',encoding='utf-8') as stream:
    json.dump({'referenceOnlyUntilAuthorModelCompared':True,'cases':cases,'exampleExpected':[1,3],
               'independentMethod':'Complex-plane multiplication, rather than copying the author matrix implementation',
               'invariants':'Distance to centre preserved; inverse rotation recovers point; centre fixed'},stream,indent=2)
print('Prepared',len(cases),'independent numerical reference cases; not yet a test of the new deck')
