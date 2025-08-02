document.addEventListener('DOMContentLoaded', () => {
    const projectFilterSelect = document.getElementById('project-filter-select');
    const membersContainer = document.getElementById('members-container');
    const tasksContainer = document.getElementById('tasks-container');
    const yesterdayTasksContainer = document.getElementById('yesterday-tasks-container');
    const todayTasksContainer = document.getElementById('today-tasks-container');
    const taskSearchInput = document.getElementById('task-search-input');
    const paginationContainer = document.getElementById('pagination-container');
    const editLogModal = document.getElementById('edit-log-modal');
    const logList = document.getElementById('log-list');
    const closeButton = document.querySelector('.close-button');

    let currentProjectId = null;
    let currentPage = 1;
    let currentSearchQuery = '';

    async function fetchProjects() {
        const projectsResponse = await fetch('/api/ds_board/projects/');
        const projects = await projectsResponse.json();
        populateProjectFilter(projects);
    }

    function populateProjectFilter(projects) {
        projects.forEach(project => {
            const option = document.createElement('option');
            option.value = project.id;
            option.textContent = project.name;
            projectFilterSelect.appendChild(option);
        });
    }

    async function fetchProjectData(projectId, page = 1, searchQuery = '') {
        if (!projectId || projectId === 'all') {
            membersContainer.innerHTML = '';
            tasksContainer.innerHTML = '';
            yesterdayTasksContainer.innerHTML = '';
            todayTasksContainer.innerHTML = '';
            paginationContainer.innerHTML = '';
            return;
        }

        currentProjectId = projectId;
        currentPage = page;
        currentSearchQuery = searchQuery;

        // Fetch members
        const usersResponse = await fetch(`/api/ds_board/project/${projectId}/users/`);
        const users = await usersResponse.json();
        renderMembers(users);

        // Fetch all tasks
        const tasksResponse = await fetch(`/api/ds_board/project/${projectId}/tasks/?page=${page}&search=${searchQuery}`);
        const tasksData = await tasksResponse.json();
        renderTasks(tasksData.tasks, tasksContainer);
        renderPagination(tasksData);

        // Fetch yesterday's tasks
        const yesterdayTasksResponse = await fetch(`/api/ds_board_updated/project/${projectId}/tasks/yesterday/`);
        const yesterdayTasks = await yesterdayTasksResponse.json();
        renderTasks(yesterdayTasks, yesterdayTasksContainer, true);

        // Fetch today's tasks
        const todayTasksResponse = await fetch(`/api/ds_board_updated/project/${projectId}/tasks/today/`);
        const todayTasks = await todayTasksResponse.json();
        renderTasks(todayTasks, todayTasksContainer, true);
    }

    async function renderMembers(users) {
        membersContainer.innerHTML = '';
        for (const user of users) {
            const memberElement = document.createElement('div');
            memberElement.classList.add('card', 'mb-2');

            const yesterdayStatsResponse = await fetch(`/api/ds_board_updated/project/${currentProjectId}/user/${user.id}/stats/yesterday/`);
            const yesterdayStats = await yesterdayStatsResponse.json();

            const todayStatsResponse = await fetch(`/api/ds_board_updated/project/${currentProjectId}/user/${user.id}/stats/today/`);
            const todayStats = await todayStatsResponse.json();

            memberElement.innerHTML = `
                <div class="card-body member-card">
                    <h5 class="card-title">${user.username}</h5>
                    <p class="card-text text-muted">${user.email}</p>
                    <div class="member-stats">
                        <div class="stat">
                            <span class="stat-label">Yesterday</span>
                            <span class="stat-value">Est: ${yesterdayStats.total_estimation_time}h</span>
                            <span class="stat-value">Spent: ${yesterdayStats.total_time_spent}h</span>
                        </div>
                        <div class="stat">
                            <span class="stat-label">Today</span>
                            <span class="stat-value">Est: ${todayStats.total_estimation_time}h</span>
                            <span class="stat-value">Spent: ${todayStats.total_time_spent}h</span>
                        </div>
                    </div>
                </div>
            `;
            membersContainer.appendChild(memberElement);
        }
    }

    function renderTasks(tasks, container, showCancelButton = false) {
        container.innerHTML = '';
        tasks.forEach(task => {
            const taskElement = document.createElement('div');
            taskElement.classList.add('card', 'mb-2');
            taskElement.setAttribute('data-task-id', task.id);
            let editLogButton = `<button class="btn btn-secondary btn-sm float-end edit-log-btn ms-2">Edit Log</button>`;
            let logTimeButton = `<button class="btn btn-primary btn-sm float-end log-time-btn ms-2">Log Time</button>`;
            let cancelButton = '';
            if (showCancelButton) {
                cancelButton = `<button class="btn btn-danger btn-sm float-end cancel-task-btn">X</button>`;
            }
            const totalLogTime = `<p class="card-text logged-time-text">Logged: ${task.total_log_time || 0}h</p>`;
            taskElement.innerHTML = `
                <div class="card-body">
                    ${editLogButton}
                    ${cancelButton}
                    <h5 class="card-title">${task.title}</h5>
                    <p class="card-text">Estimation: ${task.estimation_time}h</p>
                    <p class="card-text">Total Time Spent: <span class="total-time-spent">${task.time_spent}</span>h</p>
                    ${totalLogTime}
                </div>
            `;
            container.appendChild(taskElement);
        });
    }

    function renderPagination(paginationData) {
        paginationContainer.innerHTML = '';

        if (paginationData.has_previous) {
            const prevItem = document.createElement('li');
            prevItem.classList.add('page-item');
            prevItem.innerHTML = `<a class="page-link" href="#" data-page="${paginationData.current_page - 1}">Previous</a>`;
            paginationContainer.appendChild(prevItem);
        }

        for (let i = 1; i <= paginationData.total_pages; i++) {
            const pageItem = document.createElement('li');
            pageItem.classList.add('page-item');
            if (i === paginationData.current_page) {
                pageItem.classList.add('active');
            }
            pageItem.innerHTML = `<a class="page-link" href="#" data-page="${i}">${i}</a>`;
            paginationContainer.appendChild(pageItem);
        }

        if (paginationData.has_next) {
            const nextItem = document.createElement('li');
            nextItem.classList.add('page-item');
            nextItem.innerHTML = `<a class="page-link" href="#" data-page="${paginationData.current_page + 1}">Next</a>`;
            paginationContainer.appendChild(nextItem);
        }
    }

    function initializeSortable() {
        new Sortable(tasksContainer, {
            group: {
                name: 'tasks',
                pull: 'clone',
                put: false
            },
            animation: 150,
        });

        new Sortable(yesterdayTasksContainer, {
            group: {
                name: 'yesterday-tasks',
                put: ['tasks']
            },
            animation: 150,
            onAdd: (event) => {
                const itemEl = event.item;
                const taskId = itemEl.dataset.taskId;
                updateTaskLog(taskId, 'yesterday');

                const cardBody = itemEl.querySelector('.card-body');
                const cancelButton = `<button class="btn btn-danger btn-sm float-end cancel-task-btn ms-2">X</button>`;
                const logTimeButton = `<button class="btn btn-primary btn-sm float-end log-time-btn ms-2">Log Time</button>`;
                const editLogButton = `<button class="btn btn-secondary btn-sm float-end edit-log-btn ms-2">Edit Log</button>`;
                cardBody.innerHTML = cancelButton + logTimeButton + editLogButton + cardBody.innerHTML;
            }
        });

        new Sortable(todayTasksContainer, {
            group: {
                name: 'today-tasks',
                put: ['tasks']
            },
            animation: 150,
            onAdd: (event) => {
                const itemEl = event.item;
                const taskId = itemEl.dataset.taskId;
                updateTaskLog(taskId, 'today');

                const cardBody = itemEl.querySelector('.card-body');
                const cancelButton = `<button class="btn btn-danger btn-sm float-end cancel-task-btn">X</button>`;
                cardBody.innerHTML = cancelButton + cardBody.innerHTML;
            }
        });
    }

    async function logTime(taskId, logTime, date) {
        await fetch('/api/ds_board_updated/log_time/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken'),
            },
            body: JSON.stringify({
                task_id: taskId,
                log_time: logTime,
                date: date,
            }),
        });
    }

    async function updateTaskLog(taskId, date) {
        await fetch('/api/ds_board_updated/update_task_log/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken'),
            },
            body: JSON.stringify({
                task_id: taskId,
                date: date,
            }),
        });
    }

    async function showLogList(taskId) {
        const response = await fetch(`/api/ds_board_updated/task/${taskId}/logs/`);
        const logs = await response.json();
        logList.innerHTML = '';
        logs.forEach(log => {
            const logElement = document.createElement('div');
            logElement.setAttribute('data-log-id', log.id);
            logElement.innerHTML = `
                <p>Date: ${log.task_date}</p>
                <p>Time: <span class="log-time">${log.log_time}</span>h</p>
                <p>Notes: <span class="log-notes">${log.notes || ''}</span></p>
                <button class="btn btn-primary btn-sm edit-log-btn">Edit</button>
                <button class="btn btn-danger btn-sm delete-log-btn">Delete</button>
            `;
            logElement.querySelector('.edit-log-btn').addEventListener('click', () => editLog(log.id, logElement, taskId));
            logElement.querySelector('.delete-log-btn').addEventListener('click', () => deleteLog(log.id, logElement, taskId));
            logList.appendChild(logElement);
        });
        editLogModal.style.display = 'block';
    }

    function editLog(logId, logElement, taskId) {
        const logTimeElement = logElement.querySelector('.log-time');
        const logNotesElement = logElement.querySelector('.log-notes');
        const logDate = logElement.querySelector('p').textContent.split(': ')[1];
        const logTime = parseFloat(logTimeElement.textContent);
        const logNotes = logNotesElement.textContent;

        const logTimeInput = document.createElement('input');
        logTimeInput.type = 'number';
        logTimeInput.value = logTime;

        const logNotesInput = document.createElement('input');
        logNotesInput.type = 'text';
        logNotesInput.value = logNotes;

        const dateInput = document.createElement('input');
        dateInput.type = 'date';
        dateInput.value = logDate;

        const saveButton = document.createElement('button');
        saveButton.textContent = 'Save';
        saveButton.classList.add('btn', 'btn-success', 'btn-sm', 'ms-2');
        saveButton.addEventListener('click', () => updateLog(logId, logTimeInput.value, logNotesInput.value, dateInput.value, taskId));

        logElement.innerHTML = '';
        logElement.appendChild(dateInput);
        logElement.appendChild(logTimeInput);
        logElement.appendChild(logNotesInput);
        logElement.appendChild(saveButton);
    }

    async function updateLog(logId, logTime, logNotes, date, taskId) {
        await fetch(`/api/ds_board_updated/log/${logId}/update/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({
                log_time: logTime,
                notes: logNotes,
                task_date: date
            })
        });
        showLogList(taskId);
    }

    async function deleteLog(logId, logElement, taskId) {
        if (confirm('Are you sure you want to delete this log?')) {
            await fetch(`/api/ds_board_updated/log/${logId}/delete/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCookie('csrftoken')
                }
            });
            logElement.remove();
        }
    }

    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    document.getElementById('ds-board-container').addEventListener('click', (event) => {
        if (event.target.classList.contains('cancel-task-btn')) {
            const taskCard = event.target.closest('.card');
            const taskId = taskCard.dataset.taskId;
            taskCard.remove();
            updateTaskLog(taskId, null);
        }

        if (event.target.classList.contains('edit-log-btn')) {
            const taskCard = event.target.closest('.card');
            const taskId = taskCard.dataset.taskId;
            showLogList(taskId);
        }

        if (event.target.classList.contains('logged-time-text')) {
            const loggedTimeText = event.target;
            const taskCard = loggedTimeText.closest('.card');
            const cardBody = taskCard.querySelector('.card-body');
            const logTimeInput = cardBody.querySelector('.log-time-input');
            if (logTimeInput) {
                return;
            }

            const originalText = loggedTimeText.textContent;
            loggedTimeText.style.display = 'none';

            const input = document.createElement('input');
            input.type = 'number';
            input.min = '0';
            input.step = '0.5';
            input.placeholder = 'Hours';
            input.classList.add('log-time-input');

            const dateInput = document.createElement('input');
            dateInput.type = 'date';
            dateInput.classList.add('log-time-input', 'ms-2');

            const saveButton = document.createElement('button');
            saveButton.textContent = 'Save';
            saveButton.classList.add('btn', 'btn-success', 'btn-sm', 'ms-2');

            const cancelButton = document.createElement('button');
            cancelButton.textContent = 'Cancel';
            cancelButton.classList.add('btn', 'btn-danger', 'btn-sm', 'ms-2');

            const tempContainer = document.createElement('div');
            tempContainer.appendChild(input);
            if (taskCard.closest('.task-column').id === 'tasks-container') {
                tempContainer.appendChild(dateInput);
            }
            tempContainer.appendChild(saveButton);
            tempContainer.appendChild(cancelButton);

            loggedTimeText.parentElement.insertBefore(tempContainer, loggedTimeText.nextSibling);

            saveButton.addEventListener('click', async () => {
                const logTimeValue = input.value;
                try {
                    if (logTimeValue) {
                        const taskId = taskCard.dataset.taskId;
                        const column = taskCard.closest('.task-column');
                        let date;
                        if (column.id === 'yesterday-tasks-container') {
                            date = 'yesterday';
                        } else if (column.id === 'today-tasks-container') {
                            date = 'today';
                        } else {
                            date = dateInput.value;
                        }
                        await logTime(taskId, logTimeValue, date);
                        const totalTimeSpentEl = taskCard.querySelector('.total-time-spent');
                        const currentTotal = parseFloat(totalTimeSpentEl.textContent);
                        totalTimeSpentEl.textContent = currentTotal + parseFloat(logTimeValue);
                        loggedTimeText.textContent = `Logged: ${parseFloat(originalText.split(' ')[1]) + parseFloat(logTimeValue)}h`;
                    }
                } finally {
                    loggedTimeText.style.display = 'block';
                    tempContainer.remove();
                }
            });

            cancelButton.addEventListener('click', () => {
                loggedTimeText.style.display = 'block';
                tempContainer.remove();
            });
        }

        if (event.target.classList.contains('log-time-btn')) {
            const taskCard = event.target.closest('.card');
            const cardBody = taskCard.querySelector('.card-body');
            const logTimeInput = cardBody.querySelector('.log-time-input');
            if (logTimeInput) {
                return;
            }

            const input = document.createElement('input');
            input.type = 'number';
            input.min = '0';
            input.step = '0.5';
            input.placeholder = 'Hours';
            input.classList.add('log-time-input');

            const dateInput = document.createElement('input');
            dateInput.type = 'date';
            dateInput.classList.add('log-time-input', 'ms-2');

            const saveButton = document.createElement('button');
            saveButton.textContent = 'Save';
            saveButton.classList.add('btn', 'btn-success', 'btn-sm', 'ms-2');

            const cancelButton = document.createElement('button');
            cancelButton.textContent = 'Cancel';
            cancelButton.classList.add('btn', 'btn-danger', 'btn-sm', 'ms-2');

            saveButton.addEventListener('click', async () => {
                const logTimeValue = input.value;
                try {
                    if (logTimeValue) {
                        const taskId = taskCard.dataset.taskId;
                        const column = taskCard.closest('.task-column');
                        let date;
                        if (column.id === 'yesterday-tasks-container') {
                            date = 'yesterday';
                        } else if (column.id === 'today-tasks-container') {
                            date = 'today';
                        } else {
                            date = dateInput.value;
                        }
                        await logTime(taskId, logTimeValue, date);
                        const totalTimeSpentEl = taskCard.querySelector('.total-time-spent');
                        const currentTotal = parseFloat(totalTimeSpentEl.textContent);
                        totalTimeSpentEl.textContent = currentTotal + parseFloat(logTimeValue);
                    }
                } finally {
                    cardBody.removeChild(input);
                    if (dateInput.parentElement) {
                        cardBody.removeChild(dateInput);
                    }
                    cardBody.removeChild(saveButton);
                    cardBody.removeChild(cancelButton);
                }
            });

            cancelButton.addEventListener('click', () => {
                cardBody.removeChild(input);
                if (dateInput.parentElement) {
                    cardBody.removeChild(dateInput);
                }
                cardBody.removeChild(saveButton);
                cardBody.removeChild(cancelButton);
            });

            cardBody.appendChild(input);
            if (taskCard.closest('.task-column').id === 'tasks-container') {
                cardBody.appendChild(dateInput);
            }
            cardBody.appendChild(saveButton);
            cardBody.appendChild(cancelButton);
        }
    });

    if (projectFilterSelect) {
        projectFilterSelect.addEventListener('change', () => {
            const selectedProjectId = projectFilterSelect.value;
            fetchProjectData(selectedProjectId);
        });
    }

    if (taskSearchInput) {
        taskSearchInput.addEventListener('input', () => {
            const searchQuery = taskSearchInput.value;
            fetchProjectData(currentProjectId, 1, searchQuery);
        });
    }

    const yesterdayTaskSearchInput = document.getElementById('yesterday-task-search-input');
    if (yesterdayTaskSearchInput) {
        yesterdayTaskSearchInput.addEventListener('input', () => {
            const searchQuery = yesterdayTaskSearchInput.value.toLowerCase();
            const tasks = Array.from(yesterdayTasksContainer.children);
            tasks.forEach(task => {
                const title = task.querySelector('.card-title').textContent.toLowerCase();
                if (title.includes(searchQuery)) {
                    task.style.display = '';
                } else {
                    task.style.display = 'none';
                }
            });
        });
    }

    const todayTaskSearchInput = document.getElementById('today-task-search-input');
    if (todayTaskSearchInput) {
        todayTaskSearchInput.addEventListener('input', () => {
            const searchQuery = todayTaskSearchInput.value.toLowerCase();
            const tasks = Array.from(todayTasksContainer.children);
            tasks.forEach(task => {
                const title = task.querySelector('.card-title').textContent.toLowerCase();
                if (title.includes(searchQuery)) {
                    task.style.display = '';
                } else {
                    task.style.display = 'none';
                }
            });
        });
    }

    if (paginationContainer) {
        paginationContainer.addEventListener('click', (event) => {
            if (event.target.tagName === 'A') {
                event.preventDefault();
                const page = event.target.dataset.page;
                if (page) {
                    fetchProjectData(currentProjectId, page, currentSearchQuery);
                }
            }
        });
    }

    if(closeButton) {
        closeButton.addEventListener('click', () => {
            editLogModal.style.display = 'none';
        });
    }

    window.addEventListener('click', (event) => {
        if (event.target == editLogModal) {
            editLogModal.style.display = "none";
        }
    });

    fetchProjects();
    initializeSortable();
});
