/*
 * dashboard-search.js — Topbar global qidiruv (front).
 *
 * Input'ga yozilganda debounce bilan /dashboard/search/ ga so'rov yuboradi va
 * natijani guruhlangan dropdown qilib ko'rsatadi. Klaviatura: ↑/↓ tanlash,
 * Enter o'tish, Esc yopish. Ortiqcha so'rovni oldini olish uchun min belgi + debounce.
 */
(function () {
    'use strict';

    var input = document.getElementById('global-search-input');
    var box = document.getElementById('global-search-results');
    if (!input || !box) return;

    var URL = input.dataset.searchUrl;
    var MIN_LEN = 2;
    var DEBOUNCE = 250;

    var timer = null;
    var controller = null;
    var links = [];      // tekis <a> ro'yxati (klaviatura navigatsiyasi uchun)
    var active = -1;

    function close() {
        box.hidden = true;
        box.classList.remove('show');
        box.innerHTML = '';
        links = [];
        active = -1;
    }

    function open() {
        box.hidden = false;
        box.classList.add('show');
    }

    function esc(value) {
        var d = document.createElement('div');
        d.textContent = value == null ? '' : String(value);
        return d.innerHTML;
    }

    function render(groups) {
        box.innerHTML = '';
        links = [];
        active = -1;

        if (!groups || !groups.length) {
            var empty = document.createElement('div');
            empty.className = 'px-3 py-2 text-muted small';
            empty.textContent = 'Hech narsa topilmadi';
            box.appendChild(empty);
            open();
            return;
        }

        groups.forEach(function (group) {
            var header = document.createElement('h6');
            header.className = 'dropdown-header d-flex align-items-center gap-1';
            header.innerHTML = '<i class="' + esc(group.icon) + '"></i><span>' + esc(group.label) + '</span>';
            box.appendChild(header);

            group.items.forEach(function (it) {
                var a = document.createElement('a');
                a.className = 'dropdown-item global-search-item text-wrap';
                a.href = it.url;
                var sub = it.subtitle
                    ? '<small class="text-muted d-block">' + esc(it.subtitle) + '</small>'
                    : '';
                a.innerHTML = '<span class="d-block fw-medium">' + esc(it.title) + '</span>' + sub;
                box.appendChild(a);
                links.push(a);
            });
        });
        open();
    }

    function highlight(index) {
        links.forEach(function (a, i) { a.classList.toggle('active', i === index); });
        if (index >= 0 && links[index]) {
            links[index].scrollIntoView({ block: 'nearest' });
        }
        active = index;
    }

    function search(query) {
        if (controller) controller.abort();
        controller = new AbortController();
        fetch(URL + '?q=' + encodeURIComponent(query), {
            headers: { 'X-Requested-With': 'XMLHttpRequest' },
            signal: controller.signal,
        })
            .then(function (r) { return r.json(); })
            .then(function (data) { render(data.results); })
            .catch(function (err) { if (err.name !== 'AbortError') close(); });
    }

    input.addEventListener('input', function () {
        var query = input.value.trim();
        clearTimeout(timer);
        if (query.length < MIN_LEN) { close(); return; }
        timer = setTimeout(function () { search(query); }, DEBOUNCE);
    });

    input.addEventListener('keydown', function (e) {
        if (box.hidden) return;
        if (e.key === 'ArrowDown') {
            e.preventDefault();
            highlight(Math.min(active + 1, links.length - 1));
        } else if (e.key === 'ArrowUp') {
            e.preventDefault();
            highlight(Math.max(active - 1, 0));
        } else if (e.key === 'Enter') {
            if (active >= 0 && links[active]) {
                e.preventDefault();
                window.location = links[active].href;
            }
        } else if (e.key === 'Escape') {
            close();
        }
    });

    input.addEventListener('focus', function () {
        if (input.value.trim().length >= MIN_LEN && links.length) open();
    });

    document.addEventListener('click', function (e) {
        if (e.target !== input && !box.contains(e.target)) close();
    });
})();
