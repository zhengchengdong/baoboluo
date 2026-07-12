import re

with open('d:/baoboluo/pineapple_CircularBand.html', 'r', encoding='utf-8') as f:
    content = f.read()

# ═══════ STRIP square band rendering, KEEP PBD + prepare for circular ═══════

# Remove square band constants
content = re.sub(r'// ══════\.\?Band System ══════\.\?\r?\nconst MAX_BANDS=256;\r?\nconst bands=\[\];\r?\nconst bandVisuals=\[\];.*?let RIBBON_WIDTH_SEGMENTS = 4;.*?\r?\n\r?\n', '', content, flags=re.DOTALL)

# Remove ribbon visual slider functions
content = re.sub(r'// Ribbon visual sliders\r?\nfunction updateAllRibbonMaterials\(\).*?function rebuildAllRibbonVisuals\(\).*?\}\r?\n', '', content, flags=re.DOTALL)

# Remove ribbon render slider wiring
content = re.sub(r"\$\('sl_rw'\).*?markPbdDirty\(\);.*?\};.*?\$\('sl_rt'\).*?\};.*?\$\('sl_rr'\).*?\};.*?\$\('sl_an'\).*?\};.*?\$\('sl_rso'\).*?\};\r?\n\r?\n", '', content, flags=re.DOTALL)

# Remove target line toggle
content = re.sub(r'// Target line toggle\r?\nlet showTargetLine.*?\};\r?\n\r?\n', '', content, flags=re.DOTALL)

# Remove makeBandLine, updateBandLine
content = re.sub(r'// ── Legacy line helpers.*?function updateBandLine\(line,points3D\).*?\n\}\r?\n\r?\n', '', content, flags=re.DOTALL)

# Remove computeSmoothNormals
content = re.sub(r'// Compute smooth vertex normals.*?function computeSmoothNormals\(posArr,idxArr,vc\).*?\n\}\r?\n\r?\n', '', content, flags=re.DOTALL)

# Remove createBandRibbonMesh, updateBandRibbonMesh, updateBandRibbonMesh_offsets
content = re.sub(r'function createBandRibbonMesh\(bandIndex\).*?\n  return mesh;\r?\n\}\r?\n\r?\n', '', content, flags=re.DOTALL)
content = re.sub(r'function updateBandRibbonMesh\(mesh, band, bandIndex\).*?\n\}\r?\n\r?\n// Variant with pre-computed.*?\nfunction updateBandRibbonMesh_offsets.*?\n\}\r?\n', '', content, flags=re.DOTALL)

# Remove getExactCrossSectionPolyline
content = re.sub(r'function getExactCrossSectionPolyline\(posArr,idxArr,origin,normal\).*?\n\}\r?\n\r?\n', '', content, flags=re.DOTALL)

# Remove smoothstep
content = re.sub(r'function smoothstep\(e0,e1,x\).*?\n\}\r?\n\r?\n', '', content, flags=re.DOTALL)

# Remove band overlap/stacking
content = re.sub(r'// ══════\.\?Band overlap.*?\r?\nconst BAND_COMPRESSION_PER_LAYER.*?function computePerVertexOffsets\(bandIndex\).*?\n\}\r?\n\r?\n', '', content, flags=re.DOTALL)

# Remove addBand, removeBand, removeAllBands
content = re.sub(r'function addBand\(origin,normal\).*?\n\}\r?\nfunction removeBand\(\).*?\n\}\r?\nfunction removeAllBands\(\).*?\n  if\(_sharedRibbonMesh\).*?\n\}\r?\n\r?\n', '', content, flags=re.DOTALL)

# Remove last band panel
content = re.sub(r'// ══════\.\?Last band panel ══════\.\?\r?\nfunction updateLastBandPanel.*?\n\$\(''btn_horiz''\).*?;\r?\n\r?\n', '', content, flags=re.DOTALL)

# Remove square band WGSL shaders (bandStackCS, bandCutBinsCS, bandResolveCS, bandBuildMeshCS)
content = re.sub(r'// ══════\.\?GPU Band Rendering Shaders \(Plan C\) ══════\.\?\r?\n\r?\n// Shader C1: Per-vertex band stacking offsets\r?\nconst bandStackCS=.*?`\}\);\r?\n\r?\n// ═══════ GPU Ribbon Mesh Generation.*?\r?\n\r?\n// Shader G1: Triangle-plane intersection.*?\r?\nconst bandCutBinsCS=.*?`\}\);\r?\n\r?\n// Shader G2: Bin averaging.*?\r?\nconst bandResolveCS=.*?`\}\);\r?\n\r?\n// Shader G3: Resample \+ build ribbon.*?\r?\nconst bandBuildMeshCS=.*?`\}\);\r?\n\r?\n', '', content, flags=re.DOTALL)

