/*
 * Lector de ISBN: reads book barcodes from the camera and only ever reports
 * valid ISBN-13 values.
 *
 *   var reader = IsbnReader.create(containerEl, { wasmUrl: '/static/...' });
 *   reader.start(function (isbn13) { ... })  // Promise<boolean>: true once
 *                                            // the camera is running, false
 *                                            // if stop() came first. The
 *                                            // callback fires once, after
 *                                            // the camera is released
 *   reader.stop()                            // Promise
 *   reader.hasTorch() / reader.setTorch(on)
 *
 *   IsbnReader.toIsbn13('84-376-0494-X')     // '9788437604947' or null
 *
 * Decoding uses the browser's native BarcodeDetector when it supports EAN-13
 * (Android / Chrome) and otherwise the ZXing-C++ WebAssembly ponyfill from
 * vendor/barcode-detector (iOS Safari, Firefox). Only a horizontal band in
 * the middle of the frame is decoded; the page draws a matching guide.
 */
(function () {
  'use strict';

  // Region of the video frame that is decoded, as fractions of its size.
  // Must match .scan-guide in styles.css.
  var BAND = { left: 0.08, top: 0.3, width: 0.84, height: 0.4 };

  function isbn13CheckDigit(first12) {
    var sum = 0;
    for (var i = 0; i < 12; i++) {
      sum += Number(first12[i]) * (i % 2 === 0 ? 1 : 3);
    }
    return String((10 - (sum % 10)) % 10);
  }

  function isValidIsbn13(digits) {
    return (
      /^97[89]\d{10}$/.test(digits) &&
      isbn13CheckDigit(digits.slice(0, 12)) === digits[12]
    );
  }

  function isValidIsbn10(chars) {
    if (!/^\d{9}[\dX]$/.test(chars)) return false;
    var sum = 0;
    for (var i = 0; i < 10; i++) {
      var value = chars[i] === 'X' ? 10 : Number(chars[i]);
      sum += value * (10 - i);
    }
    return sum % 11 === 0;
  }

  /** Normalizes an ISBN-10 or ISBN-13 to ISBN-13; null when invalid. */
  function toIsbn13(text) {
    var clean = String(text || '')
      .toUpperCase()
      .replace(/[\s-]/g, '');
    if (isValidIsbn13(clean)) return clean;
    if (isValidIsbn10(clean)) {
      var first12 = '978' + clean.slice(0, 9);
      return first12 + isbn13CheckDigit(first12);
    }
    return null;
  }

  function createDetector(wasmUrl) {
    var Native = window.BarcodeDetector;
    var nativeSupportsEan = Native
      ? Native.getSupportedFormats()
          .then(function (formats) {
            return formats.indexOf('ean_13') !== -1;
          })
          .catch(function () {
            return false;
          })
      : Promise.resolve(false);

    return nativeSupportsEan.then(function (useNative) {
      if (useNative) return new Native({ formats: ['ean_13'] });

      var api = window.BarcodeDetectionAPI;
      api.prepareZXingModule({
        overrides: {
          locateFile: function (path, prefix) {
            return path.endsWith('.wasm') ? wasmUrl : prefix + path;
          },
        },
        fireImmediately: true,
      });
      return new api.BarcodeDetector({ formats: ['ean_13'] });
    });
  }

  function openCamera() {
    return navigator.mediaDevices.getUserMedia({
      audio: false,
      video: {
        facingMode: { ideal: 'environment' },
        // More pixels per bar: the default 640x480 is too coarse for EAN-13.
        width: { ideal: 1920 },
        height: { ideal: 1080 },
      },
    });
  }

  function improveFocus(track) {
    var caps = track.getCapabilities ? track.getCapabilities() : {};
    if (caps.focusMode && caps.focusMode.indexOf('continuous') !== -1) {
      return track
        .applyConstraints({ advanced: [{ focusMode: 'continuous' }] })
        .catch(function () {});
    }
    return Promise.resolve();
  }

  function create(container, options) {
    var wasmUrl = options.wasmUrl;
    var detectorPromise = null;
    var stream = null;
    var track = null;
    var video = null;
    var canvas = document.createElement('canvas');
    var ctx = canvas.getContext('2d', { willReadFrequently: true });
    var running = false;
    var session = 0;

    function detector() {
      if (!detectorPromise) detectorPromise = createDetector(wasmUrl);
      return detectorPromise;
    }

    function grabBand() {
      var vw = video.videoWidth;
      var vh = video.videoHeight;
      if (!vw || !vh) return null;
      var sx = Math.round(vw * BAND.left);
      var sy = Math.round(vh * BAND.top);
      var sw = Math.round(vw * BAND.width);
      var sh = Math.round(vh * BAND.height);
      if (canvas.width !== sw) canvas.width = sw;
      if (canvas.height !== sh) canvas.height = sh;
      ctx.drawImage(video, sx, sy, sw, sh, 0, 0, sw, sh);
      return canvas;
    }

    function firstIsbn(barcodes) {
      for (var i = 0; i < barcodes.length; i++) {
        var isbn = toIsbn13(barcodes[i].rawValue);
        if (isbn) return isbn;
      }
      return null;
    }

    function loop(det, mySession, onIsbn) {
      if (!running || mySession !== session) return;
      var frame = video.readyState >= 2 ? grabBand() : null;
      var pending = frame ? det.detect(frame) : Promise.resolve([]);
      pending
        .catch(function () {
          return [];
        })
        .then(function (barcodes) {
          if (!running || mySession !== session) return;
          var isbn = firstIsbn(barcodes);
          if (isbn) {
            stop().then(function () {
              onIsbn(isbn);
            });
            return;
          }
          requestAnimationFrame(function () {
            loop(det, mySession, onIsbn);
          });
        });
    }

    function start(onIsbn) {
      if (running) return Promise.resolve(true);
      var mySession = ++session;
      var det = detector();

      return openCamera()
        .then(function (s) {
          if (mySession !== session) {
            s.getTracks().forEach(function (t) {
              t.stop();
            });
            return null;
          }
          stream = s;
          track = s.getVideoTracks()[0];
          video = document.createElement('video');
          video.setAttribute('playsinline', '');
          video.muted = true;
          video.srcObject = s;
          container.innerHTML = '';
          container.appendChild(video);
          return Promise.all([video.play(), improveFocus(track), det]);
        })
        .then(function (results) {
          if (!results || mySession !== session) return false;
          running = true;
          loop(results[2], mySession, onIsbn);
          return true;
        })
        .catch(function (err) {
          if (mySession === session) releaseStream();
          throw err;
        });
    }

    function releaseStream() {
      if (stream) {
        stream.getTracks().forEach(function (t) {
          t.stop();
        });
      }
      stream = null;
      track = null;
      if (video) {
        video.srcObject = null;
        video.remove();
      }
      video = null;
    }

    function stop() {
      running = false;
      session++;
      releaseStream();
      return Promise.resolve();
    }

    function hasTorch() {
      var caps = track && track.getCapabilities ? track.getCapabilities() : {};
      return !!caps.torch;
    }

    function setTorch(on) {
      if (!hasTorch()) return Promise.resolve();
      return track.applyConstraints({ advanced: [{ torch: !!on }] });
    }

    return {
      start: start,
      stop: stop,
      hasTorch: hasTorch,
      setTorch: setTorch,
    };
  }

  window.IsbnReader = { create: create, toIsbn13: toIsbn13 };
})();
