/* Decorative theater only: no API, orders, role changes or telemetry writes. */
(() => {
 const root=document.querySelector('.cultivation-floor'); if(!root)return;
 const section=document.createElement('section');
 section.innerHTML='<div class="cult-toolbar"><strong>DIỄN VÕ ĐƯỜNG · MINH HỌA</strong><button type="button">Xem chuỗi trao đổi</button></div><canvas width="960" height="480" style="width:100%;height:auto;border:1px solid #438575;border-radius:12px;margin-top:16px" aria-label="Cảnh minh họa trao đổi giữa sáu phòng ban"></canvas><p aria-live="polite" style="font-size:12px;color:#b7cadb">Chỉ minh họa, không phải hoạt động trading thật.</p>';
 root.querySelector('.cult-campus').before(section);
 const canvas=section.querySelector('canvas'),ctx=canvas.getContext('2d');if(!ctx)return;
 const names=['Vân Đài','Hộ Tâm Viện','Thiên Nhãn Đài','Diễn Toán Các','Chấp Lệnh Đường','Liên Minh Các'];
 const files=['01_pm','02_risk','03_scout','04_quant','05_execution','06_community'];
 const homes=[[160,140],[480,140],[800,140],[160,365],[480,365],[800,365]];
 const images=files.map(f=>{const img=new Image();img.src='/static/images/sprites/sprite_'+f+'.png';return img;});
 const phases=[[2,3,'Thiên nhãn quan sát'],[3,1,'Diễn toán trận'],[1,0,'Hộ tâm kết giới'],[0,4,'Trao đổi quy trình'],[4,5,'Lưu trữ ấn'],[5,0,'Tổng kết hội đồng']];
 const reduced=matchMedia('(prefers-reduced-motion: reduce)'); let run=false,time=0,last=0,frame=0,previous=-1;
 const caption=section.querySelector('p');
 section.querySelector('button').onclick=()=>{if(reduced.matches){caption.textContent='Giảm chuyển động: Quan sát → phân tích → xét duyệt → trao đổi → lưu trữ. Chỉ minh họa.';return;}run=true;time=0;previous=-1;};
 function draw(now){
  const paused=document.hidden||reduced.matches||root.classList.contains('cult-paused'); if(run&&!paused)time+=last?Math.min(now-last,80):0;last=now;
  if(time>=36000){run=false;time=0;caption.textContent='Kết thúc cảnh minh họa. Không có lệnh nào được gửi.';}
  ctx.fillStyle='#102331';ctx.fillRect(0,0,960,480);ctx.strokeStyle='#264552';ctx.lineWidth=1; for(let x=0;x<960;x+=32){ctx.beginPath();ctx.moveTo(x,0);ctx.lineTo(x,480);ctx.stroke();} for(let y=0;y<480;y+=32){ctx.beginPath();ctx.moveTo(0,y);ctx.lineTo(960,y);ctx.stroke();}
  ctx.fillStyle='#31534f';ctx.fillRect(0,210,960,60);ctx.textAlign='center';ctx.font='12px sans-serif';ctx.fillStyle='#c5e4d5';ctx.fillText('THIÊN CƠ CÁC / HÀNH LANG TRAO ĐỔI',480,244);
  const positions=homes.map(([x,y],i)=>{ctx.fillStyle='#172e40';ctx.fillRect(x-125,y-112,250,165);ctx.strokeStyle='#568578';ctx.strokeRect(x-125,y-112,250,165);ctx.font='16px sans-serif';ctx.fillStyle='#e6efde';ctx.fillText(names[i],x,y-85);ctx.fillStyle='#b38c66';ctx.fillRect(x-85,y-23,100,22);ctx.fillStyle='#6acfc0';ctx.fillRect(x-60,y-52,36,24);return [x+40,y+12];});
  const index=Math.floor(time/6000),p=time%6000/6000,[from,to,label]=phases[index];
  if(run){if(previous!==index){caption.textContent=`MINH HỌA ${index+1}/6 · ${label} · Không phải sự kiện live`;previous=index;} const start=positions[from],end=positions[to],path=[start,[start[0],300],[end[0],300],end];const t=p<.42?p/.42:p>.74?(1-p)/.26:1,seg=Math.min(2,Math.floor(t*3)),b=t>=1?1:t*3-seg;positions[from]=[path[seg][0]+(path[seg+1][0]-path[seg][0])*b,path[seg][1]+(path[seg+1][1]-path[seg][1])*b];
   if(p>.42&&p<.74){const [x,y]=end,a=time/300;ctx.strokeStyle=index===2?'#c4b5fd':'#6ee7b7';ctx.lineWidth=3;ctx.beginPath();ctx.ellipse(x,y-30,48,28,a/8,0,Math.PI*2);ctx.stroke();for(let k=0;k<8;k++){ctx.fillStyle='#fde68a';ctx.fillRect(x+Math.cos(a+k*Math.PI/4)*50-3,y-30+Math.sin(a+k*Math.PI/4)*32-3,6,6);}ctx.fillStyle='#ecfdf5';ctx.fillRect(x-12,y-48,24,30);ctx.fillStyle='#315b68';ctx.fillRect(x-7,y-40,14,3);ctx.fillRect(x-7,y-33,14,3);ctx.fillStyle='#fff';ctx.font='12px sans-serif';ctx.fillText(label,x,y-75);}
  }
  positions.forEach(([x,y],i)=>{const bob=run&&i===from&&(p<.42||p>.74)?Math.sin(time/75)*3:0;ctx.fillStyle='#0006';ctx.beginPath();ctx.ellipse(x,y+12,22,7,0,0,Math.PI*2);ctx.fill();if(images[i].complete&&images[i].naturalWidth){ctx.imageSmoothingEnabled=false;ctx.drawImage(images[i],x-25,y-53+bob,50,65);}}); frame=requestAnimationFrame(draw);
 }
 frame=requestAnimationFrame(draw); window.addEventListener('pagehide',()=>cancelAnimationFrame(frame),{once:true});
})();
