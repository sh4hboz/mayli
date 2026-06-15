// Header scroll effect
const header = document.querySelector('header');
window.addEventListener('scroll', () => {
    if (window.scrollY > 50) {
        header.classList.add('scrolled');
    } else {
        header.classList.remove('scrolled');
    }
});

// Phone Input Mask (Uzbekistan Only)
const phoneInput = document.getElementById('phone');
if (phoneInput && typeof IMask !== 'undefined') {
    IMask(phoneInput, {
        mask: '+{998} (00) 000-00-00',
        lazy: false // Always show prefix
    });
}

// Booking form validation
const bookingForm = document.getElementById('booking-form');
if (bookingForm) {
    bookingForm.addEventListener('submit', (e) => {
        e.preventDefault();
        const agreement = document.getElementById('agreement');
        const phone = document.getElementById('phone');

        if (!agreement.checked) {
            alert('Iltimos, shaxsiy ma\'lumotlarni qayta ishlashga rozilik bildiring!');
            return;
        }

        // Simulating form submission
        alert('Rahmat! Buyurtmangiz qabul qilindi. Tez orada siz bilan bog\'lanamiz.');
        bookingForm.reset();
    });
}

// Smooth scroll for anchor links
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            window.scrollTo({
                top: target.offsetTop - 70,
                behavior: 'smooth'
            });
        }
    });
});

// Initialize Swiper for Emotions Section (Infinite Linear Loop)
const emotionsSwiper = new Swiper('.emotions-swiper', {
    slidesPerView: 3.5,
    spaceBetween: 20,
    loop: true,
    speed: 12000,
    autoplay: {
        delay: 0,
        disableOnInteraction: false,
    },
    freeMode: true,
    breakpoints: {
        320: {
            slidesPerView: 1.5,
        },
        768: {
            slidesPerView: 2.5,
        },
        1024: {
            slidesPerView: 3.5,
        }
    }
});

// Initialize Fancybox
if (typeof Fancybox !== 'undefined') {
    Fancybox.bind("[data-fancybox]", {
        // Custom options
    });
}

// Mobile Menu Toggle
const mobileMenuBtn = document.querySelector('.mobile-menu-btn');
const navLinks = document.querySelector('.nav-links');

if (mobileMenuBtn && navLinks) {
    mobileMenuBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        navLinks.classList.toggle('active');
        
        // Toggle mobile menu text/icon
        const isOpened = navLinks.classList.contains('active');
        mobileMenuBtn.querySelector('span').textContent = isOpened ? 'YOPISH' : 'MENU';
    });

    // Close mobile menu when clicking outside
    document.addEventListener('click', (e) => {
        if (!navLinks.contains(e.target) && !mobileMenuBtn.contains(e.target)) {
            navLinks.classList.remove('active');
            mobileMenuBtn.querySelector('span').textContent = 'MENU';
        }
    });

    // Close mobile menu when a nav link is clicked
    navLinks.querySelectorAll('a').forEach(link => {
        link.addEventListener('click', () => {
            navLinks.classList.remove('active');
            mobileMenuBtn.querySelector('span').textContent = 'MENU';
        });
    });
}
