// ── STATE ──
let selectedImages = [];   // array of File objects (photos)
let selectedAudio  = null;
let selectedVideo  = null;
let isRecording    = false;
let mediaRecorder  = null;
let audioChunks    = [];
let recInterval    = null;
let recSeconds     = 0;
let cameraStream   = null;
let currentFacing   = "environment"; // "environment" = back, "user" = front
let videoStream    = null;       // for in-app video recording
let videoRecorder  = null;
let videoChunks    = [];
let videoRecInterval = null;
let videoRecSeconds  = 0;
let userLocation   = null;
let locationAddr   = '';
let locationSource = null; // 'camera' | 'upload' | 'gps'
let userProfile    = null;

// ── ONBOARDING ──
function loadProfile() {
  try { userProfile = JSON.parse(localStorage.getItem('tampines_profile') || 'null'); } catch(e){}
  if (!userProfile || !userProfile.phone || !userProfile.name) {
    const onboardScreen = document.getElementById('onboardScreen');
    if (onboardScreen) onboardScreen.classList.add('show');
  } else { updateHeaderProfile(); }
}

function saveProfile() {
  const nameEl    = document.getElementById('onboardName');
  const phoneEl   = document.getElementById('onboardPhone');
  const addressEl = document.getElementById('onboardAddress');
  const err       = document.getElementById('onboardError');
  if (!nameEl || !phoneEl) return;
  const name    = nameEl.value.trim();
  const phone   = phoneEl.value.trim().replace(/\s/g,'');
  const address = addressEl ? addressEl.value.trim() : '';
  if (!name || !/^\d{8}$/.test(phone)) { if(err) err.classList.add('show'); return; }
  if (err) err.classList.remove('show');
  userProfile = { name, phone: '+65' + phone, homeAddress: address };
  localStorage.setItem('tampines_profile', JSON.stringify(userProfile));
  const onboardScreen = document.getElementById('onboardScreen');
  if (onboardScreen) onboardScreen.classList.remove('show');
  updateHeaderProfile();
}

function updateHeaderProfile() {
  if (!userProfile) return;
  const avatarEl = document.getElementById('profileAvatar');
  const nameEl   = document.getElementById('profileName');
  const headerEl = document.getElementById('headerProfile');
  if (!avatarEl || !nameEl || !headerEl) return; // guard: DOM not ready
  const initials = userProfile.name.split(' ').map(w=>w[0]).join('').slice(0,2).toUpperCase();
  avatarEl.textContent = initials;
  nameEl.textContent   = userProfile.name.split(' ')[0];
  headerEl.style.display = 'flex';
}

function editProfile() {
  if (!userProfile) return;
  const nameEl    = document.getElementById('onboardName');
  const phoneEl   = document.getElementById('onboardPhone');
  const addressEl = document.getElementById('onboardAddress');
  if (nameEl)    nameEl.value    = userProfile.name;
  if (phoneEl)   phoneEl.value   = userProfile.phone.replace('+65','');
  if (addressEl) addressEl.value = userProfile.homeAddress || '';
  const onboardScreen = document.getElementById('onboardScreen');
  if (onboardScreen) onboardScreen.classList.add('show');
}

// ── NAVIGATION ──
function goProfile() { window.location.href = '/profile.html'; }

// ── GPS ──
function startGPS() {
  if (!navigator.geolocation) { setGPS('', 'Location not available', false); return; }
  navigator.geolocation.getCurrentPosition(async pos => {
    // Only store as background fallback — don't override camera-locked location
    if (locationSource !== 'camera') {
      userLocation = { lat: pos.coords.latitude, lng: pos.coords.longitude };
      locationSource = 'gps';
      try {
        const res  = await fetch(`https://nominatim.openstreetmap.org/reverse?lat=${userLocation.lat}&lon=${userLocation.lng}&format=json`);
        const data = await res.json();
        const parts = (data.display_name || '').split(',');
        locationAddr = parts.slice(0,3).join(',').trim();
        setGPS('found', '📍 ' + locationAddr, true);
      } catch {
        locationAddr = `${userLocation.lat.toFixed(4)}, ${userLocation.lng.toFixed(4)}`;
        setGPS('found', '📍 Location found', true);
      }
    }
  }, () => setGPS('warn', 'Location unavailable — state your block when speaking', false),
  { timeout: 10000, enableHighAccuracy: true });
}

// Lock GPS at the exact moment camera photo is taken
async function lockCameraLocation() {
  return new Promise(resolve => {
    if (!navigator.geolocation) { resolve(); return; }
    setGPS('searching', '📍 Locking location…', false);
    navigator.geolocation.getCurrentPosition(async pos => {
      userLocation  = { lat: pos.coords.latitude, lng: pos.coords.longitude };
      locationSource = 'camera';
      try {
        const res  = await fetch(`https://nominatim.openstreetmap.org/reverse?lat=${userLocation.lat}&lon=${userLocation.lng}&format=json`);
        const data = await res.json();
        const parts = (data.display_name || '').split(',');
        locationAddr = parts.slice(0,3).join(',').trim();
        setGPS('found', '📍 ' + locationAddr, true);
      } catch {
        locationAddr = `${userLocation.lat.toFixed(4)}, ${userLocation.lng.toFixed(4)}`;
        setGPS('found', '📍 Location locked', true);
      }
      // Hide upload address strip since we have live location
      const strip = document.getElementById('uploadAddrStrip');
      if (strip) strip.style.display = 'none';
      resolve();
    }, () => {
      // GPS failed — fall back to home address
      setGPS('warn', 'GPS unavailable', false);
      resolve();
    }, { timeout: 8000, enableHighAccuracy: true });
  });
}
function setGPS(cls, text, _found) {
  const dot = document.getElementById('gpsDot');
  if (!dot) return;
  dot.className = 'gps-dot' + (cls ? ' '+cls : '');
  const textEl = document.getElementById('gpsText');
  textEl.textContent = text;
  textEl.className = 'gps-text' + (cls === 'warn' ? ' warn' : '');
}

