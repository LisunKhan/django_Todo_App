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

        // Fetch tasks
        const tasksResponse = await fetch(`/api/ds_board/project/${projectId}/tasks/?page=${page}&search=${searchQuery}`);
        const tasksData = await tasksResponse.json();
        renderTasks(tasksData.tasks, tasksContainer);
        renderPagination(tasksData);
    }

    function renderMembers(users) {
        membersContainer.innerHTML = '';
        users.forEach(user => {
            const memberElement = document.createElement('div');
            memberElement.classList.add('card', 'mb-2');
            memberElement.innerHTML = `
                <div class="card-body">
                    <h5 class="card-title">${user.username}</h5>
                </div>
            `;
            membersContainer.appendChild(memberElement);
        });
    }

    function renderTasks(tasks, container, showCancelButton = false) {
        container.innerHTML = '';
        tasks.forEach(task => {
            const taskElement = document.createElement('div');
            taskElement.classList.add('card', 'mb-2');
            taskElement.setAttribute('data-task-id', task.id);
            let editLogButton = `<button class="btn btn-primary btn-sm float-end edit-log-btn">Edit Log</button>`;
            let cancelButton = '';
            if (showCancelButton) {
                cancelButton = `<button class="btn btn-danger btn-sm float-end cancel-task-btn">X</button>`;
            }
            taskElement.innerHTML = `
                <div class="card-body">
                    ${editLogButton}
                    ${cancelButton}
                    <h5 class="card-title">${task.title}</h5>
                    <p class="card-text">Estimation: ${task.estimation_time}h</p>
                    <p class="card-text">Total Time Spent: <span class="total-time-spent">${task.time_spent}</span>h</p>
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
                cardBody.innerHTML = `<button class="btn btn-danger btn-sm float-end cancel-task-btn">X</button>` + cardBody.innerHTML;
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
                cardBody.innerHTML = `<button class="btn btn-danger btn-sm float-end cancel-task-btn">X</button>` + cardBody.innerHTML;
            }
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
        const logTime = parseFloat(logTimeElement.textContent);
        const logNotes = logNotesElement.textContent;

        const logTimeInput = document.createElement('input');
        logTimeInput.type = 'number';
        logTimeInput.value = logTime;

        const logNotesInput = document.createElement('input');
        logNotesInput.type = 'text';
        logNotesInput.value = logNotes;

        const saveButton = document.createElement('button');
        saveButton.textContent = 'Save';
        saveButton.classList.add('btn', 'btn-success', 'btn-sm', 'ms-2');
        saveButton.addEventListener('click', () => updateLog(logId, logTimeInput.value, logNotesInput.value, taskId));

        logElement.innerHTML = '';
        logElement.appendChild(logTimeInput);
        logElement.appendChild(logNotesInput);
        logElement.appendChild(saveButton);
    }

    async function updateLog(logId, logTime, logNotes, taskId) {
        await fetch(`/api/ds_board_updated/log/${logId}/update/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({
                log_time: logTime,
                notes: logNotes
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
