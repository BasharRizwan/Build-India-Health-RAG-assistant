const form = document.querySelector("#ask-form");
const question = document.querySelector("#question");
const answer = document.querySelector("#answer");
const sources = document.querySelector("#sources");
const latency = document.querySelector("#latency");
const mode = document.querySelector("#mode");

function escapeHtml(value) {
  return value
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

function renderSources(items) {
  sources.innerHTML = items.map((item) => `
    <article class="source-card">
      <h4>${escapeHtml(item.title)}</h4>
      <p>${escapeHtml(item.snippet)}</p>
      <span class="score">cosine ${Number(item.score).toFixed(3)}</span>
    </article>
  `).join("");
}

async function ask(currentQuestion) {
  const start = performance.now();
  answer.textContent = "Retrieving the strongest PIB evidence...";
  latency.textContent = "thinking";
  form.querySelector("button[type='submit']").disabled = true;

  try {
    const response = await fetch("/api/ask", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({question: currentQuestion, k: 4}),
    });
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.error || "Request failed");
    }
    answer.textContent = data.answer;
    mode.textContent = data.mode;
    renderSources(data.sources);
    latency.textContent = `${Math.round(performance.now() - start)} ms`;
  } catch (error) {
    answer.textContent = error.message;
    latency.textContent = "error";
  } finally {
    form.querySelector("button[type='submit']").disabled = false;
  }
}

form.addEventListener("submit", (event) => {
  event.preventDefault();
  const value = question.value.trim();
  if (value) {
    ask(value);
  }
});

document.querySelectorAll("[data-question]").forEach((button) => {
  button.addEventListener("click", () => {
    question.value = button.dataset.question;
    ask(button.dataset.question);
  });
});

