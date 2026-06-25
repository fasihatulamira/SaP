// Application state
const SELECTION_STORAGE_KEY = "sap_listmap_selections";
const PAGE_SIZE_STORAGE_KEY = "sap_listmap_page_size";
const PAGE_SIZE_OPTIONS = [8, 10, 15];
const DEFAULT_PAGE_SIZE = 10;

const state = {
    records: {
        topography: [],
        dted: [],
        landused: [],
        sjungu: []
    },
    selected: {
        topography: new Map(),
        dted: new Map(),
        landused: new Map(),
        sjungu: new Map()
    },
    filters: {
        topo_search: "",
        topo_year: "",
        dted_search: "",
        dted_level: "",
        land_search: "",
        sjungu_search: ""
    },
    pagination: {
        topography: { page: 1, limit: 10, total: 0, totalPages: 1 },
        dted: { page: 1, limit: 10, total: 0, totalPages: 1 },
        landused: { page: 1, limit: 10, total: 0, totalPages: 1 },
        sjungu: { page: 1, limit: 10, total: 0, totalPages: 1 }
    },
    activeTab: "topography",
    ui: { loading: false },
    reportRef: null,
    user: { username: "", role: "user" }
};

const DOM = {
    tabs: document.querySelectorAll(".tab-btn"),
    contents: document.querySelectorAll(".category-content"),
    themeToggle: document.getElementById("theme-toggle"),
    topoSearch: document.getElementById("topo-search"),
    topoYear: document.getElementById("topo-year"),
    topoTableBody: document.getElementById("topo-table-body"),
    topoPrev: document.getElementById("topo-prev"),
    topoNext: document.getElementById("topo-next"),
    topoPageInfo: document.getElementById("topo-page-info"),
    topoSelectAll: document.getElementById("topo-select-all"),
    dtedSearch: document.getElementById("dted-search"),
    dtedLevel: document.getElementById("dted-level"),
    dtedTableBody: document.getElementById("dted-table-body"),
    dtedPrev: document.getElementById("dted-prev"),
    dtedNext: document.getElementById("dted-next"),
    dtedPageInfo: document.getElementById("dted-page-info"),
    dtedSelectAll: document.getElementById("dted-select-all"),
    landSearch: document.getElementById("land-search"),
    landTableBody: document.getElementById("land-table-body"),
    landPrev: document.getElementById("land-prev"),
    landNext: document.getElementById("land-next"),
    landPageInfo: document.getElementById("land-page-info"),
    landSelectAll: document.getElementById("land-select-all"),
    sjunguSearch: document.getElementById("sjungu-search"),
    sjunguTableBody: document.getElementById("sjungu-table-body"),
    sjunguPrev: document.getElementById("sjungu-prev"),
    sjunguNext: document.getElementById("sjungu-next"),
    sjunguPageInfo: document.getElementById("sjungu-page-info"),
    sjunguSelectAll: document.getElementById("sjungu-select-all"),
    docContent: document.getElementById("doc-content"),
    docDate: document.getElementById("doc-date"),
    btnPrint: document.getElementById("btn-print"),
    btnPdf: document.getElementById("btn-pdf"),
    btnXlsx: document.getElementById("btn-xlsx"),
    btnAuditLog: document.getElementById("btn-audit-log"),
    btnClearSelection: document.getElementById("btn-clear-selection"),
    docTitleInput: document.getElementById("doc-title-input"),
    statusBanner: document.getElementById("status-banner"),
    docRef: document.getElementById("doc-ref"),
    docPageInfo: document.getElementById("doc-page-info"),
    auditModal: document.getElementById("audit-modal"),
    auditModalBackdrop: document.getElementById("audit-modal-backdrop"),
    auditModalClose: document.getElementById("audit-modal-close"),
    auditModalRefresh: document.getElementById("audit-modal-refresh"),
    auditTableBody: document.getElementById("audit-table-body"),
    pageSizeSelect: document.getElementById("page-size-select")
};

