const R=String.raw;
export async function content(a){
  a.navigationAliases={'lesson-map':'overview','band-map':'overview','recover-map':'overview','course':'overview'};
  const page=(id,sub,note)=>a.page(id,'Rotate a point about a centre',sub,null,note,{bare:true,parent:'overview',purpose:sub});
  const eq=(n,t,y=590,size=32)=>a.statement(n,t,70,y,1135,62,size);
  const route=(general=false,offsetKnown=true)=>{
    const labels=['Subtract C','Rotate about zero','Add C'];
    [70,462,854].forEach((x,i)=>a.block('operation-'+i,labels[i],x,133,354,51));
    a.arrow('route-1',429,158,27);a.arrow('route-2',821,158,27);
    const vals=general?[R`P=(x,y),\ C=(a,b)`,R`Q=(u,v)=(x-a,y-b)`,R`P'=C+Q'`]:[R`P=(4,2),\ C=(2,1)`,offsetKnown?R`Q=(u,v)=(2,1)`:R`Q=P-C`,R`P'=C+Q'`];
    a.eq('route-input',vals[0],70,197,380,43,25);
    a.eq('route-offset',vals[1],462,197,380,43,25);
    a.eq('route-output',vals[2],854,197,354,43,25);
    a.link('operation-0-text','subtract');a.link('operation-1-text',general?'horizontal':'quarter-turn');a.link('operation-2-text','add-back');
  };
  const result=(n,t,k=2,y=608)=>a.reveal(k,()=>{eq(n,t,y,35);a.line(n+'-underline',70,y+65,1135,'#777777',1);});
  const demo=async id=>a.demo(id,{x:70,y:270,w:1120,h:300,stage:1});
  page('overview','Turn around C, not around the origin',
    'Start with the known points P=(4,2) and C=(2,1). We want a quarter turn counterclockwise about C. The centre stays fixed and the distance CP stays fixed. Coordinates use rightward x and upward y with equal scales. The light circle is the set of possible positions at the same distance from C. First identify which point must remain fixed. About 30 seconds.');
  a.eq('givens',R`P=(4,2),\quad C=(2,1),\quad \theta=90^\circ\ \text{counterclockwise}`,70,130,1135,60,30);
  const X=x=>340+85*x,Y=y=>530-85*y;
  a.curve('x-axis',[[X(-1),Y(0)],[X(5),Y(0)]],'#9B9B9B',1.3);
  a.curve('y-axis',[[X(0),Y(-.6)],[X(0),Y(3.5)]],'#9B9B9B',1.3);
  a.text('x','x',X(5)+10,Y(0)-10,35,35,25);a.text('y','y',X(0)-12,Y(3.5)-40,35,35,25);
  for(let x=0;x<=4;x++)a.text('tick-x-'+x,String(x),X(x)-12,Y(0)+8,28,30,23,false,'center','#777777');
  for(let y=1;y<=3;y++)a.text('tick-y-'+y,String(y),X(0)-40,Y(y)-16,28,30,23,false,'right','#777777');
  a.shape('centre','ellipse',X(2)-5,Y(1)-5,10,10,'#202020');
  a.text('centre-label','C=(2,1)',X(2)+17,Y(1)+8,160,35,27,true);
  a.shape('point','ellipse',X(4)-6,Y(2)-6,12,12,'#202020');
  a.text('point-label','P=(4,2)',X(4)+15,Y(2)-20,180,35,27,true);
  a.curve('radius',[[X(2),Y(1)],[X(4),Y(2)]],'#202020',2.2);
  a.text('fixed-point','Keep C fixed.',900,330,290,42,29,true);
  a.reveal(1,()=>{
    const phi=Math.atan2(1,2),r=Math.sqrt(5);
    a.curve('quarter-arc',Array.from({length:49},(_,i)=>[X(2+r*Math.cos(phi+i*Math.PI/96)),Y(1+r*Math.sin(phi+i*Math.PI/96))]),'#777777',1.8);
    a.text('turn-label','90 degrees counterclockwise',760,245,440,40,27,true);
    a.text('radius-label','Keep the distance CP.',900,385,290,42,28);
  });
  a.text('goal','Find the new coordinates of the same point.',70,637,1135,44,32,true);

  page('process','Measure from C, turn, then put C back',
    'Moving the origin to C lets us turn around zero, where the coordinate directions are familiar. Q names the displacement from C to P. The scaffolding is fixed; each click fills the next actual object. Subtract C, rotate Q, then add C to get the world point P prime. We will now carry out these exact operations. About 35 seconds.');
  route(false,false);
  a.text('offset-meaning','Q is the arrow from C to P.',70,650,1135,42,30,true);
  await demo('process');
  a.reveal(2,()=>eq('subtract-build',R`Q=P-C=(2,1)`,574,28));
  a.reveal(3,()=>a.eq('rotation-build',R`Q'=(-1,2)`,480,574,330,62,28));
  a.reveal(4,()=>a.eq('add-build',R`P'=C+Q'=(1,3)`,854,574,354,62,28));

  page('subtract','1. Subtract the centre',
    'Compute the coordinate differences first. A click translates both P and C by (-2,-1); the original points remain as light outlines. C arrives at zero, and P arrives at Q=(2,1). This is the same offset, with length sqrt(5), now based at zero. A later click records the subtraction. This coordinate move prepares the rotation; it has not turned the point. About 35 seconds.');
  route(false,false);await demo('subtract');result('subtract-answer',R`Q=P-C=(4-2,\ 2-1)=(2,1)`);

  page('quarter-turn','2. Turn the offset 90 degrees counterclockwise',
    'The offset is 2 right and 1 up. Under a counterclockwise quarter turn, the rightward leg becomes 2 up, and the upward leg becomes 1 left. The first click turns the actual offset and both coordinate legs once, then holds. Read the endpoint (-1,2). The next click writes Q prime=(-v,u). A positive quarter turn swaps the coordinates and negates the new horizontal coordinate. About 45 seconds.');
  route();await demo('quarter');result('quarter-answer',R`(u,v)\mapsto(-v,u),\qquad (2,1)\mapsto Q'=(-1,2)`);

  page('add-back','3. Add the same centre back',
    'We have turned only the offset. The world point must be based at C=(2,1). A click moves the rotated arrow from zero back to the same C, keeping the arrow direction and length. It ends at P prime=(1,3). Then record (2,1)+(-1,2). Check CP and CP prime both have length sqrt(5), and the angle is counterclockwise 90 degrees. About 40 seconds.');
  route();await demo('add');result('example-answer',R`P'=C+Q'=(2,1)+(-1,2)=(1,3)`);

  page('need-rule','The same process, now with any angle',
    'The concrete example is complete. Now replace 90 degrees by a signed angle theta and use P=(x,y), C=(a,b). The outer operations already work: subtract the centre and add it back. Only the middle operation needs a rule for the rotated coordinates U,V. Its selected outline marks the object we now inspect. The next two pages answer this precise missing question. About 30 seconds.');
  route(true);
  a.shape('selected-rotation','rect',457,128,364,61,'none','#202020',2.6);
  a.text('need-question','For any angle, how do the two legs of Q determine Q\u0027?',70,245,1135,42,29,true);
  await a.demo('focus',{x:70,y:300,w:1120,h:260,stage:1});
  eq('known-outer',R`Q=(u,v)=(x-a,y-b),\qquad Q'=(U,V)`,602,30);
  a.text('prior-result','90-degree check retained: Q\u0027=(-v,u), giving P\u0027=(1,3).',70,675,1135,32,25,false,'left','#777777');

  page('horizontal','Inside the rotation: follow the horizontal leg',
    'We are inspecting the selected middle operation, not changing the process. Split Q=(u,v) into a horizontal arrow (u,0) followed by a vertical arrow (0,v). The endpoint is still Q. Turn the first arrow by theta. By the coordinate definition of cosine and sine its projections are u cos(theta) and u sin(theta). The illustration uses u=2,v=1,theta=35 degrees to keep the legs visible; the formula is general. The next page turns the remaining leg and joins it back. About 55 seconds.');
  a.text('focus-context','Q=(u,v) from subtracting C  ->  Rotate about zero  ->  Q\u0027',70,129,1135,42,27,true);
  eq('split',R`Q=(u,0)+(0,v)`,191,31);
  await a.demo('horizontal',{x:70,y:300,w:1120,h:260,stage:1});
  result('horizontal-answer',R`(u,0)\mapsto H=(u\cos\theta,\ u\sin\theta)`);

  page('vertical','Inside the rotation: turn the other leg and join',
    'The vertical unit direction is a counterclockwise quarter turn from the horizontal unit direction. After turning by theta the two remain perpendicular. Apply the already justified quarter-turn rule to (cos(theta),sin(theta)): it becomes (-sin(theta),cos(theta)). Multiply by signed v for the second leg. A rigid rotation preserves head-to-tail joins, so translate the turned vertical leg to the end of H and add its coordinates. The animation shows this turn and joining operation once. Negative u or v reverses the relevant leg; signed sine and cosine cover all quadrants. Zero legs simply vanish. About 65 seconds.');
  a.text('focus-context','Same Q=(u,v): retain H and turn the remaining vertical leg.',70,129,1135,42,27,true);
  eq('retained-horizontal',R`H=(u\cos\theta,\ u\sin\theta)`,188,28);
  a.eq('perpendicular-reason',R`(\cos\theta,\sin\theta)\xrightarrow{\,90^\circ\ \text{CCW}\,}(-\sin\theta,\cos\theta)`,70,244,1135,46,27);
  await a.demo('vertical',{x:70,y:300,w:1120,h:260,stage:1});
  a.reveal(2,()=>eq('vertical-leg',R`(0,v)\mapsto K=(-v\sin\theta,\ v\cos\theta)`,571,28));
  result('rotation-answer',R`Q'=H+K=(u\cos\theta-v\sin\theta,\ u\sin\theta+v\cos\theta)`,3,640);

  page('return-rule','Return: put the result into the same middle operation',
    'We return to the exact subtract-rotate-add layout from the question page. The centre and input keep their identities. The derived rule now fills the previously unresolved rotation operation, with its signed counterclockwise condition. Add the same centre to its two output coordinates. This establishes the general world-coordinate answer. The example at 90 degrees remains available as a check. Next we use this rule at a different angle, not begin another topic. About 45 seconds.');
  route(true);
  a.shape('selected-rotation','rect',457,128,364,61,'none','#202020',2.6);
  a.eq('returned-rule',R`U=u\cos\theta-v\sin\theta,\qquad V=u\sin\theta+v\cos\theta`,70,245,1135,48,29);
  await a.demo('return',{x:70,y:300,w:1120,h:260,stage:1});
  a.reveal(2,()=>a.eq('general-x',R`x'=a+(x-a)\cos\theta-(y-b)\sin\theta`,70,566,1135,52,30));
  a.reveal(3,()=>a.eq('general-y',R`y'=b+(x-a)\sin\theta+(y-b)\cos\theta`,70,622,1135,52,30));
  a.text('retained-example','Negative u or v: reverse the leg. Zero: omit it. Positive theta: CCW.',70,681,1135,30,24,false,'left','#777777');

  page('use-rule','Use it: the same P and C, now 30 degrees',
    'The angle changes visibly from 90 to 30 degrees; P,C and their offset (2,1) stay fixed. Retain the returned rule while substituting cos(30)=sqrt(3)/2 and sin(30)=1/2. First compute U=sqrt(3)-1/2 and V=1+sqrt(3)/2. The next click animates this actual 30-degree rotation about C once; it holds at the new point. The last click adds C, yielding (3/2+sqrt(3),2+sqrt(3)/2), approximately (3.232,2.866). About 55 seconds.');
  a.eq('changed-angle',R`P=(4,2),\ C=(2,1),\ (u,v)=(2,1),\quad \theta:\ 90^\circ\to30^\circ`,70,126,1135,56,29);
  a.eq('used-rule',R`U=u\cos\theta-v\sin\theta,\quad V=u\sin\theta+v\cos\theta`,70,196,1135,49,29);
  a.reveal(1,()=>eq('substitution',R`U=2\cdot\frac{\sqrt3}{2}-\frac12=\sqrt3-\frac12,\qquad V=2\cdot\frac12+\frac{\sqrt3}{2}=1+\frac{\sqrt3}{2}`,252,29));
  await a.demo('thirty',{x:70,y:335,w:1120,h:250,stage:2});
  result('thirty-answer',R`P'=\left(\frac32+\sqrt3,\ 2+\frac{\sqrt3}{2}\right)\approx(3.232,\ 2.866)`,3,620);

  page('takeaway','Subtract the centre. Turn the offset. Add it back.',
    'Keep one process: P to P-C to the rotated offset to C plus that offset. State the conditions: Cartesian coordinates with equal axis scale; positive angle counterclockwise, negative clockwise. The coordinate rule follows from the two rotated legs, not a matrix. At zero angle the point returns to itself, and a point equal to C remains C for every angle. Distance to C is preserved. For the given 90-degree example the answer is (1,3). This is the completed lesson. About 35 seconds.');
  route(true);
  eq('takeaway-rotation',R`(U,V)=(u\cos\theta-v\sin\theta,\ u\sin\theta+v\cos\theta)`,285,32);
  eq('takeaway-output',R`P'=(a+U,\ b+V),\qquad (u,v)=(x-a,y-b)`,390,35);
  a.text('conditions','Equal axis scales. Positive theta: counterclockwise; negative: clockwise.',70,491,1135,40,27);
  a.text('checks','Checks: C stays fixed; distance to C stays fixed; zero turn gives P.',70,550,1135,40,28);
  result('final-example',R`P=(4,2),\quad C=(2,1),\quad \theta=90^\circ\quad\Longrightarrow\quad P'=(1,3)`,1,625);
}
