with open('d:/baoboluo/pineapple_CircularBand.html', 'r', encoding='utf-8') as f:
    c = f.read()

# 1. Add circular pipelines
c = c.replace(
    'const bandVisTargetPipe=cpPipe(bandVisTargetCS,"main",[S_RO(0,CS),S_RO(1,CS),S_RO(2,CS),S_R(3,CS),U_B(4,CS)],"bandVisTarget");',
    'const bandVisTargetPipe=cpPipe(bandVisTargetCS,"main",[S_RO(0,CS),S_RO(1,CS),S_RO(2,CS),S_R(3,CS),U_B(4,CS)],"bandVisTarget");\n// Circular Band (Tube) pipelines\nconst circCutBinsPipe=cpPipe(circCutBinsCS,"main",[S_RO(0,CS),S_RO(1,CS),S_R(2,CS),S_R(3,CS),S_R(4,CS),S_R(5,CS),U_B(6,CS)],"circCutBins");\nconst circResolvePipe=cpPipe(circResolveCS,"main",[S_RO(0,CS),S_RO(1,CS),S_RO(2,CS),S_RO(3,CS),S_R(4,CS),U_B(5,CS)],"circResolve");\nconst circBuildTubePipe=cpPipe(circBuildTubeCS,"main",[S_RO(0,CS),S_R(1,CS),S_R(2,CS),S_R(3,CS),U_B(4,CS)],"circBuildTube");')

# 2. Add circular buffer declarations
buf_decl = '// Circular Band (Tube) buffers\n'
buf_decl += 'let _circBinRB,_circBinRYB,_circBinRZB,_circBinCB;\n'
buf_decl += 'let _circPolyPtsB;\n'
buf_decl += 'let _circSharedPosB,_circSharedNormB,_circSharedUVB;\n'
buf_decl += 'let _circSharedMesh;\n'
buf_decl += 'let _circCutUB,_circResolveUB,_circBuildUB;\n'
buf_decl += 'const MAX_TUBE_VERTS=256*16*6;\n'
c = c.replace('let WG,VWG;\n', 'let WG,VWG;\n' + buf_decl)

# 3. Add circular buffer creation in initGPU
buf_init = '  // Circular Band (Tube) GPU buffers\n'
buf_init += '  _circBinRB=mkBuf(CIRC_BINS*4,GPUBufferUsage.STORAGE|GPUBufferUsage.COPY_DST|GPUBufferUsage.COPY_SRC,"circBinRX");\n'
buf_init += '  _circBinRYB=mkBuf(CIRC_BINS*4,GPUBufferUsage.STORAGE|GPUBufferUsage.COPY_DST|GPUBufferUsage.COPY_SRC,"circBinRY");\n'
buf_init += '  _circBinRZB=mkBuf(CIRC_BINS*4,GPUBufferUsage.STORAGE|GPUBufferUsage.COPY_DST|GPUBufferUsage.COPY_SRC,"circBinRZ");\n'
buf_init += '  _circBinCB=mkBuf(CIRC_BINS*4,GPUBufferUsage.STORAGE|GPUBufferUsage.COPY_DST|GPUBufferUsage.COPY_SRC,"circBinC");\n'
buf_init += '  _circPolyPtsB=mkBuf(CIRC_BINS*4*4,GPUBufferUsage.STORAGE|GPUBufferUsage.COPY_SRC,"circPolyPts");\n'
buf_init += '  const TVC=MAX_TUBE_VERTS;\n'
buf_init += '  _circSharedPosB=mkBuf(MAX_CIRC_BANDS*TVC*3*4,GPUBufferUsage.STORAGE|GPUBufferUsage.VERTEX,"circSharedPos");\n'
buf_init += '  _circSharedNormB=mkBuf(MAX_CIRC_BANDS*TVC*3*4,GPUBufferUsage.STORAGE|GPUBufferUsage.VERTEX,"circSharedNorm");\n'
buf_init += '  _circSharedUVB=mkBuf(MAX_CIRC_BANDS*TVC*2*4,GPUBufferUsage.STORAGE|GPUBufferUsage.VERTEX,"circSharedUV");\n'
buf_init += '  _circCutUB=mkBuf(48,GPUBufferUsage.UNIFORM|GPUBufferUsage.COPY_DST,"circCutU");\n'
buf_init += '  _circResolveUB=mkBuf(8,GPUBufferUsage.UNIFORM|GPUBufferUsage.COPY_DST,"circResolveU");\n'
buf_init += '  _circBuildUB=mkBuf(48,GPUBufferUsage.UNIFORM|GPUBufferUsage.COPY_DST,"circBuildU");\n'
c = c.replace('  // Staging\n  staging=mkBuf', buf_init + '\n  // Staging\n  staging=mkBuf')