const TABLE_CONFIG = {
    topography: {
        keyProp: "sheetNum",
        tableBody: () => DOM.topoTableBody,
        pageInfo: () => DOM.topoPageInfo,
        prevBtn: () => DOM.topoPrev,
        nextBtn: () => DOM.topoNext,
        selectAllBtn: () => DOM.topoSelectAll,
        colspan: 5,
        emptyMessage: "No topography records found",
        rowLabel: (row) => `Select topography sheet ${row.sheetNum}`,
        columns: [
            { style: "font-weight: 600; color: var(--primary-light);", value: (row) => row.sheetNum },
            { value: (row) => row.sheetName },
            { value: (row) => row.sheetScale },
            { value: (row) => row.release_year }
        ]
    },
    dted: {
        keyProp: "id_name",
        tableBody: () => DOM.dtedTableBody,
        pageInfo: () => DOM.dtedPageInfo,
        prevBtn: () => DOM.dtedPrev,
        nextBtn: () => DOM.dtedNext,
        selectAllBtn: () => DOM.dtedSelectAll,
        colspan: 4,
        emptyMessage: "No DTED records found",
        rowLabel: (row) => `Select DTED file ${row.id_name}`,
        columns: [
            { listIndex: true, style: "text-align: center; font-weight: 600; color: var(--text-muted);" },
            { style: "word-break: break-all;", value: (row) => row.id_name },
            {
                html: (row) => `<span class="badge" style="background: rgba(6, 182, 212, 0.15); color: var(--accent); padding: 0.2rem 0.5rem; border-radius: 4px; font-weight: 600;">Level ${escapeHtml(row.level)}</span>`
            }
        ]
    },
    landused: {
        keyProp: "landused_id",
        tableBody: () => DOM.landTableBody,
        pageInfo: () => DOM.landPageInfo,
        prevBtn: () => DOM.landPrev,
        nextBtn: () => DOM.landNext,
        selectAllBtn: () => DOM.landSelectAll,
        colspan: 4,
        emptyMessage: "No land use categories found",
        rowLabel: (row) => `Select land use category ${row.category}`,
        columns: [
            { listIndex: true, style: "text-align: center; font-weight: 600; color: var(--text-muted);" },
            { value: (row) => row.category },
            { value: (row) => row.landused_id, style: "font-weight: 600; color: var(--primary-light);" }
        ]
    },
    sjungu: {
        keyProp: "sheetNum",
        tableBody: () => DOM.sjunguTableBody,
        pageInfo: () => DOM.sjunguPageInfo,
        prevBtn: () => DOM.sjunguPrev,
        nextBtn: () => DOM.sjunguNext,
        selectAllBtn: () => DOM.sjunguSelectAll,
        colspan: 4,
        emptyMessage: "No Sjung records found",
        rowLabel: (row) => `Select Sjung sheet ${row.sheetNum}`,
        columns: [
            { style: "font-weight: 600; color: var(--primary-light);", value: (row) => row.sheetNum },
            { value: (row) => row.sheetName },
            { value: (row) => row.sheetScale }
        ]
    }
};

function handleAuthFailure(response) {
    if (response.status === 401) {
        window.location.href = "/login?next=" + encodeURIComponent(window.location.pathname);
        return true;
    }
    return false;
}

function escapeHtml(value) {
    if (value === null || value === undefined) return "";
    return String(value)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#39;");
}

function showStatusBanner(message, type = "error") {
    if (!DOM.statusBanner) return;
    DOM.statusBanner.className = `status-banner ${type}`;
    DOM.statusBanner.innerHTML = `<i class="fas fa-exclamation-circle"></i> ${escapeHtml(message)}`;
    DOM.statusBanner.classList.remove("hidden");
}

function hideStatusBanner() {
    if (!DOM.statusBanner) return;
    DOM.statusBanner.classList.add("hidden");
    DOM.statusBanner.textContent = "";
}

function setTableLoading(tableBody, colspan) {
    tableBody.innerHTML = `<tr><td colspan="${colspan}" class="loading-row"><i class="fas fa-spinner fa-spin"></i> Loading records...</td></tr>`;
}

function setCategoryTableLoading(category) {
    const config = TABLE_CONFIG[category];
    setTableLoading(config.tableBody(), config.colspan);
    config.pageInfo().textContent = "Loading...";
}

function renderCategoryError(category) {
    const config = TABLE_CONFIG[category];
    config.tableBody().innerHTML = `<tr><td colspan="${config.colspan}" style="text-align: center; color: var(--text-muted);">Unable to load records</td></tr>`;
    config.pageInfo().textContent = "—";
}

function buildCategoryParams(category) {
    const { page, limit } = state.pagination[category];
    const params = new URLSearchParams({ page: String(page), limit: String(limit) });

    if (category === "topography") {
        if (state.filters.topo_search) params.set("search", state.filters.topo_search);
        if (state.filters.topo_year) params.set("year", state.filters.topo_year);
    } else if (category === "dted") {
        if (state.filters.dted_search) params.set("search", state.filters.dted_search);
        if (state.filters.dted_level) params.set("level", state.filters.dted_level);
    } else if (category === "landused") {
        if (state.filters.land_search) params.set("search", state.filters.land_search);
    } else if (category === "sjungu") {
        if (state.filters.sjungu_search) params.set("search", state.filters.sjungu_search);
    }

    return params;
}

async function fetchCategoryRecords(category, resetPage = false) {
    if (!TABLE_CONFIG[category]) return;

    if (resetPage) {
        state.pagination[category].page = 1;
    }

    setCategoryTableLoading(category);
    state.ui.loading = true;

    try {
        const params = buildCategoryParams(category);
        const response = await fetch(`/api/records/${category}?${params.toString()}`);
        if (handleAuthFailure(response)) return;

        const data = await response.json();

        if (!response.ok || data.error) {
            showStatusBanner(data.error || "Failed to load records.", "error");
            renderCategoryError(category);
            return;
        }

        hideStatusBanner();

        state.records[category] = data.items;
        state.pagination[category].page = data.page;
        state.pagination[category].limit = data.limit;
        state.pagination[category].total = data.total;
        state.pagination[category].totalPages = data.total_pages;

        renderCategoryTable(category);
    } catch (e) {
        console.error(`Network error fetching ${category} records:`, e);
        showStatusBanner("Could not connect to the server. Check that the app is running.", "error");
        renderCategoryError(category);
    } finally {
        state.ui.loading = false;
    }
}