// ── IMAGE HANDLING ──
const MAX_PHOTOS = 10;

function showPhotoLimitWarning(current, attempted) {
  const remaining = MAX_PHOTOS - current;
  let msg = '';
  if (remaining <= 0) {
    msg = `⚠️ Maximum ${MAX_PHOTOS} photos reached. Remove some before adding more.`;
  } else {
    msg = `⚠️ Only ${remaining} more photo${remaining !== 1 ? 's' : ''} allowed (max ${MAX_PHOTOS}). ${attempted - remaining} photo${attempted - remaining !== 1 ? 's' : ''} were not added.`;
  }
  // Show inline warning banner
  let banner = document.getElementById('photoLimitBanner');
  if (!banner) {
    banner = document.createElement('div');
    banner.id = 'photoLimitBanner';
    banner.style.cssText = `
      background: #fff7ed; border: 2px solid #fb923c; border-radius: 14px;
      padding: 12px 16px; margin-top: 10px; font-family: 'Nunito', sans-serif;
      font-size: 13px; font-weight: 800; color: #c2410c;
      display: flex; align-items: center; gap: 10px;
      animation: fadeInBanner 0.25s ease;
    `;
    const style = document.createElement('style');
    style.textContent = `@keyframes fadeInBanner { from { opacity:0; transform:translateY(-6px); } to { opacity:1; transform:translateY(0); } }`;
    document.head.appendChild(style);
    const gallery = document.getElementById('mediaGallery');
    gallery.parentNode.insertBefore(banner, gallery.nextSibling);
  }
  banner.innerHTML = `<span style="font-size:18px">🚫</span><span>${msg}</span>`;
  banner.style.display = 'flex';
  clearTimeout(banner._timer);
  banner._timer = setTimeout(() => { banner.style.display = 'none'; }, 5000);
  updatePhotoCounter();
}

function updatePhotoCounter() {
  const count = selectedImages.filter(Boolean).length;
  let counter = document.getElementById('photoCounter');
  if (!counter) {
    counter = document.createElement('div');
    counter.id = 'photoCounter';
    counter.style.cssText = `
      font-family: 'Nunito', sans-serif; font-size: 11px; font-weight: 900;
      color: #64748b; text-align: right; padding: 4px 2px 0;
      letter-spacing: 0.5px; text-transform: uppercase;
    `;
    const gallery = document.getElementById('mediaGallery');
    gallery.parentNode.insertBefore(counter, gallery);
  }
  if (count > 0) {
    const atMax = count >= MAX_PHOTOS;
    counter.style.color = atMax ? '#dc2626' : '#64748b';
    counter.textContent = `📷 ${count} / ${MAX_PHOTOS} photos${atMax ? ' — limit reached' : ''}`;
    counter.style.display = 'block';
  } else {
    counter.style.display = 'none';
  }
}

function handleImageFile(input) {
  const files = Array.from(input.files); if (!files.length) return;
  const current = selectedImages.filter(Boolean).length;
  const canAdd  = MAX_PHOTOS - current;
  if (canAdd <= 0) { showPhotoLimitWarning(current, files.length); input.value = ''; return; }
  const toAdd = files.slice(0, canAdd);
  toAdd.forEach(f => addImageToGallery(f));
  if (files.length > canAdd) showPhotoLimitWarning(current, files.length);
  document.getElementById('btnCamera').classList.add('done');
  input.value = '';
}
function handleUploadFile(input) {
  const files = Array.from(input.files); if (!files.length) return;
  const vids  = files.filter(f => f.type.startsWith('video/'));
  const imgs  = files.filter(f => !f.type.startsWith('video/'));
  if (vids.length) {
    selectedVideo = vids[0];
    const vid = document.getElementById('videoPreview');
    vid.src = URL.createObjectURL(vids[0]);
    document.getElementById('videoWrap').style.display = 'block';
  }
  const current = selectedImages.filter(Boolean).length;
  const canAdd  = MAX_PHOTOS - current;
  if (imgs.length > 0 && canAdd <= 0) {
    showPhotoLimitWarning(current, imgs.length);
  } else {
    const toAdd = imgs.slice(0, canAdd);
    toAdd.forEach(f => addImageToGallery(f));
    if (imgs.length > canAdd) showPhotoLimitWarning(current, imgs.length);
  }
  document.getElementById('btnUpload').classList.add('done');
  const upBadge = document.getElementById('uploadBadge');
  if (upBadge) upBadge.textContent = '✓ Added';
  document.getElementById('mediaGallery').classList.add('show');
  document.getElementById('addMorePill').style.display = 'flex';
  input.value = '';

  // Show address strip pre-filled with home address for uploaded photos
  if (locationSource !== 'camera') {
    const strip = document.getElementById('uploadAddrStrip');
    const addrInput = document.getElementById('uploadAddrInput');
    strip.style.display = 'block';
    // Pre-fill with saved home address if available and field is empty
    if (!addrInput.value && userProfile && userProfile.homeAddress) {
      addrInput.value = userProfile.homeAddress;
    }
    locationSource = 'upload';
  }
}

