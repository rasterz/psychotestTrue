async function loadInlineSvg(url) {
    const response = await fetch(url, { cache: "no-store" });
    if (!response.ok) {
        throw new Error(`SVG load failed: ${response.status}`);
    }
    return await response.text();
}

async function loadManifest(url) {
    const response = await fetch(url, { cache: "no-store" });
    if (!response.ok) {
        throw new Error(`Manifest load failed: ${response.status}`);
    }
    return await response.json();
}

function applyPieceAnimation(svg, manifest) {
    if (!svg || !manifest || !Array.isArray(manifest.pieces)) return;

    const piecesById = new Map();
    manifest.pieces.forEach((piece) => {
        if (piece && piece.id) {
            piecesById.set(piece.id, piece);
        }
    });

    svg.querySelectorAll(".piece").forEach((node) => {
        const config = piecesById.get(node.id);
        if (!config) return;

        const dx = config.initialOffset?.x ?? 0;
        const dy = config.initialOffset?.y ?? 0;
        const scale = config.initialScale ?? 0.84;
        const delay = config.delayMs ?? 0;

        node.style.setProperty("--dx", `${dx}px`);
        node.style.setProperty("--dy", `${dy}px`);
        node.style.setProperty("--sc", scale);
        node.style.transitionDelay = `${delay}ms`;
    });
}

function showFallback(container, fallbackUrl, startDelay = 1800) {
    if (!fallbackUrl) return;

    const img = document.createElement("img");
    img.src = fallbackUrl;
    img.alt = "";
    img.className = "hero-brain__fallback";

    container.innerHTML = "";
    container.appendChild(img);

    setTimeout(() => {
        container.classList.add("is-visible");
    }, startDelay);
}

async function initMiniBrain(container, startDelay = 1800) {
    const svgUrl = container.dataset.svgUrl;
    const manifestUrl = container.dataset.manifestUrl;
    const fallbackUrl = container.dataset.fallbackUrl;

    if (!svgUrl || !manifestUrl) {
        showFallback(container, fallbackUrl, startDelay);
        return;
    }

    try {
        const [svgText, manifest] = await Promise.all([
            loadInlineSvg(svgUrl),
            loadManifest(manifestUrl)
        ]);

        container.innerHTML = svgText;

        const svg = container.querySelector("svg");
        if (!svg) {
            showFallback(container, fallbackUrl, startDelay);
            return;
        }

        svg.classList.add("hero-brain-svg");
        applyPieceAnimation(svg, manifest);

        requestAnimationFrame(() => {
            requestAnimationFrame(() => {
                setTimeout(() => {
                    container.classList.add("is-visible");
                    svg.classList.add("is-visible");
                }, startDelay);
            });
        });
    } catch (error) {
        console.error("Mini brain init error:", error);
        showFallback(container, fallbackUrl, startDelay);
    }
}

document.addEventListener("DOMContentLoaded", () => {
    const miniBrains = document.querySelectorAll(".hero-brain-mini");
    miniBrains.forEach((container) => {
        initMiniBrain(container, 900);
    });
});