function saveSelectionsToSession() {
    try {
        const payload = {
            topography: Array.from(state.selected.topography.entries()),
            dted: Array.from(state.selected.dted.entries()),
            landused: Array.from(state.selected.landused.entries()),
            sjungu: Array.from(state.selected.sjungu.entries()),
            reportRef: state.reportRef
        };
        sessionStorage.setItem(SELECTION_STORAGE_KEY, JSON.stringify(payload));
    } catch (e) {
        console.warn("Could not save selections to sessionStorage:", e);
    }
}

function loadSelectionsFromSession() {
    try {
        const raw = sessionStorage.getItem(SELECTION_STORAGE_KEY);
        if (!raw) return;

        const data = JSON.parse(raw);
        ["topography", "dted", "landused", "sjungu"].forEach((category) => {
            state.selected[category] = new Map(data[category] || []);
        });
        state.reportRef = data.reportRef || null;
    } catch (e) {
        console.warn("Could not restore selections from sessionStorage:", e);
        sessionStorage.removeItem(SELECTION_STORAGE_KEY);
    }
}

function clearSelectionsFromSession() {
    sessionStorage.removeItem(SELECTION_STORAGE_KEY);
}

function applyPageSize(limit) {
    const size = PAGE_SIZE_OPTIONS.includes(limit) ? limit : DEFAULT_PAGE_SIZE;
    Object.keys(state.pagination).forEach((category) => {
        state.pagination[category].limit = size;
        state.pagination[category].page = 1;
    });
    if (DOM.pageSizeSelect) {
        DOM.pageSizeSelect.value = String(size);
    }
    try {
        localStorage.setItem(PAGE_SIZE_STORAGE_KEY, String(size));
    } catch (e) {
        console.warn("Could not save page size preference:", e);
    }
}

function initPageSize() {
    let saved = DEFAULT_PAGE_SIZE;
    try {
        const stored = parseInt(localStorage.getItem(PAGE_SIZE_STORAGE_KEY), 10);
        if (PAGE_SIZE_OPTIONS.includes(stored)) {
            saved = stored;
        }
    } catch (e) {
        /* use default */
    }
    applyPageSize(saved);
}

function onPageSizeChange() {
    if (!DOM.pageSizeSelect) return;
    const limit = parseInt(DOM.pageSizeSelect.value, 10);
    applyPageSize(limit);
    fetchCategoryRecords(state.activeTab, true);
}

document.addEventListener("DOMContentLoaded", () => {
    initTheme();
    initPageSize();
    loadSelectionsFromSession();
    fetchCurrentUser();
    fetchFilters();
    fetchCategoryRecords("topography");
    setupEventListeners();
    updateDocDate();
    renderDocumentPreview();
});

async function fetchCurrentUser() {
    try {
        const response = await fetch("/api/me");
        if (handleAuthFailure(response)) return;
        if (!response.ok) return;
        const data = await response.json();
        state.user = { username: data.username || "", role: data.role || "user" };
    } catch (e) {
        console.warn("Could not load user profile:", e);
    }
}

const LIST_SORT = {
    topography: (a, b) => String(a.sheetNum).localeCompare(String(b.sheetNum)),
    dted: (a, b) => String(a.id_name).localeCompare(String(b.id_name)),
    landused: (a, b) => Number(a.landused_id) - Number(b.landused_id),
    sjungu: (a, b) => String(a.sheetNum).localeCompare(String(b.sheetNum))
};

function getSelectedSorted(category) {
    const items = Array.from(state.selected[category].values());
    const sorter = LIST_SORT[category];
    if (!sorter) return items;
    return items.sort(sorter);
}

function getSelectionPayload() {
    return {
        topography: getSelectedSorted("topography"),
        dted: getSelectedSorted("dted"),
        landused: getSelectedSorted("landused"),
        sjungu: getSelectedSorted("sjungu")
    };
}

function getSelectionCount() {
    const payload = getSelectionPayload();
    return payload.topography.length + payload.dted.length + payload.landused.length + payload.sjungu.length;
}

const AUDIT_ACTION_LABELS = {
    login_failed: "Failed sign in",
    create_report: "Report created",
    export_xlsx: "Excel export",
    export_pdf: "PDF export",
    print: "Print",
    clear_selection: "Clear selection"
};

const AUDIT_ACTIONS_WITHOUT_SELECTION = new Set(["clear_selection", "login_failed"]);

function formatAuditAction(action) {
    return AUDIT_ACTION_LABELS[action] || action;
}

function formatAuditDetails(entry) {
    const bits = [];
    if (entry.details && typeof entry.details === "object") {
        Object.entries(entry.details).forEach(([key, value]) => {
            if (value != null && value !== "") {
                bits.push(`${key}: ${value}`);
            }
        });
    }
    return bits.length ? bits.join(" · ") : "—";
}