function addImageToGallery(file) {
  selectedImages.push(file);
  const idx = selectedImages.length - 1;
  const url = URL.createObjectURL(file);

  const wrap = document.createElement('div');
  wrap.className = 'thumb-item';
  wrap.id = 'thumb-' + idx;

  const img = document.createElement('img');
  img.src = url; img.alt = 'photo';

  const del = document.createElement('button');
  del.className = 'thumb-del';
  del.textContent = '✕';
  del.onclick = () => removeImage(idx);

  wrap.appendChild(img);
  wrap.appendChild(del);
  document.getElementById('thumbScroll').appendChild(wrap);
  document.getElementById('mediaGallery').classList.add('show');
  // Hide "Add more" pill when limit is hit
  const atMax = selectedImages.filter(Boolean).length >= MAX_PHOTOS;
  document.getElementById('addMorePill').style.display = atMax ? 'none' : 'flex';
  updatePhotoCounter();
}

function removeImage(idx) {
  selectedImages[idx] = null;
  const el = document.getElementById('thumb-' + idx);
  if (el) el.remove();
  const remaining = selectedImages.filter(Boolean);
  // Hide limit banner if we're now under the limit
  const banner = document.getElementById('photoLimitBanner');
  if (banner && remaining.length < MAX_PHOTOS) banner.style.display = 'none';
  updatePhotoCounter();
  // Re-show "Add more" pill if we dropped below limit
  if (remaining.length < MAX_PHOTOS && (remaining.length || selectedVideo)) {
    document.getElementById('addMorePill').style.display = 'flex';
  }
  if (!remaining.length && !selectedVideo) {
    document.getElementById('mediaGallery').classList.remove('show');
    document.getElementById('addMorePill').style.display = 'none';
    document.getElementById('btnCamera').classList.remove('done');
    document.getElementById('btnUpload').classList.remove('done');
  }
}

function clearVideo() {
  selectedVideo = null;
  document.getElementById('videoWrap').style.display = 'none';
  document.getElementById('videoPreview').src = '';
  const remaining = selectedImages.filter(Boolean);
  if (!remaining.length) {
    document.getElementById('mediaGallery').classList.remove('show');
    document.getElementById('addMorePill').style.display = 'none';
    document.getElementById('btnUpload').classList.remove('done');
  }
}

function clearAllMedia() {
  selectedImages = []; selectedVideo = null;
  document.getElementById('thumbScroll').innerHTML = '';
  document.getElementById('videoWrap').style.display = 'none';
  document.getElementById('videoPreview').src = '';
  document.getElementById('mediaGallery').classList.remove('show');
  document.getElementById('addMorePill').style.display = 'none';
  document.getElementById('btnCamera').classList.remove('done');
  document.getElementById('btnUpload').classList.remove('done');
  const vb = document.getElementById('btnVideo');
  if (vb) { vb.classList.remove('done'); }
  const vt = document.getElementById('videoTitle');
  if (vt) vt.textContent = 'Take Video';
}

// ── CAMERA ──
async function openCamera() {
  currentFacing = 'environment';
  try {
    await startCameraStream();
    document.getElementById('capturedImg').style.display = 'none';
    document.getElementById('camControlsLive').style.display    = 'flex';
    document.getElementById('camControlsPreview').style.display = 'none';
    document.getElementById('cameraModal').classList.add('show');
  } catch(e) { document.getElementById('imageInput').click(); }
}

async function startCameraStream() {
  if (cameraStream) { cameraStream.getTracks().forEach(t => t.stop()); cameraStream = null; }
  cameraStream = await navigator.mediaDevices.getUserMedia({
    video: { facingMode: currentFacing, width: { ideal: 1920 }, height: { ideal: 1080 } },
    audio: false
  });
  const preview = document.getElementById('cameraPreview');
  preview.srcObject = cameraStream;
  preview.style.display = 'block';
  // Mirror front camera
  preview.style.transform = currentFacing === 'user' ? 'scaleX(-1)' : 'scaleX(1)';
}

