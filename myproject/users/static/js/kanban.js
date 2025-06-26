const API_BASE_URL = '/api/tasks'; // Example placeholder for API endpoints

document.addEventListener('DOMContentLoaded', () => {
    console.log('Kanban board HTML and CSS loaded. JavaScript is active.');

    const todoTasks = document.getElementById('todo-tasks');
    const inprogressTasks = document.getElementById('inprogress-tasks');
    const doneTasks = document.getElementById('done-tasks');
    const addTaskBtns = document.querySelectorAll('.add-task-btn');

    // --- API Placeholder Functions ---
    async function createTaskAPI(taskData) {
        console.log(`API CALL (Create): Create new task with data:`, taskData);
        // Actual fetch call would be:
        // try {
        //     const response = await fetch(`${API_BASE_URL}`, {
        //         method: 'POST',
        //         headers: { 'Content-Type': 'application/json' },
        //         body: JSON.stringify(taskData)
        //     });
        //     if (!response.ok) throw new Error(`Failed to create task: ${response.statusText}`);
        //     const newTask = await response.json();
        //     console.log('Task created successfully:', newTask);
        //     // Here you might want to update the UI with the ID from the server,
        //     // e.g., find the card with the temporary ID and update its data-task-id.
        //     return newTask; // Return the created task with its new ID from server
        // } catch (error) {
        //     console.error('Error creating task:', error);
        //     // Handle error, maybe remove the optimistic UI update or notify user
        // }
        return { ...taskData, id: Date.now() }; // Simulate returning task with ID for now
    }

    async function updateTaskStatusAPI(taskId, newStatus) {
        console.log(`API CALL (Drag-Drop): Update task ${taskId} to status ${newStatus}`);
        // Actual fetch call would be:
        // try {
        //     const response = await fetch(`${API_BASE_URL}/${taskId}/status`, {
        //         method: 'PATCH', // or PUT
        //         headers: { 'Content-Type': 'application/json' },
        //         body: JSON.stringify({ status: newStatus })
        //     });
        //     if (!response.ok) throw new Error(`Failed to update status: ${response.statusText}`);
        //     const updatedTask = await response.json();
        //     console.log('Status updated successfully:', updatedTask);
        //     // Optionally update the task card's data attributes or re-render if needed
        // } catch (error) {
        //     console.error('Error updating task status:', error);
        //     // Revert UI change if API call fails (more complex UI handling)
        // }
    }

    async function updateTaskDetailsAPI(taskId, data) {
        console.log(`API CALL (Edit): Update task ${taskId} with data:`, data);
        // Actual fetch call would be:
        // try {
        //     const response = await fetch(`${API_BASE_URL}/${taskId}`, {
        //         method: 'PATCH', // or PUT
        //         headers: { 'Content-Type': 'application/json' },
        //         body: JSON.stringify(data)
        //     });
        //     if (!response.ok) throw new Error(`Failed to update task: ${response.statusText}`);
        //     const updatedTask = await response.json();
        //     console.log('Task updated successfully:', updatedTask);
        // } catch (error) {
        //     console.error('Error updating task details:', error);
        //     // Revert UI changes or notify user
        // }
    }

    async function deleteTaskAPI(taskId) {
        console.log(`API CALL (Delete): Delete task ${taskId}`);
        // Actual fetch call would be:
        // try {
        //     const response = await fetch(`${API_BASE_URL}/${taskId}`, {
        //         method: 'DELETE'
        //     });
        //     if (!response.ok) throw new Error(`Failed to delete task: ${response.statusText}`);
        //     console.log(`Task ${taskId} deleted successfully from backend.`);
        // } catch (error) {
        //     console.error('Error deleting task:', error);
        //     // If deletion fails, maybe re-add the card to the UI or notify user
        // }
    }
    // --- End API Placeholder Functions ---

    // Initialize SortableJS for each task list
    if (todoTasks && inprogressTasks && doneTasks) { // Ensure elements exist before init
        new Sortable(todoTasks, {
            group: 'shared', // set both lists to same group
            animation: 150,
            ghostClass: 'sortable-ghost', // Class name for the drop placeholder
            chosenClass: 'sortable-chosen', // Class name for the chosen item
            dragClass: 'sortable-drag', // Class name for the dragging item
            onEnd: function (evt) {
                console.log('Task moved:', evt.item, 'to', evt.to.id, 'from', evt.from.id);
                const taskId = evt.item.dataset.taskId;
                const newStatus = evt.to.id.replace('-tasks', ''); // e.g., 'todo', 'inprogress', 'done'
                updateTaskStatusAPI(taskId, newStatus);
            }
        });

        new Sortable(inprogressTasks, {
            group: 'shared',
            animation: 150,
            ghostClass: 'sortable-ghost',
            chosenClass: 'sortable-chosen',
            dragClass: 'sortable-drag',
            onEnd: function (evt) {
                console.log('Task moved:', evt.item, 'to', evt.to.id, 'from', evt.from.id);
                const taskId = evt.item.dataset.taskId;
                const newStatus = evt.to.id.replace('-tasks', '');
                updateTaskStatusAPI(taskId, newStatus);
            }
        });

        new Sortable(doneTasks, {
            group: 'shared',
            animation: 150,
            ghostClass: 'sortable-ghost',
            chosenClass: 'sortable-chosen',
            dragClass: 'sortable-drag',
            onEnd: function (evt) {
                console.log('Task moved:', evt.item, 'to', evt.to.id, 'from', evt.from.id);
                const taskId = evt.item.dataset.taskId;
                const newStatus = evt.to.id.replace('-tasks', '');
                updateTaskStatusAPI(taskId, newStatus);
            }
        });
    } else {
        console.warn('One or more task list elements not found. SortableJS not initialized.');
    }


    // Example Task data to make drag and drop testable - This should ideally come from Django context
    const initialTasks = [
        // { id: 1, title: 'Task 1: Design UI', description: 'Design the main dashboard UI elements.', status: 'todo' },
        // { id: 2, title: 'Task 2: Setup Project', description: 'Initialize project structure and dependencies.', status: 'todo' },
        // { id: 3, title: 'Task 3: Develop API', description: 'Develop backend API for tasks.', status: 'inprogress' },
        // { id: 4, title: 'Task 4: Write Tests', description: 'Write unit and integration tests.', status: 'done' },
    ];

    // Function to render tasks if they are passed via a global variable or fetched by an initial API call
    // For now, we assume tasks might be embedded or fetched separately in a Django context.
    // This function will be used by "Add New Task" and potentially by an initial load function.
    function renderTask(task) {
        const taskCard = document.createElement('div');
        taskCard.className = 'task-card';
        taskCard.setAttribute('data-task-id', task.id);
        taskCard.setAttribute('data-title', task.title);
        taskCard.setAttribute('data-description', task.description);

        const titleElement = document.createElement('h3');
        titleElement.textContent = task.title;

        const descriptionElement = document.createElement('p');
        descriptionElement.textContent = task.description;

        const actionsDiv = document.createElement('div');
        actionsDiv.className = 'actions';

        const editButton = document.createElement('button');
        editButton.className = 'edit-btn';
        editButton.title = 'Edit task';
        editButton.innerHTML = '✏️';

        const deleteButton = document.createElement('button');
        deleteButton.className = 'delete-btn';
        deleteButton.title = 'Delete task';
        deleteButton.innerHTML = '🗑️';

        actionsDiv.appendChild(editButton);
        actionsDiv.appendChild(deleteButton);

        taskCard.appendChild(titleElement);
        taskCard.appendChild(descriptionElement);
        taskCard.appendChild(actionsDiv);

        editButton.addEventListener('click', () => enableEditMode(taskCard, titleElement, descriptionElement, editButton));
        titleElement.addEventListener('dblclick', () => enableEditMode(taskCard, titleElement, descriptionElement, editButton));
        descriptionElement.addEventListener('dblclick', () => enableEditMode(taskCard, titleElement, descriptionElement, editButton));
        deleteButton.addEventListener('click', () => deleteTask(taskCard));

        return taskCard;
    }

    // Function to initially populate the board if tasks are provided (e.g. from Django context)
    // window.loadInitialTasks = function(tasks) {
    //     tasks.forEach(task => {
    //         const card = renderTask(task);
    //         if (task.status === 'todo' && todoTasks) {
    //             todoTasks.appendChild(card);
    //         } else if (task.status === 'inprogress' && inprogressTasks) {
    //             inprogressTasks.appendChild(card);
    //         } else if (task.status === 'done' && doneTasks) {
    //             doneTasks.appendChild(card);
    //         }
    //     });
    // };
    // Example: if initialTasks is populated by Django template into a JS variable:
     if (typeof initialKanbanTasks !== 'undefined' && Array.isArray(initialKanbanTasks)) {
        initialKanbanTasks.forEach(task => {
            const card = renderTask(task);
            if (task.status === 'todo' && todoTasks) {
                todoTasks.appendChild(card);
            } else if (task.status === 'inprogress' && inprogressTasks) {
                inprogressTasks.appendChild(card);
            } else if (task.status === 'done' && doneTasks) {
                doneTasks.appendChild(card);
            }
        });
    }


    function deleteTask(taskCard) {
        const taskId = taskCard.dataset.taskId;
        const taskTitle = taskCard.dataset.title;

        if (confirm(`Are you sure you want to delete task "${taskTitle}"?`)) {
            taskCard.remove();
            console.log(`Task ${taskId} (${taskTitle}) deleted from UI.`);
            deleteTaskAPI(taskId);
        } else {
            console.log(`Deletion of task ${taskId} cancelled.`);
        }
    }

    function enableEditMode(taskCard, titleElement, descriptionElement, editButton) {
        if (taskCard.classList.contains('editing')) return; // Prevent multiple edit modes
        taskCard.classList.add('editing');

        const originalTitle = titleElement.textContent;
        const originalDescription = descriptionElement.textContent;

        const titleInput = document.createElement('input');
        titleInput.type = 'text';
        titleInput.value = originalTitle;
        taskCard.insertBefore(titleInput, titleElement);
        titleElement.style.display = 'none';

        const descriptionTextarea = document.createElement('textarea');
        descriptionTextarea.value = originalDescription;
        taskCard.insertBefore(descriptionTextarea, descriptionElement);
        descriptionElement.style.display = 'none';

        editButton.innerHTML = '💾';
        editButton.title = 'Save task';

        const tempSaveListener = () => {
            saveChanges();
            newEditButton.removeEventListener('click', tempSaveListener); // Clean up self
        };

        const tempKeyListener = (e) => {
            if (e.key === 'Enter' && e.target === titleInput) {
                e.preventDefault();
                saveChanges();
                titleInput.removeEventListener('keypress', tempKeyListener); // Clean up self
            }
        };

        const newEditButton = editButton.cloneNode(true);
        editButton.parentNode.replaceChild(newEditButton, editButton);

        function saveChanges() {
            taskCard.classList.remove('editing');
            const newTitle = titleInput.value.trim();
            const newDescription = descriptionTextarea.value.trim();

            titleElement.textContent = newTitle;
            descriptionElement.textContent = newDescription;
            taskCard.setAttribute('data-title', newTitle);
            taskCard.setAttribute('data-description', newDescription);

            taskCard.removeChild(titleInput);
            taskCard.removeChild(descriptionTextarea);
            titleElement.style.display = '';
            descriptionElement.style.display = '';

            newEditButton.innerHTML = '✏️';
            newEditButton.title = 'Edit task';

            // Re-attach original edit listener logic by replacing the button again
            const finalEditButton = newEditButton.cloneNode(true);
            newEditButton.parentNode.replaceChild(finalEditButton, newEditButton);
            finalEditButton.addEventListener('click', () => enableEditMode(taskCard, titleElement, descriptionElement, finalEditButton));
            // Also re-attach dblclick to title/desc for the new elements if needed, though current structure reuses original titleElement/descriptionElement

            console.log(`Task ${taskCard.dataset.taskId} updated:`, { title: newTitle, description: newDescription });
            updateTaskDetailsAPI(taskCard.dataset.taskId, { title: newTitle, description: newDescription });

            // Clean up listeners attached to input fields if any beyond this scope
            titleInput.removeEventListener('keypress', tempKeyListener);
        }

        newEditButton.addEventListener('click', tempSaveListener);
        titleInput.addEventListener('keypress', tempKeyListener);
        titleInput.focus(); // Focus title input
    }

    // --- Add New Task Functionality ---
    if (addTaskBtns) {
        addTaskBtns.forEach(button => {
            button.addEventListener('click', () => {
                const column = button.closest('.column');
                const taskList = column.querySelector('.task-list');
                const status = column.id;
                showNewTaskForm(taskList, status, button);
                button.style.display = 'none';
            });
        });
    }


    function showNewTaskForm(taskList, status, originalAddButton) {
        const existingForm = taskList.querySelector('.new-task-form');
        if (existingForm) {
            existingForm.remove();
            if(originalAddButton) originalAddButton.style.display = ''; // Show button if form was already open
        }

        const form = document.createElement('div');
        form.className = 'new-task-form task-card';
        form.innerHTML = `
            <input type="text" placeholder="Task Title" class="new-task-title">
            <textarea placeholder="Task Description" class="new-task-description"></textarea>
            <div class="form-actions">
                <button class="save-new-task-btn">Save Task</button>
                <button class="cancel-new-task-btn">Cancel</button>
            </div>
        `;

        taskList.prepend(form);
        form.querySelector('.new-task-title').focus();

        const saveBtn = form.querySelector('.save-new-task-btn');
        const cancelBtn = form.querySelector('.cancel-new-task-btn');
        const titleInput = form.querySelector('.new-task-title');
        const descriptionInput = form.querySelector('.new-task-description');

        const saveNewTaskHandler = async () => {
            const title = titleInput.value.trim();
            const description = descriptionInput.value.trim();

            if (title) {
                const newTaskData = { title, description, status };
                const createdTask = await createTaskAPI(newTaskData);
                if (createdTask) {
                    const taskCard = renderTask(createdTask);
                    // Decide where to add: current logic is append, maybe prepend?
                    taskList.appendChild(taskCard); // Or taskList.prepend(taskCard) for top
                }
                form.remove();
                if(originalAddButton) originalAddButton.style.display = '';
            } else {
                alert('Task title cannot be empty!');
            }
        };

        const cancelNewTaskHandler = () => {
            form.remove();
            if(originalAddButton) originalAddButton.style.display = '';
        };

        const titleKeyPressHandler = (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                saveNewTaskHandler();
            }
        };

        saveBtn.addEventListener('click', saveNewTaskHandler);
        cancelBtn.addEventListener('click', cancelNewTaskHandler);
        titleInput.addEventListener('keypress', titleKeyPressHandler);
    }
});
