/**
 * Spend Tracker — Frontend Application Logic
 *
 * Handles API communication, form submission, data rendering, and UI state.
 * All API calls use the X-API-Key header stored in localStorage.
 */

// ── Configuration ────────────────────────────────────────────────────────────
const API_BASE = "http://localhost:8000";
const STORAGE_KEY = "spend_tracker_api_key";

// Category color map (matches CSS variables)
const CATEGORY_COLORS = {
    Food:          "hsl(15, 85%, 55%)",
    Transport:     "hsl(210, 75%, 55%)",
    Rent:          "hsl(270, 65%, 55%)",
    Utilities:     "hsl(45, 85%, 50%)",
    Entertainment: "hsl(330, 70%, 55%)",
    Shopping:      "hsl(160, 65%, 45%)",
    Health:        "hsl(0, 70%, 55%)",
    Education:     "hsl(195, 80%, 48%)",
    Other:         "hsl(220, 15%, 50%)",
};


// ── DOM References ───────────────────────────────────────────────────────────
const $ = (id) => document.getElementById(id);

const els = {
    apiKeyInput:       $("apiKeyInput"),
    toggleKeyBtn:      $("toggleKeyVisibility"),
    generateKeyBtn:    $("generateKeyBtn"),
    statusBanner:      $("statusBanner"),
    expenseForm:       $("expenseForm"),
    expenseAmount:     $("expenseAmount"),
    expenseCategory:   $("expenseCategory"),
    expenseNote:       $("expenseNote"),
    expenseDate:       $("expenseDate"),
    submitExpenseBtn:  $("submitExpenseBtn"),
    totalSpend:        $("totalSpend"),
    categoryCount:     $("categoryCount"),
    thisMonthSpend:    $("thisMonthSpend"),
    categoryBreakdown: $("categoryBreakdown"),
    momTable:          $("momTable"),
    expenseList:       $("expenseList"),
    filterCategory:    $("filterCategory"),
    filterStartDate:   $("filterStartDate"),
    filterEndDate:     $("filterEndDate"),
    applyFilters:      $("applyFilters"),
    insightsList:      $("insightsList"),
    insightsBadge:     $("insightsBadge"),
    // Modal
    keyModal:          $("keyModal"),
    keyName:           $("keyName"),
    generatedKeyDisplay: $("generatedKeyDisplay"),
    generatedKeyValue: $("generatedKeyValue"),
    confirmGenerateKey:$("confirmGenerateKey"),
    copyKeyBtn:        $("copyKeyBtn"),
    closeModal:        $("closeModal"),
};


// ── API Helper ───────────────────────────────────────────────────────────────

function getApiKey() {
    return els.apiKeyInput.value.trim();
}

async function apiFetch(path, options = {}) {
    const apiKey = getApiKey();
    const headers = {
        "Content-Type": "application/json",
        ...(apiKey ? { "X-API-Key": apiKey } : {}),
        ...(options.headers || {}),
    };

    const res = await fetch(`${API_BASE}${path}`, { ...options, headers });

    if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(body.detail || `HTTP ${res.status}`);
    }

    return res.json();
}


// ── Status Banner ────────────────────────────────────────────────────────────

let bannerTimeout = null;

function showBanner(message, type = "success") {
    els.statusBanner.textContent = message;
    els.statusBanner.className = `status-banner ${type}`;
    els.statusBanner.classList.remove("hidden");

    clearTimeout(bannerTimeout);
    bannerTimeout = setTimeout(() => {
        els.statusBanner.classList.add("hidden");
    }, 4000);
}


// ── Load Expenses ────────────────────────────────────────────────────────────

async function loadExpenses() {
    try {
        const params = new URLSearchParams();
        const cat = els.filterCategory.value;
        const start = els.filterStartDate.value;
        const end = els.filterEndDate.value;

        if (cat) params.set("category", cat);
        if (start) params.set("start_date", start);
        if (end) params.set("end_date", end);

        const qs = params.toString();
        const expenses = await apiFetch(`/expenses${qs ? "?" + qs : ""}`);
        renderExpenses(expenses);
    } catch (err) {
        els.expenseList.innerHTML = `<p class="empty-state">⚠ ${err.message}</p>`;
    }
}

