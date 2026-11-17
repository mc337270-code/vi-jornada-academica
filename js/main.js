const menuToggle = document.querySelector("#menuToggle");
const mainNav = document.querySelector("#mainNav");

if (menuToggle && mainNav) {
  menuToggle.addEventListener("click", () => {
    const menuAberto = mainNav.classList.toggle("is-open");
    menuToggle.setAttribute("aria-expanded", String(menuAberto));
    menuToggle.setAttribute("aria-label", menuAberto ? "Fechar navegação" : "Abrir navegação");
  });

  mainNav.querySelectorAll("a").forEach((link) => {
    link.addEventListener("click", () => {
      mainNav.classList.remove("is-open");
      menuToggle.setAttribute("aria-expanded", "false");
      menuToggle.setAttribute("aria-label", "Abrir navegação");
    });
  });
}

// O formulário de inscrição agora é enviado ao Flask por POST.
// Não interceptar o submit: o servidor valida e salva os dados no MySQL.
