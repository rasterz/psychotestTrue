
    const cardsViewBtn = document.getElementById("cardsViewBtn");
    const tableViewBtn = document.getElementById("tableViewBtn");
    const cardsWrap = document.getElementById("cardsWrap");
    const tableWrap = document.getElementById("tableWrap");
    const exportBtn = document.getElementById("exportBtn");

    const searchInput = document.getElementById("crmSearchInput");
    const filterButtons = document.querySelectorAll(".filter-btn");
    const noResultsBox = document.getElementById("noResultsBox");
    const archiveToggleBtn = document.getElementById("archiveToggleBtn");

    let currentFilter = "all";
    let archiveMode = false;

    function switchToCards() {
        cardsWrap.classList.remove("is-hidden");
        tableWrap.classList.remove("is-active");

        cardsViewBtn.classList.add("is-active");
        tableViewBtn.classList.remove("is-active");

        exportBtn.style.display = "none";
    }

    function switchToTable() {
        cardsWrap.classList.add("is-hidden");
        tableWrap.classList.add("is-active");

        tableViewBtn.classList.add("is-active");
        cardsViewBtn.classList.remove("is-active");

        exportBtn.style.display = "inline-flex";
    }

    function escapeRegExp(string) {
        return string.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
    }

    function clearHighlights(root) {
        if (!root) return;

        root.querySelectorAll(".crm-highlight").forEach((mark) => {
            const textNode = document.createTextNode(mark.textContent);
            mark.replaceWith(textNode);
        });

        root.normalize();
    }

    function highlightInElement(element, query) {
        if (!element || !query) return;

        const regex = new RegExp(`(${escapeRegExp(query)})`, "gi");

        function walk(node) {
            if (node.nodeType === Node.TEXT_NODE) {
                const text = node.nodeValue;

                if (!text || !text.trim()) return;
                if (!regex.test(text)) return;

                regex.lastIndex = 0;

                const wrapper = document.createElement("span");
                wrapper.innerHTML = text.replace(regex, '<span class="crm-highlight">$1</span>');

                const fragment = document.createDocumentFragment();
                while (wrapper.firstChild) {
                    fragment.appendChild(wrapper.firstChild);
                }

                node.parentNode.replaceChild(fragment, node);
                return;
            }

            if (node.nodeType === Node.ELEMENT_NODE) {
                const tag = node.tagName;
                if (tag === "SCRIPT" || tag === "STYLE") return;
                if (node.classList.contains("crm-highlight")) return;

                Array.from(node.childNodes).forEach(walk);
            }
        }

        walk(element);
    }

    function applyHighlights(query) {
        const normalizedQuery = (query || "").trim();

        document.querySelectorAll(".crm-item").forEach((item) => {
            clearHighlights(item);

            if (!normalizedQuery) return;
            if (item.style.display === "none") return;

            highlightInElement(item, normalizedQuery);
        });
    }



    const NEW_LEAD_HOURS = 24;