async function recordAudit(action, extra = {}) {
    const item_count = extra.item_count ?? getSelectionCount();
    if (item_count === 0 && !AUDIT_ACTIONS_WITHOUT_SELECTION.has(action)) {
        return;
    }
    try {
        const response = await fetch("/api/audit", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                action,
                report_ref: state.reportRef,
                item_count,
                details: extra.details || null
            })
        });
        if (!response.ok) {
            console.warn("Audit log failed:", response.status, await response.text());
        }
    } catch (e) {
        console.warn("Audit log failed:", e);
    }
}

function initTheme() {
    const savedTheme = localStorage.getItem("theme") || "light";
    if (savedTheme === "light") {
        document.body.classList.add("light-theme");
        DOM.themeToggle.innerHTML = '<i class="fas fa-moon"></i>';
    } else {
        document.body.classList.remove("light-theme");
        DOM.themeToggle.innerHTML = '<i class="fas fa-sun"></i>';
    }
}

function toggleTheme() {
    const isLight = document.body.classList.toggle("light-theme");
    localStorage.setItem("theme", isLight ? "light" : "dark");
    DOM.themeToggle.innerHTML = isLight ? '<i class="fas fa-moon"></i>' : '<i class="fas fa-sun"></i>';
}

async function fetchFilters() {
    try {
        const response = await fetch("/api/filters");
        if (handleAuthFailure(response)) return;

        const data = await response.json();

        if (!response.ok || data.error) {
            showStatusBanner(data.error || "Failed to load filter options.", "warning");
            return;
        }

        DOM.topoYear.innerHTML = '<option value="">All Release Years</option>';
        data.release_years.forEach((year) => {
            const option = document.createElement("option");
            option.value = year;
            option.textContent = year;
            DOM.topoYear.appendChild(option);
        });

        DOM.dtedLevel.innerHTML = '<option value="">All Levels</option>';
        data.dted_levels.forEach((level) => {
            const option = document.createElement("option");
            option.value = level;
            option.textContent = `Level ${level}`;
            DOM.dtedLevel.appendChild(option);
        });
    } catch (e) {
        console.error("Network error fetching filters:", e);
        showStatusBanner("Could not connect to the server. Check that the app is running.", "error");
    }
}

function renderAllTables() {
    Object.keys(TABLE_CONFIG).forEach(renderCategoryTable);
    renderDocumentPreview();
}

function renderCategoryTable(category) {
    const config = TABLE_CONFIG[category];
    const list = state.records[category];
    const { page, total, totalPages } = state.pagination[category];
    const tableBody = config.tableBody();

    tableBody.innerHTML = "";

    if (list.length === 0) {
        tableBody.innerHTML = `<tr><td colspan="${config.colspan}" style="text-align: center; color: var(--text-muted);">${config.emptyMessage}</td></tr>`;
        config.pageInfo().textContent = total ? `Page 1 of ${totalPages} (${total} records)` : "0 records";
        return;
    }

    list.forEach((row, rowIdx) => {
        const key = row[config.keyProp];
        const isSelected = state.selected[category].has(key);
        const tr = document.createElement("tr");
        tr.setAttribute("role", "row");
        tr.tabIndex = 0;
        tr.setAttribute("aria-selected", isSelected ? "true" : "false");
        if (isSelected) tr.classList.add("selected");

        const checkTd = document.createElement("td");
        const checkbox = document.createElement("input");
        checkbox.type = "checkbox";
        checkbox.className = "row-select-checkbox";
        checkbox.checked = isSelected;
        checkbox.setAttribute("aria-label", config.rowLabel(row));
        checkbox.addEventListener("click", (e) => e.stopPropagation());
        checkbox.addEventListener("change", () => {
            toggleSelection(category, key, row);
            renderCategoryTable(category);
        });
        checkTd.appendChild(checkbox);
        tr.appendChild(checkTd);

        const { page, limit } = state.pagination[category];
        config.columns.forEach((col) => {
            const td = document.createElement("td");
            if (col.style) td.style.cssText = col.style;
            if (col.listIndex) {
                td.textContent = String((page - 1) * limit + rowIdx + 1);
            } else if (col.html) {
                td.innerHTML = col.html(row);
            } else {
                td.textContent = col.value(row) ?? "";
            }
            tr.appendChild(td);
        });

        const activateRow = () => {
            toggleSelection(category, key, row);
            renderCategoryTable(category);
        };
        tr.addEventListener("click", activateRow);
        tr.addEventListener("keydown", (e) => {
            if (e.key === "Enter" || e.key === " ") {
                e.preventDefault();
                activateRow();
            }
        });

        tableBody.appendChild(tr);
    });

    config.pageInfo().textContent = `Page ${page} of ${totalPages} (${total} records)`;
    config.prevBtn().disabled = page === 1;
    config.nextBtn().disabled = page >= totalPages;
    updateSelectAllCheckboxState(category, list);
}

function toggleSelection(category, id, rowData) {
    const catMap = state.selected[category];
    if (catMap.has(id)) {
        catMap.delete(id);
    } else {
        catMap.set(id, rowData);
    }
    saveSelectionsToSession();
    renderDocumentPreview();
}

