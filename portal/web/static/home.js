(async () => {
  const res = await fetch("/api/me", { credentials: "same-origin" });
  if (!res.ok) {
    location.href = "/";
    return;
  }
  const user = await res.json();
  document.getElementById("name").textContent = user.name ? ", " + user.name : "";
  document.getElementById("email").textContent = user.email;
  if (user.picture) {
    const img = document.getElementById("avatar");
    img.src = user.picture;
    img.hidden = false;
  }
})();