function parseSqliteDate(dateString) {
    if (!dateString) return null;

    const trimmed = String(dateString).trim();
    const match = trimmed.match(
        /^(\d{4})-(\d{2})-(\d{2})[ T](\d{2}):(\d{2}):(\d{2})$/
    );

    if (!match) return null;

    const [, year, month, day, hour, minute, second] = match;

    return new Date(
        Number(year),
        Number(month) - 1,
        Number(day),
        Number(hour),
        Number(minute),
        Number(second)
    );
}

        function markNewLeads() {
    const now = new Date();

    document.querySelectorAll(".crm-item").forEach((item) => {
        item.classList.remove("is-new");

        const createdAt = item.getAttribute("data-created-at");
        const status = (item.getAttribute("data-status") || "new").toLowerCase();
        const leadDate = parseSqliteDate(createdAt);

        if (status !== "new") return;
        if (!leadDate || Number.isNaN(leadDate.getTime())) return;

        const diffHours = (now - leadDate) / (1000 * 60 * 60);

        if (diffHours >= 0 && diffHours <= NEW_LEAD_HOURS) {
            item.classList.add("is-new");
        }
    });
}
            function applyCrmFilters() {
        const query = (searchInput?.value || "").trim().toLowerCase();
        const items = document.querySelectorAll(".crm-item");

        let visibleCount = 0;

        items.forEach((item) => {
            const source = (item.dataset.source || "").toLowerCase();
            const searchText = (item.dataset.search || "").toLowerCase();
            const status = (item.dataset.status || "new").toLowerCase();

            const matchFilter = currentFilter === "all" || source === currentFilter;
            const matchSearch = !query || searchText.includes(query);
            const matchArchive = archiveMode ? status === "archive" : status !== "archive";

            const isVisible = matchFilter && matchSearch && matchArchive;

            if (item.classList.contains("lead-card")) {
                item.style.display = isVisible ? "" : "none";
            } else if (item.tagName === "TR") {
                item.style.display = isVisible ? "" : "none";
            }

            if (isVisible) {
                visibleCount += 1;
            }
        });

        if (noResultsBox) {
            noResultsBox.style.display = visibleCount === 0 ? "block" : "none";
        }

        applyHighlights(searchInput?.value || "");
    }

    if (cardsViewBtn && tableViewBtn && cardsWrap && tableWrap && exportBtn) {
        cardsViewBtn.addEventListener("click", function () {
            switchToCards();
        });

        tableViewBtn.addEventListener("click", function () {
            switchToTable();
        });
    }

    if (searchInput) {
        searchInput.addEventListener("input", applyCrmFilters);
    }

    filterButtons.forEach((btn) => {
        btn.addEventListener("click", function () {
            filterButtons.forEach((b) => b.classList.remove("is-active"));
            btn.classList.add("is-active");
            currentFilter = btn.dataset.filter || "all";
            applyCrmFilters();
        });
    });

    function updateArchiveButtonState() {
    if (!archiveToggleBtn) return;

    archiveToggleBtn.classList.toggle("is-active", archiveMode);
    archiveToggleBtn.textContent = archiveMode ? "← Назад к CRM" : "Архив";
}

        if (archiveToggleBtn) {
            archiveToggleBtn.addEventListener("click", function () {
                archiveMode = !archiveMode;
                updateArchiveButtonState();
                applyCrmFilters();
    });
}

function syncLeadQuickArchiveButton(leadId, status) {
    const leadCards = document.querySelectorAll(`.lead-card.crm-item[data-lead-id="${leadId}"]`);

    leadCards.forEach((card) => {
        const quickActions = card.querySelector(".quick-actions");
        if (!quickActions) return;

        let archiveBtn = quickActions.querySelector(".js-archive-action");

        if (status === "archive") {
            if (!archiveBtn) {
                archiveBtn = document.createElement("button");
                archiveBtn.type = "button";
                archiveBtn.className = "quick-action-btn quick-action-btn-return js-archive-action";
                quickActions.appendChild(archiveBtn);
            }

            archiveBtn.textContent = "Вернуть в работу";
            archiveBtn.className = "quick-action-btn quick-action-btn-return js-archive-action";
            archiveBtn.onclick = function () {
                updateLeadStatus(leadId, "in_progress");
            };
        } else {
            if (!archiveBtn) {
                archiveBtn = document.createElement("button");
                archiveBtn.type = "button";
                archiveBtn.className = "quick-action-btn quick-action-btn-danger js-archive-action";
                quickActions.appendChild(archiveBtn);
            }

            archiveBtn.textContent = "В архив";
            archiveBtn.className = "quick-action-btn quick-action-btn-danger js-archive-action";
            archiveBtn.onclick = function () {
                updateLeadStatus(leadId, "archive");
            };
        }
    });
}

function syncLeadDeleteButton(leadId, status) {
    const leadCards = document.querySelectorAll(`.lead-card.crm-item[data-lead-id="${leadId}"]`);

    leadCards.forEach((card) => {
        const quickActions = card.querySelector(".quick-actions");
        if (!quickActions) return;

        let deleteBtn = quickActions.querySelector(".js-delete-forever-action");

        if (status === "archive") {
            if (!deleteBtn) {
                deleteBtn = document.createElement("button");
                deleteBtn.type = "button";
                deleteBtn.className = "quick-action-btn quick-action-btn-danger-strong js-delete-forever-action";
                quickActions.appendChild(deleteBtn);
            }

            deleteBtn.textContent = "Удалить навсегда";
            deleteBtn.dataset.leadId = String(leadId);
            deleteBtn.onclick = function () {
                deleteLeadForever(leadId, this);
            };
        } else {
            if (deleteBtn) {
                deleteBtn.remove();
            }
        }
    });
}

