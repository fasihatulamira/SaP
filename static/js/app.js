// Application state
const state = {
    records: {
        topography: [],
        dted: [],
        landused: [],
        sjungu: []
    },
    selected: {
        topography: new Map(), // key: sheetNum, value: rowData
        dted: new Map(),       // key: id_name, value: rowData
        landused: new Map(),   // key: landused_id, value: rowData
        sjungu: new Map()      // key: sheetNum, value: rowData
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
        topography: { page: 1, limit: 8 },
        dted: { page: 1, limit: 8 },
        landused: { page: 1, limit: 8 },
        sjungu: { page: 1, limit: 8 }
    },
    activeTab: "topography"
};

// DOM elements
const DOM = {
    tabs: document.querySelectorAll(".tab-btn"),
    contents: document.querySelectorAll(".category-content"),
    themeToggle: document.getElementById("theme-toggle"),
    
    // Topography DOM
    topoSearch: document.getElementById("topo-search"),
    topoYear: document.getElementById("topo-year"),
    topoTableBody: document.getElementById("topo-table-body"),
    topoPrev: document.getElementById("topo-prev"),
    topoNext: document.getElementById("topo-next"),
    topoPageInfo: document.getElementById("topo-page-info"),
    topoSelectAll: document.getElementById("topo-select-all"),
    
    // DTED DOM
    dtedSearch: document.getElementById("dted-search"),
    dtedLevel: document.getElementById("dted-level"),
    dtedTableBody: document.getElementById("dted-table-body"),
    dtedPrev: document.getElementById("dted-prev"),
    dtedNext: document.getElementById("dted-next"),
    dtedPageInfo: document.getElementById("dted-page-info"),
    dtedSelectAll: document.getElementById("dted-select-all"),
    
    // Land Used DOM
    landSearch: document.getElementById("land-search"),
    landTableBody: document.getElementById("land-table-body"),
    landPrev: document.getElementById("land-prev"),
    landNext: document.getElementById("land-next"),
    landPageInfo: document.getElementById("land-page-info"),
    landSelectAll: document.getElementById("land-select-all"),
    
    // Sjungu DOM
    sjunguSearch: document.getElementById("sjungu-search"),
    sjunguTableBody: document.getElementById("sjungu-table-body"),
    sjunguPrev: document.getElementById("sjungu-prev"),
    sjunguNext: document.getElementById("sjungu-next"),
    sjunguPageInfo: document.getElementById("sjungu-page-info"),
    sjunguSelectAll: document.getElementById("sjungu-select-all"),
    
    // Output DOM
    docContent: document.getElementById("doc-content"),
    docDate: document.getElementById("doc-date"),
    btnPrint: document.getElementById("btn-print"),
    btnPdf: document.getElementById("btn-pdf"),
    btnClearSelection: document.getElementById("btn-clear-selection"),
    docTitleInput: document.getElementById("doc-title-input")
};

// Initialize Application
document.addEventListener("DOMContentLoaded", () => {
    initTheme();
    fetchFilters();
    fetchRecords();
    setupEventListeners();
    updateDocDate();
});

// Theme Management
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

// Fetch dynamic years and levels for filters
async function fetchFilters() {
    try {
        const response = await fetch("/api/filters");
        const data = await response.json();
        
        if (data.error) {
            console.error("Error fetching filters:", data.error);
            return;
        }
        
        // Populate Topography Years
        DOM.topoYear.innerHTML = '<option value="">All Release Years</option>';
        data.release_years.forEach(year => {
            DOM.topoYear.innerHTML += `<option value="${year}">${year}</option>`;
        });
        
        // Populate DTED Levels
        DOM.dtedLevel.innerHTML = '<option value="">All Levels</option>';
        data.dted_levels.forEach(level => {
            DOM.dtedLevel.innerHTML += `<option value="${level}">Level ${level}</option>`;
        });
    } catch (e) {
        console.error("Network error fetching filters:", e);
    }
}

