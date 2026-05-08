const sourceVideo = document.getElementById("sourceVideo");
const sketchCanvas = document.getElementById("sketchCanvas");
const statusText = document.getElementById("statusText");
const latencyText = document.getElementById("latencyText");
const startBtn = document.getElementById("startBtn");
const stopBtn = document.getElementById("stopBtn");
const captureBtn = document.getElementById("captureBtn");
const captureResult = document.getElementById("captureResult");
const savedImage = document.getElementById("savedImage");

const sketchCtx = sketchCanvas.getContext("2d");
const sendCanvas = document.createElement("canvas");
const sendCtx = sendCanvas.getContext("2d");

let mediaStream = null;
let running = false;
let requestInFlight = false;
let latestSketchDataUrl = null;
let intervalId = null;

const TARGET_WIDTH = 640;
const TARGET_HEIGHT = 480;
const FRAME_INTERVAL_MS = 120;

sendCanvas.width = TARGET_WIDTH;
sendCanvas.height = TARGET_HEIGHT;

function setStatus(message, isError = false) {
  statusText.textContent = message;
  statusText.style.color = isError ? "#ff6f91" : "#a7b4d6";
}

async function startCamera() {
  try {
    mediaStream = await navigator.mediaDevices.getUserMedia({
      video: { width: TARGET_WIDTH, height: TARGET_HEIGHT, facingMode: "user" },
      audio: false,
    });
    sourceVideo.srcObject = mediaStream;
    await sourceVideo.play();
    running = true;
    startBtn.disabled = true;
    stopBtn.disabled = false;
    captureBtn.disabled = false;
    setStatus("Camera started. Streaming sketch...");
    startFrameLoop();
  } catch (_error) {
    setStatus("Could not access webcam. Check camera permissions.", true);
  }
}

function stopCamera() {
  running = false;
  requestInFlight = false;
  if (intervalId) {
    clearInterval(intervalId);
    intervalId = null;
  }
  if (mediaStream) {
    mediaStream.getTracks().forEach((track) => track.stop());
  }
  mediaStream = null;
  startBtn.disabled = false;
  stopBtn.disabled = true;
  captureBtn.disabled = true;
  setStatus("Camera stopped.");
}

async function processFrame() {
  if (!running || requestInFlight || !mediaStream) {
    return;
  }

  requestInFlight = true;
  const startedAt = performance.now();

  try {
    sendCtx.drawImage(sourceVideo, 0, 0, TARGET_WIDTH, TARGET_HEIGHT);
    const dataUrl = sendCanvas.toDataURL("image/jpeg", 0.75);
    const response = await fetch("/api/sketch/frame/", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ frame: dataUrl, quality: 72 }),
    });

    const payload = await response.json();
    if (!response.ok) {
      throw new Error(payload.error || "Frame processing failed.");
    }

    const img = new Image();
    img.src = payload.image;
    await img.decode();
    sketchCanvas.width = payload.width || TARGET_WIDTH;
    sketchCanvas.height = payload.height || TARGET_HEIGHT;
    sketchCtx.drawImage(img, 0, 0, sketchCanvas.width, sketchCanvas.height);
    latestSketchDataUrl = payload.image;
    latencyText.textContent = `Latency: ${Math.round(performance.now() - startedAt)} ms`;
  } catch (_error) {
    setStatus("Live processing error. Retrying...", true);
  } finally {
    requestInFlight = false;
  }
}

function startFrameLoop() {
  if (intervalId) {
    clearInterval(intervalId);
  }
  intervalId = setInterval(processFrame, FRAME_INTERVAL_MS);
}

async function captureSelfie() {
  if (!latestSketchDataUrl) {
    setStatus("No sketch frame available yet. Try again in a moment.", true);
    return;
  }

  try {
    captureBtn.disabled = true;
    const response = await fetch("/api/capture/selfie/", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ image: latestSketchDataUrl }),
    });
    const payload = await response.json();
    if (!response.ok) {
      throw new Error(payload.error || "Failed to save selfie.");
    }

    savedImage.src = payload.image_url || payload.absolute_image_url;
    captureResult.classList.remove("hidden");
    setStatus("Sketch selfie saved.");
  } catch (error) {
    setStatus(
      `Unable to save selfie right now. ${error.message || ""}`.trim(),
      true
    );
  } finally {
    if (running) {
      captureBtn.disabled = false;
    }
  }
}

startBtn.addEventListener("click", startCamera);
stopBtn.addEventListener("click", stopCamera);
captureBtn.addEventListener("click", captureSelfie);
