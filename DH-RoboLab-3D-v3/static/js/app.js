/* Interface didática DH: JS visualiza, backend Python calcula. Juntas R/P configuráveis. */
(() => {
  'use strict';
  const $ = id => document.getElementById(id);
  const keys = ['theta','d','a','alpha'];
  const labels = () => [t('base'), t('jointN', {n:2}), t('jointN', {n:3})];
  const clone = value => JSON.parse(JSON.stringify(value));
  const fixed = v => Number(v).toFixed(3);
  let presets={}, rows=[], latest=null, trail=[], timer=null, signature='', requestId=0, lastExperiment=null;
  let lang = 'pt';
  try {lang = localStorage.getItem('dh-robolab-lang') === 'en' ? 'en' : 'pt';} catch (_) {}
  const t = (key, vars={}) => {
    const source = window.DH_I18N?.[lang] || {};
    return String(source[key] ?? window.DH_I18N?.pt?.[key] ?? key).replace(/\{(\w+)\}/g, (_, name) => String(vars[name] ?? ''));
  };
  function translateStatic(){
    document.documentElement.lang = lang === 'pt' ? 'pt-BR' : 'en';
    document.title = t('pageTitle');
    document.querySelectorAll('[data-i18n]').forEach(el=>{el.textContent=t(el.dataset.i18n);});
    for (const code of ['pt','en']) {
      const btn = $(code==='pt'?'langPt':'langEn');
      const active = code===lang;
      btn.classList.toggle('active',active);btn.setAttribute('aria-pressed',String(active));
    }
  }
  function changeLanguage(code){
    if (code !== 'pt' && code !== 'en') return;
    lang=code;
    try {localStorage.setItem('dh-robolab-lang',lang);} catch (_) {}
    translateStatic();
    if(rows.length && $('paramBody').children.length){
      rows.forEach((row,i)=>{
        const cell=$('paramBody').rows[i]?.cells[0];
        if(cell) cell.textContent=`${i+1}. ${labels()[i]}`;
        $(`p-${i}-type`).setAttribute('aria-label', t('jointN',{n:i+1}));
        keys.forEach(key=>$(`p-${i}-${key}`).setAttribute('aria-label',`${t('jointN',{n:i+1})}: ${key}`));
      });
      updateExperimentJoint(false);
    }
    if(latest) renderResults(latest);
    if(lastExperiment) renderExperiment(lastExperiment);
  }
  const MAX_TRAIL=250;

  function message(kind,text){$(kind==='error'?'success':'error').classList.add('hidden');$(kind).textContent=text;$(kind).classList.remove('hidden');}
  function clearMessage(){$('error').classList.add('hidden');$('success').classList.add('hidden');}
  async function api(url,payload){const r=await fetch(url,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});const j=await r.json();if(!r.ok)throw new Error(j.error || `HTTP ${r.status}`);return j;}
  function variable(item){return item.type==='P'?'d':'theta';}
  function unit(item){return item.type==='P'?'m':'°';}
  function readTable(){return rows.map((_,i)=>{
    const item={type:$(`p-${i}-type`).value};
    for(const key of keys){const raw=$(`p-${i}-${key}`).value;if(raw.trim()==='')throw new Error(t('missingField',{field:key,n:i+1}));item[key]=Number(raw);}
    return item;
  });}
  function updateExperimentJoint(resetRange=true){
    const index=Number($('expJoint').value)-1;
    const kind=$(`p-${index}-type`)?.value || rows[index]?.type || 'R';
    $('expStartLabel').textContent=t(kind==='R'?'initialTheta':'initialD');
    $('expEndLabel').textContent=t(kind==='R'?'finalTheta':'finalD');
    for(const id of ['expStart','expEnd']) {$(id).min=kind==='R'?'-360':'-5';$(id).max=kind==='R'?'360':'5';$(id).step=kind==='R'?'1':'0.05';}
    if(resetRange){$('expStart').value=kind==='R'?'-90':'0';$('expEnd').value=kind==='R'?'90':'1.2';}
  }
  function renderControls(){
    $('configurationTag').textContent=rows.map(r=>r.type).join('');
    $('paramBody').innerHTML=rows.map((r,i)=>{
      const v=variable(r);
      const selector=`<select id="p-${i}-type" aria-label="${t('jointN',{n:i+1})}"><option value="R" ${r.type==='R'?'selected':''}>R</option><option value="P" ${r.type==='P'?'selected':''}>P</option></select>`;
      return `<tr><td>${i+1}. ${labels()[i]}</td><td>${selector}</td>${keys.map(k=>`<td class="${k===v?'param-active':'param-fixed'}"><input id="p-${i}-${k}" type="number" step="${k==='theta'||k==='alpha'?1:.01}" value="${r[k]}" aria-label="${t('jointN',{n:i+1})}: ${k}"></td>`).join('')}</tr>`;
    }).join('');
    $('sliderRows').innerHTML=rows.map((r,i)=>{
      const v=variable(r), isP=r.type==='P';
      const label=`${i+1}. ${r.type} · ${isP?'d':'θ'}`;
      const val=r[v], min=isP?-1.5:-180,max=isP?1.5:180;
      const step=isP?.01:1;
      return `<div class="slider-row"><label for="s-${i}" class="${isP?'joint-p':'joint-r'}">${label}</label><input id="s-${i}" type="range" min="${min}" max="${max}" step="${step}" value="${Math.max(min,Math.min(max,val))}"><output id="s-out-${i}">${val}${unit(r)}</output></div>`;
    }).join('');
    rows.forEach((r,i)=>{
      $(`p-${i}-type`).addEventListener('change',()=>{
        try{rows=readTable();}catch(e){message('error',e.message);return;}
        signature='';renderControls();refresh();
      });
      keys.forEach(k=>$(`p-${i}-${k}`).addEventListener('input',()=>{
        if(k===variable(r)){
          const val=Number($(`p-${i}-${k}`).value);const slider=$(`s-${i}`);
          slider.value=Math.max(Number(slider.min),Math.min(Number(slider.max),val));
          $(`s-out-${i}`).textContent=Number.isFinite(val)?`${val}${unit(r)}`:'—';
        }
        schedule();
      }));
      $(`s-${i}`).addEventListener('input',e=>{
        $(`p-${i}-${variable(r)}`).value=e.target.value;
        $(`s-out-${i}`).textContent=`${e.target.value}${unit(r)}`;
        schedule();
      });
    });
    updateExperimentJoint(true);
  }
  function schedule(){clearTimeout(timer);timer=setTimeout(refresh,140);}
  async function refresh(){
    clearMessage();let configured;
    try{configured=readTable();}catch(e){message('error',e.message);return;}
    const requestedSignature=JSON.stringify(configured);
    if(requestedSignature===signature && latest)return;
    const localId=++requestId;
    try{
      const result=await api('/api/fk',{rows:configured});
      if(localId!==requestId || requestedSignature!==JSON.stringify(readTable()))return;
      rows=configured;latest=result;signature=requestedSignature;
      $('configurationTag').textContent=result.configuration;
      const p=result.end_effector;
      if(!trail.length || p.some((v,i)=>Math.abs(v-trail[trail.length-1][i])>1e-9)){
        trail.push([...p]);if(trail.length>MAX_TRAIL)trail.shift();
      }
      renderResults(result);
    }catch(e){if(localId===requestId)message('error',e.message);}
  }
  function matrixMarkup(m){return `<table class="matrix"><tbody>${m.map((r,i)=>`<tr>${r.map((v,j)=>`<td class="${j===3?'last-col':''} ${i===3?'last-row':''}">${Math.abs(v)<.00005?'0.000':Number(v).toFixed(3)}</td>`).join('')}</tr>`).join('')}</tbody></table>`;}
  function renderResults(data){
    const p=data.end_effector;
    $('px').textContent=fixed(p[0]);$('py').textContent=fixed(p[1]);$('pz').textContent=fixed(p[2]);
    $('mathStatus').textContent=`${data.configuration} · det(R) = ${data.rotation_determinant.toFixed(6)} · ${t('orthogonality')} = ${data.orthogonality_error.toExponential(1)}`;
    $('matrices').innerHTML=data.A_matrices.map((m,i)=>`<div class="matrix-card"><h3>A${i+1} · ${t('jointN',{n:i+1})} · ${data.params[i].type} (${t(data.params[i].type==='R'?'varyTheta':'varyD')})</h3>${matrixMarkup(m)}</div>`).join('');
    $('finalMatrix').innerHTML=matrixMarkup(data.T_final);
    draw3D(data);
  }
  function axisTrace(origin,R,col,length,showLegend){
    const target=[0,1,2].map(i=>origin[i]+length*R[i][col]);
    return {type:'scatter3d',mode:'lines',x:[origin[0],target[0]],y:[origin[1],target[1]],z:[origin[2],target[2]],line:{color:['#e45d62','#1caa82','#317de7'][col],width:4},showlegend:showLegend,hoverinfo:'skip'};
  }
  function lineTrace(a,b,color,width,name,dash='solid'){
    return {type:'scatter3d',mode:'lines',x:[a[0],b[0]],y:[a[1],b[1]],z:[a[2],b[2]],line:{color,width,dash},name,showlegend:false,hoverinfo:'skip'};
  }
  function draw3D(data){
    if(!window.Plotly){message('error',t('plotlyNotLoaded'));return;}
    const extent=Math.max(1.1,rows.reduce((acc,r)=>acc+Math.abs(r.a)+Math.abs(r.d),0)*1.08);
    const traces=[];
    for(const link of data.links){
      const color=link.type==='P'?'#08a18e':'#5b65ab';
      // Mostra Tz(d) ao longo de z_(i-1), seguido de Tx(a) no novo referencial.
      traces.push(lineTrace(link.start,link.after_d,color,link.type==='P'?13:8,t('jointShort',{n:link.joint,kind:link.type})));
      traces.push(lineTrace(link.after_d,link.end,'#8792a8',8,t('linkN',{n:link.joint})));
      traces.push({type:'scatter3d',mode:'markers',x:[link.start[0]],y:[link.start[1]],z:[link.start[2]],
        marker:{size:9,symbol:link.type==='R'?'circle':'square',color:link.type==='R'?'#6354cb':'#00a78d'},
        name:t('jointShort',{n:link.joint,kind:link.type}),hovertemplate:`${t('jointShort',{n:link.joint,kind:link.type})}<extra></extra>`,showlegend:false});
    }
    const ee=data.end_effector;
    traces.push({type:'scatter3d',mode:'markers',x:[ee[0]],y:[ee[1]],z:[ee[2]],marker:{size:11,color:'#e3a32e',line:{color:'#a4741a',width:2}},name:t('endEffector'),showlegend:false,
      hovertemplate:`${t('effHover')}<br>X %{x:.3f} m<br>Y %{y:.3f} m<br>Z %{z:.3f} m<extra></extra>`});
    if($('showTrail').checked && trail.length>1){traces.push({type:'scatter3d',mode:'lines',x:trail.map(v=>v[0]),y:trail.map(v=>v[1]),z:trail.map(v=>v[2]),line:{color:'#e6a42c',width:4,dash:'dash'},showlegend:false,hoverinfo:'skip'});}
    if($('showFrames').checked)data.frames.forEach((frame,i)=>{for(let j=0;j<3;j++)traces.push(axisTrace(frame.origin,frame.rotation,j,Math.max(.09,extent*.09),i===0));});
    const range=[-extent,extent];
    const axis=name=>({title:{text:name,font:{size:11,color:'#728098'}},range,zeroline:true,showbackground:true,backgroundcolor:'#f8fafc',gridcolor:'#e4e9f2',tickfont:{size:9,color:'#97a1b1'}});
    const layout={margin:{l:0,r:0,t:0,b:0},paper_bgcolor:'#fff',showlegend:false,uirevision:'preserve-camera',
      scene:{xaxis:axis('X (m)'),yaxis:axis('Y (m)'),zaxis:axis('Z (m)'),aspectmode:'cube',dragmode:'orbit',camera:{eye:{x:1.5,y:1.6,z:1.18}}}};
    window.Plotly.react('arm3d',traces,layout,{responsive:true,displaylogo:false});
  }
  function savePose(){if(!latest)return;const blob=new Blob([JSON.stringify({model:latest.configuration,convention:'classic-DH',time:new Date().toISOString(),data:latest},null,2)],{type:'application/json;charset=utf-8'});
    const a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download=`pose_dh_${latest.configuration.toLowerCase()}.json`;a.click();setTimeout(()=>URL.revokeObjectURL(a.href),2000);}
  async function runExperiment(){clearMessage();const btn=$('runExp');btn.disabled=true;btn.textContent=t('calculating');
    try{
      const body={rows:readTable(),joint:Number($('expJoint').value),start:Number($('expStart').value),end:Number($('expEnd').value),samples:Number($('expSamples').value),lang};
      const res=await api('/api/experiments',body);
      lastExperiment=res;
      renderExperiment(res);
      $('results').classList.remove('hidden');$('results').scrollIntoView({behavior:'smooth',block:'nearest'});
      message('success',t('experimentSuccess'));
    }catch(e){message('error',e.message);}finally{btn.disabled=false;btn.textContent=t('generate');}
  }
  function renderExperiment(res){
    $('resultSummary').textContent=t('experimentSummary',{config:res.configuration,joint:res.joint,kind:res.joint_type,parameter:res.varied_parameter,unit:res.parameter_unit==='graus'?t('deg'):res.parameter_unit,samples:res.samples,distance:res.travel_distance_m.toFixed(3)});
    $('downloadZip').href=res.download_url;
    const captions=['chartCoordinate','chartTrajectory','chartDistance','chartIncrement'].map(k=>t(k));
    $('figureGrid').innerHTML=res.figure_urls.map((url,i)=>`<figure class="figure"><a href="${url}" target="_blank" rel="noopener"><img src="${url}" alt="${captions[i]}" loading="lazy"></a><figcaption>${captions[i]}</figcaption></figure>`).join('');
  }
  function loadPreset(key){rows=clone(presets[key]||presets.rrr);trail=[];signature='';lastExperiment=null;renderControls();refresh();$('results').classList.add('hidden');}
  async function setup(){
    try{const r=await fetch('/api/defaults');if(!r.ok)throw new Error(t('errorBackend'));const data=await r.json();presets=data.presets;loadPreset('rrr');}
    catch(e){message('error',t('startupError',{message:e.message}));}
    $('langPt').addEventListener('click',()=>changeLanguage('pt'));
    $('langEn').addEventListener('click',()=>changeLanguage('en'));
    $('preset').addEventListener('change',e=>loadPreset(e.target.value));
    $('reset').addEventListener('click',()=>{$('preset').value='rrr';loadPreset('rrr');});
    $('expJoint').addEventListener('change',()=>updateExperimentJoint(true));
    $('saveCsv').addEventListener('click',savePose);
    $('clearTrail').addEventListener('click',()=>{trail=[];if(latest){trail.push([...latest.end_effector]);draw3D(latest);}});
    $('showFrames').addEventListener('change',()=>latest&&draw3D(latest));
    $('showTrail').addEventListener('change',()=>latest&&draw3D(latest));
    $('resetCamera').addEventListener('click',()=>window.Plotly&&latest&&window.Plotly.relayout('arm3d',{'scene.camera':{eye:{x:1.5,y:1.6,z:1.18},up:{x:0,y:0,z:1}}}));
    $('runExp').addEventListener('click',runExperiment);
  }
  translateStatic();
  setup();
})();