// Fetch records from backend based on filters
async function fetchRecords() {
    try {
        const params = new URLSearchParams({
            topo_search: state.filters.topo_search,
            topo_year: state.filters.topo_year,
            dted_search: state.filters.dted_search,
            dted_level: state.filters.dted_level,
            land_search: state.filters.land_search,
            sjungu_search: state.filters.sjungu_search
        });
        
        const response = await fetch(`/api/records?${params.toString()}`);
        const data = await response.json();
        
        if (data.error) {
            console.error("Error fetching records:", data.error);
            return;
        }
        
        state.records.topography = data.topography;
        state.records.dted = data.dted;
        state.records.landused = data.landused;
        state.records.sjungu = data.sjungu;
        
        // Reset to first page when filtering
        state.pagination.topography.page = 1;
        state.pagination.dted.page = 1;
        state.pagination.landused.page = 1;
        state.pagination.sjungu.page = 1;
        
        renderAllTables();
    } catch (e) {
        console.error("Network error fetching records:", e);
    }
}

// Render selector tables
function renderAllTables() {
    renderTopographyTable();
    renderDtedTable();
    renderLandusedTable();
    renderSjunguTable();
    renderDocumentPreview();
}

// Render Topography Table
function renderTopographyTable() {
    const list = state.records.topography;
    const { page, limit } = state.pagination.topography;
    const start = (page - 1) * limit;
    const paginatedItems = list.slice(start, start + limit);
    
    DOM.topoTableBody.innerHTML = "";
    
    if (paginatedItems.length === 0) {
        DOM.topoTableBody.innerHTML = `<tr><td colspan="5" style="text-align: center; color: var(--text-muted);">No topography records found</td></tr>`;
        DOM.topoPageInfo.textContent = "0 of 0";
        return;
    }
    
    paginatedItems.forEach(row => {
        const isSelected = state.selected.topography.has(row.sheetNum);
        const tr = document.createElement("tr");
        if (isSelected) tr.classList.add("selected");
        
        tr.innerHTML = `
            <td>
                <div class="custom-checkbox">
                    <i class="fas fa-check"></i>
                </div>
            </td>
            <td style="font-weight: 600; color: var(--primary-light);">${row.sheetNum}</td>
            <td>${row.sheetName}</td>
            <td>${row.sheetScale}</td>
            <td>${row.release_year}</td>
        `;
        
        tr.addEventListener("click", () => {
            toggleSelection("topography", row.sheetNum, row);
            renderTopographyTable();
        });
        
        DOM.topoTableBody.appendChild(tr);
    });
    
    // Update Pagination controls
    const totalPages = Math.ceil(list.length / limit);
    DOM.topoPageInfo.textContent = `Page ${page} of ${totalPages || 1}`;
    DOM.topoPrev.disabled = page === 1;
    DOM.topoNext.disabled = page === totalPages || totalPages === 0;
    
    // Update select all checkbox state
    updateSelectAllCheckboxState("topography", paginatedItems);
}

// Render DTED Table
function renderDtedTable() {
    const list = state.records.dted;
    const { page, limit } = state.pagination.dted;
    const start = (page - 1) * limit;
    const paginatedItems = list.slice(start, start + limit);
    
    DOM.dtedTableBody.innerHTML = "";
    
    if (paginatedItems.length === 0) {
        DOM.dtedTableBody.innerHTML = `<tr><td colspan="3" style="text-align: center; color: var(--text-muted);">No DTED records found</td></tr>`;
        DOM.dtedPageInfo.textContent = "0 of 0";
        return;
    }
    
    paginatedItems.forEach(row => {
        const isSelected = state.selected.dted.has(row.id_name);
        const tr = document.createElement("tr");
        if (isSelected) tr.classList.add("selected");
        
        tr.innerHTML = `
            <td>
                <div class="custom-checkbox">
                    <i class="fas fa-check"></i>
                </div>
            </td>
            <td style="word-break: break-all;">${row.id_name}</td>
            <td><span class="badge" style="background: rgba(6, 182, 212, 0.15); color: var(--accent); padding: 0.2rem 0.5rem; border-radius: 4px; font-weight: 600;">Level ${row.level}</span></td>
        `;
        
        tr.addEventListener("click", () => {
            toggleSelection("dted", row.id_name, row);
            renderDtedTable();
        });
        
        DOM.dtedTableBody.appendChild(tr);
    });
    
    const totalPages = Math.ceil(list.length / limit);
    DOM.dtedPageInfo.textContent = `Page ${page} of ${totalPages || 1}`;
    DOM.dtedPrev.disabled = page === 1;
    DOM.dtedNext.disabled = page === totalPages || totalPages === 0;
    
    updateSelectAllCheckboxState("dted", paginatedItems);
}