# Remove square band pipelines
content = re.sub(r'// ── Plan C: GPU band rendering pipeline ──\r?\nconst bandStackPipe=cpPipe.*?;\r?\n// ── GPU Ribbon Mesh Generation pipelines ──\r?\nconst bandCutBinsPipe=cpPipe.*?;\r?\nconst bandResolvePipe=cpPipe.*?;\r?\nconst bandBuildMeshPipe=cpPipe.*?;\r?\n', '', content, flags=re.DOTALL)

# Remove square band buffer declarations
content = re.sub(r'// ── Plan C: GPU band rendering buffers ──\r?\nconst MAX_RIBBON_VERTS=.*?\r?\nlet bandOffLoB.*?\r?\nlet bandStackUB.*?\r?\nlet bandStackBG.*?\r?\n// ── GPU Ribbon Mesh Gen buffers ──\r?\nlet bandBinRB.*?\r?\nlet bandBinRYB.*?\r?\nlet bandBinRZB.*?\r?\nlet bandBinCB.*?\r?\nlet bandPolyPtsB.*?\r?\n// ── Shared ribbon mesh buffers.*?\r?\nlet _sharedPosB.*?\r?\nlet _sharedNormB.*?\r?\nlet _sharedUVB.*?\r?\nlet _sharedTanB.*?\r?\nlet _greenAllB.*?\r?\nlet _sharedRibbonMesh.*?\r?\n\r?\nlet bandCutUB.*?\r?\nlet bandResolveUB.*?\r?\nlet bandBuildUB.*?\r?\n', '', content, flags=re.DOTALL)

# Remove createSharedRibbonMesh function + call
content = re.sub(r'// ── Shared ribbon mesh: one geometry, one material, all bands ──\r?\nfunction createSharedRibbonMesh\(\).*?\n  return mesh;\r?\n\}\r?\n\r?\n', '', content, flags=re.DOTALL)
content = content.replace('  _sharedRibbonMesh=createSharedRibbonMesh();\n', '')

# Remove square band buffer creation from initGPU
content = re.sub(r'  // ── Plan C: GPU band rendering buffers ──\r?\n  bandOffLoB=.*?\r?\n  bandOffHiB=.*?\r?\n  bandStackUB=.*?\r?\n\r?\n  // ── GPU Ribbon Mesh Gen buffers ──\r?\n  bandBinRB=.*?\r?\n  bandBinRYB=.*?\r?\n  bandBinRZB=.*?\r?\n  bandBinCB=.*?\r?\n  bandPolyPtsB=.*?\r?\n  const SHARED_VERTS=.*?\r?\n  _sharedPosB=.*?\r?\n  _sharedNormB=.*?\r?\n  _sharedUVB=.*?\r?\n  _sharedTanB=.*?\r?\n  _greenAllB=.*?\r?\n  bandCutUB=.*?\r?\n  bandResolveUB=.*?\r?\n  bandBuildUB=.*?\r?\n\r?\n', '', content, flags=re.DOTALL)

# Remove square band HTML panels
content = re.sub(r' <h3>🎯 最后皮筋.*?</h3>.*?<button class="btn" id="btn_horiz"[^>]*>\r?\n\r?\n', '', content, flags=re.DOTALL)
content = re.sub(r' <h3>🎀 皮筋渲染</h3>.*?<input type="range" id="sl_rso"[^>]*>\r?\n', '', content, flags=re.DOTALL)
content = re.sub(r' <label style="display:flex;align-items:center;gap:6px;cursor:pointer;margin-top:8px;">\r?\n  <input type="checkbox" id="cb_target".*?\r?\n  🟢 显示目标周长参考线\r?\n </label>\r?\n', '', content, flags=re.DOTALL)

# Fix click handler: always circular
content = content.replace(
    "    if(e.shiftKey){\n      addCircularBand(hit.point,[0,1,0]);\n    }else{\n      addBand(hit.point,[0,1,0]);\n    }",
    "    addCircularBand(hit.point,[0,1,0]);")

# Fix key handlers
content = content.replace("if(key==='r'){removeBand();return;}\n  if(key==='c'){removeAllBands();", "if(key==='c'){removeAllCircularBands();")

# Fix animation loop: bands -> circularBands, runGPUBandVis -> runGPUCircularBandVis
content = content.replace('bands.length>0&&!pbdConverged', 'circularBands.length>0&&!pbdConverged')
content = content.replace('bands.length>0&&pbdConverged', 'circularBands.length>0&&pbdConverged')
content = content.replace('await runGPUBandVis(finalSrc)', 'await runGPUCircularBandVis(finalSrc)')
content = content.replace('await runGPUBandVis(posA)', 'await runGPUCircularBandVis(posA)')

# Fix writeBandParams to use circularBands
content = content.replace('for(let b=0;b<bands.length;b++)', 'for(let b=0;b<circularBands.length;b++)')
content = content.replace('const bn=bands[b];', 'const bn=circularBands[b];')

# Fix H.bcount references
content = content.replace('H.bcount.textContent=bands.length;', 'H.bcount.textContent=circularBands.length;')