function syncLeadTableDeleteButton(leadId, status) {
    const actionsCell = document.getElementById(`table-actions-${leadId}`);
    if (!actionsCell) return;

    if (status === "archive") {

        actionsCell.innerHTML = `
            <button
                type="button"
                class="table-restore-btn"
                onclick="updateLeadStatus(${leadId}, 'new')"
            >
                Вернуть
            </button>

            <button
                type="button"
                class="table-delete-btn js-table-delete-forever-action"
                data-lead-id="${leadId}"
                onclick="deleteLeadForever(${leadId}, this)"
            >
                Удалить
            </button>
        `;

    } else {

        actionsCell.innerHTML = `
            <button
                type="button"
                class="table-archive-btn"
                onclick="updateLeadStatus(${leadId}, 'archive')"
            >
                В архив
            </button>
        `;
    }
}

    async function updateLeadStatus(id, status) {
    const relatedItems = document.querySelectorAll(`.crm-item[data-lead-id="${id}"]`);
    const shouldAnimateArchive = status === "archive" && !archiveMode;

    try {
        if (shouldAnimateArchive) {
            relatedItems.forEach((item) => item.classList.add("is-archiving"));
        }

        const response = await fetch("/crm-update-status", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                lead_id: id,
                status: status
            })
        });

        const result = await response.json();

        if (!response.ok || !result.ok) {
            relatedItems.forEach((item) => item.classList.remove("is-archiving"));
            alert(result.error || "Не удалось обновить статус");
            return;
        }

        const applyStatusUpdate = () => {
    document.querySelectorAll(`.crm-item[data-lead-id="${id}"]`).forEach((item) => {
        item.dataset.status = status;
        item.classList.remove("is-archiving");
    });

    const cardStatusSelect = document.getElementById(`status-${id}`);
    if (cardStatusSelect) {
        cardStatusSelect.value = status;
    }

    const tableStatusSelect = document.getElementById(`table-status-${id}`);
    if (tableStatusSelect) {
        tableStatusSelect.value = status;
    }

    syncLeadQuickArchiveButton(id, status);
    syncLeadDeleteButton(id, status);
    syncLeadTableDeleteButton(id, status);

    showLeadEditedBadge(id);

    markNewLeads();
    applyCrmFilters();
    showCrmToast("Статус обновлён", "success");
};

        if (shouldAnimateArchive) {
            setTimeout(applyStatusUpdate, 280);
        } else {
            applyStatusUpdate();
        }

    } catch (error) {
        relatedItems.forEach((item) => item.classList.remove("is-archiving"));
        alert("Ошибка сети при обновлении статуса");
    }
}
    updateArchiveButtonState();
    markNewLeads();
    applyCrmFilters();
    initTopTableScrollbar();

    document.querySelectorAll(".crm-item[data-lead-id]").forEach((item) => {
    const leadId = item.dataset.leadId;
    const status = (item.dataset.status || "new").toLowerCase();

    if (!leadId) return;

    syncLeadQuickArchiveButton(leadId, status);
    syncLeadDeleteButton(leadId, status);
    syncLeadTableDeleteButton(leadId, status);
});

window.addEventListener("scroll", () => {
    document.body.classList.toggle("scrolled", window.scrollY > 30);
});

let crmToastTimer = null;

function showCrmToast(message, type = "success") {
    let toast = document.getElementById("crmToast");

    if (!toast) {
        toast = document.createElement("div");
        toast.id = "crmToast";
        toast.className = "crm-toast";
        document.body.appendChild(toast);
    }

    toast.textContent = message;
    toast.className = `crm-toast is-visible is-${type}`;

    if (crmToastTimer) {
        clearTimeout(crmToastTimer);
    }

    crmToastTimer = setTimeout(() => {
        toast.classList.remove("is-visible");
    }, 1800);
}

