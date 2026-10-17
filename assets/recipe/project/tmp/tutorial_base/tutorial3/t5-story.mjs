const R=String.raw;
const source='Fall2026/Note7_PAM.pdf';
const md=R`m_\delta(t)`;
const sample=R`\sum_{n=-\infty}^{\infty}m(nT_s)\delta(t-nT_s)`;
const replicas=R`\frac1{T_s}\sum_{k=-\infty}^{\infty}M(f-kf_s)`;
const interpolation=R`g(t)=\sum_{n=-\infty}^{\infty}m(nT_s)\operatorname{sinc}\!\left(\frac{t-nT_s}{T_s}\right)`;

export async function content(a){
 a.navigationAliases={
  'lesson-map':'recap','band-map':'sampling-spectrum','recover-map':'read-samples',
  'pm-offset':'review',fm:'review',normalize:'lpf'
 };
 const note=(pages,detail)=>`${detail} Source: ${source}, pp. ${pages}.`;
 const pg=(id,title,sub,focus,pp,detail,opts={})=>a.page(id,title,sub,focus,note(pp,detail),{purpose:detail,...opts});
 const main=(name,tex,y=237,size=29)=>a.statement(name,tex,64,y,1144,54,size);
 const result=(name,tex,k,y=640,size=31)=>a.reveal(k,()=>{
  a.statement(name,tex,64,y,1144,45,size);
  a.line(name+'-emphasis',64,y+48,1144,'#777777',1.2);
 });
 const prompt=(name,label,x,y,k,w=240)=>a.reveal(k,()=>{
  a.text(name+'-label',label,x-10,y-43,w,33,25,true);
  a.arrow(name+'-pointer',x,y,Math.min(75,w-20));
 });
 const chain=(rows,y=511,step=56,size=27,last={})=>rows.forEach((tex,i)=>a.reveal(i+1,()=>{
  const final=i===rows.length-1,x=final&&last.x!==undefined?last.x:64+(i?35:0);
  a.statement('derivation-'+i,tex,x,y+i*step,1208-x,final&&last.h?last.h:i===0?64:54,final?(last.size??size+4):size);
 }));

 pg('cover','ELEG2310B','',null,'1','Tutorial 5: Pulse Modulation. Teaching Assistants: WANG, Runbang; TIAN, Feng. runbang@link.cuhk.edu.hk.',{bare:true});
 pg('system','Communication system','',null,'2','Recall the same message, transmitted signal, received signal and recovered message from Tutorials 3 and 4.',{bare:true});
 pg('ideal','Communication system','',null,'2','Use the established ideal channel r=s while generating and reconstructing the pulse signal.',{bare:true});
 pg('course','Modulation','',null,'2','Sinusoidal modulation and pulse modulation are branches of the same message-to-signal picture. The pulse-height branch uses h(t), following Note 7. AM, PM and FM provide the comparison with a sinusoidal carrier.',{bare:true});
 a.eq('course-pulse',R`s(t)=\sum_n m(nT_s)h(t-nT_s)`,64,400,1080,60,35);

 pg('overview','Pulse modulation','PAM', 'tx','2-4','The pulse replaces the sinusoid as the signal shape. Compare the response to one changing sample: height for PAM, width for PDM, and time position for PPM. Only PAM is developed here.');
 a.text('operation','One sample: change height, width, or position',64,218,1140,41,29,true);
 await a.demo('pulse-types',{y:281,h:250});
 a.reveal(2,()=>{
  a.text('choose-pam','PAM: the sample value sets the pulse height.',64,584,1140,43,32,true);
  a.line('choose-pam-underline',64,635,1140,'#777777',1.2);
 });

 pg('pam-form','PAM','Modulation','tx','5-6','Take a value every Ts seconds. Represent the sample as a weighted ideal impulse, then replace each impulse by the unit-height pulse h(t). The signal s(t) remains continuous-time. All three plots use the same sample values, including their signs. T<Ts makes the pulses distinct.');
 main('sampled-message',R`m_\delta(t)=`+sample,229,29);
 await a.demo('pam-formation',{y:300,h:250});
 a.reveal(2,()=>a.statement('pulse-definition',R`h(t)=1\ (0<t<T),\quad0\ \text{otherwise};\qquad T<T_s`,64,570,1144,50,28));
 result('pam-generation',R`s(t)=\sum_{n=-\infty}^{\infty}m(nT_s)h(t-nT_s)`,3,643,32);

 pg('pam-derivation','PAM','Modulation','tx','10','Derive the same pulse signal from the convolution m_delta*h. Substitute the complete impulse sum into the convolution, exchange the sum and integral, and use the delta sifting property. Only the pulse at each sample time survives. This establishes the preceding visual construction without a new signal model.');
 main('known-samples',R`m_\delta(t)=`+sample,224,28);
 a.statement('known-pulse',R`h(t)=1\ (0<t<T),\quad 0\ \text{otherwise}`,64,281,1144,43,27);
 a.block('convolution','Convolve with h(t)',484,353,310,61);
 a.eq('input-samples',md,170,356,260,56,32,'center');a.arrow('input-to-h',402,383,70);
 a.eq('output-pam','s(t)',876,356,190,56,32,'center');a.arrow('h-to-output',804,383,70);
 chain([
  R`s(t)=(m_\delta*h)(t)=\int_{-\infty}^{\infty}m_\delta(\tau)h(t-\tau)\,d\tau`,
  R`=\int_{-\infty}^{\infty}\left[\sum_n m(nT_s)\delta(\tau-nT_s)\right]h(t-\tau)\,d\tau`,
  R`=\sum_n m(nT_s)\int_{-\infty}^{\infty}\delta(\tau-nT_s)h(t-\tau)\,d\tau`,
  R`=\sum_n m(nT_s)h(t-nT_s)`
 ],452,56,27);
 a.flyTerm('derivation-1',R`m(nT_s)`,'derivation-2');
 a.reveal(4,()=>a.line('result-emphasis',99,671,1109,'#777777',1.2));

 pg('sampling-coefficients','PAM','Sampling','tx','6-7','The periodic impulse train has a Fourier series. On the centered period only the impulse at zero contributes to the coefficient integral. Thus every Fourier-series coefficient is 1/Ts. The complex exponentials are used solely to locate frequency copies of the same sampled signal.');
 a.text('series-purpose','Locate the frequency copies of the samples.',64,213,1144,37,29,true);
 main('impulse-train',R`\delta_{T_s}(t)=\sum_n\delta(t-nT_s),\qquad m_\delta(t)=m(t)\delta_{T_s}(t)`,261,28);
 a.reveal(1,()=>a.statement('periodic-series',R`\delta_{T_s}(t)=\sum_k a_ke^{j2\pi kt/T_s}`,64,319,1144,47,30));
 a.reveal(2,()=>a.statement('coefficient-definition',R`a_k=\frac1{T_s}\int_{-T_s/2}^{T_s/2}\delta_{T_s}(t)e^{-j2\pi kt/T_s}\,dt`,99,384,1109,54,28));
 a.reveal(3,()=>a.statement('coefficient-one-impulse',R`=\frac1{T_s}\int_{-T_s/2}^{T_s/2}\delta(t)e^{-j2\pi kt/T_s}\,dt`,99,452,1109,54,28));
 a.reveal(4,()=>a.statement('sifting-coefficient',R`=\frac1{T_s}e^{-j2\pi k\cdot0/T_s}=\frac1{T_s}\qquad(\text{every integer }k)`,99,520,1109,47,29));
 result('train-series',R`\delta_{T_s}(t)=\frac1{T_s}\sum_k e^{j2\pi kf_st},\qquad f_s=\frac1{T_s}`,5,621,32);

 pg('sampling-spectrum','PAM','Sampling','tx','7-9','Multiply the established impulse-train Fourier series by m(t), then take its Fourier transform term by term. Each modulation by exp(j2pi*k*fs*t) shifts M to k*fs. The animation copies the same spectrum to those centers. Spectral heights in the illustration are normalized by the common factor 1/Ts.');
 main('sample-product',R`m_\delta(t)=m(t)\delta_{T_s}(t)=\frac1{T_s}\sum_k m(t)e^{j2\pi kf_st}`,223,28);
 a.reveal(1,()=>a.statement('transform-definition',R`M_\delta(f)=\frac1{T_s}\sum_k\mathcal F\!\left\{m(t)e^{j2\pi kf_st}\right\}`,99,283,1109,47,28));
 a.reveal(2,()=>a.statement('replicas-result',R`=\frac1{T_s}\sum_k M(f-kf_s)`,99,342,1109,45,31));
 a.flyTerm('transform-definition',R`m(t)e^{j2\pi kf_st}`,'replicas-result',R`M(f-kf_s)`);
 a.text('spectrum-example','One shifted copy per k; triangular M(f) illustration.',64,386,1144,32,25,false);
 await a.demo('sampling-replicas',{y:425,h:235,stage:3});
 a.reveal(4,()=>a.text('spectral-takeaway','Sampling creates copies spaced by fs.',64,666,1144,35,29,true));

 pg('sampling-condition','PAM','Sampling','tx','8','Keep the same strictly bandlimited message while changing fs. Each copy has edges k*fs-W and k*fs+W. Adjacent supports do not overlap when W<=fs-W, yielding fs>=2W as in Note 7. Equality requires the usual treatment of spectral endpoints; the illustrated safely separated case uses fs>2W. Arbitrary tones at the Nyquist boundary need additional qualifications.');
 main('bandlimited-assumption',R`\text{Assume: } M(f)=0\quad(|f|>W)`,224,30);
 await a.demo('sampling-rate',{y:286,h:250});
 await a.demo('sampling-rate-up',{y:286,h:250,stage:2,continuation:true});
 a.reveal(3,()=>a.statement('neighbor-edges',R`\text{One copy ends at }W;\quad\text{the next starts at }f_s-W`,64,543,1144,41,27));
 a.reveal(4,()=>a.statement('nyquist-endpoint',R`\text{At }f_s=2W:\quad\text{no tones at the boundary }\pm W`,64,587,1144,36,25));
 result('nyquist-result',R`W\le f_s-W\quad\Longrightarrow\quad f_s\ge2W`,4,637,33);

 pg('pulse-transform','PAM','Pulse shape','band','11','Transform the same causal rectangular pulse used to form s. Integrate exp(-j2pi*f*t) over 0<t<T, factor out exp(-j*pi*f*T), and use the sine identity. sinc(x)=sin(pi*x)/(pi*x). Keep the phase factor; the plot displays magnitude only, normalized by T. H(0)=T by continuity.');
 a.statement('known-unit-pulse',R`h(t)=1\ (0<t<T),\quad 0\ \text{otherwise}`,64,224,1144,43,28);
 await a.demo('pulse-response',{y:282,h:235,stage:4});
 chain([
  R`H(f)=\int_0^T e^{-j2\pi ft}\,dt=\left[\frac{e^{-j2\pi ft}}{-j2\pi f}\right]_0^T=\frac{1-e^{-j2\pi fT}}{j2\pi f}`,
  R`=e^{-j\pi fT}\frac{e^{j\pi fT}-e^{-j\pi fT}}{j2\pi f}=e^{-j\pi fT}\frac{\sin(\pi fT)}{\pi f}`,
  R`=T e^{-j\pi fT}\operatorname{sinc}(fT)`
 ],520,61,26);
 a.reveal(3,()=>a.line('pulse-result-emphasis',99,687,1109,'#777777',1.2));

 pg('pam-spectrum','PAM','Bandwidth','band','12-14','Use s=m_delta*h, so S=M_delta H. The magnitude of each repeated spectrum is shaped by the magnitude of the same rectangular-pulse response. The figure uses fs=3W and T=1/(4W), and normalizes the common gains. The pulse spectrum has nonzero tails. Note 7 uses BT=1/T as the first-positive-null bandwidth convention; it is not strict spectral support, nor the full two-sided first-null span. With T<Ts and fs>=2W, this measure is at least 2W.');
 main('pam-transform',R`s(t)=m_\delta(t)*h(t)\quad\Longrightarrow\quad S(f)=M_\delta(f)H(f)`,226,29);
 await a.demo('pam-spectrum',{y:294,h:250});
 a.reveal(2,()=>a.statement('full-pam-spectrum',R`S(f)=\left[\frac1{T_s}\sum_k M(f-kf_s)\right]T e^{-j\pi fT}\operatorname{sinc}(fT)`,64,552,1144,50,28));
 a.reveal(3,()=>{
  a.text('bandwidth-convention','Pulse response H: first positive zero at 1/T.',64,608,1144,38,27,true);
  a.statement('pam-bandwidth',R`B_T=\frac1T\ \ge\ \frac1{T_s}=f_s\ \ge\ 2W`,64,651,1144,43,32);
 });

 pg('read-samples','PAM','Demodulation','rx','14','Start with the transmitted flat-top pulses s(t), not an already-known message. Read each isolated pulse inside its flat region, for example at nTs+T/2. Its height equals m(nTs). Use these values to form the ideal sampled signal m_delta, to which the lecture reconstruction filter applies. Directly lowpass-filtering s would retain the pulse response H and is not the reconstruction route taught here.');
 main('receiver-input',R`s(t)=\sum_n m(nT_s)h(t-nT_s),\qquad T<T_s`,223,29);
 await a.demo('read-samples',{y:297,h:250});
 a.reveal(2,()=>a.statement('height-value',R`s(nT_s+T/2)=m(nT_s)`,64,564,1144,44,31));
 result('recreated-samples',R`m_\delta(t)=`+sample,3,634,30);

 pg('lpf','PAM','Reconstruction','rx','15','Under the same bandwidth and sampling assumptions, the ideal unity-gain lowpass with cutoff fs/2 passes only the central copy. Its output is m/Ts, so the separate gain Ts restores m. The complete filter response including that gain would be Ts*H_LP. This is the receiver route from the preceding sampled pulse heights.');
 main('reconstruction-conditions',R`M(f)=0\ (|f|>W),\qquad f_s>2W\quad\text{(illustrated)}`,224,29);
 await a.demo('sampling-lpf',{y:291,h:250,stage:2});
 a.reveal(1,()=>a.statement('lpf-definition',R`H_{\mathrm{LP}}(f)=\begin{cases}1,&|f|<f_s/2\\0,&\text{otherwise}\end{cases}`,64,550,1144,81,28));
 result('reconstructed-spectrum',R`M_\delta(f)H_{\mathrm{LP}}(f)=\frac1{T_s}M(f)\quad\Longrightarrow\quad G(f)=T_s\frac1{T_s}M(f)=M(f)`,3,637,29);

 pg('reconstruction-kernel','PAM','Reconstruction','rx','15','Return to the same H_LP rectangle. Its inverse Fourier transform is h_LP(t). Evaluate the integral over -fs/2 to fs/2, combine the two exponentials using the sine identity, and identify fs*sinc(fs*t). The animation draws this impulse response and marks its zeros at integer nonzero multiples of Ts. Values at t=0 follow by continuity.');
 main('known-filter',R`H_{\mathrm{LP}}(f)=1\ (|f|<f_s/2),\quad0\ \text{otherwise}`,223,28);
 await a.demo('sinc-kernel',{y:285,h:235,stage:4});
 chain([
  R`h_{\mathrm{LP}}(t)=\int_{-f_s/2}^{f_s/2}e^{j2\pi ft}\,df=\left[\frac{e^{j2\pi ft}}{j2\pi t}\right]_{-f_s/2}^{f_s/2}`,
  R`=\frac{e^{j\pi f_st}-e^{-j\pi f_st}}{j2\pi t}=\frac{\sin(\pi f_st)}{\pi t}`,
  R`=f_s\operatorname{sinc}(f_st),\qquad f_sT_s=1`
 ],524,60,27);

 pg('interpolation-derivation','PAM','Reconstruction','rx','16','Derive interpolation from the already established reconstruction system. Substitute the ideal impulse sample sum, exchange sum and integral, sift the impulse, substitute h_LP=fs*sinc(fs*t), and cancel Ts*fs=1. Every operation is retained. The result is the same g=m from the preceding frequency-domain argument, not a new reconstruction method.');
 a.eq('known-input',md,104,232,220,54,33,'center');a.arrow('to-reconstruction',330,258,99);
 a.block('known-reconstruction','',440,229,354,61);
 a.eq('reconstruction-operation',R`T_s\times\mathrm{LPF}`,452,235,330,49,29,'center');a.arrow('to-output',807,258,97);
 a.eq('known-output','g(t)=m(t)',920,232,280,54,33,'center');
 const steps=[
  R`g(t)=T_s\int_{-\infty}^{\infty}h_{\mathrm{LP}}(\tau)m_\delta(t-\tau)\,d\tau`,
  R`=T_s\int_{-\infty}^{\infty}h_{\mathrm{LP}}(\tau)\left[\sum_n m(nT_s)\delta(t-\tau-nT_s)\right]d\tau`,
  R`=T_s\sum_n m(nT_s)\int_{-\infty}^{\infty}h_{\mathrm{LP}}(\tau)\delta(t-\tau-nT_s)\,d\tau`,
  R`=T_s\sum_n m(nT_s)h_{\mathrm{LP}}(t-nT_s)`,
  R`=T_s\sum_n m(nT_s)f_s\operatorname{sinc}\!\left[f_s(t-nT_s)\right]`,
  R`g(t)=\sum_n m(nT_s)\operatorname{sinc}\!\left(\frac{t-nT_s}{T_s}\right)`
 ];
 chain(steps,327,58,27,{x:64,h:70,size:35});
 a.flyTerm('derivation-1',R`m(nT_s)`,'derivation-2');
 a.reveal(6,()=>a.line('interpolation-emphasis',64,697,1144,'#777777',1.2));

 pg('interpolation','PAM','Reconstruction','rx','16-17','Animate the established interpolation sum: each sample scales and shifts one sinc, and their sum is the reconstructed message. For a finite, exact demonstration the example has five nonzero samples at n=-2,-1,0,1,2, with values 0.5,1,-0.5,0.8,-0.3; all other integer samples are zero. This defines a valid bandlimited example as the displayed finite sinc sum. The light curve is its full sum, the black curve the current partial sum. The general formula remains infinite. At each sample instant its own sinc equals one and every other sinc equals zero, so the value is preserved.');
 main('interpolation-result',interpolation,222,30);
 a.text('example-condition','Example: five nonzero samples',64,288,1144,37,27,true);
 await a.demo('interpolation',{y:345,h:250});
 result('sample-preservation',R`g(kT_s)=m(kT_s),\qquad k\ \text{integer}`,2,642,32);

 pg('tdm-send','TDM','Multiplexing','tx','18-19','Use the same pulse heights for multiple messages. The commutator takes one sample from each of three messages during each interval Ts, placing them in successive time slots. A message is still sampled every Ts; the common stream has three times as many pulses. In this sequential illustration the actual sampling times are t_(n,i)=nTs+(i-1)Ts/3, not simultaneous samples from all channels. Input messages are bandlimited with fs>=2W.');
 a.text('tdm-operation','Commutator: interleave three sample streams',64,222,1144,43,29,true);
 await a.demo('tdm-send',{y:294,h:250});
 a.reveal(2,()=>{
  a.statement('tdm-sample-times',R`t_{n,i}=nT_s+\frac{(i-1)T_s}{3},\qquad i=1,2,3`,64,557,790,47,29);
  a.statement('tdm-pulse-fit',R`T<T_s/3`,899,557,309,47,30);
 });
 result('tdm-rate',R`\text{Each message: }f_s=1/T_s\qquad\text{Shared stream: }3f_s`,3,636,30);

 pg('tdm-receive','TDM','Demultiplexing','rx','19','The decommutator uses the same slot assignment and timing clock to direct each pulse to the right message stream. Each stream then uses the same reconstruction filter, with its own known sample-time offset. The formula is the previous interpolation formula translated to the sample times t_(n,i). Timing synchronization is required; otherwise pulse heights can be assigned to the wrong channel. These ideal demonstrations omit transmission distortion and noise.');
 a.text('tdm-receiver-operation','Decommutator: separate the time slots',64,222,850,43,29,true);
 a.statement('tdm-receiver-pulse-fit',R`T<T_s/3`,955,222,253,43,28);
 await a.demo('tdm-receive',{y:294,h:250});
 a.reveal(2,()=>a.statement('tdm-reconstruction',R`m_i(t)=\sum_n m_i(t_{n,i})\operatorname{sinc}\!\left(\frac{t-t_{n,i}}{T_s}\right)`,64,558,1144,50,30));
 a.reveal(3,()=>{
  a.text('synchronism','Same clock and slot assignment; reconstruct each message.',64,640,1144,43,30,true);
  a.line('synchronism-emphasis',64,689,1144,'#777777',1.2);
 });

 pg('recap','PAM and TDM','Takeaways',null,'5-19','Return to the four outcomes of the same pulse-message path. Pulse height stores a sample; sampling creates copies which must remain separated; a reconstruction filter combines shifted sinc pulses to recover the message; TDM interleaves and separates several sample streams using synchronized slots. Conditions: strictly bandlimited messages, the sampling-theorem endpoint assumptions, isolated pulses with 0<T<Ts, and an ideal channel.');
 a.text('recap-assumption','Bandlimited messages; no boundary tones at equality.',64,215,1144,32,26,false);
 a.comparisonTable('takeaway-table',[
  ['Task','Operation','Result'],
  ['Generate PAM','Sample, then form pulses','Sample value = pulse height'],
  ['Avoid aliasing','Separate spectral copies',''],
  ['Recover m','Read heights, then reconstruct','Weighted sinc pulses add to m'],
  ['Share the channel','Interleave time slots','Synchronized TDM']
 ],64,253,1144,405,{fontSize:27,columnWidths:[246,419,479]});
 a.eq('recap-sampling-condition',R`f_s\ge2W`,729,433,479,45,32,'center');
 for(const [i,id] of ['pam-form','sampling-condition','interpolation','tdm-send'].entries()){
  const name='takeaway-link-'+i;a.shape(name,'rect',64,334+i*81,1144,81,'none');a.link(name,id);
 }

 pg('review','Modulation','Review',null,'2','Briefly locate PAM alongside the sinusoidal methods already studied. AM changes amplitude, PM adds message-dependent phase, FM puts the message into instantaneous frequency, and PAM puts samples into pulse heights. FDM shares frequency bands; TDM shares time slots. These are multiplexing choices and are not extra alternatives in the carrier-parameter list. Source for earlier methods: Fall2026/Notes 3-6.');
 a.comparisonTable('review-table',[
  ['Method','The message controls'],['AM','Sinusoid amplitude'],['PM','Added phase'],['FM','Instantaneous frequency'],['PAM','Pulse height']
 ],64,252,1144,340,{fontSize:29,columnWidths:[285,859]});
 a.reveal(1,()=>a.text('multiplexing-review','FDM: share frequency.     TDM: share time.',64,628,1144,47,32,true));
 a.link('review-table','course');

 pg('closing','Communication system','',null,'2','The user-approved closing picture previews the later course: the transmitter may include PCM, digital PAM and bandpass modulation; the channel r=h*s+n can introduce distortion/ISI and noise; matching receiver operations decode, detect or demodulate and reconstruct. These are topic locations, not three obligatory consecutive transmitter stages. PCM and digital modulation are not derived in this tutorial.',{bare:true});
 const yy=270;
 a.eq('future-m','m(t)',55,yy,130,64,38,'center');a.arrow('future-tx-arrow',190,yy+32,275);
 a.eq('future-s','s(t)',463,yy,130,64,38,'center');a.arrow('future-channel-arrow',597,yy+32,218);
 a.eq('future-r','r(t)',811,yy,130,64,38,'center');a.arrow('future-rx-arrow',943,yy+32,185);
 a.eq('future-output',R`\widehat m(t)`,1125,yy,135,64,38,'center');
 a.text('future-tx','TRANSMITTER',204,210,270,39,28,true,'center');
 a.text('future-channel','CHANNEL',591,210,230,39,28,true,'center');
 a.text('future-rx','RECEIVER',941,210,230,39,28,true,'center');
 a.reveal(1,()=>{
  a.text('future-tx-topics','PCM\nDigital PAM\nBandpass modulation',206,390,335,176,29,false);
  a.statement('future-channel-law',R`r=h*s+n`,589,390,290,48,29);
  a.text('future-channel-topics','h: distortion / ISI\nn: noise',589,452,335,111,28,false);
  a.text('future-rx-topics','Decode / reconstruct\nDetect symbols\nDemodulate',941,390,330,176,28,false);
 });

 pg('end','End of Tutorial 5','',null,'1','For the animated slides, contact runbang@link.cuhk.edu.hk.',{bare:true});
}