// Render Land Used Table
function renderLandusedTable() {
    const list = state.records.landused;
    const { page, limit } = state.pagination.landused;
    const start = (page - 1) * limit;
    const paginatedItems = list.slice(start, start + limit);
    
    DOM.landTableBody.innerHTML = "";
    
    if (paginatedItems.length === 0) {
        DOM.landTableBody.innerHTML = `<tr><td colspan="3" style="text-align: center; color: var(--text-muted);">No land use categories found</td></tr>`;
        DOM.landPageInfo.textContent = "0 of 0";
        return;
    }
    
    paginatedItems.forEach(row => {
        const isSelected = state.selected.landused.has(row.landused_id);
        const tr = document.createElement("tr");
        if (isSelected) tr.classList.add("selected");
        
        tr.innerHTML = `
            <td>
                <div class="custom-checkbox">
                    <i class="fas fa-check"></i>
                </div>
            </td>
            <td>${row.landused_id}</td>
            <td>${row.category}</td>
        `;
        
        tr.addEventListener("click", () => {
            toggleSelection("landused", row.landused_id, row);
            renderLandusedTable();
        });
        
        DOM.landTableBody.appendChild(tr);
    });
    
    const totalPages = Math.ceil(list.length / limit);
    DOM.landPageInfo.textContent = `Page ${page} of ${totalPages || 1}`;
    DOM.landPrev.disabled = page === 1;
    DOM.landNext.disabled = page === totalPages || totalPages === 0;
    
    updateSelectAllCheckboxState("landused", paginatedItems);
}

// Render Sjungu Table
function renderSjunguTable() {
    const list = state.records.sjungu;
    const { page, limit } = state.pagination.sjungu;
    const start = (page - 1) * limit;
    const paginatedItems = list.slice(start, start + limit);
    
    DOM.sjunguTableBody.innerHTML = "";
    
    if (paginatedItems.length === 0) {
        DOM.sjunguTableBody.innerHTML = `<tr><td colspan="4" style="text-align: center; color: var(--text-muted);">No Sjungu records found</td></tr>`;
        DOM.sjunguPageInfo.textContent = "0 of 0";
        return;
    }
    
    paginatedItems.forEach(row => {
        const isSelected = state.selected.sjungu.has(row.sheetNum);
        const tr = document.createElement("tr");
        if (isSelected) tr.classList.add("selected");
        
        tr.innerHTML = `
            <td>
                <div class="custom-checkbox">
                    <i class="fas fa-check"></i>
                </div>
            </td>
            <td style="font-weight: 600; color: var(--primary-light);">${row.sheetNum}</td>
            <td>${row.sheetName}</td>
            <td>${row.sheetScale}</td>
        `;
        
        tr.addEventListener("click", () => {
            toggleSelection("sjungu", row.sheetNum, row);
            renderSjunguTable();
        });
        
        DOM.sjunguTableBody.appendChild(tr);
    });
    
    const totalPages = Math.ceil(list.length / limit);
    DOM.sjunguPageInfo.textContent = `Page ${page} of ${totalPages || 1}`;
    DOM.sjunguPrev.disabled = page === 1;
    DOM.sjunguNext.disabled = page === totalPages || totalPages === 0;
    
    updateSelectAllCheckboxState("sjungu", paginatedItems);
}

