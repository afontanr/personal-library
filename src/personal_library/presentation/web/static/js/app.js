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

    function renderTags() {
      container.querySelectorAll('.tag').forEach(function (el) { el.remove(); });

      tags.forEach(function (tagText, i) {
        const tag = document.createElement('span');
        tag.className = 'tag';
        tag.innerHTML =
          tagText +
          '<button type="button" class="tag__remove" data-idx="' + i + '" title="Eliminar">' +
          '<svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>' +
          '</button>';
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

    function renderDates() {
      list.innerHTML = '';

      dates.forEach(function (entry, i) {
        var li = document.createElement('li');
        li.className = 'reading-dates__item';
        li.innerHTML =
          '<div class="reading-dates__icon">' +
            '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">' +
              '<rect x="3" y="4" width="18" height="18" rx="2" ry="2"/>' +
              '<line x1="16" y1="2" x2="16" y2="6"/>' +
              '<line x1="8" y1="2" x2="8" y2="6"/>' +
              '<line x1="3" y1="10" x2="21" y2="10"/>' +
            '</svg>' +
          '</div>' +
          '<div class="reading-dates__info">' +
            '<div class="reading-dates__range">' +
              formatDate(entry.start) + ' — ' + formatDate(entry.end) +
            '</div>' +
            '<div class="reading-dates__label">' + ordinalLabel(i) + '</div>' +
          '</div>' +
          '<button type="button" class="reading-dates__remove" data-idx="' + i + '" title="Eliminar">' +
            '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round">' +
              '<line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>' +
            '</svg>' +
          '</button>';
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

  /* ─────────────── PUBLIC INIT ─────────────── */

  window.PersonalLibrary = {
    initBookDetail: function (isbn) {
      initRating(isbn);
      initTags(isbn);
      initOpinion(isbn);
      initReadingDates(isbn);
    }
  };
})();
