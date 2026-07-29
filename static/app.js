// Active User Allergy State
const activeAllergies = new Set(["Gluten", "Dairy", "Nuts"]);

document.addEventListener("DOMContentLoaded", () => {
    initAllergyToggles();
    initChatForm();
    fetchDatasetStats();
});

// Initialize Allergy Toggle Buttons
function initAllergyToggles() {
    const toggleBtns = document.querySelectorAll(".toggle-btn");
    toggleBtns.forEach(btn => {
        btn.addEventListener("click", () => {
            const allergy = btn.dataset.allergy;
            if (activeAllergies.has(allergy)) {
                activeAllergies.delete(allergy);
                btn.classList.remove("active");
            } else {
                activeAllergies.add(allergy);
                btn.classList.add("active");
            }
        });
    });
}

// Quick Sample Prompt Helper
function useSamplePrompt(promptText) {
    const input = document.getElementById("user-input");
    input.value = promptText;
    document.getElementById("chat-form").dispatchEvent(new Event("submit"));
}

// Fetch Table Dataset Statistics
async function fetchDatasetStats() {
    try {
        const res = await fetch("/api/menu");
        if (res.ok) {
            const data = await res.json();
            const countEl = document.getElementById("menu-count");
            if (countEl) countEl.innerText = `${data.count} Items`;
        }
    } catch (e) {
        console.warn("Could not fetch dataset stats:", e);
    }
}

// Form Submission & Chat Execution
function initChatForm() {
    const form = document.getElementById("chat-form");
    const input = document.getElementById("user-input");
    const sendBtn = document.getElementById("send-btn");

    form.addEventListener("submit", async (e) => {
        e.preventDefault();
        const query = input.value.trim();
        if (!query) return;

        // Render User Message
        appendUserMessage(query);
        input.value = "";
        sendBtn.disabled = true;

        // Show Loading Indicator
        const loadingCard = appendLoadingMessage();

        try {
            const payload = {
                prompt: query,
                allergies: Array.from(activeAllergies)
            };

            const response = await fetch("/api/chat", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload)
            });

            const data = await response.json();
            loadingCard.remove();

            if (response.ok) {
                appendAgentMessage(data);
                updateTraceDrawer(data);
            } else {
                appendErrorMessage(data.detail || "Error evaluating request.");
            }
        } catch (err) {
            loadingCard.remove();
            appendErrorMessage("Network error connecting to agent backend server.");
        } finally {
            sendBtn.disabled = false;
        }
    });
}

// Append User Bubble to Chat
function appendUserMessage(text) {
    const display = document.getElementById("chat-display");
    const div = document.createElement("div");
    div.className = "msg-bubble msg-user";
    div.innerText = text;
    display.appendChild(div);
    display.scrollTop = display.scrollHeight;
}

// Append Loading Card
function appendLoadingMessage() {
    const display = document.getElementById("chat-display");
    const div = document.createElement("div");
    div.className = "msg-bubble msg-agent";
    div.innerHTML = `<p>🔍 <em>Analyzing McDonald's allergen table data...</em></p>`;
    display.appendChild(div);
    display.scrollTop = display.scrollHeight;
    return div;
}

// Render Agent Safety Verdict Message
function appendAgentMessage(data) {
    const display = document.getElementById("chat-display");
    const div = document.createElement("div");
    div.className = "msg-bubble msg-agent";

    const badge = data.safety_badge || "ℹ️ VERDICT";
    const statusClass = data.status || "UNKNOWN";

    let detailsHtml = "";
    if (data.details) {
        const item = data.details.item_name || "";
        const category = data.details.category || "";
        const matched = (data.details.matched_allergens || []).join(", ") || "None";
        const ingredients = data.details.ingredients_summary || "N/A";
        const allAllergens = (data.details.all_allergens_in_item || []).join(", ") || "None listed";

        detailsHtml = `
            <div class="verdict-card ${statusClass}">
                <h4>${badge}: ${item} <small>(${category})</small></h4>
                <p><strong>Verdict:</strong> ${data.details.verdict}</p>
                <p><strong>Trigger Allergens Matched:</strong> ${matched}</p>
                <p><strong>Ingredients:</strong> ${ingredients}</p>
                <p><strong>Allergens Listed:</strong> ${allAllergens}</p>
            </div>
        `;
    } else {
        detailsHtml = `
            <div class="verdict-card ${statusClass}">
                <p>${data.response.replace(/\n/g, "<br>")}</p>
            </div>
        `;
    }

    div.innerHTML = `
        ${detailsHtml}
        <div class="disclaimer-box">
            ⚠️ <strong>Disclaimer:</strong> ${data.disclaimer}
        </div>
    `;

    display.appendChild(div);
    display.scrollTop = display.scrollHeight;
}

// Append Error Message
function appendErrorMessage(errText) {
    const display = document.getElementById("chat-display");
    const div = document.createElement("div");
    div.className = "msg-bubble msg-agent";
    div.innerHTML = `<div class="verdict-card UNSAFE"><p>❌ Error: ${errText}</p></div>`;
    display.appendChild(div);
    display.scrollTop = display.scrollHeight;
}

// Update Real-Time Trace & Telemetry Drawer
function updateTraceDrawer(data) {
    const traceContent = document.getElementById("trace-content");
    const timePill = document.getElementById("trace-time");

    if (timePill) {
        timePill.innerText = `${data.execution_time_ms} ms`;
    }

    if (traceContent && data.trace) {
        traceContent.innerHTML = `<pre>${JSON.stringify(data.trace, null, 2)}</pre>`;
    }
}
