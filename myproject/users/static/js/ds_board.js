document.addEventListener('DOMContentLoaded', () => {
    const projectFilterSelect = document.getElementById('project-filter-select');
    const dsBoardContainer = document.getElementById('ds-board-container');
    const projectsDataElement = document.getElementById('ds-projects-data');
    let projects = [];

    if (projectsDataElement) {
        try {
            projects = JSON.parse(projectsDataElement.textContent);
        } catch (e) {
            console.error("Could not parse projects data:", e);
        }
    }

    // Populate project filter
    if (projectFilterSelect && projects.length > 0) {
        projects.forEach(project => {
            const option = document.createElement('option');
            option.value = project.id;
            option.textContent = project.name;
            projectFilterSelect.appendChild(option);
        });
    }

    async function fetchAndRenderBoard(projectId) {
        dsBoardContainer.innerHTML = ''; // Clear the board
        if (!projectId || projectId === 'all') {
            return;
        }

        try {
            const response = await fetch(`/api/ds_board_tasks/?project_id=${projectId}`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const usersData = await response.json();
            renderBoard(usersData);
        } catch (error) {
            console.error("Error fetching DS board tasks:", error);
        }
    }

    function renderBoard(usersData) {
        usersData.forEach(userData => {
            const userBoard = document.createElement('div');
            userBoard.className = 'user-board';
            userBoard.innerHTML = `<h2>${userData.username}</h2>`;

            const userColumns = document.createElement('div');
            userColumns.className = 'user-columns';

            const allTasksColumn = createColumn('All Tasks', `all-tasks-${userData.user_id}`);
            const yesterdayColumn = createColumn('Yesterday', `yesterday-tasks-${userData.user_id}`);
            const todayColumn = createColumn('Today', `today-tasks-${userData.user_id}`);

            userColumns.appendChild(allTasksColumn);
            userColumns.appendChild(yesterdayColumn);
            userColumns.appendChild(todayColumn);

            userBoard.appendChild(userColumns);
            dsBoardContainer.appendChild(userBoard);

            const allTasksList = allTasksColumn.querySelector('.task-list');
            const yesterdayTasksList = yesterdayColumn.querySelector('.task-list');
            const todayTasksList = todayColumn.querySelector('.task-list');

            userData.tasks.forEach(task => {
                const taskCard = createTaskCard(task);
                const taskDate = new Date(task.task_date);
                const today = new Date();
                const yesterday = new Date();
                yesterday.setDate(yesterday.getDate() - 1);

                if (task.task_date && taskDate.toDateString() === today.toDateString()) {
                    todayTasksList.appendChild(taskCard);
                } else if (task.task_date && taskDate.toDateString() === yesterday.toDateString()) {
                    yesterdayTasksList.appendChild(taskCard);
                } else {
                    allTasksList.appendChild(taskCard);
                }
            });

            new Sortable(allTasksList, {
                group: `user-${userData.user_id}`,
                animation: 150,
                onEnd: handleTaskDrop,
            });
            new Sortable(yesterdayTasksList, {
                group: `user-${userData.user_id}`,
                animation: 150,
                onEnd: handleTaskDrop,
            });
            new Sortable(todayTasksList, {
                group: `user-${userData.user_id}`,
                animation: 150,
                onEnd: handleTaskDrop,
            });
        });
    }

    function createColumn(title, id) {
        const column = document.createElement('div');
        column.className = 'user-column';
        column.innerHTML = `<h3>${title}</h3>`;
        const taskList = document.createElement('div');
        taskList.className = 'task-list';
        taskList.id = id;
        column.appendChild(taskList);
        return column;
    }

    function createTaskCard(task) {
        const card = document.createElement('div');
        card.className = 'task-card';
        card.dataset.taskId = task.id;
        card.textContent = task.title;
        return card;
    }

    async function handleTaskDrop(evt) {
        const taskId = evt.item.dataset.taskId;
        const toColumnId = evt.to.id;
        let task_date = null;

        const today = new Date();
        const yesterday = new Date();
        yesterday.setDate(yesterday.getDate() - 1);

        if (toColumnId.startsWith('today-tasks')) {
            task_date = today.toISOString().split('T')[0];
        } else if (toColumnId.startsWith('yesterday-tasks')) {
            task_date = yesterday.toISOString().split('T')[0];
        }

        try {
            const response = await fetch(`/todo/inline_edit/${taskId}/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken'),
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: JSON.stringify({ task_date: task_date })
            });
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
        } catch (error) {
            console.error("Error updating task date:", error);
            // Revert the drag-and-drop on error
            evt.from.appendChild(evt.item);
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

    projectFilterSelect.addEventListener('change', () => {
        fetchAndRenderBoard(projectFilterSelect.value);
    });

    // Initial load
    if (projectFilterSelect.value) {
        fetchAndRenderBoard(projectFilterSelect.value);
    }
});
