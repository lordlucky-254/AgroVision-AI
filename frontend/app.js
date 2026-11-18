document.querySelector('#scan').addEventListener('click', async () => {
  const image = document.querySelector('#image').files[0];
  const result = document.querySelector('#result');
  if (!image) { result.textContent = 'Choose a photo first.'; return; }
  const form = new FormData(); form.append('image', image); form.append('crop', document.querySelector('#crop').value);
  result.textContent = 'Screening…';
  try { const response = await fetch('http://127.0.0.1:8000/api/v1/diagnoses', { method: 'POST', body: form }); result.textContent = JSON.stringify(await response.json(), null, 2); }
  catch (error) { result.textContent = `API unavailable: ${error.message}`; }
});