document.addEventListener("DOMContentLoaded", () => {
    const shell = document.getElementById("brainRadialShell");
    const backdrop = document.getElementById("brainRadialBackdrop");
    const coreButton = document.getElementById("brainCoreButton");
    const coreHint = document.getElementById("brainCoreHint");
    const stage = document.getElementById("brainRadialStage");
    const level1 = document.getElementById("brainLevel1");
    const level2 = document.getElementById("brainLevel2");
    const level3 = document.getElementById("brainLevel3");
    const finalCard = document.getElementById("brainFinalCard");
    const pathNode = document.getElementById("brainPath");
    const finalTitle = document.getElementById("brainFinalTitle");
    const finalText = document.getElementById("brainFinalText");
    const brainConsultationBtn = document.getElementById("brainConsultationBtn");

    if (!shell || !backdrop || !coreButton || !stage || !level1 || !level2 || !level3 || !finalCard) return;


    const hollandTree = {
    r: {
        label: "Практика",
        children: {
            tech: {
                label: "Техника",
                children: {
                    mechanic: "Механик",
                    engineer: "Инженер-механик",
                    service: "Сервисный инженер",
                    auto: "Автомеханик",
                    cnc: "Оператор станков",
                    electrician: "Электромеханик",
                    robotics: "Техник-робототехник"
                }
            },
            build: {
                label: "Строительство",
                children: {
                    architect_tech: "Техник-проектировщик",
                    estimator: "Сметчик",
                    foreman: "Прораб",
                    installer: "Монтажник",
                    surveyor: "Геодезист",
                    engineer_build: "Инженер-строитель",
                    cad_build: "Чертёжник CAD"
                }
            },
            transport: {
                label: "Транспорт",
                children: {
                    logistic: "Логист",
                    driver: "Водитель спецтехники",
                    rail: "Специалист ж/д сферы",
                    aviation_tech: "Авиатехник",
                    dispatcher: "Диспетчер перевозок",
                    navigator: "Специалист по навигации",
                    fleet: "Менеджер автопарка"
                }
            },
            production: {
                label: "Производство",
                children: {
                    technologist: "Технолог производства",
                    quality: "Специалист ОТК",
                    operator: "Оператор линии",
                    welder: "Сварщик",
                    assembler: "Сборщик оборудования",
                    turner: "Токарь",
                    process_engineer: "Инженер-технолог"
                }
            },
            safety: {
                label: "Безопасность",
                children: {
                    rescuer: "Спасатель",
                    fire: "Пожарный",
                    industrial_safety: "Специалист по охране труда",
                    security_engineer: "Инженер по безопасности",
                    military_tech: "Военно-техническая сфера",
                    civil_defense: "Специалист ГО и ЧС",
                    technosphere: "Инженер техносферной безопасности"
                }
            },
            agro: {
                label: "Природа и агросфера",
                children: {
                    agronomist: "Агроном",
                    vet_assist: "Ветеринарный фельдшер",
                    zoo_specialist: "Зоотехник",
                    forestry: "Специалист лесного хозяйства",
                    farmer_tech: "Механизатор",
                    landscape: "Специалист по благоустройству",
                    greenhouse: "Оператор тепличного комплекса"
                }
            }
        }
    },

        i: {
        label: "Исследование",
        children: {
            science: {
                label: "Наука",
                children: {
                    biologist: "Изучение живой природы",
                    chemist: "Химические исследования",
                    physicist: "Физические исследования",
                    ecologist: "Экология и природа",
                    lab: "Работа в лаборатории",
                    microbiologist: "Микромир и бактерии",
                    geologist: "Изучение Земли"
                }
            },
            analytics: {
                label: "Аналитика",
                children: {
                    business_analyst: "Анализ бизнеса",
                    systems_analyst: "Анализ IT-систем",
                    data_analyst: "Анализ данных",
                    market_analyst: "Анализ рынка",
                    researcher: "Проведение исследований",
                    risk: "Оценка рисков",
                    product_analyst: "Анализ продукта"
                }
            },
            it: {
                label: "IT и технологии",
                children: {
                    backend: "Серверная разработка",
                    frontend: "Интерфейсы сайтов",
                    python: "Разработка на Python",
                    java: "Разработка на Java",
                    qa: "Проверка качества ПО",
                    data_science: "Данные и модели",
                    devops: "Серверы и инфраструктура",
                    ml: "Разработка ИИ"
                }
            },
            medicine: {
                label: "Медицина",
                children: {
                    doctor: "Диагностика и лечение",
                    diagnost: "Медицинская диагностика",
                    genetics: "Генетика человека",
                    neuro: "Мозг и нервная система",
                    pharmacist: "Лекарства и фармация",
                    radiologist: "Снимки и диагностика",
                    lab_doctor: "Лабораторная медицина"
                }
            },
            psychology: {
                label: "Психология",
                children: {
                    psychologist: "Психологическая помощь",
                    neuropsychologist: "Мозг и психика",
                    psychodiagnostics: "Психодиагностика",
                    hr_assessment: "Оценка людей",
                    counselor: "Консультирование",
                    profiler: "Анализ поведения",
                    research_psy: "Исследования в психологии"
                }
            },
            digital_research: {
                label: "Цифровые исследования",
                children: {
                    ux_researcher: "Исследование пользователей",
                    ai_analyst: "Анализ ИИ-решений",
                    cyber: "Кибербезопасность",
                    bioinfo: "Биоинформатика",
                    gis: "Карты и геоданные",
                    simulation: "Моделирование систем",
                    database_arch: "Структура данных"
                }
            }
        }
    },


    a: {
        label: "Творчество",
        children: {
            design: {
                label: "Дизайн",
                children: {
                    graphic: "Графический дизайнер",
                    uxui: "UX/UI дизайнер",
                    motion: "Motion-дизайнер",
                    interior: "Дизайнер интерьера",
                    brand: "Бренд-дизайнер",
                    industrial: "Промышленный дизайнер",
                    set_design: "Сценограф"
                }
            },
            media: {
                label: "Медиа",
                children: {
                    editor: "Редактор",
                    screenwriter: "Сценарист",
                    copywriter: "Копирайтер",
                    content: "Контент-креатор",
                    journalist: "Журналист",
                    producer_media: "Медиапродюсер",
                    podcaster: "Подкастер"
                }
            },
            visual: {
                label: "Визуальное искусство",
                children: {
                    illustrator: "Иллюстратор",
                    photographer: "Фотограф",
                    videographer: "Видеограф",
                    artist: "Художник",
                    animator: "Аниматор",
                    comic: "Комикс-художник",
                    colorist: "Колорист"
                }
            },
            performance: {
                label: "Сцена",
                children: {
                    actor: "Актёр",
                    presenter: "Ведущий",
                    musician: "Музыкант",
                    vocalist: "Вокалист",
                    director: "Режиссёр",
                    choreographer: "Хореограф",
                    sound_producer: "Саунд-продюсер"
                }
            },
            fashion: {
                label: "Стиль и мода",
                children: {
                    stylist: "Стилист",
                    costume: "Дизайнер одежды",
                    mua: "Визажист",
                    decorator: "Декоратор",
                    image: "Имидж-консультант",
                    textile: "Текстильный дизайнер",
                    jewelry: "Дизайнер украшений"
                }
            },
            creative_industry: {
                label: "Креативные индустрии",
                children: {
                    art_manager: "Арт-менеджер",
                    curator: "Куратор выставок",
                    game_designer: "Гейм-дизайнер",
                    narrative: "Нарративный дизайнер",
                    creative_producer: "Креативный продюсер",
                    art_director: "Арт-директор",
                    trendwatcher: "Тренд-аналитик"
                }
            }
        }
    },

    s: {
        label: "Общение",
        children: {
            education: {
                label: "Образование",
                children: {
                    teacher: "Учитель",
                    tutor: "Тьютор",
                    educator: "Педагог доп. образования",
                    methodist: "Методист",
                    speech: "Логопед",
                    curator_edu: "Куратор обучения",
                    mentor: "Наставник"
                }
            },
            helping: {
                label: "Помогающие профессии",
                children: {
                    psychologist: "Психолог",
                    social_worker: "Социальный специалист",
                    counselor: "Консультант",
                    coach: "Коуч",
                    curator: "Куратор программ",
                    mediator_help: "Семейный медиатор",
                    inclusion: "Специалист по инклюзии"
                }
            },
            medicine_people: {
                label: "Работа с людьми в медицине",
                children: {
                    nurse: "Медсестра / медбрат",
                    rehab: "Реабилитолог",
                    pediatric: "Педиатр",
                    speech_therapist: "Дефектолог",
                    health_consult: "Медицинский консультант",
                    ergotherapist: "Эрготерапевт",
                    instructor_lfk: "Инструктор ЛФК"
                }
            },
            hr: {
                label: "HR и развитие",
                children: {
                    recruiter: "Рекрутер",
                    hr_manager: "HR-менеджер",
                    adaptation: "Специалист по адаптации",
                    trainer: "Бизнес-тренер",
                    career: "Карьерный консультант",
                    employer_brand: "Специалист HR-бренда",
                    learning_dev: "L&D специалист"
                }
            },
            service: {
                label: "Сервис и сопровождение",
                children: {
                    manager: "Клиентский менеджер",
                    admin: "Администратор",
                    tourism: "Специалист по туризму",
                    event: "Организатор мероприятий",
                    support: "Специалист поддержки",
                    hostess: "Координатор сервиса",
                    customer_success: "Customer Success Manager"
                }
            },
            community: {
                label: "Сообщества и коммуникации",
                children: {
                    community: "Комьюнити-менеджер",
                    moderator: "Модератор сообществ",
                    volunteer: "Координатор волонтёров",
                    youth: "Специалист по работе с молодёжью",
                    nonprofit: "Координатор НКО-проектов",
                    curator_club: "Куратор клубов и программ",
                    partnership: "Менеджер по партнёрствам"
                }
            }
        }
    },

    e: {
        label: "Лидерство",
        children: {
            business: {
                label: "Бизнес",
                children: {
                    entrepreneur: "Предприниматель",
                    product: "Продакт-менеджер",
                    sales: "Руководитель продаж",
                    bizdev: "Business Development Manager",
                    manager: "Операционный менеджер",
                    franchise: "Менеджер развития бизнеса",
                    retail_head: "Руководитель направления"
                }
            },
            marketing: {
                label: "Маркетинг",
                children: {
                    marketer: "Маркетолог",
                    brand: "Бренд-менеджер",
                    pr: "PR-менеджер",
                    smm: "SMM-специалист",
                    producer: "Продюсер",
                    perf: "Performance-маркетолог",
                    influence: "Менеджер инфлюенсеров"
                }
            },
            law_public: {
                label: "Право и общественная сфера",
                children: {
                    lawyer: "Юрист",
                    advocate: "Адвокат",
                    diplomat: "Дипломат",
                    public_manager: "Госуправление",
                    mediator: "Медиатор",
                    policy: "Специалист по публичной политике",
                    ngo_lead: "Руководитель общественных проектов"
                }
            },
            project: {
                label: "Управление проектами",
                children: {
                    project_manager: "Project Manager",
                    scrum: "Scrum Master",
                    coordinator: "Координатор проектов",
                    account: "Аккаунт-менеджер",
                    producer_project: "Продюсер проектов",
                    delivery: "Delivery Manager",
                    operations_pm: "Операционный координатор"
                }
            },
            finance_sales: {
                label: "Финансы и продажи",
                children: {
                    sales_manager: "Менеджер по продажам",
                    account_exec: "Аккаунт-экзекьютив",
                    broker: "Брокер",
                    investment: "Инвестиционный консультант",
                    banker: "Банковская сфера",
                    key_account: "Key Account Manager",
                    real_estate: "Специалист по недвижимости"
                }
            },
            events: {
                label: "Организация и влияние",
                children: {
                    event_head: "Продюсер мероприятий",
                    wedding: "Организатор свадеб",
                    festival: "Координатор фестивалей",
                    education_events: "Менеджер образовательных программ",
                    speaker_relations: "Менеджер спикеров",
                    business_assistant: "Бизнес-ассистент",
                    producer_launch: "Продюсер запусков"
                }
            }
        }
    },

    c: {
        label: "Порядок",
        children: {
            docs: {
                label: "Документы и учёт",
                children: {
                    accountant: "Бухгалтер",
                    clerk: "Делопроизводитель",
                    archive: "Архивариус",
                    notary: "Нотариальная сфера",
                    records: "Специалист документооборота",
                    secretary: "Секретарь",
                    legal_records: "Архивист юридических документов"
                }
            },
            finance: {
                label: "Финансы",
                children: {
                    economist: "Экономист",
                    auditor: "Аудитор",
                    financier: "Финансист",
                    tax: "Налоговый специалист",
                    payroll: "Специалист по расчётам",
                    treasury: "Казначей",
                    budgeting: "Специалист по бюджетированию"
                }
            },
            admin: {
                label: "Администрирование",
                children: {
                    office: "Офис-менеджер",
                    administrator: "Администратор",
                    coordinator: "Координатор",
                    assistant: "Ассистент руководителя",
                    logistics_docs: "Логист-документооборот",
                    receptionist: "Секретарь-администратор",
                    scheduler_admin: "Планировщик процессов"
                }
            },
            law_order: {
                label: "Правила и регламенты",
                children: {
                    compliance: "Комплаенс-специалист",
                    inspector: "Инспектор",
                    customs: "Таможенная сфера",
                    legal_assistant: "Помощник юриста",
                    standardization: "Специалист по стандартизации",
                    certification: "Специалист по сертификации",
                    records_control: "Контролёр регламентов"
                }
            },
            data: {
                label: "Точность и данные",
                children: {
                    operator: "Оператор баз данных",
                    verifier: "Специалист верификации",
                    statistician: "Статистик",
                    tester: "Тестировщик",
                    scheduler: "Планировщик",
                    catalog: "Контент-менеджер каталога",
                    data_entry: "Оператор ввода данных"
                }
            },
            logistics: {
                label: "Логистика и координация",
                children: {
                    supply: "Специалист по снабжению",
                    warehouse: "Координатор склада",
                    route: "Планировщик маршрутов",
                    procurement: "Специалист по закупкам",
                    inventory: "Специалист по инвентаризации",
                    dispatch_log: "Логист-координатор",
                    customs_docs: "Специалист по сопроводительным документам"
                }
            }
        }
    }
};


    let currentLevel = 0;
    let selectedLevel1 = null;
    let selectedLevel2 = null;
    let selectedLevel3 = null;

    const stateClasses = ["is-r", "is-i", "is-a", "is-s", "is-e", "is-c"];

    function clearState() {
        shell.classList.remove(...stateClasses);
    }

    function setState(code) {
        clearState();
        if (code) {
            shell.classList.add(`is-${code}`);
        }
    }

    function openShell() {
        shell.classList.add("is-open");
        coreButton.setAttribute("aria-expanded", "true");
        stage.setAttribute("aria-hidden", "false");
    }

    function closeShell() {
        shell.classList.remove("is-open");
        shell.dataset.level = "0";
        coreButton.setAttribute("aria-expanded", "false");
        stage.setAttribute("aria-hidden", "true");
        clearState();

        currentLevel = 0;
        selectedLevel1 = null;
        selectedLevel2 = null;
        selectedLevel3 = null;

        level1.classList.remove("is-active");
        level2.classList.remove("is-active");
        level3.classList.remove("is-active");
        finalCard.classList.remove("is-active");

                level2.innerHTML = "";
        level3.innerHTML = "";
        pathNode.textContent = "";
        pathNode.classList.remove("is-visible");

        if (coreHint) {
            coreHint.classList.remove("is-hidden");
        }
        coreButton.classList.remove("is-awake");
    }

    function updatePath() {
    if (!pathNode) return;
    pathNode.textContent = "";
    pathNode.classList.remove("is-visible");
}




    function showLevel1() {
        currentLevel = 1;
        shell.dataset.level = "1";

        level1.classList.add("is-active");
        level2.classList.remove("is-active");
        level3.classList.remove("is-active");
        finalCard.classList.remove("is-active");

        level2.innerHTML = "";
        level3.innerHTML = "";
        selectedLevel2 = null;
        selectedLevel3 = null;

        updatePath();
    }

        function createButton(label, extraClass = "") {
            const button = document.createElement("button");
            button.type = "button";
            button.className = `brain-dynamic-button ${extraClass}`.trim();
            button.innerHTML = `<span>${label}</span>`;
            return button;
    }


    function getRingMetrics(level) {
    const mobile = window.innerWidth <= 640;

    if (level === 2) {
        return mobile
            ? { radiusX: 138, radiusY: 120 }
            : { radiusX: 205, radiusY: 176 };
    }

    return mobile
        ? { radiusX: 148, radiusY: 128 }
        : { radiusX: 220, radiusY: 188 };
}


function placeButtonsOnRing(container, buttons, level) {
    if (!container || !buttons.length) return;

    const { radiusX, radiusY } = getRingMetrics(level);
    const mobile = window.innerWidth <= 640;

    let cx = container.clientWidth / 2;
    let cy = container.clientHeight / 2;

    if (level === 2) {
        const stageRect = stage.getBoundingClientRect();
        const brainRect = coreButton.getBoundingClientRect();

        cx = (brainRect.left - stageRect.left) + (brainRect.width / 2);
        cy = (brainRect.top - stageRect.top) + (brainRect.height / 2);
}


    let anglesDeg = [];

    if (level === 2) {
    anglesDeg = mobile
        ? [-90, -32, 28, 88, 148, 208]
        : [-90, -34, 24, 84, 144, 204];
    } else {


        const startAngle = -90;
        const step = buttons.length <= 1 ? 0 : 360 / buttons.length;
        anglesDeg = buttons.map((_, index) => startAngle + step * index);
    }

    buttons.forEach((button, index) => {
        const angleDeg = anglesDeg[index] ?? -90;
        const angle = (angleDeg * Math.PI) / 180;

        const x = cx + Math.cos(angle) * radiusX;
        const y = cy + Math.sin(angle) * radiusY;

        button.style.left = `${x}px`;
        button.style.top = `${y}px`;
        button.style.right = "auto";
        button.style.bottom = "auto";
        button.style.transform = "translate(-50%, -50%)";
    });
}



    function renderLevel2(level1Code) {
    const items = hollandTree[level1Code].children;
    level2.innerHTML = "";

    const buttons = [];

    Object.entries(items).forEach(([key, value], index) => {
        const button = createButton(value.label, "brain-ring-button brain-level2-card");
        button.dataset.key = key;
        button.style.setProperty("--item-index", index);

        button.addEventListener("click", (event) => {
            event.stopPropagation();

            level2.querySelectorAll(".brain-level2-card").forEach((node) => {
                node.classList.remove("is-selected");
            });

            button.classList.add("is-selected");
            selectedLevel2 = key;
            selectedLevel3 = null;
            updatePath();
            renderLevel3(level1Code, key);
        });

        level2.appendChild(button);
        buttons.push(button);
    });

    requestAnimationFrame(() => {
        requestAnimationFrame(() => {
            placeButtonsOnRing(level2, buttons, 2);
        });
    });
}



    function showLevel2(level1Code) {
        currentLevel = 2;
        shell.dataset.level = "2";

        setState(level1Code);
        renderLevel2(level1Code);

        level1.classList.remove("is-active");
        level2.classList.add("is-active");
        level3.classList.remove("is-active");
        finalCard.classList.remove("is-active");

        selectedLevel3 = null;
        updatePath();
    }

    function renderLevel3(level1Code, level2Code) {
    const items = hollandTree[level1Code].children[level2Code].children;
    level3.innerHTML = "";

    const buttons = [];

    Object.values(items).forEach((label, index) => {
        const button = createButton(label, "brain-chip brain-level3-card");
        button.style.setProperty("--item-index", index);

        button.addEventListener("click", (event) => {
            event.stopPropagation();

            level3.querySelectorAll(".brain-level3-card").forEach((node) => {
                node.classList.remove("is-selected");
            });

            button.classList.add("is-selected");
            selectedLevel3 = label;
            updatePath();
            showFinal(level1Code, level2Code, label);
        });

        level3.appendChild(button);
        buttons.push(button);
    });

    currentLevel = 3;
    shell.dataset.level = "3";

    level2.classList.remove("is-active");
    level3.classList.add("is-active");
    finalCard.classList.remove("is-active");

    requestAnimationFrame(() => {
        placeButtonsOnRing(level3, buttons, 3);
    });

    updatePath();
}



    function showFinal(level1Code, level2Code, level3Label) {
        const level1Label = hollandTree[level1Code].label;
        const level2Label = hollandTree[level1Code].children[level2Code].label;

        finalTitle.textContent = level3Label;
        finalText.textContent = `Маршрут «${level1Label} → ${level2Label} → ${level3Label}» выглядит для вас особенно живым. Можно уточнить это через тест или сразу обсудить на консультации.`;


        currentLevel = 4;
        shell.dataset.level = "4";

        level3.classList.remove("is-active");
        finalCard.classList.add("is-active");

        updatePath();
    }

    function stepBack() {
        if (!shell.classList.contains("is-open")) return;

        if (currentLevel === 4) {
            finalCard.classList.remove("is-active");
            level3.classList.add("is-active");
            currentLevel = 3;
            shell.dataset.level = "3";
            selectedLevel3 = null;
            updatePath();
            return;
        }

        if (currentLevel === 3) {
            level3.classList.remove("is-active");
            level2.classList.add("is-active");
            currentLevel = 2;
            shell.dataset.level = "2";
            selectedLevel3 = null;
            updatePath();
            return;
        }

        if (currentLevel === 2) {
            showLevel1();
            return;
        }

        if (currentLevel === 1) {
            closeShell();
        }
    }

    coreButton.addEventListener("click", (event) => {
    event.stopPropagation();

    if (!shell.classList.contains("is-open")) {
        if (coreHint) {
            coreHint.classList.add("is-hidden");
        }
        coreButton.classList.add("is-awake");
        openShell();
        showLevel1();
        return;
    }

    closeShell();
});

    level1.querySelectorAll(".brain-radial-button").forEach((button) => {
        const code = button.dataset.code;

        button.addEventListener("mouseenter", () => {
            if (currentLevel === 1) setState(code);
        });

        button.addEventListener("focus", () => {
            if (currentLevel === 1) setState(code);
        });

        button.addEventListener("mouseleave", () => {
            if (currentLevel === 1) clearState();
        });

        button.addEventListener("blur", () => {
            if (currentLevel === 1) clearState();
        });

        button.addEventListener("click", (event) => {
            event.stopPropagation();
            selectedLevel1 = code;
            selectedLevel2 = null;
            selectedLevel3 = null;
            showLevel2(code);
        });
    });

    if (brainConsultationBtn) {
        brainConsultationBtn.addEventListener("click", () => {
            const openConsultationModalBtn = document.getElementById("openConsultationModal");
            if (openConsultationModalBtn) {
                openConsultationModalBtn.click();
            }
        });
    }

    backdrop.addEventListener("click", (event) => {
    event.stopPropagation();
    closeShell();
    });


    document.addEventListener("click", (event) => {
        if (!shell.contains(event.target)) {
            closeShell();
        }
    });

    document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && shell.classList.contains("is-open")) {
        closeShell();
    }
});

window.addEventListener("resize", () => {
    if (!shell.classList.contains("is-open")) return;

    if (currentLevel === 2) {
        placeButtonsOnRing(level2, [...level2.querySelectorAll(".brain-dynamic-button")], 2);
    }

    if (currentLevel === 3) {
        placeButtonsOnRing(level3, [...level3.querySelectorAll(".brain-chip")], 3);
    }
});
});