function normalizeMessengerValue(value) {
    return String(value || "")
        .trim()
        .replace(/^https?:\/\/t\.me\//i, "")
        .replace(/^https?:\/\/vk\.com\//i, "")
        .replace(/^@/, "")
        .trim();
}

function normalizePhone(value) {
    return String(value || "").replace(/[^\d+]/g, "").trim();
}

function openLeadContact(contactValue, contactMethod) {
    const rawValue = String(contactValue || "").trim();
    const method = String(contactMethod || "").trim().toLowerCase();

    if (!rawValue) {
        showCrmToast("Контакт не указан", "error");
        return;
    }

    if (method === "phone") {
        const phone = normalizePhone(rawValue);
        if (phone) {
            window.location.href = `tel:${phone}`;
            return;
        }
    }

    if (method === "telegram" || method === "max") {
        const username = normalizeMessengerValue(rawValue);
        if (username) {
            window.open(`https://t.me/${username}`, "_blank");
            return;
        }
    }

    if (method === "vk") {
        const vkValue = normalizeMessengerValue(rawValue);
        if (vkValue) {
            window.open(`https://vk.com/${vkValue}`, "_blank");
            return;
        }
    }

    copyLeadContact(rawValue);
}

async function copyLeadContact(contactValue) {
    const value = String(contactValue || "").trim();

    if (!value) {
        showCrmToast("Контакт не указан", "error");
        return;
    }

    try {
        await navigator.clipboard.writeText(value);
        showCrmToast("Контакт скопирован", "success");
    } catch (error) {
        showCrmToast("Не удалось скопировать контакт", "error");
    }
}

async function saveLeadNote(id) {
    const textarea = document.getElementById(`note-${id}`);
    if (!textarea) return;

    const saveButton = textarea.parentElement?.querySelector(".save-note-btn");
    const note = textarea.value.trim();

    try {
        if (saveButton) {
            saveButton.classList.add("is-saving");
        }

        const response = await fetch("/crm-update-note", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                lead_id: id,
                note: note
            })
        });

        const result = await response.json();

        if (!response.ok || !result.ok) {
            showCrmToast(result.error || "Не удалось сохранить заметку", "error");
            return;
        }

        showCrmToast("Заметка сохранена", "success");
    } catch (error) {
        showCrmToast("Ошибка сети при сохранении заметки", "error");
    } finally {
        if (saveButton) {
            saveButton.classList.remove("is-saving");
        }
    }
}

function escapeHtml(value) {
    return String(value || "")
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}


function formatCrmDate(dateStr) {
    if (!dateStr) return "—";

    const parts = String(dateStr).split(" ");
    if (parts.length < 2) return dateStr;

    const dateParts = parts[0].split("-");
    if (dateParts.length < 3) return dateStr;

    const time = parts[1].slice(0, 5);

    return `${dateParts[2]}.${dateParts[1]}.${dateParts[0]} • ${time}`;
}

function renderLeadNote(note) {
    const formattedDate = formatCrmDate(note.created_at);

    return `
        <div class="lead-note-item" id="note-item-${note.id}">
            <div class="lead-note-head">
                <div class="lead-note-meta">${escapeHtml(formattedDate)}</div>

                <button
                    type="button"
                    class="delete-note-btn"
                    onclick="deleteLeadNote(${note.id})"
                >
                    Удалить
                </button>
            </div>

            <div class="lead-note-text">${escapeHtml(note.note_text || "")}</div>
        </div>
    `;
}

async function addLeadNote(leadId) {
    const textarea = document.getElementById(`note-${leadId}`);
    const notesList = document.getElementById(`notes-list-${leadId}`);

    if (!textarea || !notesList) return;

    const saveButton = textarea.parentElement?.querySelector(".save-note-btn");
    const note = textarea.value.trim();

    if (!note) {
        showCrmToast("Пустую заметку нельзя сохранить", "error");
        return;
    }

    try {
        if (saveButton) {
            saveButton.classList.add("is-saving");
        }

        const response = await fetch("/crm-add-note", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                lead_id: leadId,
                note: note
            })
        });

        const result = await response.json();

        if (!response.ok || !result.ok) {
            showCrmToast(result.error || "Не удалось добавить заметку", "error");
            return;
        }

        const emptyBox = document.getElementById(`notes-empty-${leadId}`);
        if (emptyBox) {
            emptyBox.remove();
        }

        notesList.insertAdjacentHTML("afterbegin", renderLeadNote(result.note));
        textarea.value = "";
        showCrmToast("Заметка добавлена", "success");
    } catch (error) {
        showCrmToast("Ошибка сети при добавлении заметки", "error");
    } finally {
        if (saveButton) {
            saveButton.classList.remove("is-saving");
        }
    }
}

