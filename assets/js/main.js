(() => {
  const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* Header: glass over the hero, solid after it; hides on scroll down */
  const nav = document.querySelector('.nav');
  const hero = document.querySelector('.hero');
  let lastY = window.scrollY;
  const onScroll = () => {
    const y = window.scrollY;
    nav.classList.toggle('is-solid', y > hero.offsetHeight - 120);
    nav.classList.toggle('is-hidden', y > lastY && y > 400 && !nav.querySelector('.nav__mobile:not([hidden])'));
    lastY = y;
  };
  window.addEventListener('scroll', onScroll, { passive: true });
  onScroll();

  /* Mobile menu */
  const burger = nav.querySelector('.nav__burger');
  const mobile = nav.querySelector('.nav__mobile');
  burger.addEventListener('click', () => {
    const open = burger.getAttribute('aria-expanded') !== 'true';
    burger.setAttribute('aria-expanded', String(open));
    mobile.hidden = !open;
  });
  mobile.querySelectorAll('a').forEach(a => a.addEventListener('click', () => {
    burger.setAttribute('aria-expanded', 'false');
    mobile.hidden = true;
  }));

  /* Hero slider */
  const heroSlides = [
    ['أبراج الشيخ التوأم', 'طريق الملك سعود · الهدا'],
    ['برج الكورنيش', 'كورنيش الخبر · قيد التصميم'],
    ['برج بوابة الخبر', 'طريق الملك فهد · البندرية'],
    ['الشيخ أفينيو', 'طريق الملك سلمان · اليرموك'],
    ['الشيخ سكوير', 'الكورنيش · الخبر'],
    ['قرية إبريز', 'الجوهرة · الخبر'],
  ];
  const heroImgs = document.querySelectorAll('.hero__frame img');
  const heroDots = document.querySelectorAll('.hero__dots button');
  const heroName = document.querySelector('[data-hero-name]');
  const heroLoc = document.querySelector('[data-hero-loc]');
  let heroIndex = 0, heroTimer;
  const showHero = i => {
    heroIndex = (i + heroImgs.length) % heroImgs.length;
    heroImgs.forEach((img, n) => img.classList.toggle('is-active', n === heroIndex));
    heroDots.forEach((d, n) => {
      d.classList.remove('is-active');
      if (n === heroIndex) { void d.offsetWidth; d.classList.add('is-active'); }
    });
    heroName.textContent = heroSlides[heroIndex][0];
    heroLoc.textContent = heroSlides[heroIndex][1];
    clearTimeout(heroTimer);
    if (!reduceMotion) heroTimer = setTimeout(() => showHero(heroIndex + 1), 6000);
  };
  heroDots.forEach((d, n) => d.addEventListener('click', () => showHero(n)));
  showHero(0);

  /* Portfolio showcase tabs */
  const slides = document.querySelectorAll('.showcase .slide');
  const railBtns = document.querySelectorAll('.showcase__rail button');
  let showIndex = 0, showTimer;
  const showSlide = i => {
    showIndex = (i + slides.length) % slides.length;
    slides.forEach((s, n) => s.classList.toggle('is-active', n === showIndex));
    railBtns.forEach((b, n) => {
      b.classList.toggle('is-active', n === showIndex);
      b.setAttribute('aria-selected', String(n === showIndex));
    });
    clearInterval(showTimer);
    if (!reduceMotion) showTimer = setInterval(() => showSlide(showIndex + 1), 7000);
  };
  railBtns.forEach((b, n) => {
    b.setAttribute('role', 'tab');
    b.addEventListener('click', () => showSlide(n));
  });
  showSlide(0);

  /* Services cards */
  const svcTitle = document.querySelector('[data-svc-title]');
  const svcBody = document.querySelector('[data-svc-body]');
  const svcImg = document.querySelector('[data-svc-img]');
  document.querySelectorAll('.svc').forEach(card => {
    card.setAttribute('role', 'tab');
    card.addEventListener('click', () => {
      document.querySelectorAll('.svc').forEach(c => {
        c.classList.toggle('is-active', c === card);
        c.setAttribute('aria-selected', String(c === card));
      });
      svcTitle.textContent = card.dataset.title;
      svcBody.textContent = card.dataset.body;
      svcImg.style.opacity = 0;
      setTimeout(() => { svcImg.src = card.dataset.img; svcImg.style.opacity = 1; }, 250);
    });
  });

  /* Reveal + counters */
  const fmt = n => n.toLocaleString('en-US');
  const countUp = el => {
    const target = +el.dataset.count;
    if (reduceMotion) return;
    const start = performance.now(), dur = 1600;
    const tick = t => {
      const p = Math.min(1, (t - start) / dur);
      el.textContent = fmt(Math.round(target * (1 - Math.pow(1 - p, 3))));
      if (p < 1) requestAnimationFrame(tick);
    };
    requestAnimationFrame(tick);
  };
  const io = new IntersectionObserver(entries => {
    entries.forEach(e => {
      if (!e.isIntersecting) return;
      e.target.classList.add('is-in');
      e.target.querySelectorAll('[data-count]').forEach(countUp);
      io.unobserve(e.target);
    });
  }, { threshold: 0.15 });
  document.querySelectorAll('.reveal').forEach(el => io.observe(el));
})();