async function flipCamera() {
  currentFacing = currentFacing === 'environment' ? 'user' : 'environment';
  const btn = document.getElementById('camFlipBtn');
  if (btn) { btn.style.transform = 'rotate(180deg)'; setTimeout(() => btn.style.transform = '', 300); }
  try {
    await startCameraStream();
  } catch(e) {
    // flip failed — revert
    currentFacing = currentFacing === 'environment' ? 'user' : 'environment';
    await startCameraStream();
  }
}
function capturePhoto() {
  const v = document.getElementById('cameraPreview');
  const c = document.getElementById('cameraCanvas');
  c.width = v.videoWidth; c.height = v.videoHeight;
  c.getContext('2d').drawImage(v, 0, 0);
  const img = document.getElementById('capturedImg');
  img.src = c.toDataURL('image/jpeg');
  img.style.display = 'block';
  v.style.display   = 'none';
  document.getElementById('camControlsLive').style.display    = 'none';
  document.getElementById('camControlsPreview').style.display = 'flex';
}
function retakePhoto() {
  document.getElementById('cameraPreview').style.display  = 'block';
  document.getElementById('capturedImg').style.display    = 'none';
  document.getElementById('camControlsLive').style.display    = 'flex';
  document.getElementById('camControlsPreview').style.display = 'none';
}
async function useCapture() {
  const c   = document.getElementById('cameraCanvas');
  const img = document.getElementById('capturedImg');
  closeCamera();
  await lockCameraLocation();
  c.toBlob(blob => {
    if (!blob) return;
    const file = new File([blob], 'camera_photo.jpg', { type:'image/jpeg' });
    addImageToGallery(file);
    document.getElementById('btnCamera').classList.add('done');
    const camBadge = document.getElementById('cameraBadge');
    if (camBadge) camBadge.textContent = '✓';
  }, 'image/jpeg', 0.85);
}
function closeCamera() {
  if (cameraStream) { cameraStream.getTracks().forEach(t=>t.stop()); cameraStream=null; }
  document.getElementById('cameraModal').classList.remove('show');
}

// ── VIDEO RECORDING ──
let videoFacing = 'environment';

async function startVideoStream() {
  if (videoStream) { videoStream.getTracks().forEach(t => t.stop()); videoStream = null; }
  videoStream = await navigator.mediaDevices.getUserMedia({
    video: { facingMode: videoFacing, width: { ideal: 1920 }, height: { ideal: 1080 } },
    audio: true
  });
  const preview = document.getElementById('videoRecordPreview');
  preview.srcObject = videoStream;
  preview.style.transform = videoFacing === 'user' ? 'scaleX(-1)' : 'scaleX(1)';
}

async function openVideoModal() {
  videoFacing = 'environment';
  try {
    await startVideoStream();
    document.getElementById('videoRecordPreview').style.display = 'block';
    document.getElementById('videoPlayback').style.display      = 'none';
    document.getElementById('videoRecTimer').style.display      = 'none';
    document.getElementById('vidControlsIdle').style.display      = 'flex';
    document.getElementById('vidControlsRecording').style.display = 'none';
    document.getElementById('vidControlsPreview').style.display   = 'none';
    document.getElementById('videoModal').classList.add('show');
  } catch(e) {
    showError('Camera/microphone access denied for video.');
  }
}

async function flipVideoCamera() {
  videoFacing = videoFacing === 'environment' ? 'user' : 'environment';
  const btn = document.getElementById('vidFlipBtn');
  if (btn) { btn.style.transform = 'rotate(180deg)'; setTimeout(() => btn.style.transform = '', 300); }
  try {
    await startVideoStream();
  } catch(e) {
    videoFacing = videoFacing === 'environment' ? 'user' : 'environment';
    await startVideoStream();
  }
}

function startVideoRecord() {
  videoChunks = []; videoRecSeconds = 0;
  videoRecorder = new MediaRecorder(videoStream);
  videoRecorder.ondataavailable = e => { if(e.data.size>0) videoChunks.push(e.data); };
  videoRecorder.onstop = () => {
    const blob = new Blob(videoChunks, { type:'video/webm' });
    const url  = URL.createObjectURL(blob);
    const pb   = document.getElementById('videoPlayback');
    pb.src = url; pb.style.display = 'block';
    document.getElementById('videoRecordPreview').style.display   = 'none';
    document.getElementById('videoRecTimer').style.display        = 'none';
    document.getElementById('vidControlsRecording').style.display = 'none';
    document.getElementById('vidControlsPreview').style.display   = 'flex';
    videoRecorder._blob = blob;
  };
  videoRecorder.start();
  videoRecInterval = setInterval(() => {
    videoRecSeconds++;
    const m = Math.floor(videoRecSeconds / 60), s = videoRecSeconds % 60;
    const t = document.getElementById('videoRecTimer');
    t.textContent = '⏺ ' + String(m).padStart(2,'0') + ':' + String(s).padStart(2,'0');
    t.style.display = 'block';
  }, 1000);
  document.getElementById('vidControlsIdle').style.display      = 'none';
  document.getElementById('vidControlsRecording').style.display = 'flex';
}

function stopVideoRecord() {
  clearInterval(videoRecInterval);
  if (videoRecorder && videoRecorder.state !== 'inactive') videoRecorder.stop();
}

function retakeVideo() {
  document.getElementById('videoPlayback').style.display = 'none';
  document.getElementById('videoRecordPreview').style.display = 'block';
  document.getElementById('videoRecTimer').style.display      = 'none';
  document.getElementById('vidControlsPreview').style.display   = 'none';
  document.getElementById('vidControlsIdle').style.display      = 'flex';
  videoRecSeconds = 0;
  document.getElementById('videoRecordPreview').srcObject = videoStream;
}