# Fix info bar
content = content.replace(
    ' Click surface to bind band (normal dir) &nbsp; <span class="kb">Shift+Click</span>=圆皮筋 &nbsp; <span class="kb">R</span>=割一&nbsp; <span class="kb">T</span>=割圆&nbsp; <span class="kb">C</span>=全部割掉',
    ' Click = bind circular band &nbsp; <span class="kb">T</span>=cut one &nbsp; <span class="kb">C</span>=cut all')

# Fix removeAllBands remanants in animation loop (needsRestore section)
content = content.replace('removeAllBands();removeAllCircularBands()', 'removeAllCircularBands()')

# ── NOW ADD circular band code ──

# Add circular band state + functions before model loading
circ_code = """// ══════.? Circular Band (Tube) Parameters ══════.?
const MAX_CIRC_BANDS = 64;
const circularBands = [];
const circBandVisuals = [];
let TUBE_RADIUS = 0.018;
let TUBE_RADIAL_SEGS = 12;
let TUBE_RING_SEGS = 192;
const CIRC_BINS = 64;
let circVisDirty = false;

$('sl_tr').oninput=e=>{
  TUBE_RADIUS=+e.target.value;$('sv_tr').textContent=TUBE_RADIUS.toFixed(3);
  for(const b of circularBands)b.tubeRadius=TUBE_RADIUS;
  circVisDirty=true;
};
$('sl_rs').oninput=e=>{
  TUBE_RADIAL_SEGS=+e.target.value|0;$('sv_rs').textContent=TUBE_RADIAL_SEGS;
  circVisDirty=true;
};

// ══════.?Circular Band (Tube) add/remove ══════.?
function addCircularBand(origin, normal){
  if(circularBands.length>=MAX_CIRC_BANDS){console.warn('max circular bands');return;}
  const nl=Math.sqrt(normal[0]**2+normal[1]**2+normal[2]**2);
  const nn=[normal[0]/nl,normal[1]/nl,normal[2]/nl];
  const pre=computeBandRestRadii(origin,nn,proxyRestPositions,proxyIdxArr);
  if(!pre){console.warn('cross-section too small');return;}
  const band={
    planeOrigin:[...origin],
    planeNormal:[...nn],
    tubeRadius:TUBE_RADIUS,
    restCircum:BAND_REST_CIRCUM,
    stiffness:BAND_STIFF,
    influRadius:BAND_INFLU,
    preScale:pre.preScale,
    restRadii:pre.radii,
    restCentroid:pre.centroid,
    restPerimeter:pre.restPerimeter,
  };
  circularBands.push(band);
  circBandVisuals.push({});
  writeBandRestRadii(circularBands.length-1,pre.radii);
  circVisDirty=true;markPbdDirty();
  H.bcount.textContent=circularBands.length;
}
function removeCircularBand(){
  if(circularBands.length===0)return;
  circularBands.pop();
  circBandVisuals.pop();
  needsRestore=true;markPbdDirty();circVisDirty=true;
  H.bcount.textContent=circularBands.length;
  if(circularBands.length===0&&_circSharedMesh){
    _circSharedMesh.geometry.setDrawRange(0,0);_circSharedMesh.visible=false;
  }
}
function removeAllCircularBands(){
  while(circularBands.length>0){circularBands.pop();circBandVisuals.pop();}
  needsRestore=true;markPbdDirty();circVisDirty=true;
  H.bcount.textContent=0;
  if(_circSharedMesh){_circSharedMesh.geometry.setDrawRange(0,0);_circSharedMesh.visible=false;}
}

"""

content = content.replace(
    '// ══════.?Model Loading (dual: proxy + high-res) ══════.?',
    circ_code + '\n' + '// ══════.?Model Loading (dual: proxy + high-res) ══════.?')

# Add HTML sliders for circular band
html_circ = """ <h3>🔴 圆皮筋</h3>
 <label>管半径 <span class="val" id="sv_tr">0.018</span></label>
 <input type="range" id="sl_tr" min="0.005" max="0.08" step="0.001" value="0.018">
 <label>截面细分 <span class="val" id="sv_rs">12</span></label>
 <input type="range" id="sl_rs" min="4" max="24" step="1" value="12">
"""
content = content.replace(' <h3>💡 光照</h3>', html_circ + '\n <h3>💡 光照</h3>')

# Now check what's missing from the circular band infrastructure
needed = ['circBuildTubeCS', 'circCutBinsCS', 'circResolveCS', 'circCutBinsPipe', 
          'circResolvePipe', 'circBuildTubePipe', 'runGPUCircularBandVis',
          '_circBinRB', '_circSharedPosB', '_circSharedMesh', 'createCircSharedMesh',
          'MAX_TUBE_VERTS']

missing = [n for n in needed if n not in content]
if missing:
    print("STILL MISSING circular band code:")
    for m in missing:
        print(f"  - {m}")
    print("These must be manually added!")
else:
    print("All circular band code present!")

# Save
with open('d:/baoboluo/pineapple_CircularBand.html', 'w', encoding='utf-8') as f:
    f.write(content)

print(f"\nDone. File size: {len(content)} chars")
print("Lines:", content.count('\n'))
