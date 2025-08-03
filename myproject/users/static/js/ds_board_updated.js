document.addEventListener('DOMContentLoaded', () => {
    const projectFilterSelect = document.getElementById('project-filter-select');
    const userRowsContainer = document.getElementById('user-rows-container');
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
        projects.forEach((project, index) => {
            const option = document.createElement('option');
            option.value = project.id;
            option.textContent = project.name;
            if (index === 0) {
                option.selected = true;
            }
            projectFilterSelect.appendChild(option);
        });

        if (projects.length > 0) {
            fetchProjectData(projects[0].id);
        }
    }

    async function fetchProjectData(projectId, page = 1, searchQuery = '') {
        if (!projectId || projectId === 'all') {
            userRowsContainer.innerHTML = '';
            paginationContainer.innerHTML = '';
            return;
        }

        currentProjectId = projectId;
        currentPage = page;
        currentSearchQuery = searchQuery;

        userRowsContainer.innerHTML = '';

        const usersResponse = await fetch(`/api/ds_board/project/${projectId}/users/`);
        const users = await usersResponse.json();

        for (const user of users) {
            await renderUserRow(user, page, searchQuery);
        }
    }

    async function renderUserRow(user, page, searchQuery) {
        const userRow = document.createElement('div');
        userRow.classList.add('user-row', 'mb-4');
        userRow.innerHTML = `
            <div class="row">
                <div class="col-md-12">
                    <h3>${user.username}</h3>
                </div>
            </div>
            <div class="row">
                <div class="col-md-4">
                    <h2>All Tasks</h2>
                    <div class="task-column all-tasks-container" data-user-id="${user.id}"></div>
                </div>
                <div class="col-md-4">
                    <h2>Yesterday's Tasks</h2>
                    <div class="task-column yesterday-tasks-container" data-user-id="${user.id}"></div>
                </div>
                <div class="col-md-4">
                    <h2>Today's Tasks</h2>
                    <div class="task-column today-tasks-container" data-user-id="${user.id}"></div>
                </div>
            </div>
        `;
        userRowsContainer.appendChild(userRow);

        const allTasksContainer = userRow.querySelector('.all-tasks-container');
        const yesterdayTasksContainer = userRow.querySelector('.yesterday-tasks-container');
        const todayTasksContainer = userRow.querySelector('.today-tasks-container');

        // Fetch all tasks for the user
        const tasksResponse = await fetch(`/api/ds_board/project/${currentProjectId}/tasks/?page=${page}&search=${searchQuery}&user_id=${user.id}`);
        const tasksData = await tasksResponse.json();
        renderTasks(tasksData.tasks, allTasksContainer);
        if (user.id === users[0].id) { // Render pagination only for the first user to avoid duplicates
            renderPagination(tasksData);
        }


        // Fetch yesterday's tasks for the user
        const yesterdayTasksResponse = await fetch(`/api/ds_board_updated/project/${currentProjectId}/tasks/yesterday/?user_id=${user.id}`);
        const yesterdayTasks = await yesterdayTasksResponse.json();
        renderTasks(yesterdayTasks, yesterdayTasksContainer, true);

        // Fetch today's tasks for the user
        const todayTasksResponse = await fetch(`/api/ds_board_updated/project/${currentProjectId}/tasks/today/?user_id=${user.id}`);
        const todayTasks = await todayTasksResponse.json();
        renderTasks(todayTasks, todayTasksContainer, true);

        initializeSortable(allTasksContainer, yesterdayTasksContainer, todayTasksContainer);
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

    function initializeSortable(allTasksContainer, yesterdayTasksContainer, todayTasksContainer) {
        new Sortable(allTasksContainer, {
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

        const addLogButton = document.createElement('button');
        addLogButton.textContent = 'Add New Log';
        addLogButton.classList.add('btn', 'btn-primary', 'mb-3');
        addLogButton.addEventListener('click', () => addLog(taskId));
        logList.appendChild(addLogButton);

        const table = document.createElement('table');
        table.classList.add('table');
        const thead = document.createElement('thead');
        thead.innerHTML = `
            <tr>
                <th>Date</th>
                <th>Time (h)</th>
                <th>Notes</th>
                <th>Actions</th>
            </tr>
        `;
        table.appendChild(thead);

        const tbody = document.createElement('tbody');
        logs.forEach(log => {
            const row = document.createElement('tr');
            row.setAttribute('data-log-id', log.id);
            row.innerHTML = `
                <td>${log.task_date}</td>
                <td><span class="log-time">${log.log_time}</span></td>
                <td><span class="log-notes">${log.notes || ''}</span></td>
                <td>
                    <button class="btn btn-sm btn-edit">Edit</button>
                    <button class="btn btn-sm btn-delete">Delete</button>
                </td>
            `;
            row.querySelector('.btn-edit').addEventListener('click', () => editLog(log.id, row, taskId));
            row.querySelector('.btn-delete').addEventListener('click', () => deleteLog(log.id, row, taskId));
            tbody.appendChild(row);
        });
        table.appendChild(tbody);
        logList.appendChild(table);
        editLogModal.style.display = 'block';
    }

    function addLog(taskId) {
        const table = logList.querySelector('table');
        const tbody = table.querySelector('tbody');
        const newRow = document.createElement('tr');
        newRow.innerHTML = `
            <td><input type="date" class="form-control" value="${new Date().toISOString().slice(0, 10)}"></td>
            <td><input type="number" class="form-control" placeholder="Time"></td>
            <td><input type="text" class="form-control" placeholder="Notes"></td>
            <td>
                <button class="btn btn-sm btn-save-new">Save</button>
                <button class="btn btn-sm btn-cancel-new">Cancel</button>
            </td>
        `;
        tbody.appendChild(newRow);

        newRow.querySelector('.btn-save-new').addEventListener('click', () => {
            const date = newRow.querySelector('input[type="date"]').value;
            const time = newRow.querySelector('input[type="number"]').value;
            const notes = newRow.querySelector('input[type="text"]').value;
            saveNewLog(taskId, time, notes, date);
        });

        newRow.querySelector('.btn-cancel-new').addEventListener('click', () => {
            newRow.remove();
        });
    }

    async function saveNewLog(taskId, logTime, notes, date) {
        const response = await fetch(`/api/ds_board_updated/task/${taskId}/log/create/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({
                log_time: logTime,
                notes: notes,
                task_date: date
            })
        });
        const data = await response.json();
        if (data.success) {
            const taskCard = document.querySelector(`[data-task-id="${taskId}"]`);
            if (taskCard) {
                const totalTimeSpentEl = taskCard.querySelector('.total-time-spent');
                const loggedTimeTextEl = taskCard.querySelector('.logged-time-text');
                if (totalTimeSpentEl) {
                    totalTimeSpentEl.textContent = data.total_time_spent;
                }
                if (loggedTimeTextEl) {
                    loggedTimeTextEl.textContent = `Logged: ${data.total_log_time}h`;
                }
            }
            showLogList(taskId);
        }
    }

    function editLog(logId, logElement, taskId) {
        const tds = logElement.querySelectorAll('td');
        const logDate = tds[0].textContent;
        const logTime = parseFloat(tds[1].textContent);
        const logNotes = tds[2].textContent;

        tds[0].innerHTML = `<input type="date" class="form-control" value="${logDate}">`;
        tds[1].innerHTML = `<input type="number" class="form-control" value="${logTime}">`;
        tds[2].innerHTML = `<input type="text" class="form-control" value="${logNotes}">`;
        tds[3].innerHTML = `
            <button class="btn btn-sm btn-save">Save</button>
            <button class="btn btn-sm btn-cancel">Cancel</button>
        `;

        const dateInput = tds[0].querySelector('input');
        const timeInput = tds[1].querySelector('input');
        const notesInput = tds[2].querySelector('input');

        tds[3].querySelector('.btn-save').addEventListener('click', () => {
            updateLog(logId, timeInput.value, notesInput.value, dateInput.value, taskId);
        });
        tds[3].querySelector('.btn-cancel').addEventListener('click', () => {
            showLogList(taskId);
        });
    }

    async function updateLog(logId, logTime, logNotes, date, taskId) {
        const response = await fetch(`/api/ds_board_updated/log/${logId}/update/`, {
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
        const data = await response.json();
        if (data.success) {
            const taskCard = document.querySelector(`[data-task-id="${taskId}"]`);
            if (taskCard) {
                const totalTimeSpentEl = taskCard.querySelector('.total-time-spent');
                const loggedTimeTextEl = taskCard.querySelector('.logged-time-text');
                if (totalTimeSpentEl) {
                    totalTimeSpentEl.textContent = data.total_time_spent;
                }
                if (loggedTimeTextEl) {
                    loggedTimeTextEl.textContent = `Logged: ${data.total_log_time}h`;
                }
            }
            showLogList(taskId);
        }
    }

    async function deleteLog(logId, logElement, taskId) {
        if (confirm('Are you sure you want to delete this log?')) {
            const response = await fetch(`/api/ds_board_updated/log/${logId}/delete/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCookie('csrftoken')
                }
            });
            const data = await response.json();
            if (data.success) {
                const taskCard = document.querySelector(`[data-task-id="${taskId}"]`);
                if (taskCard) {
                    const totalTimeSpentEl = taskCard.querySelector('.total-time-spent');
                    const loggedTimeTextEl = taskCard.querySelector('.logged-time-text');
                    if (totalTimeSpentEl) {
                        totalTimeSpentEl.textContent = data.total_time_spent;
                    }
                    if (loggedTimeTextEl) {
                        loggedTimeTextEl.textContent = `Logged: ${data.total_log_time}h`;
                    }
                }
                logElement.remove();
            }
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

    document.getElementById('user-rows-container').addEventListener('click', (event) => {
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
});
