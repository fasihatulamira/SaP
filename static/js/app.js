// Application state
const SELECTION_STORAGE_KEY = "gis_info_selections";
const PAGE_SIZE_STORAGE_KEY = "gis_info_page_size";
const PAGE_SIZE_OPTIONS = [8, 10, 15];
const DEFAULT_PAGE_SIZE = 10;
const DEFAULT_DOC_SUBTITLE = "EKSESAIS";
const EXPORT_NAME_PREFIX = "KEMBARAN I - GIS INFO";

function getDocumentSubtitle() {
    return (DOM.docTitleInput && DOM.docTitleInput.value.trim()) || DEFAULT_DOC_SUBTITLE;
}

function getExportBasename() {
    const subtitle = getDocumentSubtitle().replace(/\s+/g, " ").trim();
    return `${EXPORT_NAME_PREFIX} ${subtitle}`;
}

function getExportFilename(extension) {
    const ext = String(extension || "pdf").replace(/^\./, "");
    // Keep spaces; strip characters illegal in Windows/macOS filenames
    const safe = getExportBasename().replace(/[<>:"/\\|?*\u0000-\u001f]/g, "").trim();
    return `${safe}.${ext}`;
}

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
    btnDocx: document.getElementById("btn-docx"),
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
    auditDocEditModal: document.getElementById("audit-doc-edit-modal"),
    auditDocEditBackdrop: document.getElementById("audit-doc-edit-backdrop"),
    auditDocEditClose: document.getElementById("audit-doc-edit-close"),
    auditDocEditCancel: document.getElementById("audit-doc-edit-cancel"),
    auditDocEditForm: document.getElementById("audit-doc-edit-form"),
    auditDocEditFilename: document.getElementById("audit-doc-edit-filename"),
    auditDocEditFile: document.getElementById("audit-doc-edit-file"),
    auditDocEditError: document.getElementById("audit-doc-edit-error"),
    auditDocEditSave: document.getElementById("audit-doc-edit-save"),
    pageSizeSelect: document.getElementById("page-size-select"),
    recordModal: document.getElementById("record-modal"),
    recordModalBackdrop: document.getElementById("record-modal-backdrop"),
    recordModalClose: document.getElementById("record-modal-close"),
    recordModalCancel: document.getElementById("record-modal-cancel"),
    recordModalTitle: document.getElementById("record-modal-title"),
    recordForm: document.getElementById("record-form"),
    recordFormFields: document.getElementById("record-form-fields"),
    recordModalSave: document.getElementById("record-modal-save"),
    crudActions: document.querySelectorAll(".crud-actions")
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
        emptyMessage: "No Topo Raster records found",
        rowLabel: (row) => `Select Topo Raster sheet ${row.sheetNum}`,
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
        colspan: 3,
        emptyMessage: "No DTED records found",
        rowLabel: (row) => `Select DTED file ${row.id_name}`,
        columns: [
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
        colspan: 2,
        emptyMessage: "No landused categories found",
        rowLabel: (row) => `Select landused category ${row.category}`,
        columns: [
            { value: (row) => row.category }
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
        emptyMessage: "No Topo records found",
        rowLabel: (row) => `Select Topo sheet ${row.sheetNum}`,
        columns: [
            { style: "font-weight: 600; color: var(--primary-light);", value: (row) => row.sheetNum },
            { value: (row) => row.sheetName },
            { value: (row) => row.sheetScale }
        ]
    }
};

const RECORD_SCHEMA = {
    topography: {
        label: "Topo Raster",
        fields: [
            { name: "sheetNum", label: "Sheet Number", type: "text", required: true, primaryKey: true },
            { name: "sheetName", label: "Sheet Name", type: "text", required: true },
            { name: "sheetScale", label: "Scale", type: "text", required: true },
            { name: "release_year", label: "Release Year", type: "number", required: true }
        ]
    },
    landused: {
        label: "Landused",
        fields: [
            { name: "landused_id", label: "Landused ID", type: "number", required: true, primaryKey: true },
            { name: "category", label: "Category", type: "text", required: true }
        ]
    },
    dted: {
        label: "DTED",
        fields: [
            { name: "id_name", label: "Elevation ID / Path Name", type: "text", required: true, primaryKey: true },
            { name: "level", label: "DTED Level", type: "number", required: true }
        ]
    },
    sjungu: {
        label: "Topo",
        fields: [
            { name: "sheetNum", label: "Sheet Number", type: "text", required: true, primaryKey: true },
            { name: "sheetName", label: "Sheet Name", type: "text", required: true },
            { name: "sheetScale", label: "Scale", type: "text", required: true }
        ]
    }
};

const recordModalState = {
    category: null,
    mode: "add",
    recordId: null,
    recordData: null
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
    const icon = type === "success" ? "fa-check-circle" : "fa-exclamation-circle";
    DOM.statusBanner.className = `status-banner ${type}`;
    DOM.statusBanner.innerHTML = `<i class="fas ${icon}"></i> ${escapeHtml(message)}`;
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

    const maxAttempts = 3;

    for (let attempt = 1; attempt <= maxAttempts; attempt++) {
        try {
            const params = buildCategoryParams(category);
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 45000);
            let response;
            try {
                response = await fetch(`/api/records/${category}?${params.toString()}`, {
                    signal: controller.signal
                });
            } finally {
                clearTimeout(timeoutId);
            }

            if (handleAuthFailure(response)) {
                state.ui.loading = false;
                return;
            }

            const data = await response.json();

            if (!response.ok || data.error) {
                if (attempt < maxAttempts && (response.status >= 500 || response.status === 503)) {
                    await new Promise((r) => setTimeout(r, 1200 * attempt));
                    continue;
                }
                showStatusBanner(
                    data.error || data.detail || "Failed to load records.",
                    "error"
                );
                renderCategoryError(category);
                state.ui.loading = false;
                return;
            }

            hideStatusBanner();
            state.records[category] = data.items;
            state.pagination[category].page = data.page;
            state.pagination[category].limit = data.limit;
            state.pagination[category].total = data.total;
            state.pagination[category].totalPages = data.total_pages;
            renderCategoryTable(category);
            state.ui.loading = false;
            return;
        } catch (e) {
            console.error(`Network error fetching ${category} (attempt ${attempt}):`, e);
            if (attempt < maxAttempts) {
                await new Promise((r) => setTimeout(r, 1000 * attempt));
                continue;
            }
            showStatusBanner(
                "Could not load records. The database may be waking up — wait a few seconds and refresh.",
                "error"
            );
            renderCategoryError(category);
            state.ui.loading = false;
        }
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
    sjungu: (a, b) => String(a.sheetNum).localeCompare(String(b.sheetNum))
};

function getSelectedSorted(category) {
    const items = Array.from(state.selected[category].values());
    if (category === "landused") {
        return items.map((row, idx) => ({ ...row, landused_id: idx + 1 }));
    }
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
    export_docx: "Word export",
    export_pdf: "PDF export",
    print: "Print",
    clear_selection: "Clear selection"
};

const AUDIT_ACTIONS_WITHOUT_SELECTION = new Set(["clear_selection", "login_failed"]);
const AUDIT_TABLE_COLSPAN = 7;
let auditDocEditState = { auditId: null, filename: "" };

function formatAuditAction(action) {
    return AUDIT_ACTION_LABELS[action] || action;
}

function getAuditDetailLabel(entry) {
    const details = entry.details && typeof entry.details === "object" ? entry.details : {};
    return (
        details.report_title
        || details.filename
        || entry.document_filename
        || entry.report_ref
        || formatAuditAction(entry.action)
    );
}

function formatAuditDetails(entry) {
    if (entry.has_document) {
        return getAuditDetailLabel(entry);
    }
    const bits = [];
    if (entry.details && typeof entry.details === "object") {
        Object.entries(entry.details).forEach(([key, value]) => {
            if (key === "document_available" || key === "mime_type") return;
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

async function archiveAuditDocument(action, blob, filename) {
    const itemCount = getSelectionCount();
    if (itemCount === 0 || !blob) return false;

    const formData = new FormData();
    formData.append("action", action);
    formData.append("report_ref", state.reportRef || "");
    formData.append("item_count", String(itemCount));
    formData.append(
        "report_title",
        getDocumentSubtitle()
    );
    formData.append("filename", filename);
    formData.append("mime_type", blob.type || "application/pdf");
    formData.append("file", blob, filename);

    try {
        const response = await fetch("/api/audit/document", {
            method: "POST",
            body: formData
        });
        if (handleAuthFailure(response)) return false;
        if (!response.ok) {
            console.warn("Document archive failed:", response.status, await response.text());
            return false;
        }
        return true;
    } catch (e) {
        console.warn("Document archive failed:", e);
        return false;
    }
}

function applyPdfFrameChrome(frame) {
    frame.style.width = "794px";
    frame.style.maxWidth = "794px";
    frame.style.overflow = "visible";
    frame.style.border = "none";
    frame.style.outline = "none";
    frame.style.boxShadow = "none";
    frame.style.filter = "none";
    frame.style.borderRadius = "0";
    frame.style.background = "#ffffff";
}

function clearPdfFrameChrome(frame) {
    frame.style.width = "";
    frame.style.maxWidth = "";
    frame.style.overflow = "";
    frame.style.border = "";
    frame.style.outline = "";
    frame.style.boxShadow = "";
    frame.style.filter = "";
    frame.style.borderRadius = "";
    frame.style.background = "";
}

function setPdfCaptureMode(enabled) {
    const frame = document.getElementById("printable-document");
    document.body.classList.toggle("pdf-exporting", enabled);
    if (DOM.docContent) DOM.docContent.classList.toggle("pdf-capture", enabled);
    if (!frame) return;

    frame.classList.toggle("pdf-capture", enabled);
    if (enabled) {
        // Capture at full A4 content width so the right edge is not clipped
        // by the narrow preview column / overflow-x:hidden on body.
        applyPdfFrameChrome(frame);
        // html2canvas paints ancestor glass shadows / backdrop-filter as faint edges.
        let parent = frame.parentElement;
        while (parent) {
            parent.dataset.pdfExportBackdrop = parent.style.backdropFilter || "";
            parent.dataset.pdfExportShadow = parent.style.boxShadow || "";
            parent.dataset.pdfExportBorder = parent.style.border || "";
            parent.style.backdropFilter = "none";
            parent.style.webkitBackdropFilter = "none";
            parent.style.boxShadow = "none";
            parent.style.border = "none";
            parent.style.filter = "none";
            parent = parent.parentElement;
        }
    } else {
        clearPdfFrameChrome(frame);
        document.querySelectorAll("[data-pdf-export-backdrop]").forEach((node) => {
            node.style.backdropFilter = node.dataset.pdfExportBackdrop || "";
            node.style.webkitBackdropFilter = "";
            node.style.boxShadow = node.dataset.pdfExportShadow || "";
            node.style.border = node.dataset.pdfExportBorder || "";
            node.style.filter = "";
            delete node.dataset.pdfExportBackdrop;
            delete node.dataset.pdfExportShadow;
            delete node.dataset.pdfExportBorder;
        });
    }
}

function preparePdfCloneDocument(clonedDoc) {
    clonedDoc.body.classList.add("pdf-exporting");
    const clonedFrame = clonedDoc.getElementById("printable-document");
    if (clonedFrame) {
        clonedFrame.classList.add("pdf-capture");
        applyPdfFrameChrome(clonedFrame);
    }
    const clonedContent = clonedDoc.getElementById("doc-content");
    if (clonedContent) {
        clonedContent.style.overflow = "visible";
    }
    clonedDoc.querySelectorAll(".glass-card, .preview-panel, header, main, body").forEach((node) => {
        node.style.backdropFilter = "none";
        node.style.webkitBackdropFilter = "none";
        node.style.filter = "none";
        node.style.boxShadow = "none";
        node.style.border = "none";
    });
}

async function buildPreviewPdfBlob(filename) {
    const element = document.getElementById("printable-document");
    setPdfCaptureMode(true);
    await waitForReflow();
    await new Promise((resolve) => setTimeout(resolve, 150));

    const captureWidth = Math.ceil(Math.max(element.scrollWidth, element.offsetWidth, 794));
    const captureHeight = Math.ceil(
        Math.max(element.scrollHeight, element.offsetHeight, DOM.docContent?.scrollHeight || 0, 800)
    );

    const opt = {
        margin: [12, 12, 12, 12],
        filename,
        image: { type: "jpeg", quality: 0.98 },
        html2canvas: {
            scale: 2,
            useCORS: true,
            logging: false,
            scrollX: 0,
            scrollY: 0,
            x: 0,
            y: 0,
            width: captureWidth,
            height: captureHeight,
            windowWidth: captureWidth,
            windowHeight: captureHeight,
            backgroundColor: "#ffffff",
            onclone: preparePdfCloneDocument
        },
        jsPDF: { unit: "mm", format: "a4", orientation: "portrait" },
        pagebreak: {
            mode: ["css"],
            avoid: [".doc-page-header", ".doc-title-block", ".doc-section-title"]
        }
    };

    try {
        const pdf = await html2pdf().set(opt).from(element).toPdf().get("pdf");
        const totalPages = pdf.internal.getNumberOfPages();
        if (DOM.docPageInfo) {
            DOM.docPageInfo.textContent = `Page 1 of ${totalPages}`;
        }
        return { pdf, blob: pdf.output("blob") };
    } finally {
        setPdfCaptureMode(false);
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
                <p>Select records from the categories in the left panel to compile your GIS INFO document.</p>
            </div>
        `;
        DOM.btnClearSelection.disabled = true;
        DOM.btnPrint.disabled = true;
        DOM.btnPdf.disabled = true;
        if (DOM.btnXlsx) DOM.btnXlsx.disabled = true;
        if (DOM.btnDocx) DOM.btnDocx.disabled = true;
        if (DOM.docRef) DOM.docRef.textContent = "—";
        if (DOM.docPageInfo) DOM.docPageInfo.textContent = "Page 1 of 1";
        return;
    }

    updateDocumentMetadata(selectedTopo, selectedDted, selectedLand, selectedSjungu);

    DOM.btnClearSelection.disabled = false;
    DOM.btnPrint.disabled = false;
    DOM.btnPdf.disabled = false;
    if (DOM.btnXlsx) DOM.btnXlsx.disabled = false;
    if (DOM.btnDocx) DOM.btnDocx.disabled = false;

    let html = "";
    let sectionOrdinal = 0;
    const sectionLetter = () => String.fromCharCode(65 + (sectionOrdinal++));

    if (selectedTopo.length > 0 || selectedSjungu.length > 0) {
        const totalLabel = formatTopoSjungTotal(selectedTopo.length, selectedSjungu.length);
        let rowNum = 0;
        html += `
            <div class="doc-section">
                <div class="doc-section-title">${sectionLetter()}. Raster Topography</div>
                <table class="doc-table doc-table-topo">
                    <colgroup>
                        <col class="col-num">
                        <col class="col-sheet-num">
                        <col class="col-sheet-name">
                        <col class="col-sheet-scale">
                        <col class="col-release-year">
                    </colgroup>
                    <thead>
                        <tr>
                            <th>NUM.</th>
                            <th>SHEET NUM.</th>
                            <th>SHEET NAME</th>
                            <th>SHEET SCALE</th>
                            <th>RELEASE YEAR</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${selectedTopo.map((row) => {
                            rowNum += 1;
                            return `
                            <tr>
                                <td class="doc-input-text">${rowNum}</td>
                                <td class="doc-input-text">${escapeHtml(row.sheetNum)}</td>
                                <td class="doc-input-text">${escapeHtml(row.sheetName)}</td>
                                <td class="doc-input-text">${escapeHtml(row.sheetScale)}</td>
                                <td class="doc-input-text">${escapeHtml(row.release_year)}</td>
                            </tr>`;
                        }).join("")}
                        ${selectedSjungu.map((row) => {
                            rowNum += 1;
                            return `
                            <tr>
                                <td class="doc-input-text">${rowNum}</td>
                                <td class="doc-input-text">${escapeHtml(row.sheetNum)}</td>
                                <td class="doc-input-text">${escapeHtml(row.sheetName)}</td>
                                <td class="doc-input-text">${escapeHtml(row.sheetScale)}</td>
                                <td class="doc-input-text"></td>
                            </tr>`;
                        }).join("")}
                        <tr class="doc-total-row">
                            <td colspan="4">TOTAL</td>
                            <td class="doc-input-text">${totalLabel}</td>
                        </tr>
                    </tbody>
                </table>
            </div>
        `;
    }

    if (selectedLand.length > 0) {
        html += `
            <div class="doc-section doc-section-follow">
                <div class="doc-section-title">${sectionLetter()}. Landused</div>
                <table class="doc-table doc-table-landused">
                    <colgroup>
                        <col class="col-num">
                        <col class="col-category">
                        <col class="col-landused-id">
                    </colgroup>
                    <thead>
                        <tr>
                            <th>NUM.</th>
                            <th>CATEGORY</th>
                            <th>LANDUSED ID</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${selectedLand.map((row, idx) => `
                            <tr>
                                <td class="doc-input-text">${idx + 1}</td>
                                <td class="doc-input-text doc-cell-left">${escapeHtml(row.category)}</td>
                                <td class="doc-input-text">${escapeHtml(row.landused_id)}</td>
                            </tr>
                        `).join("")}
                        <tr class="doc-total-row">
                            <td colspan="2">TOTAL</td>
                            <td class="doc-input-text">${selectedLand.length}</td>
                        </tr>
                    </tbody>
                </table>
            </div>
        `;
    }

    if (selectedDted.length > 0) {
        html += `
            <div class="doc-section doc-section-follow">
                <div class="doc-section-title">${sectionLetter()}. Digital Terrain Elevation Data (DTED)</div>
                <table class="doc-table doc-table-dted">
                    <colgroup>
                        <col class="col-num">
                        <col class="col-id-name">
                        <col class="col-level">
                    </colgroup>
                    <thead>
                        <tr>
                            <th>NUM.</th>
                            <th>IDENTIFICATION NAME</th>
                            <th>LEVEL</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${selectedDted.map((row, idx) => `
                            <tr>
                                <td class="doc-input-text">${idx + 1}</td>
                                <td class="doc-input-text doc-cell-left">${escapeHtml(row.id_name)}</td>
                                <td class="doc-input-text">${escapeHtml(row.level)}</td>
                            </tr>
                        `).join("")}
                        <tr class="doc-total-row">
                            <td colspan="2">TOTAL</td>
                            <td class="doc-input-text">${selectedDted.length}</td>
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
                report_title: getDocumentSubtitle()
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
        const filename = getExportFilename("xlsx");
        link.href = url;
        link.download = filename;
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

async function exportWord() {
    const payload = getSelectionPayload();
    const itemCount = getSelectionCount();
    if (itemCount === 0) return;

    if (DOM.btnDocx) {
        DOM.btnDocx.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Word';
        DOM.btnDocx.disabled = true;
    }

    try {
        const response = await fetch("/api/export/docx", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                ...payload,
                report_ref: state.reportRef,
                report_title: getDocumentSubtitle()
            })
        });
        if (handleAuthFailure(response)) return;
        if (!response.ok) {
            const err = await response.json();
            showStatusBanner(err.error || "Word export failed.", "error");
            return;
        }

        const blob = await response.blob();
        const url = URL.createObjectURL(blob);
        const link = document.createElement("a");
        const filename = getExportFilename("docx");
        link.href = url;
        link.download = filename;
        link.click();
        URL.revokeObjectURL(url);
    } catch (e) {
        console.error("Word export failed:", e);
        showStatusBanner("Word export failed.", "error");
    } finally {
        if (DOM.btnDocx) {
            DOM.btnDocx.innerHTML = '<i class="fas fa-file-word"></i> Word';
            DOM.btnDocx.disabled = getSelectionCount() === 0;
        }
    }
}

function updateDocumentTitleText() {
    const inputTitle = DOM.docTitleInput.value.trim();
    const docTitleEl = document.getElementById("document-title-header");
    if (docTitleEl) {
        docTitleEl.textContent = inputTitle || DEFAULT_DOC_SUBTITLE;
    }
}

function waitForReflow() {
    return new Promise((resolve) => {
        requestAnimationFrame(() => requestAnimationFrame(resolve));
    });
}

async function generatePDF() {
    const filename = getExportFilename("pdf");

    DOM.btnPdf.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Generating...';
    DOM.btnPdf.disabled = true;

    try {
        const { pdf, blob } = await buildPreviewPdfBlob(filename);
        pdf.save(filename);
        await archiveAuditDocument("export_pdf", blob, filename);
    } catch (err) {
        console.error("PDF generation failed:", err);
        showStatusBanner("PDF generation failed.", "error");
    } finally {
        DOM.btnPdf.innerHTML = '<i class="fas fa-file-pdf"></i> Generate PDF';
        DOM.btnPdf.disabled = getSelectionCount() === 0;
    }
}

async function printDocument() {
    const filename = getExportFilename("pdf");
    const previousTitle = document.title;
    document.title = getExportBasename();

    DOM.btnPrint.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Preparing...';
    DOM.btnPrint.disabled = true;

    try {
        const { blob } = await buildPreviewPdfBlob(filename);
        await archiveAuditDocument("print", blob, filename);
    } catch (err) {
        console.warn("Print archive failed:", err);
        showStatusBanner("Could not archive print document, continuing to print.", "error");
    } finally {
        DOM.btnPrint.innerHTML = '<i class="fas fa-print"></i> Print';
        DOM.btnPrint.disabled = getSelectionCount() === 0;
    }

    document.body.classList.add("is-printing");
    const restorePrintChrome = () => {
        document.body.classList.remove("is-printing");
        document.title = previousTitle;
        window.removeEventListener("afterprint", restorePrintChrome);
    };
    window.addEventListener("afterprint", restorePrintChrome);
    window.print();
    // Fallback if afterprint never fires (some browsers)
    setTimeout(restorePrintChrome, 2000);
}

function getRecordId(category, row) {
    const keyProp = TABLE_CONFIG[category].keyProp;
    return row[keyProp];
}

function getSelectedRecords(category) {
    return getSelectedSorted(category);
}

function openRecordModal(category, mode, row = null) {
    const schema = RECORD_SCHEMA[category];
    if (!schema || !DOM.recordModal) return;

    recordModalState.category = category;
    recordModalState.mode = mode;
    recordModalState.recordData = row;
    recordModalState.recordId = row ? getRecordId(category, row) : null;

    const actionLabel = mode === "add" ? "Add" : "Edit";
    DOM.recordModalTitle.innerHTML = `<i class="fas fa-database"></i> ${actionLabel} ${escapeHtml(schema.label)} Record`;

    DOM.recordFormFields.innerHTML = schema.fields
        .filter((field) => !(mode === "add" && field.hideOnAdd))
        .map((field) => {
            const value = row ? (row[field.name] ?? "") : "";
            const disabled = mode === "edit" && (field.primaryKey || field.readOnlyOnEdit);
            const required = field.required ? "required" : "";
            return `
                <div class="record-form-field">
                    <label for="record-field-${field.name}">${escapeHtml(field.label)}</label>
                    <input
                        type="${field.type}"
                        id="record-field-${field.name}"
                        name="${field.name}"
                        value="${escapeHtml(value)}"
                        ${required}
                        ${disabled ? "disabled" : ""}
                    >
                </div>
            `;
        })
        .join("");

    DOM.recordModal.classList.remove("hidden");
    const firstInput = DOM.recordFormFields.querySelector("input:not([disabled])");
    if (firstInput) firstInput.focus();
}

function closeRecordModal() {
    if (!DOM.recordModal) return;
    DOM.recordModal.classList.add("hidden");
    recordModalState.category = null;
    recordModalState.mode = "add";
    recordModalState.recordId = null;
    recordModalState.recordData = null;
    if (DOM.recordForm) DOM.recordForm.reset();
}

function collectRecordFormData(category) {
    const schema = RECORD_SCHEMA[category];
    const data = {};
    schema.fields.forEach((field) => {
        if (recordModalState.mode === "add" && field.hideOnAdd) return;
        const input = document.getElementById(`record-field-${field.name}`);
        if (!input) return;
        if (field.type === "number") {
            data[field.name] = input.value === "" ? null : Number(input.value);
        } else {
            data[field.name] = input.value.trim();
        }
    });
    return data;
}

function removeRecordFromSelection(category, recordId) {
    const catMap = state.selected[category];
    if (catMap.has(recordId)) {
        catMap.delete(recordId);
        saveSelectionsToSession();
    }
}

function upsertRecordInSelection(category, record) {
    const keyProp = TABLE_CONFIG[category].keyProp;
    const recordId = record[keyProp];
    if (state.selected[category].has(recordId)) {
        state.selected[category].set(recordId, record);
        saveSelectionsToSession();
    }
}

async function saveRecordFromModal(event) {
    event.preventDefault();
    const { category, mode, recordId } = recordModalState;
    if (!category) return;

    const payload = collectRecordFormData(category);
    const schema = RECORD_SCHEMA[category];
    for (const field of schema.fields) {
        if (field.hideOnAdd && mode === "add") continue;
        if (field.primaryKey && mode === "edit") continue;
        if (field.required && (payload[field.name] === "" || payload[field.name] === null || Number.isNaN(payload[field.name]))) {
            showStatusBanner(`${field.label} is required.`, "error");
            return;
        }
    }

    DOM.recordModalSave.disabled = true;
    DOM.recordModalSave.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Saving...';

    try {
        const url = mode === "add"
            ? `/api/records/${category}`
            : `/api/records/${category}/${encodeURIComponent(recordId)}`;
        const response = await fetch(url, {
            method: mode === "add" ? "POST" : "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });

        if (handleAuthFailure(response)) return;

        const data = await response.json().catch(() => ({}));
        if (!response.ok) {
            showStatusBanner(data.error || "Failed to save record.", "error");
            return;
        }

        hideStatusBanner();
        closeRecordModal();

        if (mode === "edit") {
            upsertRecordInSelection(category, data.record || payload);
        }

        await fetchFilters();
        await fetchCategoryRecords(category, mode === "add");
        renderDocumentPreview();
        showStatusBanner(`Record ${mode === "add" ? "created" : "updated"} successfully.`, "success");
        setTimeout(hideStatusBanner, 2500);
    } catch (e) {
        console.error("Failed to save record:", e);
        showStatusBanner("Could not save record. Check your connection.", "error");
    } finally {
        DOM.recordModalSave.disabled = false;
        DOM.recordModalSave.innerHTML = '<i class="fas fa-save"></i> Save';
    }
}

async function deleteSelectedRecords(category) {
    const selected = getSelectedRecords(category);
    if (selected.length === 0) {
        showStatusBanner("Select at least one record to delete.", "error");
        return;
    }

    const schema = RECORD_SCHEMA[category];
    const noun = selected.length === 1 ? "record" : `${selected.length} records`;
    const confirmed = window.confirm(`Delete ${noun} from ${schema.label}? This cannot be undone.`);
    if (!confirmed) return;

    let deletedCount = 0;
    let lastError = "";

    for (const row of selected) {
        const recordId = getRecordId(category, row);
        try {
            const response = await fetch(`/api/records/${category}/${encodeURIComponent(recordId)}`, {
                method: "DELETE"
            });
            if (handleAuthFailure(response)) return;

            const data = await response.json().catch(() => ({}));
            if (!response.ok) {
                lastError = data.error || "Failed to delete record.";
                continue;
            }

            removeRecordFromSelection(category, recordId);
            deletedCount += 1;
        } catch (e) {
            console.error("Failed to delete record:", e);
            lastError = "Could not connect to the server.";
        }
    }

    if (deletedCount > 0) {
        await fetchFilters();
        await fetchCategoryRecords(category, true);
        renderDocumentPreview();
        showStatusBanner(`${deletedCount} record(s) deleted.`, "success");
        setTimeout(hideStatusBanner, 2500);
    } else if (lastError) {
        showStatusBanner(lastError, "error");
    }
}

function handleCrudAdd(category) {
    openRecordModal(category, "add");
}

function handleCrudEdit(category) {
    const selected = getSelectedRecords(category);
    if (selected.length === 0) {
        showStatusBanner("Select one record to edit.", "error");
        return;
    }
    if (selected.length > 1) {
        showStatusBanner("Select only one record to edit.", "error");
        return;
    }
    openRecordModal(category, "edit", selected[0]);
}

function setupCrudEventListeners() {
    if (!DOM.crudActions || DOM.crudActions.length === 0) return;

    DOM.crudActions.forEach((group) => {
        const category = group.getAttribute("data-category");
        const addBtn = group.querySelector(".btn-crud-add");
        const editBtn = group.querySelector(".btn-crud-edit");
        const deleteBtn = group.querySelector(".btn-crud-delete");

        if (addBtn) addBtn.addEventListener("click", () => handleCrudAdd(category));
        if (editBtn) editBtn.addEventListener("click", () => handleCrudEdit(category));
        if (deleteBtn) deleteBtn.addEventListener("click", () => deleteSelectedRecords(category));
    });

    if (DOM.recordForm) DOM.recordForm.addEventListener("submit", saveRecordFromModal);
    if (DOM.recordModalClose) DOM.recordModalClose.addEventListener("click", closeRecordModal);
    if (DOM.recordModalCancel) DOM.recordModalCancel.addEventListener("click", closeRecordModal);
    if (DOM.recordModalBackdrop) DOM.recordModalBackdrop.addEventListener("click", closeRecordModal);
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
    DOM.btnPrint.addEventListener("click", printDocument);
    DOM.btnPdf.addEventListener("click", generatePDF);
    if (DOM.btnXlsx) DOM.btnXlsx.addEventListener("click", exportExcel);
    if (DOM.btnDocx) DOM.btnDocx.addEventListener("click", exportWord);
    if (DOM.btnAuditLog) DOM.btnAuditLog.addEventListener("click", openAuditModal);
    if (DOM.auditModalClose) DOM.auditModalClose.addEventListener("click", closeAuditModal);
    if (DOM.auditModalBackdrop) DOM.auditModalBackdrop.addEventListener("click", closeAuditModal);
    if (DOM.auditModalRefresh) DOM.auditModalRefresh.addEventListener("click", fetchAuditLogs);
    if (DOM.auditDocEditClose) DOM.auditDocEditClose.addEventListener("click", closeAuditDocumentEdit);
    if (DOM.auditDocEditBackdrop) DOM.auditDocEditBackdrop.addEventListener("click", closeAuditDocumentEdit);
    if (DOM.auditDocEditCancel) DOM.auditDocEditCancel.addEventListener("click", closeAuditDocumentEdit);
    if (DOM.auditDocEditForm) DOM.auditDocEditForm.addEventListener("submit", saveAuditDocumentEdit);
    if (DOM.pageSizeSelect) DOM.pageSizeSelect.addEventListener("change", onPageSizeChange);
    DOM.docTitleInput.addEventListener("input", updateDocumentTitleText);
    setupCrudEventListeners();
}

function openAuditModal() {
    if (!DOM.auditModal) return;
    DOM.auditModal.classList.remove("hidden");
    fetchAuditLogs();
}

function closeAuditModal() {
    closeAuditDocumentEdit();
    if (!DOM.auditModal) return;
    DOM.auditModal.classList.add("hidden");
}

async function fetchAuditLogs() {
    if (!DOM.auditTableBody) return;
    const colspan = AUDIT_TABLE_COLSPAN;
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
            const auditId = escapeHtml(String(entry.id));
            const filename = escapeHtml(entry.document_filename || details);
            const detailsCell = entry.has_document
                ? `<td class="audit-details-cell">
                     <div class="audit-doc-row">
                       <button type="button" class="audit-doc-link" data-audit-id="${auditId}" title="View archived document">
                         <i class="fas fa-file-alt"></i> ${escapeHtml(details)}
                       </button>
                       <button type="button" class="btn btn-outline btn-crud audit-doc-edit" data-audit-id="${auditId}" data-filename="${filename}" title="Edit document">
                         <i class="fas fa-pen"></i> Edit
                       </button>
                       <button type="button" class="btn btn-outline btn-crud audit-doc-delete" data-audit-id="${auditId}" data-filename="${filename}" title="Delete document">
                         <i class="fas fa-trash-alt"></i> Delete
                       </button>
                     </div>
                   </td>`
                : `<td class="audit-details-cell" title="${escapeHtml(details)}">${escapeHtml(details)}</td>`;
            return `
            <tr>
                <td>${escapeHtml(entry.created_at)}</td>
                <td>${escapeHtml(entry.username)}</td>
                <td><span class="role-tag role-${escapeHtml(entry.role)}">${escapeHtml(entry.role)}</span></td>
                <td><span class="audit-action-tag">${escapeHtml(formatAuditAction(entry.action))}</span></td>
                <td>${escapeHtml(entry.report_ref || "—")}</td>
                <td>${escapeHtml(String(entry.item_count ?? 0))}</td>
                ${detailsCell}
            </tr>
        `;
        }).join("");

        DOM.auditTableBody.querySelectorAll(".audit-doc-link").forEach((btn) => {
            btn.addEventListener("click", () => openAuditDocument(btn.getAttribute("data-audit-id")));
        });
        DOM.auditTableBody.querySelectorAll(".audit-doc-edit").forEach((btn) => {
            btn.addEventListener("click", () => openAuditDocumentEdit(
                btn.getAttribute("data-audit-id"),
                btn.getAttribute("data-filename") || ""
            ));
        });
        DOM.auditTableBody.querySelectorAll(".audit-doc-delete").forEach((btn) => {
            btn.addEventListener("click", () => deleteAuditDocument(
                btn.getAttribute("data-audit-id"),
                btn.getAttribute("data-filename") || ""
            ));
        });
    } catch (e) {
        console.error("Failed to load audit log:", e);
        DOM.auditTableBody.innerHTML = `<tr><td colspan="${colspan}" style="text-align:center;color:var(--text-muted);">Unable to load audit log</td></tr>`;
    }
}

function openAuditDocument(auditId) {
    if (!auditId) return;
    window.open(`/api/audit/${encodeURIComponent(auditId)}/document`, "_blank", "noopener,noreferrer");
}

function setAuditDocEditError(message) {
    if (!DOM.auditDocEditError) return;
    if (!message) {
        DOM.auditDocEditError.textContent = "";
        DOM.auditDocEditError.classList.add("hidden");
        return;
    }
    DOM.auditDocEditError.textContent = message;
    DOM.auditDocEditError.classList.remove("hidden");
}

function openAuditDocumentEdit(auditId, filename) {
    if (!auditId || !DOM.auditDocEditModal) return;
    auditDocEditState = { auditId, filename: filename || "" };
    if (DOM.auditDocEditFilename) DOM.auditDocEditFilename.value = filename || "";
    if (DOM.auditDocEditFile) DOM.auditDocEditFile.value = "";
    setAuditDocEditError("");
    DOM.auditDocEditModal.classList.remove("hidden");
    if (DOM.auditDocEditFilename) DOM.auditDocEditFilename.focus();
}

function closeAuditDocumentEdit() {
    if (!DOM.auditDocEditModal) return;
    DOM.auditDocEditModal.classList.add("hidden");
    auditDocEditState = { auditId: null, filename: "" };
    if (DOM.auditDocEditForm) DOM.auditDocEditForm.reset();
    setAuditDocEditError("");
    if (DOM.auditDocEditSave) DOM.auditDocEditSave.disabled = false;
}

async function saveAuditDocumentEdit(event) {
    event.preventDefault();
    const auditId = auditDocEditState.auditId;
    if (!auditId) return;

    const filename = DOM.auditDocEditFilename ? DOM.auditDocEditFilename.value.trim() : "";
    const file = DOM.auditDocEditFile && DOM.auditDocEditFile.files[0];
    if (!filename && !file) {
        setAuditDocEditError("Enter a filename or choose a replacement file.");
        return;
    }

    const formData = new FormData();
    if (filename) formData.append("filename", filename);
    if (file) formData.append("file", file);

    if (DOM.auditDocEditSave) DOM.auditDocEditSave.disabled = true;
    setAuditDocEditError("");

    try {
        const response = await fetch(`/api/audit/${encodeURIComponent(auditId)}/document`, {
            method: "PUT",
            body: formData,
        });
        if (handleAuthFailure(response)) return;
        const data = await response.json().catch(() => ({}));
        if (!response.ok || data.error) {
            setAuditDocEditError(data.error || "Unable to save document.");
            return;
        }
        closeAuditDocumentEdit();
        await fetchAuditLogs();
    } catch (e) {
        console.error("Failed to edit audit document:", e);
        setAuditDocEditError("Unable to save document.");
    } finally {
        if (DOM.auditDocEditSave) DOM.auditDocEditSave.disabled = false;
    }
}

async function deleteAuditDocument(auditId, filename) {
    if (!auditId) return;
    const label = filename ? `"${filename}"` : "this archived document";
    const confirmed = window.confirm(
        `Delete ${label} and its audit log entry? This cannot be undone.`
    );
    if (!confirmed) return;

    try {
        const response = await fetch(`/api/audit/${encodeURIComponent(auditId)}`, {
            method: "DELETE",
        });
        if (handleAuthFailure(response)) return;
        const data = await response.json().catch(() => ({}));
        if (!response.ok || data.error) {
            window.alert(data.error || "Unable to delete document.");
            return;
        }
        await fetchAuditLogs();
    } catch (e) {
        console.error("Failed to delete audit document:", e);
        window.alert("Unable to delete document.");
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
    if (!DOM.docDate) return;
    const today = new Date();
    const options = { year: "numeric", month: "long", day: "numeric" };
    DOM.docDate.textContent = today.toLocaleDateString("en-US", options);
}