function toggleSelectAll(category) {
    const pageItems = state.records[category];
    const catMap = state.selected[category];
    const keyProp = TABLE_CONFIG[category].keyProp;
    const allSelected = pageItems.every((row) => catMap.has(row[keyProp]));

    if (allSelected) {
        pageItems.forEach((row) => catMap.delete(row[keyProp]));
    } else {
        pageItems.forEach((row) => catMap.set(row[keyProp], row));
    }

    saveSelectionsToSession();
    renderAllTables();
}

function updateSelectAllCheckboxState(category, pageItems) {
    const catMap = state.selected[category];
    const keyProp = TABLE_CONFIG[category].keyProp;
    const checkAllBtn = TABLE_CONFIG[category].selectAllBtn();

    if (pageItems.length === 0) {
        checkAllBtn.innerHTML = '<i class="far fa-square"></i> Select Page';
        return;
    }

    const allSelected = pageItems.every((row) => catMap.has(row[keyProp]));
    const someSelected = pageItems.some((row) => catMap.has(row[keyProp]));

    if (allSelected) {
        checkAllBtn.innerHTML = '<i class="fas fa-check-square" style="color: var(--success);"></i> Select Page';
    } else if (someSelected) {
        checkAllBtn.innerHTML = '<i class="fas fa-minus-square" style="color: var(--primary-light);"></i> Select Page';
    } else {
        checkAllBtn.innerHTML = '<i class="far fa-square"></i> Select Page';
    }
}

function clearAllSelection() {
    const prevCount = getSelectionCount();
    const prevRef = state.reportRef;
    state.selected.topography.clear();
    state.selected.dted.clear();
    state.selected.landused.clear();
    state.selected.sjungu.clear();
    state.reportRef = null;
    clearSelectionsFromSession();
    renderAllTables();
    if (prevCount > 0) {
        recordAudit("clear_selection", { item_count: prevCount, details: { report_ref: prevRef } });
    }
}

function generateReportRef() {
    const now = new Date();
    const year = now.getFullYear();
    const stamp = String(now.getTime()).slice(-5);
    const suffix = Math.random().toString(36).substring(2, 4).toUpperCase();
    return `LM-${year}-${stamp}${suffix}`;
}

function estimatePageCount(selectedTopo, selectedDted, selectedLand, selectedSjungu) {
    const rowCount = selectedTopo.length + selectedSjungu.length + selectedLand.length + selectedDted.length;
    const sectionCount = [
        selectedTopo.length + selectedSjungu.length,
        selectedLand.length,
        selectedDted.length
    ].filter((n) => n > 0).length;

    const totalRows = rowCount + sectionCount;
    const rowsPerPage = 22;
    return Math.max(1, Math.ceil(totalRows / rowsPerPage));
}

function updateDocumentMetadata(selectedTopo, selectedDted, selectedLand, selectedSjungu) {
    if (!state.reportRef) {
        state.reportRef = generateReportRef();
        saveSelectionsToSession();
        recordAudit("create_report");
    }
    if (DOM.docRef) {
        DOM.docRef.textContent = state.reportRef;
    }
    if (DOM.docPageInfo) {
        const totalPages = estimatePageCount(selectedTopo, selectedDted, selectedLand, selectedSjungu);
        DOM.docPageInfo.textContent = `Page 1 of ${totalPages}`;
    }
}

function formatTopoSjungTotal(topoCount, sjungCount) {
    if (topoCount > 0 && sjungCount > 0) {
        return `${topoCount} + ${sjungCount}`;
    }
    return String(topoCount || sjungCount);
}

