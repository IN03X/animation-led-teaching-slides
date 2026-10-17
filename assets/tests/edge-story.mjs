export async function content(a){
 a.navigationAliases={'overview':'cover','lesson-map':'cover'};
 a.page('cover','Engine regression','Known input',null,'Regression fixture, not a teaching template.',{bare:true,purpose:'Test authored cover click states and a single relocation.'});
 a.text('input','Known value: x = 2',64,180,900,50,30,true);
 a.shape('moving-point','ellipse',100,280,30,30,'#202020');
 a.reveal(1,()=>a.statement('rule','y=x+1',64,380,1100,60,32));
 a.relocate('moving-point',2,100,0,0);
 a.page('end','Engine regression','Result',null,'The same rule gives y=3.',{bare:true,purpose:'Test authored end page click states without a course alias.'});
 a.statement('known-rule','y=x+1',64,220,1100,60,32);
 a.reveal(1,()=>a.statement('result','y=2+1=3',64,360,1100,60,35));
}
