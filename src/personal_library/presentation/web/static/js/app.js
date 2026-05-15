(function () {
  'use strict';

  const STORAGE_PREFIX = 'pl_';

  function getBookData(isbn, key) {
    try {
      const raw = localStorage.getItem(`${STORAGE_PREFIX}${isbn}_${key}`);
      return raw ? JSON.parse(raw) : null;
    } catch {
      return null;
    }
  }

  function setBookData(isbn, key, value) {
    localStorage.setItem(`${STORAGE_PREFIX}${isbn}_${key}`, JSON.stringify(value));
  }

  /* ─────────────── STAR RATING ─────────────── */

  function initRating(isbn) {
    const container = document.getElementById('star-container');
    const valueDisplay = document.getElementById('rating-value');
    if (!container || !valueDisplay) return;

    let currentRating = getBookData(isbn, 'rating') || 0;

    function renderStars(rating) {
      const stars = container.querySelectorAll('.star-rating__star');
      stars.forEach(function (star) {
        const idx = parseInt(star.dataset.star, 10);
        star.classList.remove('is-full', 'is-half');

        if (rating >= idx) {
          star.classList.add('is-full');
        } else if (rating >= idx - 0.5) {
          star.classList.add('is-half');
        }
      });

      valueDisplay.textContent = rating > 0 ? rating.toFixed(1) : '—';
    }

    function getRatingFromEvent(star, e) {
      const rect = star.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const idx = parseInt(star.dataset.star, 10);
      return x < rect.width / 2 ? idx - 0.5 : idx;
    }

    container.addEventListener('mousemove', function (e) {
      const star = e.target.closest('.star-rating__star');
      if (!star) return;
      const hoverRating = getRatingFromEvent(star, e);
      renderStars(hoverRating);
    });

    container.addEventListener('mouseleave', function () {
      renderStars(currentRating);
    });

    container.addEventListener('click', function (e) {
      const star = e.target.closest('.star-rating__star');
      if (!star) return;
      const newRating = getRatingFromEvent(star, e);
      currentRating = currentRating === newRating ? 0 : newRating;
      setBookData(isbn, 'rating', currentRating);
      renderStars(currentRating);
    });

    renderStars(currentRating);
  }

  /* ─────────────── TAGS ─────────────── */

  function initTags(isbn) {
    const container = document.getElementById('tags-container');
    const form = document.getElementById('tag-add-form');
    const input = document.getElementById('tag-input');
    const addBtn = document.getElementById('tag-add-btn');
    if (!container || !form || !input || !addBtn) return;

    let tags = getBookData(isbn, 'tags') || [];

    function makeTagRemoveSvg() {
      var svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
      svg.setAttribute('width', '10');
      svg.setAttribute('height', '10');
      svg.setAttribute('viewBox', '0 0 24 24');
      svg.setAttribute('fill', 'none');
      svg.setAttribute('stroke', 'currentColor');
      svg.setAttribute('stroke-width', '3');
      svg.setAttribute('stroke-linecap', 'round');
      var l1 = document.createElementNS('http://www.w3.org/2000/svg', 'line');
      l1.setAttribute('x1', '18'); l1.setAttribute('y1', '6');
      l1.setAttribute('x2', '6'); l1.setAttribute('y2', '18');
      svg.appendChild(l1);
      var l2 = document.createElementNS('http://www.w3.org/2000/svg', 'line');
      l2.setAttribute('x1', '6'); l2.setAttribute('y1', '6');
      l2.setAttribute('x2', '18'); l2.setAttribute('y2', '18');
      svg.appendChild(l2);
      return svg;
    }

    function renderTags() {
      container.querySelectorAll('.tag').forEach(function (el) { el.remove(); });

      tags.forEach(function (tagText, i) {
        var tag = document.createElement('span');
        tag.className = 'tag';
        tag.textContent = tagText;

        var btn = document.createElement('button');
        btn.type = 'button';
        btn.className = 'tag__remove';
        btn.dataset.idx = String(i);
        btn.title = 'Eliminar';
        btn.appendChild(makeTagRemoveSvg());

        tag.appendChild(btn);
        container.insertBefore(tag, form);
      });
    }

    function addTag(text) {
      const clean = text.trim();
      if (!clean || tags.includes(clean)) return;
      tags.push(clean);
      setBookData(isbn, 'tags', tags);
      renderTags();
    }

    function removeTag(idx) {
      tags.splice(idx, 1);
      setBookData(isbn, 'tags', tags);
      renderTags();
    }

    container.addEventListener('click', function (e) {
      const removeBtn = e.target.closest('.tag__remove');
      if (removeBtn) {
        removeTag(parseInt(removeBtn.dataset.idx, 10));
      }
    });

    addBtn.addEventListener('click', function () {
      if (form.classList.contains('is-open')) {
        addTag(input.value);
        input.value = '';
        form.classList.remove('is-open');
      } else {
        form.classList.add('is-open');
        input.focus();
      }
    });

    input.addEventListener('keydown', function (e) {
      if (e.key === 'Enter') {
        e.preventDefault();
        addTag(input.value);
        input.value = '';
        input.focus();
      } else if (e.key === 'Escape') {
        input.value = '';
        form.classList.remove('is-open');
      }
    });

    renderTags();
  }

  /* ─────────────── OPINION ─────────────── */

  function initOpinion(isbn) {
    const textarea = document.getElementById('opinion-box');
    if (!textarea) return;

    const saved = getBookData(isbn, 'opinion');
    if (saved) textarea.value = saved;

    let debounceTimer;
    textarea.addEventListener('input', function () {
      clearTimeout(debounceTimer);
      debounceTimer = setTimeout(function () {
        setBookData(isbn, 'opinion', textarea.value);
      }, 400);
    });
  }

  /* ─────────────── READING DATES ─────────────── */

  function initReadingDates(isbn) {
    const list = document.getElementById('reading-dates-list');
    const addBtn = document.getElementById('add-reading-date');
    const startInput = document.getElementById('date-start');
    const endInput = document.getElementById('date-end');
    if (!list || !addBtn || !startInput || !endInput) return;

    let dates = getBookData(isbn, 'reading_dates') || [];

    function formatDate(dateStr) {
      if (!dateStr) return '...';
      const d = new Date(dateStr + 'T00:00:00');
      return d.toLocaleDateString('es-ES', { day: 'numeric', month: 'short', year: 'numeric' });
    }

    function ordinalLabel(idx) {
      var n = idx + 1;
      if (n === 1) return 'Primera lectura';
      if (n === 2) return 'Segunda lectura';
      if (n === 3) return 'Tercera lectura';
      return 'Lectura #' + n;
    }

    function makeCalendarSvg() {
      var svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
      svg.setAttribute('viewBox', '0 0 24 24'); svg.setAttribute('fill', 'none');
      svg.setAttribute('stroke', 'currentColor'); svg.setAttribute('stroke-width', '2');
      svg.setAttribute('stroke-linecap', 'round'); svg.setAttribute('stroke-linejoin', 'round');
      ['rect|x=3,y=4,w=18,h=18,rx=2,ry=2',
       'line|x1=16,y1=2,x2=16,y2=6',
       'line|x1=8,y1=2,x2=8,y2=6',
       'line|x1=3,y1=10,x2=21,y2=10'].forEach(function (def) {
        var [tag, attrs] = def.split('|');
        var el = document.createElementNS('http://www.w3.org/2000/svg', tag);
        attrs.split(',').forEach(function (pair) {
          var kv = pair.split('='); el.setAttribute(kv[0], kv[1]);
        });
        svg.appendChild(el);
      });
      return svg;
    }

    function makeRemoveSvg() {
      var svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
      svg.setAttribute('width', '12'); svg.setAttribute('height', '12');
      svg.setAttribute('viewBox', '0 0 24 24'); svg.setAttribute('fill', 'none');
      svg.setAttribute('stroke', 'currentColor'); svg.setAttribute('stroke-width', '2.5');
      svg.setAttribute('stroke-linecap', 'round');
      var l1 = document.createElementNS('http://www.w3.org/2000/svg', 'line');
      l1.setAttribute('x1', '18'); l1.setAttribute('y1', '6');
      l1.setAttribute('x2', '6'); l1.setAttribute('y2', '18');
      svg.appendChild(l1);
      var l2 = document.createElementNS('http://www.w3.org/2000/svg', 'line');
      l2.setAttribute('x1', '6'); l2.setAttribute('y1', '6');
      l2.setAttribute('x2', '18'); l2.setAttribute('y2', '18');
      svg.appendChild(l2);
      return svg;
    }

    function renderDates() {
      list.innerHTML = '';

      dates.forEach(function (entry, i) {
        var li = document.createElement('li');
        li.className = 'reading-dates__item';

        var iconDiv = document.createElement('div');
        iconDiv.className = 'reading-dates__icon';
        iconDiv.appendChild(makeCalendarSvg());

        var infoDiv = document.createElement('div');
        infoDiv.className = 'reading-dates__info';

        var rangeDiv = document.createElement('div');
        rangeDiv.className = 'reading-dates__range';
        rangeDiv.textContent = formatDate(entry.start) + ' \u2014 ' + formatDate(entry.end);

        var labelDiv = document.createElement('div');
        labelDiv.className = 'reading-dates__label';
        labelDiv.textContent = ordinalLabel(i);

        infoDiv.appendChild(rangeDiv);
        infoDiv.appendChild(labelDiv);

        var btn = document.createElement('button');
        btn.type = 'button';
        btn.className = 'reading-dates__remove';
        btn.dataset.idx = String(i);
        btn.title = 'Eliminar';
        btn.appendChild(makeRemoveSvg());

        li.appendChild(iconDiv);
        li.appendChild(infoDiv);
        li.appendChild(btn);
        list.appendChild(li);
      });
    }

    list.addEventListener('click', function (e) {
      var btn = e.target.closest('.reading-dates__remove');
      if (!btn) return;
      dates.splice(parseInt(btn.dataset.idx, 10), 1);
      setBookData(isbn, 'reading_dates', dates);
      renderDates();
    });

    addBtn.addEventListener('click', function () {
      var start = startInput.value;
      var end = endInput.value;
      if (!start && !end) return;
      dates.push({ start: start || null, end: end || null });
      setBookData(isbn, 'reading_dates', dates);
      startInput.value = '';
      endInput.value = '';
      renderDates();
    });

    renderDates();
  }

  /* ─────────────── SAVE BUTTON ─────────────── */

  function initSaveButton(isbn) {
    var saveBtn = document.getElementById('save-book-btn');
    var statusMsg = document.getElementById('save-status-message');
    if (!saveBtn) return;

    saveBtn.addEventListener('click', function () {
      var title = document.getElementById('book-title-input');
      var authors = document.getElementById('book-authors-input');
      var publishedDate = document.getElementById('book-date-input');
      var description = document.getElementById('book-description-edit');
      var statusSelect = document.getElementById('book-status-select');

      var isbn10 = null;
      var isbn10El = document.querySelector('.book-detail__isbn span:last-child');
      if (isbn10El && isbn10El.textContent.trim() && saveBtn.dataset.inCollection === 'true') {
        isbn10 = isbn10El.textContent.trim();
      }

      var coverUrl = null;
      var coverImg = document.querySelector('.book-detail__cover');
      if (coverImg && coverImg.src) {
        coverUrl = coverImg.src;
      }

      var rating = getBookData(isbn, 'rating') || null;
      var tags = getBookData(isbn, 'tags') || [];
      var opinion = getBookData(isbn, 'opinion') || null;
      var readingDates = getBookData(isbn, 'reading_dates') || [];

      var readingPeriods = readingDates.map(function (entry) {
        return { start_date: entry.start || null, end_date: entry.end || null };
      });

      var body = {
        isbn_13: isbn,
        isbn_10: isbn10,
        title: title ? title.value.trim() : '',
        authors: authors ? authors.value.split(',').map(function (s) { return s.trim(); }).filter(Boolean) : [],
        description: description ? description.value.trim() : null,
        published_date: publishedDate ? publishedDate.value.trim() || null : null,
        cover_image_url: coverUrl,
        status: statusSelect ? statusSelect.value : 'new',
        rating: rating,
        tags: tags,
        opinion: opinion,
        reading_periods: readingPeriods
      };

      saveBtn.disabled = true;
      saveBtn.textContent = 'Guardando...';
      statusMsg.textContent = '';
      statusMsg.className = 'save-status-message';

      fetch('/api/collection', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
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
          statusMsg.textContent = 'Guardado correctamente.';
          statusMsg.className = 'save-status-message is-success';
          saveBtn.textContent = 'Guardar cambios';

          if (saveBtn.dataset.inCollection === 'false') {
            saveBtn.dataset.inCollection = 'true';
            var badgeContainer = saveBtn.parentElement;
            var badge = document.createElement('div');
            badge.className = 'in-collection-badge';
            badge.innerHTML = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"></polyline></svg> En tu colecci\u00f3n';
            badgeContainer.insertBefore(badge, saveBtn.parentElement.firstChild);
          }

          setTimeout(function () {
            statusMsg.textContent = '';
          }, 3000);
        })
        .catch(function (err) {
          statusMsg.textContent = err.message;
          statusMsg.className = 'save-status-message is-error';
          saveBtn.textContent = 'A\u00f1adir a mi colecci\u00f3n';
        })
        .finally(function () {
          saveBtn.disabled = false;
        });
    });
  }

  /* ─────────────── PUBLIC INIT ─────────────── */

  window.PersonalLibrary = {
    initBookDetail: function (isbn) {
      initRating(isbn);
      initTags(isbn);
      initOpinion(isbn);
      initReadingDates(isbn);
      initSaveButton(isbn);
    }
  };
})();