function renderDocumentPreview() {
    const selectedTopo = getSelectedSorted("topography");
    const selectedDted = getSelectedSorted("dted");
    const selectedLand = getSelectedSorted("landused");
    const selectedSjungu = getSelectedSorted("sjungu");
    const hasItems = selectedTopo.length > 0 || selectedDted.length > 0 || selectedLand.length > 0 || selectedSjungu.length > 0;

    if (!hasItems) {
        DOM.docContent.innerHTML = `
            <div class="empty-state">
                <div class="empty-state-icon"><i class="fas fa-file-invoice"></i></div>
                <h3>Your Document is Empty</h3>
                <p>Select records from the categories in the left panel to compile your customized map & topography report.</p>
            </div>
        `;
        DOM.btnClearSelection.disabled = true;
        DOM.btnPrint.disabled = true;
        DOM.btnPdf.disabled = true;
        if (DOM.btnXlsx) DOM.btnXlsx.disabled = true;
        if (DOM.docRef) DOM.docRef.textContent = "—";
        if (DOM.docPageInfo) DOM.docPageInfo.textContent = "Page 1 of 1";
        return;
    }

    updateDocumentMetadata(selectedTopo, selectedDted, selectedLand, selectedSjungu);

    DOM.btnClearSelection.disabled = false;
    DOM.btnPrint.disabled = false;
    DOM.btnPdf.disabled = false;
    if (DOM.btnXlsx) DOM.btnXlsx.disabled = false;

    let html = "";

    if (selectedTopo.length > 0 || selectedSjungu.length > 0) {
        const totalCount = selectedTopo.length + selectedSjungu.length;
        const totalLabel = formatTopoSjungTotal(selectedTopo.length, selectedSjungu.length);
        html += `
            <div class="doc-section">
                <div class="doc-section-title">
                    <span>1. TOPOGRAPHY & SJUNG RECORDS</span>
                    <span class="doc-section-count">${totalCount} item(s)</span>
                </div>
                <table class="doc-table">
                    <thead>
                        <tr>
                            <th style="width: 8%; text-align: center;">No.</th>
                            <th style="width: 22%;">Sheet Number</th>
                            <th style="width: 40%;">Sheet Name</th>
                            <th style="width: 15%;">Scale</th>
                            <th style="width: 15%;">Year</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${selectedTopo.map((row, idx) => `
                            <tr>
                                <td style="text-align: center; font-weight: 600; color: #64748b;">${idx + 1}.</td>
                                <td style="font-weight: 700; color: #1e3a8a;">${escapeHtml(row.sheetNum)}</td>
                                <td>${escapeHtml(row.sheetName)}</td>
                                <td>${escapeHtml(row.sheetScale)}</td>
                                <td>${escapeHtml(row.release_year)}</td>
                            </tr>
                        `).join("")}
                        ${selectedSjungu.map((row, idx) => `
                            <tr>
                                <td style="text-align: center; font-weight: 600; color: #64748b;">${idx + 1}.</td>
                                <td style="font-weight: 700; color: #1e3a8a;">${escapeHtml(row.sheetNum)}</td>
                                <td>${escapeHtml(row.sheetName)}</td>
                                <td>${escapeHtml(row.sheetScale)}</td>
                                <td></td>
                            </tr>
                        `).join("")}
                        <tr class="doc-total-row">
                            <td colspan="4">TOTAL</td>
                            <td>${totalLabel}</td>
                        </tr>
                    </tbody>
                </table>
            </div>
        `;
    }

    if (selectedLand.length > 0) {
        html += `
            <div class="doc-section doc-section-follow">
                <div class="doc-section-title">
                    <span>2. LAND USE CATEGORIES</span>
                    <span class="doc-section-count">${selectedLand.length} item(s)</span>
                </div>
                <table class="doc-table">
                    <thead>
                        <tr>
                            <th style="width: 10%; text-align: center;">No.</th>
                            <th style="width: 55%;">Category</th>
                            <th style="width: 35%;">Land Used ID</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${selectedLand.map((row, idx) => `
                            <tr>
                                <td style="text-align: center; font-weight: 600; color: #64748b;">${idx + 1}.</td>
                                <td>${escapeHtml(row.category)}</td>
                                <td style="font-weight: 700;">${escapeHtml(row.landused_id)}</td>
                            </tr>
                        `).join("")}
                        <tr class="doc-total-row">
                            <td colspan="2">TOTAL</td>
                            <td>${selectedLand.length}</td>
                        </tr>
                    </tbody>
                </table>
            </div>
        `;
    }

    if (selectedDted.length > 0) {
        html += `
            <div class="doc-section doc-section-follow">
                <div class="doc-section-title">
                    <span>3. DIGITAL TERRAIN ELEVATION DATA (DTED)</span>
                    <span class="doc-section-count">${selectedDted.length} item(s)</span>
                </div>
                <table class="doc-table">
                    <thead>
                        <tr>
                            <th style="width: 8%; text-align: center;">No.</th>
                            <th style="width: 72%;">Elevation ID / File Name</th>
                            <th style="width: 20%;">DTED Level</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${selectedDted.map((row, idx) => `
                            <tr>
                                <td style="text-align: center; font-weight: 600; color: #64748b;">${idx + 1}.</td>
                                <td style="font-family: monospace; font-size: 0.75rem;">${escapeHtml(row.id_name)}</td>
                                <td style="font-weight: 700;">Level ${escapeHtml(row.level)}</td>
                            </tr>
                        `).join("")}
                        <tr class="doc-total-row">
                            <td colspan="2">TOTAL</td>
                            <td>${selectedDted.length}</td>
                        </tr>
                    </tbody>
                </table>
            </div>
        `;
    }

    DOM.docContent.innerHTML = html;
}

async function exportExcel() {
    const payload = getSelectionPayload();
    const itemCount = getSelectionCount();
    if (itemCount === 0) return;

    if (DOM.btnXlsx) {
        DOM.btnXlsx.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Excel';
        DOM.btnXlsx.disabled = true;
    }

    try {
        const response = await fetch("/api/export/xlsx", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                ...payload,
                report_ref: state.reportRef,
                report_title: DOM.docTitleInput.value.trim() || "SaP LISTMAP DATA SPECIFICATION REPORT"
            })
        });
        if (handleAuthFailure(response)) return;
        if (!response.ok) {
            const err = await response.json();
            showStatusBanner(err.error || "Excel export failed.", "error");
            return;
        }

        const blob = await response.blob();
        const url = URL.createObjectURL(blob);
        const link = document.createElement("a");
        const refSuffix = state.reportRef ? `_${state.reportRef}` : "";
        link.href = url;
        link.download = `SaP_ListMap_Export${refSuffix}_${new Date().toISOString().split("T")[0]}.xlsx`;
        link.click();
        URL.revokeObjectURL(url);
    } catch (e) {
        console.error("Excel export failed:", e);
        showStatusBanner("Excel export failed.", "error");
    } finally {
        if (DOM.btnXlsx) {
            DOM.btnXlsx.innerHTML = '<i class="fas fa-file-excel"></i> Excel';
            DOM.btnXlsx.disabled = getSelectionCount() === 0;
        }
    }
}

