(function () {
  'use strict';

  var cameraView = document.getElementById('camera-view');
  var startBtn = document.getElementById('scan-start-btn');
  var statusEl = document.getElementById('scan-status');
  var scanResult = document.getElementById('scan-result');
  var resultIsbn = document.getElementById('result-isbn');
  var saveForm = document.getElementById('save-book-form');
  var lookupResult = document.getElementById('book-lookup-result');
  var lookupError = document.getElementById('lookup-error');
  var saveStatus = document.getElementById('scan-save-status');
  var unsupportedEl = document.getElementById('unsupported-browser');
  var coverPreview = document.getElementById('scan-cover-preview');

  var torchBtn = document.getElementById('scan-torch-btn');
  var manualForm = document.getElementById('manual-isbn-form');
  var manualInput = document.getElementById('manual-isbn-input');
  var manualError = document.getElementById('manual-isbn-error');

  var bookPayload = null;
  var torchOn = false;
  var reader = IsbnReader.create(document.getElementById('scanner-reader'), {
    wasmUrl: document.getElementById('scanner-reader').dataset.wasmUrl,
  });

  var cameraSupported = !!(
    navigator.mediaDevices && navigator.mediaDevices.getUserMedia
  );
  if (!cameraSupported) {
    unsupportedEl.style.display = 'block';
    if (startBtn) startBtn.disabled = true;
  }

  startBtn.addEventListener('click', startScanning);

  function startScanning() {
    startBtn.disabled = true;
    startBtn.textContent = 'Iniciando...';
    statusEl.textContent = '';

    reader
      .start(showResult)
      .then(function (started) {
        if (!started) return;
        cameraView.classList.add('is-scanning');
        startBtn.style.display = 'none';
        statusEl.textContent =
          'Pon el código dentro de la franja, en horizontal y a un palmo.';
        torchOn = false;
        torchBtn.setAttribute('aria-pressed', 'false');
        torchBtn.style.display = reader.hasTorch() ? 'inline-flex' : 'none';
      })
      .catch(function (err) {
        startBtn.disabled = false;
        startBtn.textContent = 'Iniciar cámara';
        statusEl.textContent =
          'Error al acceder a la cámara: ' +
          ((err && err.message) || err || 'Permiso denegado');
      });
  }

  torchBtn.addEventListener('click', function () {
    torchOn = !torchOn;
    reader.setTorch(torchOn).catch(function () {});
    torchBtn.setAttribute('aria-pressed', String(torchOn));
  });

  manualForm.addEventListener('submit', function (e) {
    e.preventDefault();
    var isbn = IsbnReader.toIsbn13(manualInput.value);
    if (!isbn) {
      manualError.textContent =
        'ISBN no válido. Revisa los 10 o 13 dígitos.';
      manualError.style.display = 'block';
      return;
    }
    manualError.style.display = 'none';
    reader.stop().then(function () {
      showResult(isbn);
    });
  });

  function showResult(isbn) {
    statusEl.textContent = '';
    cameraView.classList.remove('is-scanning');
    cameraView.style.display = 'none';
    torchBtn.style.display = 'none';
    manualForm.style.display = 'none';
    manualInput.value = '';

    resultIsbn.textContent = isbn;
    scanResult.style.display = 'block';

    lookupBook(isbn);
  }

  function lookupBook(isbn) {
    lookupResult.innerHTML =
      '<p class="scan-loading">Buscando libro en el catálogo…</p>';
    lookupError.style.display = 'none';
    saveForm.style.display = 'none';
    coverPreview.style.display = 'none';

    // A book already saved (in the collection or in futuras compras) opens
    // its own page, so scanning never overwrites it from this form.
    fetch('/api/collection/' + encodeURIComponent(isbn))
      .then(function (response) {
        if (response.ok) {
          window.location.href = '/book/' + encodeURIComponent(isbn);
          return null;
        }
        return lookupCatalog(isbn);
      })
      .catch(function () {
        return lookupCatalog(isbn);
      });
  }

  function lookupCatalog(isbn) {
    return fetch('/api/books/' + encodeURIComponent(isbn))
      .then(function (response) {
        if (!response.ok) {
          if (response.status === 404) {
            throw new Error('Libro no encontrado para ese ISBN.');
          }
          if (response.status === 502) {
            return response.json().then(function (data) {
              throw new Error(
                data.detail ||
                  'El servicio de catálogo no respondió correctamente.'
              );
            });
          }
          throw new Error('Error del servidor (' + response.status + ').');
        }
        return response.json();
      })
      .then(function (book) {
        bookPayload = book;
        lookupResult.innerHTML = '';
        showSaveForm(book);
      })
      .catch(function (err) {
        lookupResult.innerHTML = '';
        lookupError.textContent = err.message;
        lookupError.style.display = 'block';
      });
  }

  function showSaveForm(book) {
    document.getElementById('scan-title-input').value = book.title || '';
    document.getElementById('scan-authors-input').value = (
      book.authors || []
    ).join(', ');
    document.getElementById('scan-description-area').value =
      book.description || '';
    document.getElementById('scan-status-select').value = 'new';

    if (book.cover_image_url) {
      coverPreview.innerHTML = '';
      var img = document.createElement('img');
      img.src = book.cover_image_url;
      img.alt = 'Portada';
      img.className = 'scan-form__cover-img';
      coverPreview.appendChild(img);
      coverPreview.style.display = 'block';
    } else {
      coverPreview.style.display = 'none';
    }

    saveForm.style.display = 'block';
  }

  function saveScannedBook(statusOverride, triggerBtn) {
    var saveBtn = document.getElementById('scan-save-btn');
    var toBuyBtn = document.getElementById('scan-to-buy-btn');
    var idleLabel = triggerBtn.textContent;
    saveBtn.disabled = true;
    if (toBuyBtn) toBuyBtn.disabled = true;
    triggerBtn.textContent = 'Guardando...';
    saveStatus.textContent = '';
    saveStatus.className = 'save-status-message';

    var isbn = resultIsbn.textContent.trim();
    var title = document.getElementById('scan-title-input').value.trim();
    var authorsRaw = document.getElementById('scan-authors-input').value;
    var authors = authorsRaw
      .split(',')
      .map(function (s) {
        return s.trim();
      })
      .filter(Boolean);
    var status =
      statusOverride || document.getElementById('scan-status-select').value;
    var description =
      document.getElementById('scan-description-area').value.trim() || null;

    var body = {
      isbn_13: isbn,
      title: title,
      authors: authors,
      description: description,
      published_date: bookPayload ? bookPayload.published_date : null,
      cover_image_url: bookPayload ? bookPayload.cover_image_url : null,
      isbn_10: bookPayload ? bookPayload.isbn_10 : null,
      status: status,
    };

    fetch('/api/collection', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    })
      .then(function (response) {
        if (!response.ok) {
          return response.json().then(function (err) {
            throw new Error(err.detail || 'Error al guardar');
          });
        }
        return response.json();
      })
      .then(function () {
        window.location.href = status === 'to_buy' ? '/futuras-compras' : '/';
      })
      .catch(function (err) {
        saveStatus.textContent = err.message;
        saveStatus.className = 'save-status-message is-error';
        saveBtn.disabled = false;
        if (toBuyBtn) toBuyBtn.disabled = false;
        triggerBtn.textContent = idleLabel;
      });
  }

  saveForm.addEventListener('submit', function (e) {
    e.preventDefault();
    saveScannedBook(null, document.getElementById('scan-save-btn'));
  });

  var scanToBuyBtn = document.getElementById('scan-to-buy-btn');
  if (scanToBuyBtn) {
    scanToBuyBtn.addEventListener('click', function () {
      saveScannedBook('to_buy', scanToBuyBtn);
    });
  }

  var anotherBtn = document.getElementById('scan-another-btn');
  if (anotherBtn) {
    anotherBtn.addEventListener('click', resetScanner);
  }

  function resetScanner() {
    reader.stop().then(resetUI);
  }

  function resetUI() {
    scanResult.style.display = 'none';
    cameraView.style.display = 'block';
    manualForm.style.display = '';
    startBtn.style.display = 'inline-flex';
    startBtn.disabled = !cameraSupported;
    startBtn.textContent = 'Iniciar cámara';
    statusEl.textContent = '';
    saveForm.style.display = 'none';
    lookupResult.innerHTML = '';
    lookupError.style.display = 'none';
    saveStatus.textContent = '';
    coverPreview.style.display = 'none';
    bookPayload = null;
  }

  function releaseCamera() {
    reader.stop();
  }
  window.addEventListener('beforeunload', releaseCamera);
  window.addEventListener('pagehide', releaseCamera);
})();