async function deleteLeadNote(noteId) {

    const noteItem = document.getElementById(`note-item-${noteId}`);
    const notesList = noteItem?.parentElement;

    if (!noteItem) return;

    noteItem.classList.add("is-deleting");

    try {

        const response = await fetch("/crm-delete-note", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                note_id: noteId
            })
        });

        const result = await response.json();

        if (!response.ok || !result.ok) {
            noteItem.classList.remove("is-deleting");
            showCrmToast(result.error || "Не удалось удалить заметку", "error");
            return;
        }

        setTimeout(() => {

            noteItem.remove();

            if (notesList && !notesList.querySelector(".lead-note-item")) {

                const leadId = notesList.id.replace("notes-list-", "");

                notesList.innerHTML = `
                <div class="lead-notes-empty" id="notes-empty-${leadId}">
                    Пока нет заметок
                </div>
                `;
            }

        }, 200);

        showCrmToast("Заметка удалена", "success");

    } catch (error) {

        noteItem.classList.remove("is-deleting");
        showCrmToast("Ошибка сети при удалении заметки", "error");

    }
}

function normalizeDisplayValue(value) {
    const text = String(value ?? "").trim();
    return text || "—";
}

function rebuildLeadSearchIndex(leadId) {
    const items = document.querySelectorAll(`.crm-item[data-lead-id="${leadId}"]`);

    items.forEach((item) => {
        const parts = [];

        const cardName = item.querySelector('[data-bind="full_name"]')?.textContent || "";
        const cardContact = item.querySelector('[data-bind="contact_value"]')?.textContent || "";
        const cardMethod = item.querySelector('[data-bind="contact_method"]')?.textContent || "";
        const cardAge = item.querySelector('[data-bind="age"]')?.textContent || "";
        const cardCity = item.querySelector('[data-bind="city"]')?.textContent || "";
        const cardCategory = item.querySelector('[data-bind="category"]')?.textContent || "";
        const cardMessage = item.querySelector('[data-bind="request_message"]')?.textContent || "";

        parts.push(cardName, cardContact, cardMethod, cardAge, cardCity, cardCategory, cardMessage);
        item.dataset.search = parts.join(" ").toLowerCase();
    });
}

function showLeadEditedBadge(leadId) {
    const badge = document.getElementById(`edited-badge-${leadId}`);
    if (!badge) return;

    badge.classList.add("is-visible");

    if (badge._hideTimer) {
        clearTimeout(badge._hideTimer);
    }

    badge._hideTimer = setTimeout(() => {
        badge.classList.remove("is-visible");
    }, 5 * 60 * 1000);
}

function syncLeadFieldInCard(leadId, field, value) {
    const card = document.querySelector(`.lead-card.crm-item[data-lead-id="${leadId}"]`);
    if (!card) return;

    if (field === "full_name") {
        const node = card.querySelector('[data-bind="full_name"]');
        if (node) node.textContent = normalizeDisplayValue(value);
    }

    if (field === "contact_value") {
        const node = card.querySelector('[data-bind="contact_value"]');
        if (node) node.textContent = normalizeDisplayValue(value);
    }

    if (field === "contact_method") {
        const node = card.querySelector('[data-bind="contact_method"]');
        if (node) node.textContent = normalizeDisplayValue(value);
    }

    if (field === "age") {
        const node = card.querySelector('[data-bind="age"]');
        if (node) node.textContent = normalizeDisplayValue(value);
    }

    if (field === "city") {
        const node = card.querySelector('[data-bind="city"]');
        if (node) node.textContent = normalizeDisplayValue(value);
    }

    if (field === "category") {
        const node = card.querySelector('[data-bind="category"]');
        const separator = card.querySelector('[data-bind-separator="category"]');

        if (node) {
            node.textContent = String(value || "").trim();
        }

        if (separator) {
            separator.innerHTML = String(value || "").trim() ? "<br>" : "";
        }
    }

    if (field === "request_message") {
        let messageBox = card.querySelector(".message-box");
        let messageText = card.querySelector('[data-bind="request_message"]');
        const cleanValue = String(value || "").trim();

        if (cleanValue) {
            if (!messageBox) {
                const sections = card.querySelector(".lead-sections");
                if (sections) {
                    sections.insertAdjacentHTML(
                        "afterend",
                        `
                        <div class="message-box">
                            <div class="section-title">Запрос / сообщение</div>
                            <div class="message-text" data-bind="request_message"></div>
                        </div>
                        `
                    );
                }
                messageText = card.querySelector('[data-bind="request_message"]');
            }

            if (messageText) {
                messageText.textContent = cleanValue;
            }
        } else {
            if (messageBox) {
                messageBox.remove();
            }
        }
    }

    rebuildLeadSearchIndex(leadId);
    showLeadEditedBadge(leadId);
}