function updateDocumentTitleText() {
    const inputTitle = DOM.docTitleInput.value.trim();
    const docTitleEl = document.getElementById("document-title-header");
    if (docTitleEl) {
        docTitleEl.textContent = inputTitle || "SaP LISTMAP DATA SPECIFICATION REPORT";
    }
}

function setPdfCaptureMode(enabled) {
    const frame = document.getElementById("printable-document");
    if (frame) frame.classList.toggle("pdf-capture", enabled);
    if (DOM.docContent) DOM.docContent.classList.toggle("pdf-capture", enabled);
}

function waitForReflow() {
    return new Promise((resolve) => {
        requestAnimationFrame(() => requestAnimationFrame(resolve));
    });
}

async function generatePDF() {
    const element = document.getElementById("printable-document");
    const refSuffix = state.reportRef ? `_${state.reportRef}` : "";
    const opt = {
        margin: 15,
        filename: `SaP_ListMap_Report${refSuffix}_${new Date().toISOString().split("T")[0]}.pdf`,
        image: { type: "jpeg", quality: 0.98 },
        html2canvas: { scale: 2, useCORS: true, logging: false, scrollY: 0 },
        jsPDF: { unit: "mm", format: "a4", orientation: "portrait" },
        pagebreak: {
            mode: ["css", "legacy"],
            avoid: "tr"
        }
    };

    DOM.btnPdf.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Generating...';
    DOM.btnPdf.disabled = true;

    setPdfCaptureMode(true);
    await waitForReflow();

    try {
        const pdf = await html2pdf().set(opt).from(element).toPdf().get("pdf");
        const totalPages = pdf.internal.getNumberOfPages();
        if (DOM.docPageInfo) {
            DOM.docPageInfo.textContent = `Page 1 of ${totalPages}`;
        }
        pdf.save(opt.filename);
        recordAudit("export_pdf");
    } catch (err) {
        console.error("PDF generation failed:", err);
        showStatusBanner("PDF generation failed.", "error");
    } finally {
        setPdfCaptureMode(false);
        DOM.btnPdf.innerHTML = '<i class="fas fa-file-pdf"></i> Generate PDF';
        DOM.btnPdf.disabled = getSelectionCount() === 0;
    }
}

