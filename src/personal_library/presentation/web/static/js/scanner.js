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

  var bookPayload = null;
  var scanner = null;
  var scanning = false;

  if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
    unsupportedEl.style.display = 'block';
    if (startBtn) startBtn.disabled = true;
    return;
  }

  scanner = new Html5Qrcode('scanner-reader', {
    formatsToSupport: [
      Html5QrcodeSupportedFormats.EAN_13,
      Html5QrcodeSupportedFormats.EAN_8,
      Html5QrcodeSupportedFormats.UPC_A,
      Html5QrcodeSupportedFormats.UPC_E,
    ],
    useBarCodeDetectorIfSupported: false,
    verbose: false,
  });

  startBtn.addEventListener('click', startScanning);

  function startScanning() {
    if (scanning) return;

    startBtn.disabled = true;
    startBtn.textContent = 'Iniciando...';
    statusEl.textContent = '';

    scanner
      .start(
        { facingMode: 'environment' },
        { fps: 10 },
        function (decodedText) {
          if (!scanning) return;
          onBarcodeDetected(decodedText);
        },
        function () {}
      )
      .then(function () {
        scanning = true;
        startBtn.style.display = 'none';
        statusEl.textContent =
          'Apunta la cámara al código de barras del libro...';
      })
      .catch(function (err) {
        startBtn.disabled = false;
        startBtn.textContent = 'Iniciar cámara';
        statusEl.textContent =
          'Error al acceder a la cámara: ' + (err || 'Permiso denegado');
      });
  }

  function onBarcodeDetected(value) {
    scanning = false;

    scanner
      .stop()
      .then(function () {
        showResult(value);
      })
      .catch(function () {
        showResult(value);
      });
  }

  function showResult(value) {
    statusEl.textContent = '';
    cameraView.style.display = 'none';

    resultIsbn.textContent = value;
    scanResult.style.display = 'block';

    lookupBook(value);
  }

  function lookupBook(isbn) {
    lookupResult.innerHTML =
      '<p class="scan-loading">Buscando libro en el catálogo…</p>';
    lookupError.style.display = 'none';
    saveForm.style.display = 'none';
    coverPreview.style.display = 'none';

    fetch('/api/books/' + encodeURIComponent(isbn))
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
      coverPreview.innerHTML =
        '<img src="' +
        book.cover_image_url +
        '" alt="Portada" class="scan-form__cover-img">';
      coverPreview.style.display = 'block';
    } else {
      coverPreview.style.display = 'none';
    }

    saveForm.style.display = 'block';
  }

  saveForm.addEventListener('submit', function (e) {
    e.preventDefault();

    var saveBtn = document.getElementById('scan-save-btn');
    saveBtn.disabled = true;
    saveBtn.textContent = 'Guardando...';
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
    var status = document.getElementById('scan-status-select').value;
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
        window.location.href = '/';
      })
      .catch(function (err) {
        saveStatus.textContent = err.message;
        saveStatus.className = 'save-status-message is-error';
        saveBtn.disabled = false;
        saveBtn.textContent = 'Guardar en mi colección';
      });
  });

  var anotherBtn = document.getElementById('scan-another-btn');
  if (anotherBtn) {
    anotherBtn.addEventListener('click', resetScanner);
  }

  function resetScanner() {
    scanning = false;
    scanner.stop().catch(function () {});

    scanResult.style.display = 'none';
    cameraView.style.display = 'block';
    startBtn.style.display = 'inline-flex';
    startBtn.disabled = false;
    startBtn.textContent = 'Iniciar cámara';
    statusEl.textContent = '';
    saveForm.style.display = 'none';
    lookupResult.innerHTML = '';
    lookupError.style.display = 'none';
    saveStatus.textContent = '';
    coverPreview.style.display = 'none';
    bookPayload = null;
  }
})();
