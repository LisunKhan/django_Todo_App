document.addEventListener('DOMContentLoaded', () => {
    const dsBoardContainer = document.getElementById('ds-board-container');
    const projectId = 1; // This should be dynamically set

    async function fetchProjectData() {
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

    function createTaskCard(task) {
        const taskCard = document.createElement('div');
        taskCard.classList.add('task-card');
        taskCard.textContent = task.title;
        taskCard.setAttribute('draggable', true);
        taskCard.setAttribute('data-task-id', task.id);
        return taskCard;
    }

    function handleAddTask(event) {
        const todayColumn = event.target.parentElement;
        const taskTitle = prompt('Enter task title:');
        if (taskTitle) {
            const task = {
                id: Date.now(), // temporary ID
                title: taskTitle,
                status: 'todo'
            };
            const taskCard = createTaskCard(task);
            todayColumn.appendChild(taskCard);
        }
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
        const targetColumn = event.target.closest('.task-column');
        if (targetColumn) {
            targetColumn.appendChild(taskCard);
        }
    }

    fetchProjectData();
});