function setupEventListeners() {
    DOM.tabs.forEach((tab) => {
        tab.addEventListener("click", () => {
            const target = tab.getAttribute("data-tab");
            DOM.tabs.forEach((t) => t.classList.remove("active"));
            DOM.contents.forEach((c) => c.classList.remove("active"));
            tab.classList.add("active");
            document.getElementById(`${target}-content`).classList.add("active");
            state.activeTab = target;
            fetchCategoryRecords(target);
        });
    });

    DOM.themeToggle.addEventListener("click", toggleTheme);

    DOM.topoSearch.addEventListener("input", debounce(() => {
        state.filters.topo_search = DOM.topoSearch.value;
        fetchCategoryRecords("topography", true);
    }, 300));
    DOM.topoYear.addEventListener("change", () => {
        state.filters.topo_year = DOM.topoYear.value;
        fetchCategoryRecords("topography", true);
    });
    DOM.topoSelectAll.addEventListener("click", () => toggleSelectAll("topography"));
    DOM.topoPrev.addEventListener("click", () => {
        if (state.pagination.topography.page > 1) {
            state.pagination.topography.page--;
            fetchCategoryRecords("topography");
        }
    });
    DOM.topoNext.addEventListener("click", () => {
        if (state.pagination.topography.page < state.pagination.topography.totalPages) {
            state.pagination.topography.page++;
            fetchCategoryRecords("topography");
        }
    });

    DOM.dtedSearch.addEventListener("input", debounce(() => {
        state.filters.dted_search = DOM.dtedSearch.value;
        fetchCategoryRecords("dted", true);
    }, 300));
    DOM.dtedLevel.addEventListener("change", () => {
        state.filters.dted_level = DOM.dtedLevel.value;
        fetchCategoryRecords("dted", true);
    });
    DOM.dtedSelectAll.addEventListener("click", () => toggleSelectAll("dted"));
    DOM.dtedPrev.addEventListener("click", () => {
        if (state.pagination.dted.page > 1) {
            state.pagination.dted.page--;
            fetchCategoryRecords("dted");
        }
    });
    DOM.dtedNext.addEventListener("click", () => {
        if (state.pagination.dted.page < state.pagination.dted.totalPages) {
            state.pagination.dted.page++;
            fetchCategoryRecords("dted");
        }
    });

    DOM.landSearch.addEventListener("input", debounce(() => {
        state.filters.land_search = DOM.landSearch.value;
        fetchCategoryRecords("landused", true);
    }, 300));
    DOM.landSelectAll.addEventListener("click", () => toggleSelectAll("landused"));
    DOM.landPrev.addEventListener("click", () => {
        if (state.pagination.landused.page > 1) {
            state.pagination.landused.page--;
            fetchCategoryRecords("landused");
        }
    });
    DOM.landNext.addEventListener("click", () => {
        if (state.pagination.landused.page < state.pagination.landused.totalPages) {
            state.pagination.landused.page++;
            fetchCategoryRecords("landused");
        }
    });

    DOM.sjunguSearch.addEventListener("input", debounce(() => {
        state.filters.sjungu_search = DOM.sjunguSearch.value;
        fetchCategoryRecords("sjungu", true);
    }, 300));
    DOM.sjunguSelectAll.addEventListener("click", () => toggleSelectAll("sjungu"));
    DOM.sjunguPrev.addEventListener("click", () => {
        if (state.pagination.sjungu.page > 1) {
            state.pagination.sjungu.page--;
            fetchCategoryRecords("sjungu");
        }
    });
    DOM.sjunguNext.addEventListener("click", () => {
        if (state.pagination.sjungu.page < state.pagination.sjungu.totalPages) {
            state.pagination.sjungu.page++;
            fetchCategoryRecords("sjungu");
        }
    });

    DOM.btnClearSelection.addEventListener("click", clearAllSelection);
    DOM.btnPrint.addEventListener("click", () => {
        recordAudit("print");
        window.print();
    });
    DOM.btnPdf.addEventListener("click", generatePDF);
    if (DOM.btnXlsx) DOM.btnXlsx.addEventListener("click", exportExcel);
    if (DOM.btnAuditLog) DOM.btnAuditLog.addEventListener("click", openAuditModal);
    if (DOM.auditModalClose) DOM.auditModalClose.addEventListener("click", closeAuditModal);
    if (DOM.auditModalBackdrop) DOM.auditModalBackdrop.addEventListener("click", closeAuditModal);
    if (DOM.auditModalRefresh) DOM.auditModalRefresh.addEventListener("click", fetchAuditLogs);
    if (DOM.pageSizeSelect) DOM.pageSizeSelect.addEventListener("change", onPageSizeChange);
    DOM.docTitleInput.addEventListener("input", updateDocumentTitleText);
}

function openAuditModal() {
    if (!DOM.auditModal) return;
    DOM.auditModal.classList.remove("hidden");
    fetchAuditLogs();
}

function closeAuditModal() {
    if (!DOM.auditModal) return;
    DOM.auditModal.classList.add("hidden");
}

async function fetchAuditLogs() {
    if (!DOM.auditTableBody) return;
    const colspan = 7;
    DOM.auditTableBody.innerHTML = `<tr><td colspan="${colspan}" class="loading-row"><i class="fas fa-spinner fa-spin"></i> Loading...</td></tr>`;

    try {
        const response = await fetch("/api/audit?limit=50");
        if (handleAuthFailure(response)) return;
        if (response.status === 403) {
            DOM.auditTableBody.innerHTML = `<tr><td colspan="${colspan}" style="text-align:center;color:var(--text-muted);">Admin access required</td></tr>`;
            return;
        }
        const data = await response.json();
        if (!response.ok || data.error) {
            DOM.auditTableBody.innerHTML = `<tr><td colspan="${colspan}" style="text-align:center;color:var(--text-muted);">Unable to load audit log</td></tr>`;
            return;
        }

        if (!data.items.length) {
            DOM.auditTableBody.innerHTML = `<tr><td colspan="${colspan}" style="text-align:center;color:var(--text-muted);">No audit entries yet</td></tr>`;
            return;
        }

        DOM.auditTableBody.innerHTML = data.items.map((entry) => {
            const details = formatAuditDetails(entry);
            return `
            <tr>
                <td>${escapeHtml(entry.created_at)}</td>
                <td>${escapeHtml(entry.username)}</td>
                <td><span class="role-tag role-${escapeHtml(entry.role)}">${escapeHtml(entry.role)}</span></td>
                <td><span class="audit-action-tag">${escapeHtml(formatAuditAction(entry.action))}</span></td>
                <td>${escapeHtml(entry.report_ref || "—")}</td>
                <td>${escapeHtml(String(entry.item_count ?? 0))}</td>
                <td class="audit-details-cell" title="${escapeHtml(details)}">${escapeHtml(details)}</td>
            </tr>
        `;
        }).join("");
    } catch (e) {
        console.error("Failed to load audit log:", e);
        DOM.auditTableBody.innerHTML = `<tr><td colspan="${colspan}" style="text-align:center;color:var(--text-muted);">Unable to load audit log</td></tr>`;
    }
}

function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

function updateDocDate() {
    const today = new Date();
    const options = { year: "numeric", month: "long", day: "numeric" };
    DOM.docDate.textContent = today.toLocaleDateString("en-US", options);
}