// Toggle row selection
function toggleSelection(category, id, rowData) {
    const catMap = state.selected[category];
    if (catMap.has(id)) {
        catMap.delete(id);
    } else {
        catMap.set(id, rowData);
    }
    renderDocumentPreview();
}

// Toggle select all on current page
function toggleSelectAll(category) {
    const list = state.records[category];
    const { page, limit } = state.pagination[category];
    const start = (page - 1) * limit;
    const paginatedItems = list.slice(start, start + limit);
    
    const catMap = state.selected[category];
    const keyProp = category === "topography" ? "sheetNum" : (category === "dted" ? "id_name" : (category === "sjungu" ? "sheetNum" : "landused_id"));
    
    // Check if all paginated items are already selected
    const allSelected = paginatedItems.every(row => catMap.has(row[keyProp]));
    
    if (allSelected) {
        // Deselect all on current page
        paginatedItems.forEach(row => catMap.delete(row[keyProp]));
    } else {
        // Select all on current page
        paginatedItems.forEach(row => catMap.set(row[keyProp], row));
    }
    
    renderAllTables();
}

// Helper to keep Select All checkbox icons accurately showing current page state
function updateSelectAllCheckboxState(category, paginatedItems) {
    const catMap = state.selected[category];
    const keyProp = category === "topography" ? "sheetNum" : (category === "dted" ? "id_name" : (category === "sjungu" ? "sheetNum" : "landused_id"));
    const domKey = category === "topography" ? "topoSelectAll" : (category === "dted" ? "dtedSelectAll" : (category === "sjungu" ? "sjunguSelectAll" : "landSelectAll"));
    const checkAllBtn = DOM[domKey];
    
    if (paginatedItems.length === 0) {
        checkAllBtn.innerHTML = '<i class="far fa-square"></i>';
        return;
    }
    
    const allSelected = paginatedItems.every(row => catMap.has(row[keyProp]));
    const someSelected = paginatedItems.some(row => catMap.has(row[keyProp]));
    
    if (allSelected) {
        checkAllBtn.innerHTML = '<i class="fas fa-check-square" style="color: var(--success);"></i>';
    } else if (someSelected) {
        checkAllBtn.innerHTML = '<i class="fas fa-minus-square" style="color: var(--primary-light);"></i>';
    } else {
        checkAllBtn.innerHTML = '<i class="far fa-square"></i>';
    }
}

// Clear all selection Map caches
function clearAllSelection() {
    state.selected.topography.clear();
    state.selected.dted.clear();
    state.selected.landused.clear();
    state.selected.sjungu.clear();
    renderAllTables();
}