function useVideo() {
  const blob = videoRecorder && videoRecorder._blob;
  if (!blob) { closeVideoModal(); return; }
  selectedVideo = new File([blob], 'recorded_video.webm', { type:'video/webm' });
  const url = URL.createObjectURL(blob);
  const vid = document.getElementById('videoPreview');
  vid.src = url;
  document.getElementById('videoWrap').style.display = 'block';
  document.getElementById('mediaGallery').classList.add('show');
  document.getElementById('btnVideo').classList.add('done');
  document.getElementById('videoTitle').textContent = 'Video Ready';
  closeVideoModal();
}

function closeVideoModal() {
  clearInterval(videoRecInterval);
  if (videoRecorder && videoRecorder.state !== 'inactive') videoRecorder.stop();
  if (videoStream) { videoStream.getTracks().forEach(t=>t.stop()); videoStream=null; }
  document.getElementById('videoModal').classList.remove('show');
}

// ── RECORDING ──
async function toggleRecording() {
  if (isRecording) { stopRecording(); return; }
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio:true });
    audioChunks=[]; recSeconds=0;
    mediaRecorder = new MediaRecorder(stream);
    mediaRecorder.ondataavailable = e => { if(e.data.size>0) audioChunks.push(e.data); };
    mediaRecorder.onstop = () => {
      stream.getTracks().forEach(t=>t.stop());
      const blob = new Blob(audioChunks, { type:'audio/webm' });
      selectedAudio = new File([blob], 'voice.webm', { type:'audio/webm' });
      const url = URL.createObjectURL(blob);
      document.getElementById('voicePlayer').src = url;
      const mins=Math.floor(recSeconds/60), secs=recSeconds%60;
      document.getElementById('voiceDuration').textContent =
        `Voice recorded (${mins}:${String(secs).padStart(2,'0')})`;
      document.getElementById('voicePreview').classList.add('show');
    };
    mediaRecorder.start();
    isRecording=true;
    recInterval = setInterval(()=>{
      recSeconds++;
      const m=Math.floor(recSeconds/60), s=recSeconds%60;
      document.getElementById('speakTimer').textContent =
        String(m).padStart(2,'0')+':'+String(s).padStart(2,'0');
    },1000);
    document.getElementById('speakBtn').classList.add('recording');
    document.getElementById('speakBtn').classList.remove('done');
    document.getElementById('speakBadge').textContent = '⏹';
    document.getElementById('speakRing').innerHTML = '<svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="#ffffff" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><rect x="6" y="6" width="12" height="12" rx="2"/></svg>';
    document.getElementById('speakTitle').textContent  = 'Recording';
    document.getElementById('speakSub').textContent    = 'Tap to stop';
    document.getElementById('waveform').classList.add('show');
    document.getElementById('speakTimer').style.display= 'block';
    document.getElementById('speakTimer').textContent  = '00:00';
  } catch(e) { showError('Microphone access denied.'); }
}
function stopRecording() {
  if (mediaRecorder && mediaRecorder.state!=='inactive') mediaRecorder.stop();
  clearInterval(recInterval);
  isRecording=false;
  document.getElementById('speakBtn').classList.remove('recording');
  document.getElementById('speakBtn').classList.add('done');
  document.getElementById('speakRing').innerHTML = '<svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="#ffffff" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>';
  document.getElementById('speakTitle').textContent = 'Recorded';
  document.getElementById('speakSub').textContent   = 'Tap to redo';
  document.getElementById('speakBadge').textContent = '✓';
  document.getElementById('waveform').classList.remove('show');
  document.getElementById('speakTimer').style.display= 'none';
}

// ── SEND REPORT → now redirects to confirm page ──
let pendingFormData = null;

async function sendReport() {
  const images = selectedImages.filter(Boolean);
  if (!images.length && !selectedVideo && !selectedAudio) {
    showError('Please add a photo or voice recording first.'); return;
  }
  sessionStorage.removeItem('tampines_came_back'); // clear any stale back-flag
  document.getElementById('errorBox').style.display = 'none';

  const profile = userProfile || JSON.parse(localStorage.getItem('tampines_profile')||'null');

  // ── Resolve location string ──
  let location = '';
  if (locationSource === 'upload') {
    const addrInput = document.getElementById('uploadAddrInput');
    location = (addrInput && addrInput.value.trim()) || (profile && profile.homeAddress) || '';
  } else if (locationAddr) {
    location = locationAddr;
  } else if (userLocation) {
    location = `${userLocation.lat.toFixed(5)}, ${userLocation.lng.toFixed(5)}`;
  }

  // ── Serialize images → base64 thumbnails for sessionStorage ──
  const sendBtn = document.getElementById('sendBtn');
  if (sendBtn) { sendBtn.disabled = true; sendBtn.textContent = '⏳ Preparing…'; }

  let thumbnails = [];
  try {
    thumbnails = await Promise.all(
      images.map(file => fileToDataURI(file))
    );
  } catch(e) { thumbnails = []; }

  // ── Serialize audio blob → base64 ──
  if (selectedAudio) {
    try {
      const audioB64 = await blobToBase64(selectedAudio);
      sessionStorage.setItem('tampines_pending_audio', audioB64);
    } catch(e) { sessionStorage.removeItem('tampines_pending_audio'); }
  } else {
    sessionStorage.removeItem('tampines_pending_audio');
  }

  // ── Save pending report metadata ──
  const pendingReport = {
    thumbnails,
    location,
    locationSource,
    hasAudio: !!selectedAudio,
    imageCount: images.length,
    preLabels: [],
  };
  sessionStorage.setItem('tampines_pending_report', JSON.stringify(pendingReport));

  // ── Navigate to confirmation page ──
  window.location.href = '/confirm.html';
}

