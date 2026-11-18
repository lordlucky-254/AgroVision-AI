const scanButton = document.querySelector('#scan');
const result = document.querySelector('#result');
const modelStatus = document.querySelector('#model-status');
const historyList = document.querySelector('#history-list');
const historyKey = 'agrovision.scan-history.v1';
const maxHistory = 20;

function readHistory() {
  const saved = localStorage.getItem(historyKey);
  if (!saved) return [];
  const parsed = JSON.parse(saved);
  return Array.isArray(parsed) ? parsed.slice(0, maxHistory) : [];
}

function renderHistory() {
  historyList.replaceChildren();
  try {
    for (const scan of readHistory()) {
      const item = document.createElement('li');
      const title = document.createElement('strong');
      title.textContent = scan.diagnosis;
      const details = document.createElement('span');
      details.textContent = `${scan.crop} · ${new Date(scan.created_at).toLocaleString()}`;
      item.append(title, details);
      historyList.append(item);
    }
  } catch {
    const item = document.createElement('li');
    item.textContent = 'Local scan history is unavailable in this browser.';
    historyList.append(item);
  }
}

function saveHistory(scan) {
  const previous = readHistory();
  const summary = {
    id: scan.id,
    created_at: scan.created_at,
    crop: scan.crop,
    diagnosis: scan.diagnosis,
  };
  localStorage.setItem(historyKey, JSON.stringify([summary, ...previous].slice(0, maxHistory)));
  renderHistory();
}

async function loadModelStatus() {
  try {
    const response = await fetch('/api/v1/model');
    if (!response.ok) throw new Error('Model status unavailable.');
    const status = await response.json();
    modelStatus.textContent = status.ready
      ? `Model ready: ${status.model}. Predictions still require expert confirmation.`
      : 'No trained model is installed. The scanner will not produce a disease prediction.';
    modelStatus.classList.toggle('ready', status.ready);
  } catch (error) {
    modelStatus.textContent = `Could not check model availability: ${error.message}`;
  }
}

scanButton.addEventListener('click', async () => {
  const image = document.querySelector('#image').files[0];
  if (!image) {
    result.textContent = 'Choose a photo first.';
    return;
  }
  if (image.size > 10 * 1024 * 1024) {
    result.textContent = 'This image is larger than 10 MB. Choose a smaller photo.';
    return;
  }

  const form = new FormData();
  form.append('image', image);
  form.append('crop', document.querySelector('#crop').value);
  result.textContent = 'Screening…';
  scanButton.disabled = true;
  try {
    const response = await fetch('/api/v1/diagnoses', { method: 'POST', body: form });
    const body = await response.json();
    if (!response.ok) {
      result.textContent = body.detail || 'The image could not be uploaded.';
      return;
    }

    const candidates = Array.isArray(body.candidates)
      ? body.candidates.map((candidate) =>
        `${candidate.label} — model score ${(candidate.score * 100).toFixed(1)}% (uncalibrated)`)
      : [];
    result.textContent = [
      body.diagnosis,
      ...candidates,
      body.next_steps,
      body.score_note,
    ].filter(Boolean).join('\n\n');
    try {
      saveHistory(body);
    } catch {
      result.textContent += '\n\nThis scan could not be saved to local browser history.';
    }
  } catch (error) {
    result.textContent = `API unavailable: ${error.message}`;
  } finally {
    scanButton.disabled = false;
  }
});

document.querySelector('#clear-history').addEventListener('click', () => {
  try {
    localStorage.removeItem(historyKey);
    renderHistory();
  } catch {
    modelStatus.textContent = 'Could not clear local history in this browser.';
  }
});

renderHistory();
loadModelStatus();
