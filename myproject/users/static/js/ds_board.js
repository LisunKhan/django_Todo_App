document.addEventListener('DOMContentLoaded', () => {
    const dsBoardContainer = document.getElementById('ds-board-container');
    const projectFilterSelect = document.getElementById('project-filter-select');
    const modal = document.getElementById('add-task-modal');
    const closeButton = document.querySelector('.close-button');
    let currentUserId;

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

        users.forEach(user => {
            const userRow = document.createElement('div');
            userRow.classList.add('user-row');
            userRow.setAttribute('data-user-id', user.id);

            const userInfo = document.createElement('div');
            userInfo.classList.add('user-info');
            userInfo.textContent = user.username;
            userRow.appendChild(userInfo);

            const yesterdayTasksColumn = createColumn("Yesterday's Tasks");
            userRow.appendChild(yesterdayTasksColumn);

            const todayTasksColumn = createColumn("Today's Tasks", true);
            userRow.appendChild(todayTasksColumn);

            const totalTimeColumn = createColumn('Total Time (min)');
            userRow.appendChild(totalTimeColumn);

            const blockersColumn = createColumn('Blockers');
            userRow.appendChild(blockersColumn);

            dsBoardContainer.appendChild(userRow);
        });

        populateTasks(tasks, yesterdayLogs, todayLogs, blockers);
        renderTaskPool(tasks);
        addDragAndDropListeners();
    }

    function createColumn(title, isToday = false) {
        const column = document.createElement('div');
        column.classList.add('task-column');
        column.innerHTML = `<h4>${title}</h4>`;
        if (isToday) {
            const addTaskButton = document.createElement('button');
            addTaskButton.textContent = '+ Add Task';
            addTaskButton.addEventListener('click', handleAddTask);
            column.appendChild(addTaskButton);
        }
        return column;
    }

    function populateTasks(tasks, yesterdayLogs, todayLogs, blockers) {
        yesterdayLogs.forEach(log => {
            const task = tasks.find(t => t.id === log.task_id);
            if (task) {
                const taskCard = createTaskCard(task);
                const userRow = document.querySelector(`.user-row[data-user-id='${task.user_id}']`);
                if (userRow) {
                    userRow.children[1].appendChild(taskCard);
                }
            }
        });

        todayLogs.forEach(log => {
            const task = tasks.find(t => t.id === log.task_id);
            if (task) {
                const taskCard = createTaskCard(task);
                const userRow = document.querySelector(`.user-row[data-user-id='${task.user_id}']`);
                if (userRow) {
                    userRow.children[2].appendChild(taskCard);
                }
            }
        });

        blockers.forEach(blocker => {
            const taskCard = createTaskCard(blocker);
            const userRow = document.querySelector(`.user-row[data-user-id='${blocker.user_id}']`);
            if (userRow) {
                userRow.children[4].appendChild(taskCard);
            }
        });
    }

    function renderTaskPool(tasks) {
        const taskPool = document.createElement('div');
        taskPool.classList.add('task-pool');
        taskPool.innerHTML = '<h3>Task Pool</h3>';

        const todoTasks = tasks.filter(task => task.status === 'todo');
        const inProgressTasks = tasks.filter(task => task.status === 'inprogress');
        const doneTasks = tasks.filter(task => task.status === 'done');

        taskPool.innerHTML += '<h4>To Do</h4>';
        todoTasks.forEach(task => {
            const taskCard = createTaskCard(task);
            taskPool.appendChild(taskCard);
        });

        taskPool.innerHTML += '<h4>In Progress</h4>';
        inProgressTasks.forEach(task => {
            const taskCard = createTaskCard(task);
            taskPool.appendChild(taskCard);
        });

        taskPool.innerHTML += '<h4>Done</h4>';
        doneTasks.forEach(task => {
            const taskCard = createTaskCard(task);
            taskPool.appendChild(taskCard);
        });

        dsBoardContainer.appendChild(taskPool);
    }

    async function createTaskCard(task) {
        const taskCard = document.createElement('div');
        taskCard.classList.add('task-card', `status-${task.status}`);
        taskCard.setAttribute('draggable', true);
        taskCard.setAttribute('data-task-id', task.id);
        taskCard.setAttribute('data-user-id', task.user_id);

        const header = document.createElement('div');
        header.classList.add('task-card-header');

        const title = document.createElement('h5');
        title.textContent = task.title;
        header.appendChild(title);

        const avatar = document.createElement('img');
        avatar.classList.add('user-avatar');
        const response = await fetch(`/api/ds_board/user/${task.user_id}/profile_picture/`);
        const data = await response.json();
        avatar.src = data.profile_picture_url || '/static/images/default_avatar.png';
        header.appendChild(avatar);

        taskCard.appendChild(header);

        const description = document.createElement('p');
        description.textContent = task.description;
        taskCard.appendChild(description);

        const estimation = document.createElement('p');
        estimation.textContent = `Estimation: ${task.estimation_time}h`;
        taskCard.appendChild(estimation);

        return taskCard;
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

    closeButton.addEventListener('click', () => {
        modal.style.display = 'none';
    });

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

    function addDragAndDropListeners() {
        const taskCards = document.querySelectorAll('.task-card');
        const columns = document.querySelectorAll('.task-column');

        taskCards.forEach(card => {
            card.addEventListener('dragstart', handleDragStart);
        });

        columns.forEach(column => {
            column.addEventListener('dragover', handleDragOver);
            column.addEventListener('drop', handleDrop);
        });
    }

    function handleDragStart(event) {
        event.dataTransfer.setData('text/plain', event.target.dataset.taskId);
    }

    function handleDragOver(event) {
        event.preventDefault();
    }

    function handleDrop(event) {
        event.preventDefault();
        const taskId = event.dataTransfer.getData('text/plain');
        const taskCard = document.querySelector(`[data-task-id='${taskId}']`);
        const taskUserId = parseInt(taskCard.dataset.userId);

        if (taskUserId !== currentUserId) {
            alert("You can only move your own tasks.");
            return;
        }

        const targetColumn = event.target.closest('.task-column');
        if (targetColumn) {
            targetColumn.appendChild(taskCard);
        }
    }

    projectFilterSelect.addEventListener('change', () => {
        const selectedProjectId = projectFilterSelect.value;
        fetchProjectData(selectedProjectId);
    });

    fetchCurrentUser().then(() => {
        fetchProjects();
    });
});