# 4. Add createCircSharedMesh function
mesh_fn = '\n'
mesh_fn += '// Shared circular tube mesh: one geometry, one material, all circular bands\n'
mesh_fn += 'function createCircSharedMesh(){\n'
mesh_fn += '  const geo=new THREE.BufferGeometry();\n'
mesh_fn += '  const posArr=new Float32Array(MAX_TUBE_VERTS*3);\n'
mesh_fn += '  const normArr=new Float32Array(MAX_TUBE_VERTS*3);\n'
mesh_fn += '  const uvArr=new Float32Array(MAX_TUBE_VERTS*2);\n'
mesh_fn += '  const posAttr=new THREE.Float32BufferAttribute(posArr,3);\n'
mesh_fn += '  const normAttr=new THREE.Float32BufferAttribute(normArr,3);\n'
mesh_fn += '  const uvAttr=new THREE.Float32BufferAttribute(uvArr,2);\n'
mesh_fn += '  const FC=MAX_CIRC_BANDS*MAX_TUBE_VERTS;\n'
mesh_fn += '  for(const a of[posAttr,normAttr])Object.defineProperty(a,"count",{get(){return FC;},configurable:true});\n'
mesh_fn += '  for(const a of[uvAttr])Object.defineProperty(a,"count",{get(){return FC;},configurable:true});\n'
mesh_fn += '  posAttr.needsUpdate=true;normAttr.needsUpdate=true;uvAttr.needsUpdate=true;\n'
mesh_fn += '  geo.setAttribute("position",posAttr);geo.setAttribute("normal",normAttr);geo.setAttribute("uv",uvAttr);\n'
mesh_fn += '  geo.setDrawRange(0,0);\n'
mesh_fn += '  const mat=new THREE.MeshStandardMaterial({color:"#d4a017",roughness:0.45,metalness:0.0,side:THREE.DoubleSide,depthTest:true,depthWrite:true,polygonOffset:true,polygonOffsetFactor:1.0,polygonOffsetUnits:1.0});\n'
mesh_fn += '  const mesh=new THREE.Mesh(geo,mat);mesh.renderOrder=2;mesh.frustumCulled=false;mesh.visible=false;\n'
mesh_fn += '  geo.boundingSphere=new THREE.Sphere(new THREE.Vector3(0,0,0),100);\n'
mesh_fn += '  geo.boundingBox=new THREE.Box3(new THREE.Vector3(-100,-100,-100),new THREE.Vector3(100,100,100));\n'
mesh_fn += '  scene.add(mesh);\n'
mesh_fn += '  const an=["position","normal","uv"];const sb=[_circSharedPosB,_circSharedNormB,_circSharedUVB];\n'
mesh_fn += '  for(let i=0;i<an.length;i++){const a=geo.attributes[an[i]];renderer.backend.createAttribute(a);const be=renderer.backend.get(a);if(be)be.buffer=sb[i];a.needsUpdate=false;}\n'
mesh_fn += '  return mesh;\n}\n'

c = c.replace(
    '\n}\n\n// ========== GPU PBD: write band params',
    '\n  _circSharedMesh=createCircSharedMesh();\n}\n\n' + mesh_fn + '\n// ========== GPU PBD: write band params')

