// Mostrar el botón cuando se desplaza hacia abajo 100px desde la parte superior del documento
window.onscroll = function () {
    scrollFunction();
  };
  
  function scrollFunction() {
    var scrollToTopBtn = document.getElementById("scrollToTopBtn");
    if (document.body.scrollTop > 600 || document.documentElement.scrollTop > 600) {
      scrollToTopBtn.style.display = "block";
    } else {
      scrollToTopBtn.style.display = "none";
    }
  }
  
  // Cuando el usuario hace clic en el botón, desplázate hacia arriba con una animación suave
  function scrollToTop() {
    const scrollStep = -window.scrollY / (1000 / 15), // Ajusta los 1000ms de transición a pasos de 15ms
          scrollInterval = setInterval(() => {
            if ( window.scrollY !== 0 ) {
              window.scrollBy( 0, scrollStep );
            }
            else clearInterval(scrollInterval);
          }, 15);
  }
  // Función para detectar cuándo un elemento está en la vista
  function isElementInViewport(el) {
    const rect = el.getBoundingClientRect();
    return (
      rect.top <= (window.innerHeight || document.documentElement.clientHeight) &&
      rect.bottom >= 0
    );
  }
  
  function handleScroll() {
    const elements = document.querySelectorAll('.fade-in');
    elements.forEach((element) => {
      if (isElementInViewport(element)) {
        element.classList.add('visible');
      } else {
        element.classList.remove('visible'); // Elimina la clase cuando no está visible
      }
    });
  }
  
  window.addEventListener('scroll', handleScroll);
  document.addEventListener('DOMContentLoaded', handleScroll);

  