// Helpers
function fileToDataURI(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload  = e => resolve(e.target.result);
    reader.onerror = reject;
    reader.readAsDataURL(file);
  });
}
function blobToBase64(blob) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload  = e => resolve(e.target.result.split(',')[1]);
    reader.onerror = reject;
    reader.readAsDataURL(blob);
  });
}

function setLoadingStep(n) {
  for(let i=1;i<=4;i++){
    const el=document.getElementById('ls'+i);
    if(el) el.className='ls'+(i<=n?' active':'');
  }
}

async function submitClarification(skip=false) {
  document.getElementById('clarifModal').classList.remove('show');
  const answer = skip ? '' : (document.getElementById('clarifAnswer').value.trim());
  if (pendingFormData && answer) pendingFormData.append('extra_context', answer);
  document.getElementById('loadingScreen').classList.add('show');
  setLoadingStep(3);
  try {
    const res  = await fetch('/analyze', { method:'POST', body: pendingFormData });
    const data = await res.json();
    if (data.error) throw new Error(data.error);
    showSuccess(data);
  } catch(err) {
    document.getElementById('loadingScreen').classList.remove('show');
    showError(err.message);
  }
}

// ── AGENCY CATEGORY → ICON ──
const AGENCY_ICONS = {
  cleanliness:'🗑️', structural:'🔧', electrical:'⚡',
  water:'💧', safety:'⚠️', noise:'🔊',
  pest:'🐀', vehicles:'🚗', greenery:'🌿', general:'📋'
};

