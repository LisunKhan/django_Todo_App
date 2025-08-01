document.addEventListener('DOMContentLoaded', () => {
    const projectFilterSelect = document.getElementById('project-filter-select');
    const membersContainer = document.getElementById('members-container');
    const tasksContainer = document.getElementById('tasks-container');
    const yesterdayTasksContainer = document.getElementById('yesterday-tasks-container');
    const todayTasksContainer = document.getElementById('today-tasks-container');
    const taskSearchInput = document.getElementById('task-search-input');
    const paginationContainer = document.getElementById('pagination-container');

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
            let cancelButton = '';
            if (showCancelButton) {
                cancelButton = `<button class="btn btn-danger btn-sm float-end cancel-task-btn">X</button>`;
            }
            taskElement.innerHTML = `
                <div class="card-body">
                    ${cancelButton}
                    <h5 class="card-title">${task.title}</h5>
                    <p class="card-text">Estimation: ${task.estimation_time}h</p>
                    <p class="card-text">Total Time Spent: ${task.time_spent}h</p>
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

        [yesterdayTasksContainer, todayTasksContainer].forEach(container => {
            new Sortable(container, {
                group: 'tasks',
                animation: 150,
                onAdd: (event) => {
                    const itemEl = event.item;
                    const taskId = itemEl.dataset.taskId;
                    let date;
                    if (event.to.id === 'yesterday-tasks-container') {
                        date = 'yesterday';
                    } else if (event.to.id === 'today-tasks-container') {
                        date = 'today';
                    }
                    updateTaskLog(taskId, date);

                    console.log('onAdd triggered');
                    // Add cancel button
                    const cardBody = itemEl.querySelector('.card-body');
                    cardBody.innerHTML = `<button class="btn btn-danger btn-sm float-end cancel-task-btn">X</button>` + cardBody.innerHTML;
                }
            });
        });
    }

    async function updateTaskLog(taskId, date) {
        console.log(`updateTaskLog called with taskId: ${taskId}, date: ${date}`);
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

    const dsBoardContainer = document.getElementById('ds-board-container');
    if (dsBoardContainer) {
        dsBoardContainer.addEventListener('click', (event) => {
            if (event.target.classList.contains('cancel-task-btn')) {
                console.log('Cancel button clicked');
                const taskCard = event.target.closest('.card');
                console.log('taskCard:', taskCard);
                const taskId = taskCard.dataset.taskId;
                console.log('taskId:', taskId);
                taskCard.remove();
                updateTaskLog(taskId, null);
            }
        });
    }

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
    } else {
        console.error('paginationContainer not found');
    }

    fetchProjects();
    initializeSortable();
});