async function saveLeadField(leadId, field, value) {
    try {
        const response = await fetch("/crm-update-field", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                lead_id: leadId,
                field: field,
                value: value
            })
        });

        const result = await response.json();

        if (!response.ok || !result.ok) {
            showCrmToast(result.error || "Не удалось сохранить поле", "error");
            return;
        }

        syncLeadFieldInCard(leadId, field, result.value);
        applyCrmFilters();
        showCrmToast("Изменения сохранены", "success");
    } catch (error) {
        showCrmToast("Ошибка сети при сохранении поля", "error");
    }
}


async function deleteLeadForever(leadId, buttonEl = null) {
    const deleteButtons = document.querySelectorAll(
        `.js-delete-forever-action[data-lead-id="${leadId}"], .js-table-delete-forever-action[data-lead-id="${leadId}"]`
    );

    const currentButton =
        buttonEl ||
        document.querySelector(`.js-delete-forever-action[data-lead-id="${leadId}"]`) ||
        document.querySelector(`.js-table-delete-forever-action[data-lead-id="${leadId}"]`);

    if (!currentButton) return;

    if (currentButton.dataset.isDeleting === "1") {
        return;
    }

    const confirmed = currentButton.dataset.confirmDelete === "1";

    if (!confirmed) {
        showCrmToast("Нажми ещё раз, чтобы удалить навсегда", "error");

        deleteButtons.forEach((btn) => {
            btn.dataset.confirmDelete = "1";
        });

        setTimeout(() => {
            deleteButtons.forEach((btn) => {
                if (btn.dataset.isDeleting !== "1") {
                    delete btn.dataset.confirmDelete;
                }
            });
        }, 5000);

        return;
    }

    const relatedItems = document.querySelectorAll(`.crm-item[data-lead-id="${leadId}"]`);

    try {
        deleteButtons.forEach((btn) => {
            btn.dataset.isDeleting = "1";
            btn.disabled = true;
        });

        relatedItems.forEach((item) => item.classList.add("is-archiving"));

        const response = await fetch("/crm-delete-lead", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ lead_id: leadId })
        });

        const result = await response.json();

        if (!response.ok || !result.ok) {
            relatedItems.forEach((item) => item.classList.remove("is-archiving"));

            deleteButtons.forEach((btn) => {
                delete btn.dataset.isDeleting;
                btn.disabled = false;
            });

            showCrmToast(result.error || "Не удалось удалить заявку", "error");
            return;
        }

        setTimeout(() => {
            relatedItems.forEach((item) => item.remove());
            applyCrmFilters();
        }, 220);

        showCrmToast("Запись удалена навсегда", "success");
    } catch (error) {
        relatedItems.forEach((item) => item.classList.remove("is-archiving"));

        deleteButtons.forEach((btn) => {
            delete btn.dataset.isDeleting;
            btn.disabled = false;
        });

        showCrmToast("Ошибка сети при удалении заявки", "error");
    }
}

function initTopTableScrollbar() {
    const tableWrap = document.getElementById("tableWrap");
    const tableScrollTop = document.getElementById("tableScrollTop");
    const tableScrollTopInner = document.getElementById("tableScrollTopInner");
    const crmTable = document.querySelector(".crm-table");

    if (!tableWrap || !tableScrollTop || !tableScrollTopInner || !crmTable) return;

    function syncTopScrollbar() {
        const isTableMode = tableWrap.classList.contains("is-active");
        tableScrollTop.classList.toggle("is-active", isTableMode);

        tableScrollTopInner.style.width = `${crmTable.scrollWidth}px`;
    }

    let syncingFromTop = false;
    let syncingFromBottom = false;

    tableScrollTop.addEventListener("scroll", () => {
        if (syncingFromBottom) return;
        syncingFromTop = true;
        tableWrap.scrollLeft = tableScrollTop.scrollLeft;
        syncingFromTop = false;
    });

    tableWrap.addEventListener("scroll", () => {
        if (syncingFromTop) return;
        syncingFromBottom = true;
        tableScrollTop.scrollLeft = tableWrap.scrollLeft;
        syncingFromBottom = false;
    });

    window.addEventListener("resize", syncTopScrollbar);

    syncTopScrollbar();

    const observer = new MutationObserver(syncTopScrollbar);
    observer.observe(tableWrap, { attributes: true, childList: true, subtree: true });
}