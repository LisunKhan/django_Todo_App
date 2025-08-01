document.addEventListener('DOMContentLoaded', () => {
    const projectFilterSelect = document.getElementById('project-filter-select');
    const membersContainer = document.getElementById('members-container');
    const tasksContainer = document.getElementById('tasks-container');
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
        renderTasks(tasksData.tasks);
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

    function renderTasks(tasks) {
        tasksContainer.innerHTML = '';
        tasks.forEach(task => {
            const taskElement = document.createElement('div');
            taskElement.classList.add('card', 'mb-2');
            taskElement.innerHTML = `
                <div class="card-body">
                    <h5 class="card-title">${task.title}</h5>
                    <p class="card-text">${task.description}</p>
                    <p class="card-text"><small class="text-muted">Status: ${task.status}</small></p>
                </div>
            `;
            tasksContainer.appendChild(taskElement);
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

    projectFilterSelect.addEventListener('change', () => {
        const selectedProjectId = projectFilterSelect.value;
        fetchProjectData(selectedProjectId);
    });

    taskSearchInput.addEventListener('input', () => {
        const searchQuery = taskSearchInput.value;
        fetchProjectData(currentProjectId, 1, searchQuery);
    });

    paginationContainer.addEventListener('click', (event) => {
        if (event.target.tagName === 'A') {
            event.preventDefault();
            const page = event.target.dataset.page;
            if (page) {
                fetchProjectData(currentProjectId, page, currentSearchQuery);
            }
        }
    });

    fetchProjects();
});
