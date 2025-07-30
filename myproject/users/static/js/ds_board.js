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

    async function fetchProjectData(projectId) {
        if (!projectId || projectId === 'all') {
            dsBoardContainer.innerHTML = '';
            return;
        }

        const usersResponse = await fetch(`/api/ds_board/project/${projectId}/users/`);
        const users = await usersResponse.json();

        const tasksResponse = await fetch(`/api/ds_board/project/${projectId}/tasks/`);
        const tasks = await tasksResponse.json();

        const yesterdayLogsResponse = await fetch(`/api/ds_board/project/${projectId}/logs/?date=yesterday`);
        const yesterdayLogs = await yesterdayLogsResponse.json();

        const todayLogsResponse = await fetch(`/api/ds_board/project/${projectId}/logs/?date=today`);
        const todayLogs = await todayLogsResponse.json();

        const blockersResponse = await fetch(`/api/ds_board/project/${projectId}/blockers/`);
        const blockers = await blockersResponse.json();

        renderDSBoard(users, tasks, yesterdayLogs, todayLogs, blockers);
    }

    function renderDSBoard(users, tasks, yesterdayLogs, todayLogs, blockers) {
        dsBoardContainer.innerHTML = '';

        const table = document.createElement('table');
        table.classList.add('ds-board-table');

        const header = table.createTHead();
        const headerRow = header.insertRow();
        const headers = ['Name', 'All Tasks', 'Yesterday', 'Today', 'Blockers'];
        headers.forEach(text => {
            const th = document.createElement('th');
            th.textContent = text;
            headerRow.appendChild(th);
        });

        const body = table.createTBody();
        users.forEach(user => {
            const userRow = body.insertRow();
            userRow.setAttribute('data-user-id', user.id);

            const nameCell = userRow.insertCell();
            nameCell.textContent = user.username;

            const allTasksCell = userRow.insertCell();
            allTasksCell.classList.add('task-column', 'all-tasks-column');

            const yesterdayCell = userRow.insertCell();
            yesterdayCell.classList.add('task-column');

            const todayCell = userRow.insertCell();
            todayCell.classList.add('task-column', 'today-column');

            const blockersCell = userRow.insertCell();
            blockersCell.classList.add('task-column', 'blockers-column');

            const addTaskButton = document.createElement('button');
            addTaskButton.classList.add('add-task-button');
            addTaskButton.textContent = '+ Add a card';
            addTaskButton.addEventListener('click', handleAddTask);
            todayCell.appendChild(addTaskButton);
        });

        dsBoardContainer.appendChild(table);

        populateTasks(tasks, yesterdayLogs, todayLogs, blockers);
        initializeSortable();
    }

    async function populateTasks(tasks, yesterdayLogs, todayLogs, blockers) {
        const renderedTaskIds = new Set();
        const userRows = document.querySelectorAll('.ds-board-table tbody tr');

        userRows.forEach(userRow => {
            const allTasksCell = userRow.querySelector('.all-tasks-column');
            const yesterdayCell = userRow.cells[2];
            const todayCell = userRow.cells[3];
            const blockersCell = userRow.cells[4];

            [allTasksCell, yesterdayCell, todayCell, blockersCell].forEach(cell => {
                while (cell.children.length > (cell.classList.contains('today-column') ? 1 : 0)) {
                    cell.removeChild(cell.lastChild);
                }
            });
        });

        for (const log of yesterdayLogs) {
            const task = tasks.find(t => t.id === log.task_id);
            if (task && !renderedTaskIds.has(task.id)) {
                const taskCard = await createTaskCard(task, false);
                const userRow = document.querySelector(`tr[data-user-id='${task.user_id}']`);
                if (userRow) {
                    userRow.cells[2].appendChild(taskCard);
                    renderedTaskIds.add(task.id);
                }
            }
        }

        for (const log of todayLogs) {
            const task = tasks.find(t => t.id === log.task_id);
            if (task && !renderedTaskIds.has(task.id)) {
                const taskCard = await createTaskCard(task, false);
                const userRow = document.querySelector(`tr[data-user-id='${task.user_id}']`);
                if (userRow) {
                    userRow.cells[3].appendChild(taskCard);
                    renderedTaskIds.add(task.id);
                }
            }
        }

        for (const blocker of blockers) {
            const taskCard = await createTaskCard(blocker, false);
            const userRow = document.querySelector(`tr[data-user-id='${blocker.user_id}']`);
            if (userRow) {
                userRow.cells[4].appendChild(taskCard);
            }
        }

        for (const task of tasks) {
            if (!renderedTaskIds.has(task.id)) {
                const taskCard = await createTaskCard(task, true);
                const userRow = document.querySelector(`tr[data-user-id='${task.user_id}']`);
                if (userRow) {
                    userRow.querySelector('.all-tasks-column').appendChild(taskCard);
                }
            }
        }
    }


    async function createTaskCard(task, fromAllTasks = false) {
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

        if (!fromAllTasks) {
            const cancelButton = document.createElement('button');
            cancelButton.textContent = 'Cancel';
            cancelButton.addEventListener('click', () => {
                taskCard.remove();
            });
            taskCard.appendChild(cancelButton);
        }

        return taskCard;
    }

    function showLogTimeInput(taskCard, taskId, log_date = null) {
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
        saveLogButton.addEventListener('click', () => saveLogTime(taskCard, taskId, logTimeInput.value, log_date));

        taskCard.appendChild(logTimeInput);
        taskCard.appendChild(saveLogButton);
    }

    async function saveLogTime(taskCard, taskId, logTime, log_date = null) {
        const response = await fetch('/api/ds_board/log_time/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({
                task_id: taskId,
                log_time: logTime,
                date: log_date ? log_date.toISOString().split('T')[0] : null
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
        const todayCell = event.target.parentElement;
        const userRow = todayCell.parentElement;
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
            const taskCard = await createTaskCard(task);
            const userRow = document.querySelector(`tr[data-user-id='${task.user_id}']`);
            if (userRow) {
                userRow.cells[3].appendChild(taskCard);
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

    function initializeSortable() {
        const taskColumns = document.querySelectorAll('.task-column');
        taskColumns.forEach(column => {
            new Sortable(column, {
                group: {
                    name: 'shared',
                    put: (to, from) => {
                        return !from.el.classList.contains('all-tasks-column') || !to.el.classList.contains('all-tasks-column');
                    }
                },
                animation: 150,
                ghostClass: 'sortable-ghost',
                chosenClass: 'sortable-chosen',
                dragClass: 'sortable-drag',
                onStart: function (evt) {
                    if (evt.from.classList.contains('all-tasks-column')) {
                        evt.item.classList.add('cloned-task');
                    }
                },
                onEnd: async function (evt) {
                    const item = evt.item;
                    const to = evt.to;
                    if (item.classList.contains('cloned-task')) {
                        item.classList.remove('cloned-task');
                        const originalItem = document.querySelector(`[data-task-id='${item.dataset.taskId}'].task-card`);
                        const clonedItem = item.cloneNode(true);
                        to.replaceChild(clonedItem, item);

                        const taskId = clonedItem.dataset.taskId;
                        let log_date = new Date();
                        if (to.parentElement.cells[2] === to) { // Yesterday's column
                            log_date.setDate(log_date.getDate() - 1);
                            showLogTimeInput(clonedItem, taskId, log_date);
                        } else {
                            await fetch('/api/ds_board/log_task_placement/', {
                                method: 'POST',
                                headers: {
                                    'Content-Type': 'application/json',
                                    'X-CSRFToken': getCookie('csrftoken')
                                },
                                body: JSON.stringify({
                                    task_id: taskId,
                                    date: log_date.toISOString().split('T')[0]
                                })
                            });
                        }
                    }
                }
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