// ── SUCCESS ──
function showSuccess(data) {
  const analysis = data.analysis || {};
  const routes   = data.routes   || [];

  const priority = (analysis.priority || 'LOW').toUpperCase();
  const header   = document.getElementById('successHeader');
  const icon     = document.getElementById('successIcon');
  const headline = document.getElementById('successHeadline');
  if (priority === 'CRITICAL') {
    header.style.background = '#dc2626';
    icon.textContent = '🚨';
    headline.textContent = 'CRITICAL — Call 995 Now!';
  } else if (priority === 'HIGH') {
    header.style.background = '#c2410c';
    icon.textContent = '⚠️';
    headline.textContent = 'High Priority — Agencies Notified!';
  } else {
    header.style.background = 'var(--green)';
    icon.textContent = '✅';
    headline.textContent = 'Report Sent!';
  }

  document.getElementById('successTime').textContent =
    'Submitted ' + new Date().toLocaleString('en-SG');
  document.getElementById('residentMsg').textContent =
    analysis.resident_message || 'Your report has been received. We will attend to it shortly.';

  const chip = document.getElementById('priorityVal');
  chip.textContent = priority;
  chip.className   = 'priority-chip ' + priority.toLowerCase();

  // Safety card
  const safetyCard  = document.getElementById('safetyCard');
  const safetySteps = document.getElementById('safetySteps');
  const safetyTitle = document.getElementById('safetyCardTitle');
  safetySteps.innerHTML = '';
  if (priority === 'CRITICAL' || priority === 'HIGH') {
    safetyCard.classList.add('show');
    if (priority === 'CRITICAL') {
      safetyCard.classList.add('critical-card');
      safetyTitle.textContent = '🚨 CALL 995 IMMEDIATELY — Then:';
      ['Evacuate the area immediately','Do not re-enter','Await SCDF instructions'].forEach(s => {
        const d = document.createElement('div'); d.className='safety-step'; d.textContent='• '+s; safetySteps.appendChild(d);
      });
    } else {
      safetyCard.classList.remove('critical-card');
      safetyTitle.textContent = '👉 What to Do Now';
      ['Do not touch exposed wires or wet switches','Keep children away from the area',
       'If flooding, move valuables higher','If sparks appear, call 995 immediately'].forEach(s => {
        const d = document.createElement('div'); d.className='safety-step'; d.textContent='• '+s; safetySteps.appendChild(d);
      });
    }
  } else {
    safetyCard.classList.remove('show');
  }

  // Agency list
  const agencyList = document.getElementById('agencyList');
  agencyList.innerHTML = '';
  if (routes.length > 0) {
    routes.forEach(route => {
      const cat = route.category || 'general';
      const labelsStr = (route.labels_covered||[]).map(l=>l.replace(/_/g,' ')).join(', ');
      const row = document.createElement('div');
      row.className = 'agency-row';
      row.innerHTML = `
        <div class="agency-icon-box ${cat}">${AGENCY_ICONS[cat]||'📋'}</div>
        <div style="flex:1;min-width:0;">
          <div class="agency-name">${route.agency}</div>
          <div class="agency-labels">${labelsStr}</div>
          <div class="agency-sla">⏱ Response within ${route.sla}</div>
        </div>
        <div class="agency-check">✅</div>`;
      agencyList.appendChild(row);
    });
  } else {
    agencyList.innerHTML = '<div class="agency-row"><div class="agency-name">Town Council</div></div>';
  }

  document.getElementById('caseIdVal').textContent = data.case_id || '—';

  const locCard = document.getElementById('locationCard');
  const locVal  = document.getElementById('locationVal');
  locCard.style.display = 'block';
  if (data.location) { locVal.textContent = '📍 ' + data.location; }
  else { locVal.textContent = '⚠️ Location not detected — state your block when speaking.'; locVal.style.color='var(--red)'; }

  const txCard = document.getElementById('transcriptCard');
  const txVal  = document.getElementById('transcriptVal');
  txCard.style.display = 'block';
  txVal.textContent = data.transcript ? '"' + data.transcript + '"' : 'No voice recorded.';
  if (!data.transcript) txVal.style.color = 'var(--muted)';

  const waCard = document.getElementById('whatsappCard');
  const waVal  = document.getElementById('whatsappVal');
  if (userProfile && userProfile.phone) {
    waCard.style.display = 'block';
    const waOk = data.dispatch && data.dispatch.whatsapp_sent;
    if (waOk) {
      waVal.textContent = '✅ WhatsApp confirmation sent to ' + userProfile.phone;
      waVal.style.color = '';
    } else if (!data.dispatch) {
      waVal.textContent = '⚠️ WhatsApp not sent — no report to confirm.';
      waVal.style.color = 'var(--red)';
    } else {
      waVal.style.color = 'var(--red)';
      waVal.innerHTML =
        '❌ WhatsApp delivery failed for ' + userProfile.phone +
        '.<br><small>Check that your number joined the Twilio sandbox ' +
        'by sending <b>join &lt;sandbox-word&gt;</b> to +1 415 523 8886, ' +
        'or verify TWILIO_FROM_PHONE in your .env.</small>';
    }
  } else { waCard.style.display = 'none'; }

  // ── Save to history ──
  if (typeof window.saveToHistory === 'function') {
    const labelsSummary = (analysis.final_labels || [])
      .map(l => l.replace(/_/g, ' ')).join(', ');
    const summaryText = analysis.case_summary
      || analysis.resident_message
      || (labelsSummary ? 'Issues reported: ' + labelsSummary : null)
      || 'Report submitted';

    const histEntry = {
      caseId:     data.case_id || '—',
      priority:   (analysis.priority || 'LOW').toUpperCase(),
      summary:    summaryText,
      agencies:   (data.routes || []).map(r => r.agency).join(' | '),
      location:   data.location || locationAddr || '',
      transcript: data.transcript || '',
      date:       new Date().toLocaleString('en-SG'),
      thumbnail:  null
    };

    const firstImg = (selectedImages || []).find(Boolean);
    if (firstImg) {
      const reader = new FileReader();
      reader.onload = function(e) {
        const imgEl = new Image();
        imgEl.onload = function() {
          const MAX = 1200;
          const scale = Math.min(1, MAX / Math.max(imgEl.width, imgEl.height));
          const canvas = document.createElement('canvas');
          canvas.width  = Math.round(imgEl.width  * scale);
          canvas.height = Math.round(imgEl.height * scale);
          canvas.getContext('2d').drawImage(imgEl, 0, 0, canvas.width, canvas.height);
          histEntry.thumbnail = canvas.toDataURL('image/jpeg', 0.92);
          window.saveToHistory(histEntry);
        };
        imgEl.src = e.target.result;
      };
      reader.readAsDataURL(firstImg);
    } else {
      // Coming from confirm.html redirect — use thumbnail embedded in data
      if (data._thumbnail) histEntry.thumbnail = data._thumbnail;
      window.saveToHistory(histEntry);
    }
  }

  document.getElementById('loadingScreen').classList.remove('show');
  document.getElementById('successScreen').classList.add('show');
}

