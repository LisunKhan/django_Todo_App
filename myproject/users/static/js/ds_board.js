document.addEventListener('DOMContentLoaded', () => {
    const dsBoardContainer = document.getElementById('ds-board-container');
    const projectFilterSelect = document.getElementById('project-filter-select');
    const modal = document.getElementById('add-task-modal');
    const editLogModal = document.getElementById('edit-log-modal');
    const closeButtons = document.querySelectorAll('.close-button');
    let currentUserId;

    closeButtons.forEach(button => {
        button.addEventListener('click', () => {
            modal.style.display = 'none';
            editLogModal.style.display = 'none';
        });
    });

    async function fetchCurrentUser() {
        const response = await fetch('/api/ds_board/current_user/');
        const data = await response.json();
        currentUserId = data.user_id;
    }

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

    let allTasks = [];
    async function fetchProjectData(projectId) {
        if (!projectId || projectId === 'all') {
            dsBoardContainer.innerHTML = '';
            return;
        }

        const usersResponse = await fetch(`/api/ds_board/project/${projectId}/users/`);
        const users = await usersResponse.json();

        const tasksResponse = await fetch(`/api/ds_board/project/${projectId}/tasks/`);
        const tasksData = await tasksResponse.json();
        allTasks = tasksData;

        const yesterdayLogsResponse = await fetch(`/api/ds_board/project/${projectId}/logs/?date=yesterday`);
        const yesterdayLogs = await yesterdayLogsResponse.json();

        const todayLogsResponse = await fetch(`/api/ds_board/project/${projectId}/logs/?date=today`);
        const todayLogs = await todayLogsResponse.json();

        const blockersResponse = await fetch(`/api/ds_board/project/${projectId}/blockers/`);
        const blockers = await blockersResponse.json();

        renderDSBoard(users, allTasks, yesterdayLogs, todayLogs, blockers);
    }

    function renderDSBoard(users, tasks, yesterdayLogs, todayLogs, blockers) {
        dsBoardContainer.innerHTML = '';

        users.forEach(user => {
            const userRow = document.createElement('div');
            userRow.classList.add('user-row');
            userRow.setAttribute('data-user-id', user.id);

            const userInfo = document.createElement('div');
            userInfo.classList.add('user-info');
            userInfo.textContent = user.username;
            userRow.appendChild(userInfo);

            const allTasksColumn = createColumn('All Tasks');
            allTasksColumn.classList.add('task-pool');
            userRow.appendChild(allTasksColumn);

            const yesterdayTasksColumn = createColumn("Yesterday's Tasks");
            userRow.appendChild(yesterdayTasksColumn);

            const todayTasksColumn = createColumn("Today's Tasks", true);
            userRow.appendChild(todayTasksColumn);

            const blockersColumn = createColumn('Blockers');
            userRow.appendChild(blockersColumn);

            dsBoardContainer.appendChild(userRow);
        });

        populateTasks(tasks, yesterdayLogs, todayLogs, blockers);
        initializeSortable();
    }

    function createColumn(title, isToday = false) {
        const column = document.createElement('div');
        column.classList.add('task-column');
        if (title === 'Total Time (min)') {
            title = 'Total Time (hours)';
        }
        column.innerHTML = `<h4>${title}</h4>`;
        if (title === 'All Tasks') {
            const searchInput = document.createElement('input');
            searchInput.type = 'text';
            searchInput.placeholder = 'Search tasks...';
            searchInput.classList.add('task-search-input');
            searchInput.addEventListener('input', (e) => {
                const searchQuery = e.target.value.toLowerCase();
                filterAllTasks(searchQuery);
            });
            column.appendChild(searchInput);
        }
        if (isToday) {
            const addTaskButton = document.createElement('button');
            addTaskButton.classList.add('add-task-button');
            addTaskButton.textContent = '+ Add a card';
            addTaskButton.addEventListener('click', handleAddTask);
            column.appendChild(addTaskButton);
        }
        return column;
    }

    function filterAllTasks(searchQuery) {
        const userRows = document.querySelectorAll('.user-row');
        userRows.forEach(userRow => {
            const allTasksColumn = userRow.querySelector('.task-pool');
            const taskCards = allTasksColumn.querySelectorAll('.task-card');
            taskCards.forEach(taskCard => {
                const title = taskCard.querySelector('h5').textContent.toLowerCase();
                if (title.includes(searchQuery)) {
                    taskCard.style.display = '';
                } else {
                    taskCard.style.display = 'none';
                }
            });
        });
    }

    async function populateTasks(tasks, yesterdayLogs, todayLogs, blockers) {
        const renderedTaskIds = new Set();
        const userRows = document.querySelectorAll('.user-row');
        userRows.forEach(userRow => {
            const allTasksColumn = userRow.querySelector('.task-pool');
            const yesterdayTasksColumn = userRow.children[2];
            const todayTasksColumn = userRow.children[3];
            const blockersColumn = userRow.children[4];

            const columnsToClear = [allTasksColumn, yesterdayTasksColumn, todayTasksColumn, blockersColumn];
            columnsToClear.forEach(column => {
                const taskCards = column.querySelectorAll('.task-card');
                taskCards.forEach(card => card.remove());
            });
        });

        for (const log of yesterdayLogs) {
            const task = tasks.find(t => t.id === log.task_id);
            if (task && !renderedTaskIds.has(task.id)) {
                const taskCard = await createTaskCard(task);
                const userRow = document.querySelector(`.user-row[data-user-id='${task.user_id}']`);
                if (userRow) {
                    userRow.children[2].appendChild(taskCard);
                    renderedTaskIds.add(task.id);
                }
            }
        }

        for (const log of todayLogs) {
            const task = tasks.find(t => t.id === log.task_id);
            if (task && !renderedTaskIds.has(task.id)) {
                const taskCard = await createTaskCard(task);
                const userRow = document.querySelector(`.user-row[data-user-id='${task.user_id}']`);
                if (userRow) {
                    userRow.children[3].appendChild(taskCard);
                    renderedTaskIds.add(task.id);
                }
            }
        }

        for (const blocker of blockers) {
            const taskCard = await createTaskCard(blocker);
            const userRow = document.querySelector(`.user-row[data-user-id='${blocker.user_id}']`);
            if (userRow) {
                userRow.children[4].appendChild(taskCard);
            }
        }

        for (const task of tasks) {
            if (!renderedTaskIds.has(task.id)) {
                const taskCard = await createTaskCard(task);
                const userRow = document.querySelector(`.user-row[data-user-id='${task.user_id}']`);
                if (userRow) {
                    const allTasksColumn = userRow.querySelector('.task-pool');
                    allTasksColumn.appendChild(taskCard);
                }
            }
        }
    }


    async function createTaskCard(task) {
        const taskCard = document.createElement('div');
        taskCard.classList.add('task-card');
        taskCard.setAttribute('draggable', true);
        taskCard.setAttribute('data-task-id', task.id);
        taskCard.setAttribute('data-user-id', task.user_id);

        const header = document.createElement('div');
        header.classList.add('task-card-header');

        const title = document.createElement('h5');
        title.textContent = task.title;
        header.appendChild(title);

        const status = document.createElement('div');
        status.classList.add('task-status', `status-${task.status}`);
        status.textContent = task.status;
        header.appendChild(status);

        const response = await fetch(`/api/ds_board/user/${task.user_id}/profile_picture/`);
        const data = await response.json();
        if (data.profile_picture_url) {
            const avatar = document.createElement('img');
            avatar.classList.add('user-avatar');
            avatar.src = data.profile_picture_url;
            header.appendChild(avatar);
        }

        taskCard.appendChild(header);

        const estimation = document.createElement('p');
        estimation.textContent = `Estimation: ${task.estimation_time}h`;
        taskCard.appendChild(estimation);

        const totalTime = document.createElement('p');
        const totalTimeResponse = await fetch(`/api/ds_board/task/${task.id}/total_time/`);
        const totalTimeData = await totalTimeResponse.json();
        totalTime.textContent = `Total Time Spent: ${totalTimeData.total_time.toFixed(2)}h`;

        const editLogButton = document.createElement('button');
        editLogButton.textContent = 'Edit Log';
        editLogButton.addEventListener('click', () => showLogList(task.id));
        totalTime.appendChild(editLogButton);

        taskCard.appendChild(totalTime);

        const logTimeButton = document.createElement('button');
        logTimeButton.textContent = 'Log Time';
        logTimeButton.addEventListener('click', () => showLogTimeInput(taskCard, task.id));
        taskCard.appendChild(logTimeButton);

        return taskCard;
    }

    function showLogTimeInput(taskCard, taskId) {
        const existingLogTimeInput = taskCard.querySelector('.log-time-input');
        if (existingLogTimeInput) {
            return;
        }

        const logTimeInput = document.createElement('input');
        logTimeInput.type = 'number';
        logTimeInput.min = '0';
        logTimeInput.step = '0.5';
        logTimeInput.placeholder = 'Hours';
        logTimeInput.classList.add('log-time-input');

        const saveLogButton = document.createElement('button');
        saveLogButton.textContent = 'Save';
        saveLogButton.addEventListener('click', () => saveLogTime(taskCard, taskId, logTimeInput.value));

        taskCard.appendChild(logTimeInput);
        taskCard.appendChild(saveLogButton);
    }

    async function showLogList(taskId) {
        const response = await fetch(`/api/ds_board/task/${taskId}/logs/`);
        const logs = await response.json();
        const logList = document.getElementById('log-list');
        logList.innerHTML = '';
        logs.forEach(log => {
            const logElement = document.createElement('div');
            logElement.setAttribute('data-log-id', log.id);
            logElement.innerHTML = `
                <p>Date: ${log.task_date}</p>
                <p>Time: <span class="log-time">${log.log_time}</span>h</p>
                <p>Notes: <span class="log-notes">${log.notes || ''}</span></p>
                <button class="edit-log-button">Edit</button>
                <button class="delete-log-button">Delete</button>
            `;
            logElement.querySelector('.edit-log-button').addEventListener('click', () => editLog(log.id, logElement, taskId));
            logElement.querySelector('.delete-log-button').addEventListener('click', () => deleteLog(log.id, logElement, taskId));
            logList.appendChild(logElement);
        });
        const modal = document.getElementById('edit-log-modal');
        modal.style.display = 'block';
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
        saveButton.addEventListener('click', () => updateLog(logId, logTimeInput.value, logNotesInput.value, taskId));

        logElement.innerHTML = '';
        logElement.appendChild(logTimeInput);
        logElement.appendChild(logNotesInput);
        logElement.appendChild(saveButton);
    }

    async function updateLog(logId, logTime, logNotes, taskId) {
        const response = await fetch(`/api/ds_board/log/${logId}/update/`, {
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

        if (response.ok) {
            showLogList(taskId);
            const taskCard = document.querySelector(`[data-task-id='${taskId}']`);
            const totalTimeElement = taskCard.querySelector('p:nth-child(3)');
            const totalTimeResponse = await fetch(`/api/ds_board/task/${taskId}/total_time/`);
            const totalTimeData = await totalTimeResponse.json();
            totalTimeElement.textContent = `Total Time Spent: ${totalTimeData.total_time.toFixed(2)}h`;
        }
    }

    async function deleteLog(logId, logElement, taskId) {
        if (confirm('Are you sure you want to delete this log?')) {
            await fetch(`/api/ds_board/log/${logId}/delete/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCookie('csrftoken')
                }
            });
            logElement.remove();
            const taskCard = document.querySelector(`[data-task-id='${taskId}']`);
            const totalTimeElement = taskCard.querySelector('p:nth-child(3)');
            const totalTimeResponse = await fetch(`/api/ds_board/task/${taskId}/total_time/`);
            const totalTimeData = await totalTimeResponse.json();
            totalTimeElement.textContent = `Total Time Spent: ${totalTimeData.total_time.toFixed(2)}h`;
        }
    }

    async function saveLogTime(taskCard, taskId, logTime) {
        const response = await fetch('/api/ds_board/log_time/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({
                task_id: taskId,
                log_time: logTime
            })
        });

        if (response.ok) {
            const logTimeInput = taskCard.querySelector('.log-time-input');
            const saveLogButton = logTimeInput.nextElementSibling;
            logTimeInput.parentElement.removeChild(logTimeInput);
            saveLogButton.parentElement.removeChild(saveLogButton);

            const totalTimeElement = taskCard.querySelector('p:nth-child(3)');
            const totalTimeResponse = await fetch(`/api/ds_board/task/${taskId}/total_time/`);
            const totalTimeData = await totalTimeResponse.json();
            totalTimeElement.textContent = `Total Time Spent: ${totalTimeData.total_time.toFixed(2)}h`;

            const editLogButton = document.createElement('button');
            editLogButton.textContent = 'Edit Log';
            editLogButton.addEventListener('click', () => showLogList(taskId));
            totalTimeElement.appendChild(editLogButton);
        }
    }

    function handleAddTask(event) {
        const todayColumn = event.target.parentElement;
        const userRow = todayColumn.parentElement;
        const userId = parseInt(userRow.dataset.userId);

        if (userId !== currentUserId) {
            alert("You can only add tasks to your own board.");
            return;
        }

        const taskProjectSelect = document.getElementById('task-project');
        taskProjectSelect.innerHTML = '';
        const projects = Array.from(projectFilterSelect.options).slice(1);
        projects.forEach(option => {
            const newOption = document.createElement('option');
            newOption.value = option.value;
            newOption.textContent = option.textContent;
            taskProjectSelect.appendChild(newOption);
        });

        modal.style.display = 'block';
    }

    window.addEventListener('click', (event) => {
        if (event.target === modal) {
            modal.style.display = 'none';
        }
    });

    const addTaskForm = document.getElementById('add-task-form');
    addTaskForm.addEventListener('submit', async (event) => {
        event.preventDefault();
        const title = document.getElementById('task-title').value;
        const estimationTime = document.getElementById('task-estimation').value;
        const projectId = document.getElementById('task-project').value;

        const response = await fetch('/api/ds_board/create_task/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({
                title: title,
                estimation_time: estimationTime,
                project_id: projectId
            })
        });

        if (response.ok) {
            const task = await response.json();
            const taskCard = createTaskCard(task);
            const userRow = document.querySelector(`.user-row[data-user-id='${task.user_id}']`);
            if (userRow) {
                userRow.children[2].appendChild(taskCard);
            }
            modal.style.display = 'none';
            addTaskForm.reset();
        }
    });

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


    async function updateTaskLog(taskId, date) {
        await fetch('/api/ds_board/update_task_log/', {
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

    function initializeSortable() {
        const columns = document.querySelectorAll('.task-column');
        const taskPools = document.querySelectorAll('.task-pool');

        columns.forEach(column => {
            new Sortable(column, {
                group: 'tasks',
                animation: 150,
                ghostClass: 'sortable-ghost',
                chosenClass: 'sortable-chosen',
                dragClass: 'sortable-drag',
                onAdd: (event) => {
                    const taskId = event.item.dataset.taskId;
                    const toColumn = event.to;

                    let date;
                    if (toColumn.children[0].textContent === "Today's Tasks") {
                        date = 'today';
                    } else if (toColumn.children[0].textContent === "Yesterday's Tasks") {
                        date = 'yesterday';
                    } else {
                        date = null;
                    }

                    updateTaskLog(taskId, date);
                },
                onEnd: (event) => {
                    if (event.from === event.to) {
                        return; // Ignore if the item was moved within the same list
                    }
                    const taskId = event.item.dataset.taskId;
                    const toColumn = event.to;

                    let date;
                    if (toColumn.children[0].textContent === "Today's Tasks") {
                        date = 'today';
                    } else if (toColumn.children[0].textContent === "Yesterday's Tasks") {
                        date = 'yesterday';
                    } else {
                        date = null;
                    }

                    updateTaskLog(taskId, date);
                }
            });
        });

        taskPools.forEach(pool => {
            new Sortable(pool, {
                group: {
                    name: 'tasks',
                    pull: 'clone',
                    put: false
                },
                animation: 150,
                ghostClass: 'sortable-ghost',
                chosenClass: 'sortable-chosen',
                dragClass: 'sortable-drag',
                sort: false
            });
        });
    }

    projectFilterSelect.addEventListener('change', () => {
        const selectedProjectId = projectFilterSelect.value;
        fetchProjectData(selectedProjectId);
    });

    fetchCurrentUser().then(() => {
        fetchProjects();
    });
});
