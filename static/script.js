/* ================================================================
   EXPENSELENS AI — CLIENT SCRIPT
   Vanilla JavaScript only. Handles form interactivity, the edit
   modal, delete confirmations, file upload feedback, and renders
   every Chart.js visualization from data injected by Flask/Jinja.
   No ML/business logic lives here -- that all stays in Python.
================================================================ */

(function () {
    "use strict";

    const CHART_COLORS = [
        "#4C6EF5", "#7048E8", "#2F9E44", "#E8590C", "#E03131",
        "#0CA678", "#F59F00", "#1098AD", "#D6336C", "#5C7CFA",
        "#845EF7", "#37B24D", "#FF922B", "#495057", "#20C997",
    ];

    /* ============================================================
       CATEGORY "OTHER" TOGGLE (add + edit forms)
    ============================================================ */

    function wireCategoryToggle(selectEl, fieldEl) {
        if (!selectEl || !fieldEl) return;
        function sync() {
            fieldEl.hidden = selectEl.value !== "Other";
        }
        selectEl.addEventListener("change", sync);
        sync();
    }

    /* ============================================================
       FILE UPLOAD FEEDBACK
    ============================================================ */

    function wireFileInput(inputId, labelId, defaultText) {
        const input = document.getElementById(inputId);
        const label = document.getElementById(labelId);
        if (!input || !label) return;
        input.addEventListener("change", function () {
            label.textContent = input.files.length ? input.files[0].name : defaultText;
        });
    }

    /* ============================================================
       DELETE CONFIRMATION
    ============================================================ */

    function wireDeleteConfirmations() {
        document.querySelectorAll(".confirm-delete").forEach(function (btn) {
            btn.addEventListener("click", function (e) {
                if (!window.confirm("Delete this expense? This cannot be undone.")) {
                    e.preventDefault();
                }
            });
        });
    }

    /* ============================================================
       EDIT EXPENSE MODAL (expenses.html)
    ============================================================ */

    function initEditModal() {
        const modal = document.getElementById("editModal");
        const form = document.getElementById("editForm");
        if (!modal || !form) return;

        const closeBtn = document.getElementById("editModalClose");
        const categorySelect = document.getElementById("edit_category");
        const customField = document.getElementById("editCustomCategoryField");
        wireCategoryToggle(categorySelect, customField);

        document.querySelectorAll(".edit-btn").forEach(function (btn) {
            btn.addEventListener("click", function () {
                const id = btn.dataset.id;
                form.action = "/expenses/edit/" + id;
                document.getElementById("edit_date").value = btn.dataset.date;
                document.getElementById("edit_amount").value = btn.dataset.amount;
                document.getElementById("edit_description").value = btn.dataset.description || "";

                const category = btn.dataset.category;
                const knownOption = Array.from(categorySelect.options).some(function (o) { return o.value === category; });
                if (knownOption) {
                    categorySelect.value = category;
                    customField.hidden = true;
                } else {
                    categorySelect.value = "Other";
                    customField.hidden = false;
                    document.getElementById("edit_custom_category").value = category;
                }

                modal.classList.add("active");
            });
        });

        function close() { modal.classList.remove("active"); }
        if (closeBtn) closeBtn.addEventListener("click", close);
        modal.addEventListener("click", function (e) {
            if (e.target === modal) close();
        });
        document.addEventListener("keydown", function (e) {
            if (e.key === "Escape") close();
        });
    }

    /* ============================================================
       CHARTS
    ============================================================ */

    function renderCategoryPieChart() {
        const canvas = document.getElementById("categoryPieChart");
        const data = window.__CATEGORY_DATA__;
        if (!canvas || !data || !data.length || typeof Chart === "undefined") return;

        new Chart(canvas, {
            type: "doughnut",
            data: {
                labels: data.map(function (c) { return c.category; }),
                datasets: [{
                    data: data.map(function (c) { return c.amount; }),
                    backgroundColor: CHART_COLORS,
                    borderWidth: 0,
                }],
            },
            options: {
                responsive: true,
                plugins: { legend: { position: "right", labels: { boxWidth: 12, font: { size: 11 } } } },
            },
        });
    }

    function renderCategoryBarChart() {
        const canvas = document.getElementById("categoryBarChart");
        const data = window.__MONTH_SUMMARY__;
        if (!canvas || !data || !data.length || typeof Chart === "undefined") return;

        new Chart(canvas, {
            type: "bar",
            data: {
                labels: data.map(function (c) { return c.category; }),
                datasets: [{
                    label: "Amount Spent",
                    data: data.map(function (c) { return c.amount; }),
                    backgroundColor: "#4C6EF5",
                    borderRadius: 6,
                }],
            },
            options: {
                responsive: true,
                plugins: { legend: { display: false } },
                scales: { y: { beginAtZero: true } },
            },
        });
    }

    function renderYearlyTrendChart() {
        const canvas = document.getElementById("yearlyTrendChart");
        const data = window.__YEAR_SUMMARY__;
        const monthNames = window.__MONTH_NAMES__;
        if (!canvas || !data || !data.length || typeof Chart === "undefined") return;

        new Chart(canvas, {
            type: "line",
            data: {
                labels: data.map(function (m) { return monthNames[m.month - 1]; }),
                datasets: [{
                    label: "Monthly Spending",
                    data: data.map(function (m) { return m.total; }),
                    borderColor: "#7048E8",
                    backgroundColor: "rgba(112, 72, 232, 0.12)",
                    tension: 0.35,
                    fill: true,
                    pointRadius: 4,
                }],
            },
            options: {
                responsive: true,
                plugins: { legend: { display: false } },
                scales: { y: { beginAtZero: true } },
            },
        });
    }

    function renderFeatureImportanceChart() {
        const canvas = document.getElementById("featureImportanceChart");
        const data = window.__FEATURE_IMPORTANCE__;
        if (!canvas || !data || !data.length || typeof Chart === "undefined") return;

        new Chart(canvas, {
            type: "bar",
            data: {
                labels: data.map(function (f) { return f.feature; }),
                datasets: [{
                    label: "Importance (%)",
                    data: data.map(function (f) { return f.importance; }),
                    backgroundColor: "#2F9E44",
                    borderRadius: 6,
                }],
            },
            options: {
                indexAxis: "y",
                responsive: true,
                plugins: { legend: { display: false } },
                scales: { x: { beginAtZero: true } },
            },
        });
    }

    /* ============================================================
       LOADING OVERLAY (index.html upload form)
    ============================================================ */

    function initLoadingOverlay() {
        const overlay = document.getElementById("loadingOverlay");
        const uploadForm = document.getElementById("uploadForm");
        if (overlay && uploadForm) {
            uploadForm.addEventListener("submit", function () {
                overlay.classList.add("active");
            });
        }
    }

    /* ============================================================
       BOOTSTRAP
    ============================================================ */

    document.addEventListener("DOMContentLoaded", function () {
        wireCategoryToggle(document.getElementById("category"), document.getElementById("customCategoryField"));
        wireFileInput("csv_file", "importFilename", "Click to select a CSV file");
        wireDeleteConfirmations();
        initEditModal();
        initLoadingOverlay();

        renderCategoryPieChart();
        renderCategoryBarChart();
        renderYearlyTrendChart();
        renderFeatureImportanceChart();
    });
})();
