const btn = document.getElementById("upload-btn");
const fileInput = document.getElementById("file");
const status = document.getElementById("status");

btn?.addEventListener("click", async () => {
  const file = fileInput.files[0];
  if (!file) {
    status.textContent = "Выберите файл";
    status.className = "status error";
    return;
  }
  btn.disabled = true;
  status.className = "status";
  status.textContent = "Распознаём…";

  const form = new FormData();
  form.append("file", file);
  try {
    const resp = await fetch("/api/recognize", { method: "POST", body: form });
    if (!resp.ok) throw new Error("HTTP " + resp.status);
    status.textContent = "Готово! Переходим к предпросмотру…";
    window.location.href = "/preview";
  } catch (e) {
    status.textContent = "Ошибка: " + e.message;
    status.className = "status error";
    btn.disabled = false;
  }
});