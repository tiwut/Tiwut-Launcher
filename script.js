document.addEventListener('DOMContentLoaded', () => {

    const elementsToAnimate = document.querySelectorAll('.animate-on-scroll');
    const header = document.querySelector('.main-header');
    const background = document.querySelector('.background-canvas');

    // 1. Scroll Animations (Intersection Observer)
    const observer = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('active');
                observer.unobserve(entry.target); 
            }
        });
    }, {
        threshold: 0.15,
        rootMargin: '0px 0px -50px 0px'
    });

    elementsToAnimate.forEach(element => {
        const delay = element.getAttribute('data-animation-delay');
        if (delay) {
            element.style.transitionDelay = `${delay / 1000}s`;
        }
        observer.observe(element);
    });

    // 2. Header Blur/Shadow Effect on Scroll
    window.addEventListener('scroll', () => {
        if (window.scrollY > 50) {
            header.classList.add('scrolled');
        } else {
            header.classList.remove('scrolled');
        }
        
        // 3. Background Parallax Effect
        if (background) {
            const scrollValue = window.scrollY * 0.1;
            background.style.transform = `translateY(${scrollValue}px) scale(1.05) blur(8px) brightness(0.6)`;
        }
    });
});