# 5. Add runGPUCircularBandVis 
run_fn = '\n'
run_fn += '// ========== GPU Circular Band (Tube) Visualization ==========\n'
run_fn += 'let _circCutU8=null,_circCutF32=null,_circBuildU8=null,_circBuildF32=null,_circResU32=null,_circZeroBins=null;\n\n'
run_fn += 'async function runGPUCircularBandVis(finalSrc){\n'
run_fn += '  if(!_circBinRB){return 0;}\n'
run_fn += '  const bc=circularBands.length;\n'
run_fn += '  if(bc===0){if(_circSharedMesh){_circSharedMesh.geometry.setDrawRange(0,0);_circSharedMesh.visible=false;}return 0;}\n'
run_fn += '  const t0=performance.now();\n'
run_fn += '  const srcPos=(finalSrc===posA)?posA:posB;\n'
run_fn += '  const ringSegs=TUBE_RING_SEGS,radialSegs=TUBE_RADIAL_SEGS,totalVerts=ringSegs*radialSegs*6;\n'
run_fn += '  if(!_circCutU8){_circCutU8=new Uint32Array(new ArrayBuffer(48));_circCutF32=new Float32Array(_circCutU8.buffer);}\n'
run_fn += '  if(!_circBuildU8){_circBuildU8=new Uint32Array(new ArrayBuffer(48));_circBuildF32=new Float32Array(_circBuildU8.buffer);}\n'
run_fn += '  if(!_circResU32){_circResU32=new Uint32Array(new ArrayBuffer(8));}\n'
run_fn += '  if(!_circZeroBins){_circZeroBins=new Uint32Array(CIRC_BINS);}\n'
run_fn += '  let cx=0,cy=0,cz=0;\n'
run_fn += '  for(let i=0;i<proxyVertexCount;i++){cx+=proxyRestPositions[i*3];cy+=proxyRestPositions[i*3+1];cz+=proxyRestPositions[i*3+2];}\n'
run_fn += '  cx/=proxyVertexCount;cy/=proxyVertexCount;cz/=proxyVertexCount;\n'
run_fn += '  for(let b=0;b<bc;b++){\n'
run_fn += '    const band=circularBands[b];if(!band)continue;\n'
run_fn += '    const enc=device.createCommandEncoder();\n'
run_fn += '    queue.writeBuffer(_circBinRB,0,_circZeroBins);queue.writeBuffer(_circBinRYB,0,_circZeroBins);\n'
run_fn += '    queue.writeBuffer(_circBinRZB,0,_circZeroBins);queue.writeBuffer(_circBinCB,0,_circZeroBins);\n'
run_fn += '    _circCutU8[0]=proxyTriCount;_circCutU8[1]=proxyVertexCount;\n'
run_fn += '    _circCutF32[2]=band.planeOrigin[0];_circCutF32[3]=band.planeOrigin[1];_circCutF32[4]=band.planeOrigin[2];\n'
run_fn += '    _circCutF32[5]=band.planeNormal[0];_circCutF32[6]=band.planeNormal[1];_circCutF32[7]=band.planeNormal[2];\n'
run_fn += '    _circCutF32[8]=band.tubeRadius;_circCutF32[9]=cx;_circCutF32[10]=cy;_circCutF32[11]=cz;\n'
run_fn += '    queue.writeBuffer(_circCutUB,0,_circCutU8);\n'
run_fn += '    const cutBG=device.createBindGroup({layout:circCutBinsPipe.bgl,entries:[\n'
run_fn += '      {binding:0,resource:{buffer:srcPos}},{binding:1,resource:{buffer:idxB}},\n'
run_fn += '      {binding:2,resource:{buffer:_circBinRB}},{binding:3,resource:{buffer:_circBinRYB}},\n'
run_fn += '      {binding:4,resource:{buffer:_circBinRZB}},{binding:5,resource:{buffer:_circBinCB}},\n'
run_fn += '      {binding:6,resource:{buffer:_circCutUB}}]});\n'
run_fn += '    {const cp=enc.beginComputePass();cp.setPipeline(circCutBinsPipe.pipe);cp.setBindGroup(0,cutBG);cp.dispatchWorkgroups(VWG,1,1);cp.end();}\n'
run_fn += '    _circResU32[0]=ringSegs;queue.writeBuffer(_circResolveUB,0,_circResU32);\n'
run_fn += '    const resolveBG=device.createBindGroup({layout:circResolvePipe.bgl,entries:[\n'
run_fn += '      {binding:0,resource:{buffer:_circBinRB}},{binding:1,resource:{buffer:_circBinRYB}},\n'
run_fn += '      {binding:2,resource:{buffer:_circBinRZB}},{binding:3,resource:{buffer:_circBinCB}},\n'
run_fn += '      {binding:4,resource:{buffer:_circPolyPtsB}},{binding:5,resource:{buffer:_circResolveUB}}]});\n'
run_fn += '    {const cp=enc.beginComputePass();cp.setPipeline(circResolvePipe.pipe);cp.setBindGroup(0,resolveBG);cp.dispatchWorkgroups(1,1,1);cp.end();}\n'
run_fn += '    _circBuildU8[0]=ringSegs;_circBuildU8[1]=radialSegs;\n'
run_fn += '    _circBuildF32[2]=band.tubeRadius;\n'
run_fn += '    _circBuildF32[3]=band.planeNormal[0];_circBuildF32[4]=band.planeNormal[1];_circBuildF32[5]=band.planeNormal[2];\n'
run_fn += '    _circBuildF32[6]=cx;_circBuildF32[7]=cy;_circBuildF32[8]=cz;\n'
run_fn += '    queue.writeBuffer(_circBuildUB,0,_circBuildU8);\n'
run_fn += '    const bandVtxOff=b*totalVerts;\n'
run_fn += '    const buildBG=device.createBindGroup({layout:circBuildTubePipe.bgl,entries:[\n'
run_fn += '      {binding:0,resource:{buffer:_circPolyPtsB}},\n'
run_fn += '      {binding:1,resource:{buffer:_circSharedPosB,offset:bandVtxOff*3*4,size:totalVerts*3*4}},\n'
run_fn += '      {binding:2,resource:{buffer:_circSharedNormB,offset:bandVtxOff*3*4,size:totalVerts*3*4}},\n'
run_fn += '      {binding:3,resource:{buffer:_circSharedUVB,offset:bandVtxOff*2*4,size:totalVerts*2*4}},\n'
run_fn += '      {binding:4,resource:{buffer:_circBuildUB}}]});\n'
run_fn += '    {const cp=enc.beginComputePass();cp.setPipeline(circBuildTubePipe.pipe);cp.setBindGroup(0,buildBG);cp.dispatchWorkgroups(1,1,1);cp.end();}\n'
run_fn += '    device.queue.submit([enc.finish()]);\n'
run_fn += '  }\n'
run_fn += '  if(_circSharedMesh){if(bc>0){_circSharedMesh.geometry.setDrawRange(0,bc*totalVerts);_circSharedMesh.visible=true;}else{_circSharedMesh.geometry.setDrawRange(0,0);_circSharedMesh.visible=false;}}\n'
run_fn += '  return performance.now()-t0;\n}\n'

c = c.replace(
    '\n\n// ========== Interaction ==========',
    run_fn + '\n// ========== Interaction ==========')

with open('d:/baoboluo/pineapple_CircularBand.html', 'w', encoding='utf-8') as f:
    f.write(c)
print('Done! Lines:', c.count('\n'))
print('Has circBuildTubeCS:', 'circBuildTubeCS' in c)
print('Has runGPUCircularBandVis:', 'runGPUCircularBandVis' in c)
print('Has createCircSharedMesh:', 'createCircSharedMesh' in c)
