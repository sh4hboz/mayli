/* ===== MAYLI RESTOBAR — Website JS ===== */
document.addEventListener('DOMContentLoaded', function () {

  // === HEADER SCROLL ===
  const header = document.getElementById('header');
  window.addEventListener('scroll', () => {
    header && header.classList.toggle('scrolled', window.scrollY > 60);
  });

  // === MOBILE MENU ===
  const menuBtn = document.getElementById('mobileMenuBtn');
  const navLinks = document.getElementById('nav-links');
  if (menuBtn && navLinks) {
    menuBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      const isOpen = navLinks.classList.toggle('open');
      menuBtn.classList.toggle('active', isOpen);
      document.body.classList.toggle('menu-open', isOpen);
    });
    document.addEventListener('click', (e) => {
      if (!menuBtn.contains(e.target) && !navLinks.contains(e.target)) {
        menuBtn.classList.remove('active');
        navLinks.classList.remove('open');
        document.body.classList.remove('menu-open');
      }
    });
    // Nav link bosilganda menyuni yopish
    navLinks.querySelectorAll('a').forEach(a => {
      a.addEventListener('click', () => {
        menuBtn.classList.remove('active');
        navLinks.classList.remove('open');
        document.body.classList.remove('menu-open');
      });
    });
  }

  // === MOBILE MENU DRAWER ===
  const mobileMenuBtn = document.getElementById('mobileMenuBtn');
  const mobileMenuDrawer = document.getElementById('mobileMenuDrawer');
  const mobileMenuBackdrop = document.getElementById('mobileMenuBackdrop');
  const mobileMenuClose = document.getElementById('mobileMenuClose');

  function closeDrawer() {
    mobileMenuDrawer && mobileMenuDrawer.classList.remove('active');
    mobileMenuBackdrop && mobileMenuBackdrop.classList.remove('active');
    document.body.classList.remove('menu-open');
  }

  if (mobileMenuBtn && mobileMenuDrawer && mobileMenuBackdrop) {
    // Hamburger click
    mobileMenuBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      const isOpen = mobileMenuDrawer.classList.toggle('active');
      mobileMenuBackdrop.classList.toggle('active', isOpen);
      document.body.classList.toggle('menu-open', isOpen);
    });

    // Close button click
    if (mobileMenuClose) {
      mobileMenuClose.addEventListener('click', (e) => {
        e.stopPropagation();
        closeDrawer();
      });
    }

    // Backdrop click - yopish
    mobileMenuBackdrop.addEventListener('click', closeDrawer);

    // Drawer link click - yopish
    mobileMenuDrawer.querySelectorAll('.mobile-menu-nav a').forEach(link => {
      link.addEventListener('click', closeDrawer);
    });

    // Outside click - yopish
    document.addEventListener('click', (e) => {
      if (!mobileMenuBtn.contains(e.target) && !mobileMenuDrawer.contains(e.target)) {
        closeDrawer();
      }
    });
  }

  // === SCROLL TO TOP ===
  const scrollBtn = document.getElementById('scrollTopBtn');
  if (scrollBtn) {
    scrollBtn.addEventListener('click', () => window.scrollTo({ top: 0, behavior: 'smooth' }));
  }

  // === FLOATING BUTTONS ROTATION (tel/tg/ig — har 3 soniyada) ===
  const fabItems = document.querySelectorAll('.fab-rotate-item');
  if (fabItems.length > 1) {
    let fabCurrent = 0;
    setInterval(() => {
      fabItems[fabCurrent].classList.remove('fab-rotate-active');
      fabCurrent = (fabCurrent + 1) % fabItems.length;
      fabItems[fabCurrent].classList.add('fab-rotate-active');
    }, 3000);
  }

  // === LANG DROPDOWN ===
  const langDropdown = document.getElementById('langDropdown');
  const langDropdownBtn = document.getElementById('langDropdownBtn');
  if (langDropdown && langDropdownBtn) {
    langDropdownBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      langDropdown.classList.toggle('open');
      const isOpen = langDropdown.classList.contains('open');
      langDropdownBtn.setAttribute('aria-expanded', isOpen);
    });
    document.addEventListener('click', () => {
      langDropdown.classList.remove('open');
      langDropdownBtn.setAttribute('aria-expanded', 'false');
    });
    langDropdown.addEventListener('click', (e) => e.stopPropagation());
  }

  // === SCROLL REVEAL ===
  const reveals = document.querySelectorAll('.reveal');
  const revealObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('visible');
        revealObserver.unobserve(entry.target);
      }
    });
  }, { threshold: 0.12, rootMargin: '0px 0px -40px 0px' });
  reveals.forEach(el => revealObserver.observe(el));

  // === HERO SWIPER ===
  if (document.querySelector('.hero-swiper')) {
    new Swiper('.hero-swiper', {
      loop: true, autoplay: { delay: 5000, disableOnInteraction: false },
      effect: 'fade', fadeEffect: { crossFade: true },
    });
  }

  // === FEATURED DISHES SWIPER ===
  if (document.querySelector('.dishes-swiper')) {
    new Swiper('.dishes-swiper', {
      slidesPerView: 1.2, spaceBetween: 16, loop: false,
      breakpoints: {
        480: { slidesPerView: 2, spaceBetween: 16 },
        768: { slidesPerView: 3, spaceBetween: 20 },
        1024: { slidesPerView: 4, spaceBetween: 20 },
      },
      navigation: { nextEl: '.dishes-next', prevEl: '.dishes-prev' },
    });
  }

  // === GALLERY SWIPER ===
  if (document.querySelector('.gallery-swiper')) {
    new Swiper('.gallery-swiper', {
      slidesPerView: 1.2, spaceBetween: 16, loop: true,
      autoplay: { delay: 0, disableOnInteraction: false },
      speed: 5000,
      breakpoints: {
        480: { slidesPerView: 2, spaceBetween: 16 },
        768: { slidesPerView: 3, spaceBetween: 20 },
        1024: { slidesPerView: 4, spaceBetween: 20 },
      },
    });
  }

  // === TESTIMONIALS SWIPER ===
  const testSwiper = document.querySelector('.testimonials-swiper');
  if (testSwiper) {
    const slideCount = testSwiper.querySelectorAll('.swiper-slide').length;
    new Swiper('.testimonials-swiper', {
      slidesPerView: 1, spaceBetween: 20,
      loop: slideCount >= 2,
      autoplay: { delay: 4500, disableOnInteraction: false },
      breakpoints: {
        640: { slidesPerView: Math.min(2, slideCount) },
        1024: { slidesPerView: Math.min(3, slideCount) },
      },
    });
  }

  // === FANCYBOX GALLERY ===
  if (typeof Fancybox !== 'undefined') {
    Fancybox.bind('[data-fancybox="gallery"], [data-fancybox="gallery-home"]', {
      Toolbar: { display: { left: [], middle: [], right: ['close'] } },
    });
  }

  // === MENU FILTERS ===
  // <a href> teglar URL'ni o'zi boshqaradi — JS kerak emas.

  // === MENU SEARCH ===
  const searchForm = document.getElementById('menuSearchForm');
  if (searchForm) {
    searchForm.addEventListener('submit', function (e) {
      e.preventDefault();
      const q = this.querySelector('input').value.trim();
      const searchParams = new URLSearchParams(window.location.search);
      if (q) searchParams.set('q', q);
      else searchParams.delete('q');
      window.location.search = searchParams.toString();
    });
  }

  // === AJAX FORMS (contact & vacancy) ===
  document.querySelectorAll('.ajax-form').forEach(form => {
    form.addEventListener('submit', function (e) {
      e.preventDefault();
      const formData = new FormData(this);
      const btn = this.querySelector('[type=submit]');
      if (btn) { btn.disabled = true; btn.textContent = '...'; }
      fetch(this.action || window.location.href, {
        method: 'POST',
        headers: { 'X-Requested-With': 'XMLHttpRequest' },
        body: formData,
      })
        .then(r => r.json())
        .then(data => {
          const msgEl = form.querySelector('.form-result');
          const msgs = window.SITE_MESSAGES || {};
          if (data.success) {
            form.reset();
            if (msgEl) { msgEl.className = 'form-success'; msgEl.textContent = data.message || msgs.success || 'OK'; }
            form.dispatchEvent(new CustomEvent('mayli:form-success'));
          } else {
            if (msgEl) { msgEl.className = 'form-error'; msgEl.textContent = data.error || msgs.error || 'Error'; }
          }
        })
        .catch(() => {
          const msgEl = form.querySelector('.form-result');
          const msgs = window.SITE_MESSAGES || {};
          if (msgEl) { msgEl.className = 'form-error'; msgEl.textContent = msgs.network || 'Network error'; }
        })
        .finally(() => {
          if (btn) { btn.disabled = false; btn.textContent = btn.dataset.label || '→'; }
        });
    });
  });

  // === CHAT WIDGET (bir tomonlama → Telegram) ===
  // Mehmon xabar yozadi → /chat/send/ ga POST → admin Telegram botiga boradi.
  // Real-time javob yo'q; admin Telegramdan javob beradi yoki qo'ng'iroq qiladi.
  const chatWidget = document.getElementById('chatWidget');
  const chatOpenBtn = document.getElementById('chatOpenBtn');
  const chatCloseBtn = document.getElementById('chatCloseBtn');
  const chatSendBtn = document.getElementById('chatSendBtn');
  const chatInput = document.getElementById('chatInput');
  const chatBody = document.getElementById('chatBody');

  // Visitor UUID: localStorage'dan olish yoki yangi yaratish
  function getVisitorId() {
    let id = localStorage.getItem('mayli_visitor_id');
    if (!id) {
      if (typeof crypto !== 'undefined' && crypto.randomUUID) {
        id = crypto.randomUUID();
      } else {
        id = 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
          const r = Math.random() * 16 | 0;
          return (c === 'x' ? r : (r & 0x3 | 0x8)).toString(16);
        });
      }
      localStorage.setItem('mayli_visitor_id', id);
    }
    return id;
  }

  const visitorId = getVisitorId();
  const chatLang = (chatWidget && chatWidget.dataset.lang) || 'uz';

  function getCsrfToken() {
    let csrfToken = null;
    if (document.cookie && document.cookie !== '') {
      const cookies = document.cookie.split(';');
      for (let i = 0; i < cookies.length; i++) {
        const cookie = cookies[i].trim();
        if (cookie.substring(0, 10) === 'csrftoken=') {
          csrfToken = decodeURIComponent(cookie.substring(10));
          break;
        }
      }
    }
    return csrfToken;
  }

  function appendChatMessage(sender, text, time) {
    if (!chatBody) return;
    const div = document.createElement('div');
    div.className = 'chat-msg chat-msg-' + sender;
    const span = document.createElement('span');
    span.textContent = text;
    div.appendChild(span);
    if (time) {
      const t = document.createElement('small');
      t.className = 'chat-time';
      t.textContent = time;
      div.appendChild(t);
    }
    chatBody.appendChild(div);
    chatBody.scrollTop = chatBody.scrollHeight;
  }

  function sendChatMessage() {
    const text = chatInput && chatInput.value.trim();
    if (!text) return;

    const now = new Date();
    const timeStr = now.getHours().toString().padStart(2, '0') + ':' + now.getMinutes().toString().padStart(2, '0');

    appendChatMessage('visitor', text, timeStr);
    chatInput.value = '';
    if (chatSendBtn) chatSendBtn.disabled = true;

    const body = new URLSearchParams();
    body.append('message', text);
    body.append('visitor_id', visitorId);
    body.append('lang', chatLang);

    fetch('/chat/send/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
        'X-CSRFToken': getCsrfToken(),
        'X-Requested-With': 'XMLHttpRequest',
      },
      body: body.toString(),
    })
    .then(r => r.json())
    .then(data => {
      if (data && data.reply) {
        appendChatMessage('bot', data.reply, '');
      } else if (data && data.error) {
        appendChatMessage('system', data.error, '');
      }
    })
    .catch(() => {
      const offlineMsgs = (window.SITE_MESSAGES || {}).chat_offline || {};
      const msg = offlineMsgs[chatLang] || offlineMsgs['uz'] || '💬 Xabar yuborilmadi. Iltimos, telefon orqali bog\'laning.';
      appendChatMessage('system', msg, '');
    })
    .finally(() => {
      if (chatSendBtn) chatSendBtn.disabled = false;
      if (chatInput) chatInput.focus();
    });
  }

  function openChat() {
    if (chatWidget) chatWidget.classList.add('open');
    if (chatInput) chatInput.focus();
  }
  function closeChat() {
    if (chatWidget) chatWidget.classList.remove('open');
  }

  if (chatOpenBtn) chatOpenBtn.addEventListener('click', openChat);
  if (chatCloseBtn) chatCloseBtn.addEventListener('click', closeChat);
  if (chatSendBtn) chatSendBtn.addEventListener('click', sendChatMessage);
  if (chatInput) {
    chatInput.addEventListener('keydown', function(e) {
      if (e.key === 'Enter') sendChatMessage();
    });
  }

  // === PROMO CARDS — klik bilan expand ===
  document.querySelectorAll('.promo-card').forEach(card => {
    card.addEventListener('click', function() {
      this.classList.toggle('expanded');
    });
  });

  // === ALERTS AUTO-HIDE ===
  setTimeout(() => {
    document.querySelectorAll('.alert').forEach(el => {
      el.style.transition = 'opacity .5s';
      el.style.opacity = '0';
      setTimeout(() => el.remove(), 500);
    });
  }, 4000);

  // === SITE MODALS (bron + vakansiya) ===
  let lastModalTrigger = null;

  function openModal(modal) {
    if (!modal) return;
    modal.classList.add('open');
    modal.setAttribute('aria-hidden', 'false');
    document.body.classList.add('modal-open');
    const firstInput = modal.querySelector('input:not([type=hidden]):not([tabindex="-1"]), textarea');
    if (firstInput) setTimeout(() => firstInput.focus(), 50);
  }

  function closeModal(modal) {
    if (!modal) return;
    modal.classList.remove('open');
    modal.setAttribute('aria-hidden', 'true');
    document.body.classList.remove('modal-open');
    if (lastModalTrigger) { lastModalTrigger.focus(); lastModalTrigger = null; }
  }

  // Bron modalini ochish
  document.querySelectorAll('[data-booking-open]').forEach(btn => {
    btn.addEventListener('click', function () {
      lastModalTrigger = this;
      openModal(document.getElementById('bookingModal'));
    });
  });

  // Vakansiya modalini ochish (vacancy_id + lavozim nomini uzatish)
  document.querySelectorAll('[data-vacancy-open]').forEach(btn => {
    btn.addEventListener('click', function () {
      lastModalTrigger = this;
      const modal = document.getElementById('vacancyModal');
      if (!modal) return;
      const idField = modal.querySelector('[name=vacancy_id]');
      if (idField) idField.value = this.dataset.vacancyId || '';
      const posEl = modal.querySelector('#vacancyModalPosition');
      if (posEl) posEl.textContent = this.dataset.vacancyTitle || '';
      openModal(modal);
    });
  });

  // Yopish: close tugmasi yoki backdrop
  document.querySelectorAll('[data-modal-close]').forEach(el => {
    el.addEventListener('click', function () {
      closeModal(this.closest('.site-modal'));
    });
  });

  // Esc bilan yopish
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') {
      document.querySelectorAll('.site-modal.open').forEach(closeModal);
    }
  });

  // Modal ichidagi forma muvaffaqiyatli yuborilganda — avtomatik yopish
  document.querySelectorAll('.site-modal .ajax-form').forEach(form => {
    form.addEventListener('mayli:form-success', function () {
      const modal = form.closest('.site-modal');
      setTimeout(() => closeModal(modal), 1800);
    });
  });

});

/* === TELEFON INPUT MASK (barcha tel inputlar uchun umumiy) ===
   O'zbekiston formati: +998 XX XXX-XX-XX. IMask kutubxonasi orqali.
   Backend (clean_uz_phone) raqamdan boshqasini tozalaydi -> mask belgilar zararsiz.
   website.js `defer` bilan yuklanadi -> DOM (modallar ham) tayyor bo'ladi. */
(function () {
  if (typeof IMask === 'undefined') return;
  document.querySelectorAll('input[type="tel"], input[name="phone"]').forEach(function (el) {
    if (el.dataset.maskInit) return;   // ikki marta init bo'lmasin
    el.dataset.maskInit = '1';
    IMask(el, { mask: '+{998} 00 000-00-00' });
  });
})();
