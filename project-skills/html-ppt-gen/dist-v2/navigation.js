// Presentation Navigation
let currentSlide = 1;
let totalSlides = 0;

// Initialize
document.addEventListener('DOMContentLoaded', () => {
  const navButtons = document.querySelectorAll('.nav-btn');
  totalSlides = navButtons.length;
  updateNavigation();
  
  // Keyboard navigation
  document.addEventListener('keydown', (e) => {
    if (e.key === 'ArrowRight' || e.key === ' ') {
      nextSlide();
    } else if (e.key === 'ArrowLeft') {
      prevSlide();
    } else if (e.key >= '1' && e.key <= '9') {
      const num = parseInt(e.key);
      if (num <= totalSlides) {
        loadSlide(num);
      }
    }
  });
});

function loadSlide(num) {
  if (num < 1 || num > totalSlides) return;
  
  currentSlide = num;
  const frame = document.getElementById('slideFrame');
  frame.src = `slide-${String(num).padStart(2, '0')}.html`;
  
  updateNavigation();
}

function nextSlide() {
  if (currentSlide < totalSlides) {
    loadSlide(currentSlide + 1);
  }
}

function prevSlide() {
  if (currentSlide > 1) {
    loadSlide(currentSlide - 1);
  }
}

function updateNavigation() {
  // Update active button
  const buttons = document.querySelectorAll('.nav-btn');
  buttons.forEach((btn, index) => {
    if (index + 1 === currentSlide) {
      btn.classList.add('active');
    } else {
      btn.classList.remove('active');
    }
  });
  
  // Update counter
  document.getElementById('currentSlide').textContent = currentSlide;
}