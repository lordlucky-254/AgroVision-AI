document.querySelector('#scan').addEventListener('click', async () => {
  const image = document.querySelector('#image').files[0];
  const result = document.querySelector('#result');
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
  try {
    const response = await fetch('/api/v1/diagnoses', { method: 'POST', body: form });
    const body = await response.json();
    if (!response.ok) {
      result.textContent = body.detail || 'The image could not be uploaded.';
      return;
    }

    result.textContent = [
      body.diagnosis,
      body.symptoms,
      body.next_steps,
      'A trained image model is not connected yet; no disease prediction was made.',
    ].join('\n\n');
  } catch (error) {
    result.textContent = `API unavailable: ${error.message}`;
  }
});