function renderExpenses(expenses) {
    if (!expenses.length) {
        els.expenseList.innerHTML = '<p class="empty-state">No expenses yet</p>';
        return;
    }

    els.expenseList.innerHTML = expenses
        .map((e) => {
            const color = CATEGORY_COLORS[e.category] || CATEGORY_COLORS.Other;
            const dateStr = new Date(e.date).toLocaleDateString("en-IN", {
                day: "numeric",
                month: "short",
                year: "numeric",
            });
            return `
                <div class="expense-item">
                    <span class="expense-category-tag"
                          style="background: ${color}22; color: ${color}; border: 1px solid ${color}44;">
                        ${e.category}
                    </span>
                    <div class="expense-details">
                        <span class="expense-note">${e.note || "—"}</span>
                        <span class="expense-date">${dateStr}</span>
                    </div>
                    <span class="expense-amount">₹${e.amount.toFixed(2)}</span>
                </div>`;
        })
        .join("");
}


// ── Load Summary ─────────────────────────────────────────────────────────────

async function loadSummary() {
    try {
        const data = await apiFetch("/summary");
        renderSummary(data);
    } catch (err) {
        // Silently fail for summary — user will see empty state
        console.warn("Failed to load summary:", err.message);
    }
}

function renderSummary(data) {
    // Top cards
    els.totalSpend.textContent = `₹${data.total_spend.toFixed(2)}`;
    els.categoryCount.textContent = data.by_category.length;

    // Current month total
    const now = new Date();
    const currentMonthKey = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}`;
    const currentMonth = data.month_over_month.find((m) => m.month === currentMonthKey);
    els.thisMonthSpend.textContent = currentMonth
        ? `₹${currentMonth.total.toFixed(2)}`
        : "₹0.00";

    // Category breakdown
    renderCategoryBreakdown(data.by_category);

    // Month-over-month table
    renderMomTable(data.month_over_month);
}

function renderCategoryBreakdown(categories) {
    if (!categories.length) {
        els.categoryBreakdown.innerHTML =
            '<p class="empty-state">Add expenses to see the breakdown</p>';
        return;
    }

    const maxTotal = Math.max(...categories.map((c) => c.total));

    els.categoryBreakdown.innerHTML = categories
        .map((c) => {
            const color = CATEGORY_COLORS[c.category] || CATEGORY_COLORS.Other;
            const pct = maxTotal > 0 ? (c.total / maxTotal) * 100 : 0;
            return `
                <div class="category-row">
                    <span class="category-dot" style="background: ${color}"></span>
                    <span class="category-name">${c.category}</span>
                    <div class="category-bar-wrapper">
                        <div class="category-bar" style="width: ${pct}%; background: ${color}"></div>
                    </div>
                    <span class="category-amount">₹${c.total.toFixed(2)}</span>
                </div>`;
        })
        .join("");
}

function renderMomTable(months) {
    if (!months.length) {
        els.momTable.innerHTML =
            '<p class="empty-state">Add expenses to see trends</p>';
        return;
    }

    const rows = months
        .map((m) => {
            let changeClass = "change-neutral";
            let changeStr = "—";
            if (m.change_percent !== null) {
                changeClass =
                    m.change_percent > 0 ? "change-positive" : "change-negative";
                const sign = m.change_percent > 0 ? "+" : "";
                changeStr = `${sign}${m.change_percent.toFixed(1)}%`;
            }
            return `
                <tr>
                    <td>${m.month}</td>
                    <td>₹${m.total.toFixed(2)}</td>
                    <td class="${changeClass}">${changeStr}</td>
                </tr>`;
        })
        .join("");

    els.momTable.innerHTML = `
        <table>
            <thead>
                <tr>
                    <th>Month</th>
                    <th>Total</th>
                    <th>Change</th>
                </tr>
            </thead>
            <tbody>${rows}</tbody>
        </table>`;
}


// ── Load Insights ────────────────────────────────────────────────────────────

async function loadInsights() {
    try {
        const data = await apiFetch("/insights");
        renderInsights(data);
    } catch (err) {
        console.warn("Failed to load insights:", err.message);
    }
}

function renderInsights(data) {
    const flagged = data.flagged_categories;

    // Update badge
    els.insightsBadge.textContent = flagged.length;
    els.insightsBadge.className = flagged.length > 0 ? "badge alert" : "badge";

    if (!flagged.length) {
        els.insightsList.innerHTML =
            '<p class="empty-state">No alerts — your spending is steady 🎉</p>';
        return;
    }

    els.insightsList.innerHTML = flagged
        .map(
            (i) => `
            <div class="insight-item">
                <div class="insight-category">
                    ⚠ ${i.category} +${i.increase_percent.toFixed(1)}%
                </div>
                <div class="insight-detail">
                    ₹${i.previous_spend.toFixed(2)} (${i.previous_month})
                    → ₹${i.current_spend.toFixed(2)} (${i.current_month})
                </div>
            </div>`
        )
        .join("");
}


// ── Add Expense ──────────────────────────────────────────────────────────────

async function handleAddExpense(e) {
    e.preventDefault();

    const amount = parseFloat(els.expenseAmount.value);
    const category = els.expenseCategory.value;
    const note = els.expenseNote.value.trim();
    const date = els.expenseDate.value;

    // Client-side checks
    if (!amount || amount <= 0) {
        showBanner("Amount must be a positive number", "error");
        return;
    }
    if (!category) {
        showBanner("Please select a category", "error");
        return;
    }
    if (!date) {
        showBanner("Please select a date", "error");
        return;
    }
    if (!getApiKey()) {
        showBanner("Enter your API key first", "error");
        return;
    }

    try {
        els.submitExpenseBtn.disabled = true;
        els.submitExpenseBtn.textContent = "Adding…";

        await apiFetch("/expenses", {
            method: "POST",
            body: JSON.stringify({ amount, category, note: note || null, date }),
        });

        showBanner(`Added ₹${amount.toFixed(2)} for ${category}`, "success");
        els.expenseForm.reset();
        // Set date back to today
        els.expenseDate.value = todayISO();

        // Refresh all data
        await Promise.all([loadExpenses(), loadSummary(), loadInsights()]);
    } catch (err) {
        showBanner(err.message, "error");
    } finally {
        els.submitExpenseBtn.disabled = false;
        els.submitExpenseBtn.textContent = "Add Expense";
    }
}


// ── API Key Modal ────────────────────────────────────────────────────────────

function openModal() {
    els.keyModal.classList.remove("hidden");
    els.generatedKeyDisplay.classList.add("hidden");
    els.keyName.value = "";
    els.keyName.focus();
}

function closeModal() {
    els.keyModal.classList.add("hidden");
}

async function handleGenerateKey() {
    const name = els.keyName.value.trim();
    if (!name) {
        showBanner("Please enter a name for the key", "error");
        return;
    }

    try {
        els.confirmGenerateKey.disabled = true;
        els.confirmGenerateKey.textContent = "Generating…";

        const res = await fetch(`${API_BASE}/auth/generate-key`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ name }),
        });

        if (!res.ok) {
            const body = await res.json().catch(() => ({}));
            throw new Error(body.detail || `HTTP ${res.status}`);
        }

        const data = await res.json();
        els.generatedKeyValue.textContent = data.key;
        els.generatedKeyDisplay.classList.remove("hidden");

        // Auto-fill the API key input
        els.apiKeyInput.value = data.key;
        localStorage.setItem(STORAGE_KEY, data.key);

        showBanner("API key generated and saved!", "success");
    } catch (err) {
        showBanner(err.message, "error");
    } finally {
        els.confirmGenerateKey.disabled = false;
        els.confirmGenerateKey.textContent = "Generate";
    }
}


// ── Utilities ────────────────────────────────────────────────────────────────

function todayISO() {
    return new Date().toISOString().split("T")[0];
}


// ── Initialization ───────────────────────────────────────────────────────────

function init() {
    // Restore API key from localStorage
    const savedKey = localStorage.getItem(STORAGE_KEY);
    if (savedKey) {
        els.apiKeyInput.value = savedKey;
    }

    // Default the expense date to today
    els.expenseDate.value = todayISO();

    // Event listeners
    els.expenseForm.addEventListener("submit", handleAddExpense);
    els.applyFilters.addEventListener("click", loadExpenses);
    els.generateKeyBtn.addEventListener("click", openModal);
    els.confirmGenerateKey.addEventListener("click", handleGenerateKey);
    els.closeModal.addEventListener("click", closeModal);
    els.keyModal.addEventListener("click", (e) => {
        if (e.target === els.keyModal) closeModal();
    });

    // Toggle key visibility
    els.toggleKeyBtn.addEventListener("click", () => {
        const isPassword = els.apiKeyInput.type === "password";
        els.apiKeyInput.type = isPassword ? "text" : "password";
        els.toggleKeyBtn.textContent = isPassword ? "🙈" : "👁";
    });

    // Save API key to localStorage on change
    els.apiKeyInput.addEventListener("input", () => {
        localStorage.setItem(STORAGE_KEY, els.apiKeyInput.value);
    });

    // Copy key button
    els.copyKeyBtn.addEventListener("click", () => {
        navigator.clipboard.writeText(els.generatedKeyValue.textContent);
        els.copyKeyBtn.textContent = "Copied!";
        setTimeout(() => (els.copyKeyBtn.textContent = "Copy"), 2000);
    });

    // Initial data load (only if we have an API key)
    if (savedKey) {
        loadExpenses();
        loadSummary();
        loadInsights();
    }
}

document.addEventListener("DOMContentLoaded", init);
