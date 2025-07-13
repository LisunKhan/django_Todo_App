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
        card.dataset.title = task.title;
        card.dataset.description = task.description;
        card.dataset.timeSpent = task.time_spent_hours;
        card.dataset.taskDate = task.task_date;

        card.innerHTML = `
            <h5>${task.title}</h5>
            <p>${task.description}</p>
            <div class="task-meta">
                <span>Date: ${task.task_date || 'N/A'}</span>
                <span>Time: ${task.time_spent_hours || 0}h</span>
            </div>
            <button class="edit-task-btn">Edit</button>
        `;

        card.querySelector('.edit-task-btn').addEventListener('click', () => {
            showEditModal(task);
        });

        return card;
    }

    function showEditModal(task) {
        const modal = document.createElement('div');
        modal.className = 'modal';
        modal.innerHTML = `
            <div class="modal-content">
                <span class="close-btn">&times;</span>
                <h2>Edit Task</h2>
                <input type="text" id="edit-title" value="${task.title}">
                <textarea id="edit-description">${task.description}</textarea>
                <input type="date" id="edit-task-date" value="${task.task_date || ''}">
                <input type="number" id="edit-time-spent" value="${task.time_spent_hours || 0}">
                <button id="save-edit-btn">Save</button>
            </div>
        `;

        document.body.appendChild(modal);

        modal.querySelector('.close-btn').addEventListener('click', () => {
            document.body.removeChild(modal);
        });

        modal.querySelector('#save-edit-btn').addEventListener('click', async () => {
            const newTitle = document.getElementById('edit-title').value;
            const newDescription = document.getElementById('edit-description').value;
            const newTaskDate = document.getElementById('edit-task-date').value;
            const newTimeSpent = document.getElementById('edit-time-spent').value;

            const updatedTask = {
                title: newTitle,
                description: newDescription,
                task_date: newTaskDate,
                time_spent_hours: newTimeSpent,
            };

            try {
                const response = await fetch(`/todo/inline_edit/${task.id}/`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': getCookie('csrftoken'),
                        'X-Requested-With': 'XMLHttpRequest'
                    },
                    body: JSON.stringify(updatedTask)
                });
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                const responseData = await response.json();
                if (responseData.success) {
                    // Update the card in the UI
                    const card = document.querySelector(`.task-card[data-task-id="${task.id}"]`);
                    card.querySelector('h5').textContent = newTitle;
                    card.querySelector('p').textContent = newDescription;
                    card.querySelector('.task-meta span:first-child').textContent = `Date: ${newTaskDate || 'N/A'}`;
                    card.querySelector('.task-meta span:last-child').textContent = `Time: ${newTimeSpent || 0}h`;
                    // Update dataset attributes
                    card.dataset.title = newTitle;
                    card.dataset.description = newDescription;
                    card.dataset.taskDate = newTaskDate;
                    card.dataset.timeSpent = newTimeSpent;

                    document.body.removeChild(modal);
                }
            } catch (error) {
                console.error("Error updating task:", error);
            }
        });
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