// ── RESET ──
function resetApp() {
  selectedImages=[]; selectedAudio=null; selectedVideo=null;
  pendingFormData = null;
  locationSource = null;
  document.getElementById('uploadAddrStrip').style.display = 'none';
  document.getElementById('uploadAddrInput').value = '';
  if(isRecording) stopRecording();
  clearAllMedia();

  const sb = document.getElementById('speakBtn');
  sb.className = 'act-btn act-speak';
  document.getElementById('speakRing').innerHTML = '<svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="#ffffff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 1a3 3 0 00-3 3v8a3 3 0 006 0V4a3 3 0 00-3-3z"/><path d="M19 10v2a7 7 0 01-14 0v-2"/><line x1="12" y1="19" x2="12" y2="23"/><line x1="8" y1="23" x2="16" y2="23"/></svg>';
  document.getElementById('speakTitle').textContent    = 'Speak';
  document.getElementById('speakSub').textContent      = 'Voice report';
  document.getElementById('speakBadge').textContent    = 'Rec';
  const cb = document.getElementById('btnCamera');
  cb.classList.remove('done');
  const camBadgeR = document.getElementById('cameraBadge');
  if (camBadgeR) camBadgeR.textContent = 'Snap';
  const ub = document.getElementById('btnUpload');
  ub.classList.remove('done');
  const upBadgeR = document.getElementById('uploadBadge');
  if (upBadgeR) upBadgeR.textContent = 'Gallery';
  const vb = document.getElementById('btnVideo');
  if (vb) vb.classList.remove('done');
  const vt = document.getElementById('videoTitle');
  if (vt) vt.textContent = 'Take Video';
  document.getElementById('waveform').classList.remove('show');
  document.getElementById('speakTimer').style.display  = 'none';
  document.getElementById('voicePreview').classList.remove('show');
  document.getElementById('voicePlayer').src           = '';

  document.getElementById('successScreen').classList.remove('show');
  document.getElementById('successHeader').style.background = '';
  document.getElementById('locationCard').style.display   = 'none';
  document.getElementById('transcriptCard').style.display = 'none';
  document.getElementById('whatsappCard').style.display   = 'none';
  document.getElementById('locationVal').style.color      = '';
  document.getElementById('transcriptVal').style.color    = '';
  document.getElementById('safetyCard').classList.remove('show','critical-card');
  document.getElementById('agencyList').innerHTML         = '';

  startGPS();
}

// ── ERROR ──
function showError(msg) {
  const box = document.getElementById('errorBox');
  if (!box) return;
  box.textContent = '⚠️ ' + msg;
  box.style.display = 'block';
  setTimeout(() => { box.style.display = 'none'; }, 6000);
}
// ── Show success if returning from confirm page ──
(function checkReturnSuccess() {
  const raw = sessionStorage.getItem('tampines_success');
  if (!raw) return;
  sessionStorage.removeItem('tampines_success');
  try {
    const data = JSON.parse(raw);
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', () => showSuccess(data));
    } else {
      setTimeout(() => showSuccess(data), 100);
    }
  } catch(e) {}
})();

// ── Restore pending report when user presses "Go back" from confirm page ──
async function restoreFromConfirmBack() {
  const raw = sessionStorage.getItem('tampines_pending_report');
  if (!raw) return;

  let pending;
  try { pending = JSON.parse(raw); } catch(e) { return; }

  // ── Restore thumbnails as display-only image previews ──
  const thumbs = pending.thumbnails || [];
  if (thumbs.length) {
    for (let i = 0; i < thumbs.length; i++) {
      const dataURI = thumbs[i];
      // Convert base64 dataURI back to a File-like Blob and add to gallery
      try {
        const res  = await fetch(dataURI);
        const blob = await res.blob();
        const file = new File([blob], `restored_photo_${i+1}.jpg`, { type: blob.type || 'image/jpeg' });
        addImageToGallery(file);
      } catch(e) { /* skip broken thumb */ }
    }
    document.getElementById('btnUpload').classList.add('done');
    document.getElementById('btnCamera').classList.add('done');
    const upBadge = document.getElementById('uploadBadge');
    if (upBadge) upBadge.textContent = '✓ Added';
  }

  // ── Restore audio ──
  const audioB64 = sessionStorage.getItem('tampines_pending_audio');
  if (audioB64 && pending.hasAudio) {
    try {
      const byteStr = atob(audioB64);
      const arr = new Uint8Array(byteStr.length);
      for (let i = 0; i < byteStr.length; i++) arr[i] = byteStr.charCodeAt(i);
      const blob = new Blob([arr], { type: 'audio/webm' });
      selectedAudio = blob;

      const url    = URL.createObjectURL(blob);
      const player = document.getElementById('voicePlayer');
      if (player) { player.src = url; }

      const preview = document.getElementById('voicePreview');
      if (preview) preview.classList.add('show');

      const speakBtn = document.getElementById('speakBtn');
      if (speakBtn) speakBtn.classList.add('done');
      const speakTitle = document.getElementById('speakTitle');
      if (speakTitle) speakTitle.textContent = 'Recorded';
      const speakSub = document.getElementById('speakSub');
      if (speakSub) speakSub.textContent = 'Tap to redo';
      const speakBadge = document.getElementById('speakBadge');
      if (speakBadge) speakBadge.textContent = '✓';
      const speakRing = document.getElementById('speakRing');
      if (speakRing) speakRing.innerHTML = '<svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="#ffffff" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>';
    } catch(e) { /* skip */ }
  }

  // ── Restore location ──
  if (pending.location) {
    locationAddr   = pending.location;
    locationSource = pending.locationSource || 'upload';
    if (locationSource === 'upload') {
      const strip = document.getElementById('uploadAddrStrip');
      const addrInput = document.getElementById('uploadAddrInput');
      if (strip)     strip.style.display = 'block';
      if (addrInput) addrInput.value     = pending.location;
    } else {
      setGPS('found', '📍 ' + pending.location, true);
    }
  }
}

// Run restore on DOMContentLoaded (only if NOT showing success)
document.addEventListener('DOMContentLoaded', () => {
  if (!sessionStorage.getItem('tampines_success') && sessionStorage.getItem('tampines_came_back')) {
    sessionStorage.removeItem('tampines_came_back');
    restoreFromConfirmBack();
  }
});