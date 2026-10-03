document.querySelectorAll('.interactive').forEach(card=>{card.addEventListener('mousemove',e=>{const r=card.getBoundingClientRect();card.style.background=`radial-gradient(circle at ${e.clientX-r.left}px ${e.clientY-r.top}px, rgba(35,139,255,.10), transparent 38%), linear-gradient(145deg,rgba(13,28,47,.88),rgba(7,15,27,.92))`});card.addEventListener('mouseleave',()=>card.style.background='')});
setTimeout(()=>document.querySelectorAll('.flash').forEach(el=>{el.style.opacity='0';el.style.transform='translateY(-8px)'}),3500);

// Upload interactions
const dz=document.getElementById('dropZone'), input=document.getElementById('datasetInput'), fileName=document.getElementById('fileName');
if(dz&&input){['dragenter','dragover'].forEach(e=>dz.addEventListener(e,x=>{x.preventDefault();dz.classList.add('drag')}));['dragleave','drop'].forEach(e=>dz.addEventListener(e,x=>{x.preventDefault();dz.classList.remove('drag')}));dz.addEventListener('drop',e=>{if(e.dataTransfer.files.length){input.files=e.dataTransfer.files;if(fileName)fileName.textContent=e.dataTransfer.files[0].name}});input.addEventListener('change',()=>{if(input.files.length&&fileName)fileName.textContent=input.files[0].name})}