// Render Document Printable Card Layout (A4 format)
function renderDocumentPreview() {
    const selectedTopo = Array.from(state.selected.topography.values());
    const selectedDted = Array.from(state.selected.dted.values());
    const selectedLand = Array.from(state.selected.landused.values());
    const selectedSjungu = Array.from(state.selected.sjungu.values());
    
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
        return;
    }
    
    DOM.btnClearSelection.disabled = false;
    DOM.btnPrint.disabled = false;
    DOM.btnPdf.disabled = false;
    
    let html = "";
    
    // Render Category 1: Topography & Sjungu Section (Combined)
    if (selectedTopo.length > 0 || selectedSjungu.length > 0) {
        const totalCount = selectedTopo.length + selectedSjungu.length;
        html += `
            <div class="doc-section">
                <div class="doc-section-title">
                    <span>1. TOPOGRAPHY & SJUNGU RECORDS</span>
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
                                <td style="font-weight: 700; color: #1e3a8a;">${row.sheetNum}</td>
                                <td>${row.sheetName}</td>
                                <td>${row.sheetScale}</td>
                                <td>${row.release_year}</td>
                            </tr>
                        `).join("")}
                        ${selectedSjungu.map((row, idx) => `
                            <tr>
                                <td style="text-align: center; font-weight: 600; color: #64748b;">${idx + 1}.</td>
                                <td style="font-weight: 700; color: #1e3a8a;">${row.sheetNum}</td>
                                <td>${row.sheetName}</td>
                                <td>${row.sheetScale}</td>
                                <td></td>
                            </tr>
                        `).join("")}
                    </tbody>
                </table>
            </div>
        `;
    }
    
    // Render Category 2: Land Used Section
    if (selectedLand.length > 0) {
        html += `
            <div class="doc-section" style="margin-top: 1.5rem;">
                <div class="doc-section-title">
                    <span>2. LAND USE CATEGORIES</span>
                    <span class="doc-section-count">${selectedLand.length} item(s)</span>
                </div>
                <table class="doc-table">
                    <thead>
                        <tr>
                            <th style="width: 25%;">Land Used ID</th>
                            <th style="width: 75%;">Description & Category Name</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${selectedLand.map(row => `
                            <tr>
                                <td style="font-weight: 700;">${row.landused_id}</td>
                                <td>${row.category}</td>
                            </tr>
                        `).join("")}
                    </tbody>
                </table>
            </div>
        `;
    }

    // Render Category 3: DTED Section
    if (selectedDted.length > 0) {
        html += `
            <div class="doc-section" style="margin-top: 1.5rem;">
                <div class="doc-section-title">
                    <span>3. DIGITAL TERRAIN ELEVATION DATA (DTED)</span>
                    <span class="doc-section-count">${selectedDted.length} item(s)</span>
                </div>
                <table class="doc-table">
                    <thead>
                        <tr>
                            <th style="width: 80%;">Elevation ID / File Name</th>
                            <th style="width: 20%;">DTED Level</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${selectedDted.map(row => `
                            <tr>
                                <td style="font-family: monospace; font-size: 0.75rem;">${row.id_name}</td>
                                <td style="font-weight: 700;">Level ${row.level}</td>
                            </tr>
                        `).join("")}
                    </tbody>
                </table>
            </div>
        `;
    }
    
    DOM.docContent.innerHTML = html;
}

// Update printed document title when user types in UI
function updateDocumentTitleText() {
    const inputTitle = DOM.docTitleInput.value.trim();
    const docTitleEl = document.getElementById("document-title-header");
    if (docTitleEl) {
        docTitleEl.textContent = inputTitle || "SaP LISTMAP DATA SPECIFICATION REPORT";
    }
}

// Generate PDF direct download using html2pdf
function generatePDF() {
    const element = document.getElementById("printable-document");
    const opt = {
        margin:       15,
        filename:     `SaP_ListMap_Report_${new Date().toISOString().split('T')[0]}.pdf`,
        image:        { type: 'jpeg', quality: 0.98 },
        html2canvas:  { scale: 2, useCORS: true, logging: false },
        jsPDF:        { unit: 'mm', format: 'a4', orientation: 'portrait' }
    };
    
    // Show spinner or disabling button states
    DOM.btnPdf.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Generating...';
    DOM.btnPdf.disabled = true;
    
    html2pdf().from(element).set(opt).save().then(() => {
        DOM.btnPdf.innerHTML = '<i class="fas fa-file-pdf"></i> Generate PDF';
        DOM.btnPdf.disabled = false;
    }).catch(err => {
        console.error("PDF generation failed:", err);
        DOM.btnPdf.innerHTML = '<i class="fas fa-file-pdf"></i> Generate PDF';
        DOM.btnPdf.disabled = false;
    });
}

// Setup all frontend event listeners
function setupEventListeners() {
    // Tab shifting
    DOM.tabs.forEach(tab => {
        tab.addEventListener("click", () => {
            const target = tab.getAttribute("data-tab");
            
            DOM.tabs.forEach(t => t.classList.remove("active"));
            DOM.contents.forEach(c => c.classList.remove("active"));
            
            tab.classList.add("active");
            document.getElementById(`${target}-content`).classList.add("active");
            state.activeTab = target;
        });
    });
    
    // Theme toggling
    DOM.themeToggle.addEventListener("click", toggleTheme);
    
    // Topography searches & filters
    DOM.topoSearch.addEventListener("input", debounce(() => {
        state.filters.topo_search = DOM.topoSearch.value;
        fetchRecords();
    }, 300));
    
    DOM.topoYear.addEventListener("change", () => {
        state.filters.topo_year = DOM.topoYear.value;
        fetchRecords();
    });
    
    DOM.topoSelectAll.addEventListener("click", () => toggleSelectAll("topography"));
    
    DOM.topoPrev.addEventListener("click", () => {
        if (state.pagination.topography.page > 1) {
            state.pagination.topography.page--;
            renderTopographyTable();
        }
    });
    DOM.topoNext.addEventListener("click", () => {
        const maxPage = Math.ceil(state.records.topography.length / state.pagination.topography.limit);
        if (state.pagination.topography.page < maxPage) {
            state.pagination.topography.page++;
            renderTopographyTable();
        }
    });
    
    // DTED searches & filters
    DOM.dtedSearch.addEventListener("input", debounce(() => {
        state.filters.dted_search = DOM.dtedSearch.value;
        fetchRecords();
    }, 300));
    
    DOM.dtedLevel.addEventListener("change", () => {
        state.filters.dted_level = DOM.dtedLevel.value;
        fetchRecords();
    });
    
    DOM.dtedSelectAll.addEventListener("click", () => toggleSelectAll("dted"));
    
    DOM.dtedPrev.addEventListener("click", () => {
        if (state.pagination.dted.page > 1) {
            state.pagination.dted.page--;
            renderDtedTable();
        }
    });
    DOM.dtedNext.addEventListener("click", () => {
        const maxPage = Math.ceil(state.records.dted.length / state.pagination.dted.limit);
        if (state.pagination.dted.page < maxPage) {
            state.pagination.dted.page++;
            renderDtedTable();
        }
    });
    
    // Land Used searches & filters
    DOM.landSearch.addEventListener("input", debounce(() => {
        state.filters.land_search = DOM.landSearch.value;
        fetchRecords();
    }, 300));
    
    DOM.landSelectAll.addEventListener("click", () => toggleSelectAll("landused"));
    
    DOM.landPrev.addEventListener("click", () => {
        if (state.pagination.landused.page > 1) {
            state.pagination.landused.page--;
            renderLandusedTable();
        }
    });
    DOM.landNext.addEventListener("click", () => {
        const maxPage = Math.ceil(state.records.landused.length / state.pagination.landused.limit);
        if (state.pagination.landused.page < maxPage) {
            state.pagination.landused.page++;
            renderLandusedTable();
        }
    });
    
    // Sjungu searches & filters
    DOM.sjunguSearch.addEventListener("input", debounce(() => {
        state.filters.sjungu_search = DOM.sjunguSearch.value;
        fetchRecords();
    }, 300));
    
    DOM.sjunguSelectAll.addEventListener("click", () => toggleSelectAll("sjungu"));
    
    DOM.sjunguPrev.addEventListener("click", () => {
        if (state.pagination.sjungu.page > 1) {
            state.pagination.sjungu.page--;
            renderSjunguTable();
        }
    });
    DOM.sjunguNext.addEventListener("click", () => {
        const maxPage = Math.ceil(state.records.sjungu.length / state.pagination.sjungu.limit);
        if (state.pagination.sjungu.page < maxPage) {
            state.pagination.sjungu.page++;
            renderSjunguTable();
        }
    });
    
    // Action panel triggers
    DOM.btnClearSelection.addEventListener("click", clearAllSelection);
    DOM.btnPrint.addEventListener("click", () => window.print());
    DOM.btnPdf.addEventListener("click", generatePDF);
    DOM.docTitleInput.addEventListener("input", updateDocumentTitleText);
}

// Helper: Debouncer to prevent hammering database while searching
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

// Update dynamic date in document card footer/header
function updateDocDate() {
    const today = new Date();
    const options = { year: 'numeric', month: 'long', day: 'numeric' };
    const dateStr = today.toLocaleDateString('en-US', options);
    DOM.docDate.textContent = dateStr;
}
