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

const registrationForm = document.querySelector("#registrationForm");
const prototypeNotice = document.querySelector("#prototypeNotice");
if (registrationForm && prototypeNotice) {
  registrationForm.addEventListener("submit", (event) => {
    event.preventDefault();
    prototypeNotice.textContent = "Prévia visual: seus dados não foram enviados nem armazenados. O envio será habilitado após a integração segura com o banco de dados.";
    prototypeNotice.scrollIntoView({ behavior: "smooth", block: "nearest" });
  });
}
