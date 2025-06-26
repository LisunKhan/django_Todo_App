const API_BASE_URL = '/api/tasks'; // Placeholder, will be adjusted or URLs constructed directly

// Helper function to get CSRF token from cookies
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
const CSRF_TOKEN = getCookie('csrftoken');

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
        // return { ...taskData, id: Date.now() }; // Simulate returning task with ID for now - OLD
        try {
            const response = await fetch('/add_todo/', { // URL for creating tasks
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': CSRF_TOKEN,
                    'X-Requested-With': 'XMLHttpRequest' // Backend expects this for JSON handling
                },
                body: JSON.stringify(taskData) // taskData should include title, description, status
            });

            if (!response.ok) {
                // Try to parse error if backend sends JSON error response
                let errorData;
                try {
                    errorData = await response.json();
                } catch (e) {
                    // Not a JSON error response
                    errorData = { error: `HTTP error! status: ${response.status}` };
                }
                console.error('Error creating task:', errorData);
                throw new Error(errorData.error || `Failed to create task. Status: ${response.status}`);
            }

            const result = await response.json();
            if (result.success && result.todo) {
                return result.todo; // Return the full task object from the server, including its new ID
            } else {
                console.error('Failed to create task, server response:', result);
                throw new Error(result.errors || 'Task creation was not successful.');
            }
        } catch (error) { // This catches network errors or errors thrown from response.ok check
            console.error('Error in createTaskAPI:', error.message);
            alert(`Error creating task: ${error.message}\nPlease try again.`);
            return null; // Indicate failure
        }
    }

    async function updateTaskStatusAPI(taskId, newStatus) { // Called on drag-and-drop
        console.log(`Attempting to update task ${taskId} to status ${newStatus}`);
        const payload = { status: newStatus };
        try {
            const response = await fetch(`/todo/inline_edit/${taskId}/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': CSRF_TOKEN,
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: JSON.stringify(payload)
            });

            if (!response.ok) {
                let errorData;
                try { errorData = await response.json(); } catch (e) { errorData = { error: `HTTP error! status: ${response.status}` }; }
                console.error('Error updating task status:', errorData);
                throw new Error(errorData.error || `Failed to update status. Status: ${response.status}`);
            }

            const result = await response.json();
            if (result.success && result.todo) {
                console.log('Task status updated successfully:', result.todo);
                const taskCard = document.querySelector(`.task-card[data-task-id="${taskId}"]`);
                if (taskCard) {
                    taskCard.setAttribute('data-status', result.todo.status);
                    // Update other relevant data attributes if the server could have changed them
                    taskCard.setAttribute('data-title', result.todo.title);
                    taskCard.setAttribute('data-description', result.todo.description || '');
                    taskCard.setAttribute('data-task-date', result.todo.task_date || '');
                    taskCard.setAttribute('data-time-spent', String(result.todo.time_spent_hours || '0'));

                    // Update the status badge
                    const statusBadge = taskCard.querySelector('.task-status-badge');
                    if (statusBadge) {
                        const newStatus = result.todo.status;
                        statusBadge.textContent = newStatus.charAt(0).toUpperCase() + newStatus.slice(1);
                        // Remove old status classes (be specific to avoid removing task-status-badge)
                        statusBadge.classList.remove('status-todo', 'status-inprogress', 'status-in-progress', 'status-done');
                        // Add new status class
                        statusBadge.classList.add(`status-${newStatus.toLowerCase().replace(/\s+/g, '-')}`);
                    }

                    // Check if the card is in the correct column according to the server response
                    const targetColumnId = `${result.todo.status}-tasks`;
                    if (taskCard.parentElement.id !== targetColumnId) {
                        console.warn(`Task ${taskId} moved to ${newStatus} optimistically, but server returned status ${result.todo.status}. Moving to correct column.`);
                        const targetColumnElement = document.getElementById(targetColumnId);
                        if (targetColumnElement) {
                            targetColumnElement.appendChild(taskCard);
                        } else {
                            console.error(`Target column ${targetColumnId} not found for task ${taskId}.`);
                        }
                    }
                }
            } else {
                console.error('Failed to update task status, server response:', result);
                throw new Error(result.errors || 'Task status update was not successful.');
            }
        } catch (error) {
            console.error('Error in updateTaskStatusAPI:', error.message);
            alert(`Error updating task status: ${error.message}\nThe task may not have moved to the correct status on the server. Please refresh or try moving again.`);
            // TODO: Consider reverting the drag-and-drop move in the UI if API call fails.
            // This requires access to evt.from from SortableJS, which might mean moving this logic
            // directly into the onEnd handler or passing more context. For now, the card might be in the wrong column visually.
        }
    }

    async function updateTaskDetailsAPI(taskId, updateData) { // Called on inline edit save
        console.log(`Attempting to update task ${taskId} with data:`, updateData); // {title, description}
        try {
            const response = await fetch(`/todo/inline_edit/${taskId}/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': CSRF_TOKEN,
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: JSON.stringify(updateData)
            });

            if (!response.ok) {
                let errorData;
                try { errorData = await response.json(); } catch (e) { errorData = { error: `HTTP error! status: ${response.status}` }; }
                console.error('Error updating task details:', errorData);
                throw new Error(errorData.error || `Failed to update details. Status: ${response.status}`);
            }

            const result = await response.json();
            if (result.success && result.todo) {
                console.log('Task details updated successfully:', result.todo);
                const taskCard = document.querySelector(`.task-card[data-task-id="${taskId}"]`);
                if (taskCard) {
                    // Update data attributes with server response
                    taskCard.setAttribute('data-title', result.todo.title);
                    taskCard.setAttribute('data-description', result.todo.description || '');
                    taskCard.setAttribute('data-status', result.todo.status); // Status might change if API allows
                    taskCard.setAttribute('data-task-date', result.todo.task_date || '');
                    taskCard.setAttribute('data-time-spent', String(result.todo.time_spent_hours || '0'));

                    // Update visible text content from server response
                    const titleElement = taskCard.querySelector('h3');
                    const descriptionElement = taskCard.querySelector('p');
                    if (titleElement) titleElement.textContent = result.todo.title;
                    if (descriptionElement) descriptionElement.textContent = result.todo.description || '';

                    // Update visual date and time from server response for consistency
                    const taskDateDisplayElement = taskCard.querySelector('.task-date .date-value');
                    if (taskDateDisplayElement) {
                        let displayDate = 'Not set';
                        if (result.todo.task_date) { // Assuming result.todo.task_date is YYYY-MM-DD
                            const dateParts = result.todo.task_date.split('-');
                            if (dateParts.length === 3) {
                                const localDate = new Date(parseInt(dateParts[0]), parseInt(dateParts[1]) - 1, parseInt(dateParts[2]), 12,0,0); // Noon
                                if (!isNaN(localDate.getTime())) {
                                    displayDate = localDate.toLocaleDateString();
                                }
                            } else { // Handle other potential date string from server if not YYYY-MM-DD
                                const genericDate = new Date(result.todo.task_date);
                                if(!isNaN(genericDate.getTime())){
                                    displayDate = genericDate.toLocaleDateString();
                                }
                            }
                        }
                        taskDateDisplayElement.textContent = displayDate;
                    }

                    const timeSpentDisplayElement = taskCard.querySelector('.task-time-spent .time-value');
                    if (timeSpentDisplayElement) {
                        timeSpentDisplayElement.textContent = String(result.todo.time_spent_hours || '0');
                    }

                    // If status changed via this endpoint (though not primary intent of this func)
                    // ensure card is in correct column
                    const targetColumnId = `${result.todo.status}-tasks`;
                    if (taskCard.parentElement.id !== targetColumnId) {
                        console.warn(`Task ${taskId} status changed via details update to ${result.todo.status}. Moving to correct column.`);
                        const targetColumnElement = document.getElementById(targetColumnId);
                        if (targetColumnElement) {
                            targetColumnElement.appendChild(taskCard);
                        }
                    }
                }
            } else {
                console.error('Failed to update task details, server response:', result);
                throw new Error(result.errors || 'Task details update was not successful.');
            }
        } catch (error) {
            console.error('Error in updateTaskDetailsAPI:', error.message);
            alert(`Error updating task details: ${error.message}\nYour changes might not have been saved. Please refresh and try again.`);
            // TODO: Consider reverting UI changes if API call fails. This would mean
            // the saveChanges function in enableEditMode would need to know about the original values,
            // and then reset the h3/p textContent and data-* attributes.
        }
    }

    async function deleteTaskAPI(taskId) {
        console.log(`Attempting to delete task ${taskId}`);
        try {
            const response = await fetch(`/delete_todo/${taskId}/`, { // URL for deleting tasks
                method: 'POST', // Your backend expects POST for AJAX deletion
                headers: {
                    'X-CSRFToken': CSRF_TOKEN,
                    'X-Requested-With': 'XMLHttpRequest' // Backend expects this for AJAX handling
                }
                // No body is needed for this specific delete endpoint as per typical Django patterns
            });

            if (!response.ok) {
                let errorData;
                try { errorData = await response.json(); } catch (e) { errorData = { error: `HTTP error! status: ${response.status}` }; }
                console.error('Error deleting task:', errorData);
                throw new Error(errorData.error || `Failed to delete task. Status: ${response.status}`);
            }

            const result = await response.json();
            if (result.success) {
                console.log(`Task ${taskId} deleted successfully from backend.`);
                // UI is already optimistically updated (card removed).
            } else {
                console.error('Failed to delete task, server response:', result);
                throw new Error(result.errors || 'Task deletion was not successful.');
            }
        } catch (error) {
            console.error('Error in deleteTaskAPI:', error.message);
            alert(`Error deleting task: ${error.message}\nThe task might not have been deleted from the server. Please refresh.`);
            // TODO: If deletion fails, re-add the card to the UI. This would mean not removing it
            // from the DOM until after successful API response, or having a mechanism to re-render it.
            // For now, the card remains removed optimistically.
        }
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
        taskCard.setAttribute('data-description', task.description || ''); // Ensure not undefined
        taskCard.setAttribute('data-status', task.status);
        taskCard.setAttribute('data-task-date', task.task_date || '');
        taskCard.setAttribute('data-time-spent', String(task.time_spent_hours || '0'));

        // Create and add status badge
        const statusBadge = document.createElement('div');
        statusBadge.className = `task-status-badge status-${task.status.toLowerCase().replace(/\s+/g, '-')}`;
        statusBadge.textContent = task.status.charAt(0).toUpperCase() + task.status.slice(1); // Capitalize first letter
        taskCard.appendChild(statusBadge); // Append, CSS will handle positioning

        const titleElement = document.createElement('h3');
        titleElement.textContent = task.title;

        const descriptionElement = document.createElement('p');
        descriptionElement.textContent = task.description;

        // New elements for Task Date and Time Spent
        const taskDateElement = document.createElement('div');
        taskDateElement.className = 'task-meta task-date';
        // Display user-friendly date, or "Not set"
        let displayDate = 'Not set';
        if (task.task_date) {
            const dateObj = new Date(task.task_date);
            // Check if date is valid before formatting
            if (!isNaN(dateObj.getTime())) {
                displayDate = dateObj.toLocaleDateString();
            }
        }
        taskDateElement.innerHTML = `<strong>Date:</strong> <span class="date-value">${displayDate}</span>`;

        const timeSpentElement = document.createElement('div');
        timeSpentElement.className = 'task-meta task-time-spent';
        timeSpentElement.innerHTML = `<strong>Time Spent:</strong> <span class="time-value">${task.time_spent_hours || '0'}</span> hours`;

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
        taskCard.appendChild(taskDateElement); // Add new element
        taskCard.appendChild(timeSpentElement); // Add new element
        taskCard.appendChild(actionsDiv);

        editButton.addEventListener('click', () => enableEditMode(taskCard, titleElement, descriptionElement, taskDateElement, timeSpentElement, editButton));
        titleElement.addEventListener('dblclick', () => enableEditMode(taskCard, titleElement, descriptionElement, taskDateElement, timeSpentElement, editButton));
        descriptionElement.addEventListener('dblclick', () => enableEditMode(taskCard, titleElement, descriptionElement, taskDateElement, timeSpentElement, editButton));
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
    //  if (typeof initialKanbanTasks !== 'undefined' && Array.isArray(initialKanbanTasks)) {
    //     initialKanbanTasks.forEach(task => {
    //         const card = renderTask(task);
    //         if (task.status === 'todo' && todoTasks) {
    //             todoTasks.appendChild(card);
    //         } else if (task.status === 'inprogress' && inprogressTasks) {
    //             inprogressTasks.appendChild(card);
    //         } else if (task.status === 'done' && doneTasks) {
    //             doneTasks.appendChild(card);
    //         }
    //     });
    // }

    async function fetchAndRenderInitialTasks() {
        try {
            // Adjust the URL if your users app is namespaced in Django URLs, e.g., /users/api/kanban_tasks/
            const response = await fetch('/api/kanban_tasks/');
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const tasks = await response.json();

            tasks.forEach(task => {
                const card = renderTask(task);
                if (task.status === 'todo' && todoTasks) {
                    todoTasks.appendChild(card);
                } else if (task.status === 'inprogress' && inprogressTasks) {
                    inprogressTasks.appendChild(card);
                } else if (task.status === 'done' && doneTasks) {
                    doneTasks.appendChild(card);
                }
            });
        } catch (error) {
            console.error("Error fetching initial tasks:", error.message);
            alert("Failed to load tasks. Please check the console for more details or try refreshing the page.");
        }
    }

    fetchAndRenderInitialTasks(); // Call this function when DOM is loaded


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

    function enableEditMode(taskCard, titleElement, descriptionElement, taskDateElement, timeSpentElement, editButton) {
        if (taskCard.classList.contains('editing')) return; // Prevent multiple edit modes
        taskCard.classList.add('editing');

        const originalTitle = taskCard.dataset.title; // Use data attribute for original value
        const originalDescription = taskCard.dataset.description; // Use data attribute
        const originalTaskDate = taskCard.dataset.taskDate;
        const originalTimeSpent = taskCard.dataset.timeSpent;

        const titleInput = document.createElement('input');
        titleInput.type = 'text';
        titleInput.value = originalTitle;
        taskCard.insertBefore(titleInput, titleElement);
        titleElement.style.display = 'none';

        const descriptionTextarea = document.createElement('textarea');
        descriptionTextarea.value = originalDescription;
        taskCard.insertBefore(descriptionTextarea, descriptionElement);
        descriptionElement.style.display = 'none';

        // Create and setup Task Date input
        const taskDateInput = document.createElement('input');
        taskDateInput.type = 'date';
        let initialDateForInput = '';
        if (originalTaskDate) {
            if (originalTaskDate.includes('T')) { // If it's a full ISO string like "2023-10-26T10:00:00Z"
                initialDateForInput = originalTaskDate.split('T')[0];
            } else if (originalTaskDate.match(/^\d{4}-\d{2}-\d{2}$/)) { // If it's already YYYY-MM-DD
                initialDateForInput = originalTaskDate;
            } else {
                // Attempt to parse other date formats (e.g., "October 26, 2023")
                const d = new Date(originalTaskDate);
                if (!isNaN(d.getTime())) {
                    // Format to YYYY-MM-DD for the input field from local date parts
                    const year = d.getFullYear();
                    const month = String(d.getMonth() + 1).padStart(2, '0');
                    const day = String(d.getDate()).padStart(2, '0');
                    initialDateForInput = `${year}-${month}-${day}`;
                }
            }
        }
        taskDateInput.value = initialDateForInput;
        taskCard.insertBefore(taskDateInput, taskDateElement);
        taskDateElement.style.display = 'none';

        // Create and setup Time Spent input
        const timeSpentInput = document.createElement('input');
        timeSpentInput.type = 'number';
        timeSpentInput.value = originalTimeSpent || '0';
        timeSpentInput.min = '0'; // Optional: prevent negative numbers
        timeSpentInput.step = '0.1'; // Optional: allow decimal hours
        taskCard.insertBefore(timeSpentInput, timeSpentElement);
        timeSpentElement.style.display = 'none';

        editButton.innerHTML = '💾';
        editButton.title = 'Save task';

        // Forward new input elements to saveChanges
        const tempSaveListener = () => {
            saveChanges(titleInput, descriptionTextarea, taskDateInput, timeSpentInput); // Pass inputs
            newEditButton.removeEventListener('click', tempSaveListener); // Clean up self
        };

        const tempKeyListener = (e) => {
            if (e.key === 'Enter' && e.target === titleInput) {
                e.preventDefault();
                // Call saveChanges with the input elements it needs
                saveChanges(titleInput, descriptionTextarea, taskDateInput, timeSpentInput);
                titleInput.removeEventListener('keypress', tempKeyListener); // Clean up self
            }
        };

        const newEditButton = editButton.cloneNode(true);
        editButton.parentNode.replaceChild(newEditButton, editButton);

        // Definition of the nested saveChanges function
        // It uses variables from enableEditMode's scope: taskCard, titleElement, descriptionElement, taskDateElement, timeSpentElement, newEditButton, titleInput (for removing keylistener), tempKeyListener
        function saveChanges(currentTitleInput, currentDescriptionTextarea, currentTaskDateInput, currentTimeSpentInput) {
            taskCard.classList.remove('editing');
            const newTitle = currentTitleInput.value.trim();
            const newDescription = currentDescriptionTextarea.value.trim();
            const newTaskDate = currentTaskDateInput.value; // This will be YYYY-MM-DD from the date input
            const newTimeSpent = currentTimeSpentInput.value.trim() || '0'; // Default to '0' if empty

            // Update display elements (text content)
            titleElement.textContent = newTitle;
            descriptionElement.textContent = newDescription;

            // Update date display: format YYYY-MM-DD to locale string, or "Not set"
            let displayDate = 'Not set';
            if (newTaskDate) { // newTaskDate is 'YYYY-MM-DD'
                // Create date object assuming input is local date.
                // Adding time component to avoid potential off-by-one day issues with UTC conversion by toLocaleDateString
                const dateParts = newTaskDate.split('-');
                const localDate = new Date(parseInt(dateParts[0]), parseInt(dateParts[1]) - 1, parseInt(dateParts[2]), 12, 0, 0); // Noon to be safe
                if (!isNaN(localDate.getTime())) {
                    displayDate = localDate.toLocaleDateString();
                }
            }
            taskDateElement.querySelector('.date-value').textContent = displayDate;
            timeSpentElement.querySelector('.time-value').textContent = newTimeSpent; // Already string '0' or valid number

            // Update data attributes on the task card
            taskCard.setAttribute('data-title', newTitle);
            taskCard.setAttribute('data-description', newDescription);
            taskCard.setAttribute('data-task-date', newTaskDate); // Store as YYYY-MM-DD
            taskCard.setAttribute('data-time-spent', newTimeSpent);

            // Remove input fields from the DOM
            if (currentTitleInput.parentNode === taskCard) taskCard.removeChild(currentTitleInput);
            if (currentDescriptionTextarea.parentNode === taskCard) taskCard.removeChild(currentDescriptionTextarea);
            if (currentTaskDateInput.parentNode === taskCard) taskCard.removeChild(currentTaskDateInput);
            if (currentTimeSpentInput.parentNode === taskCard) taskCard.removeChild(currentTimeSpentInput);

            // Restore display of original static elements
            titleElement.style.display = '';
            descriptionElement.style.display = '';
            taskDateElement.style.display = '';
            timeSpentElement.style.display = '';

            // Reset the save button to an edit button
            newEditButton.innerHTML = '✏️';
            newEditButton.title = 'Edit task';

            // Re-attach the edit listener to the button.
            // Need to clone the button *again* to effectively replace it and its listeners,
            // then add the new 'enableEditMode' listener to this fresh button.
            const finalEditButton = newEditButton.cloneNode(true); // Clone the button (which is currently the save button)
            newEditButton.parentNode.replaceChild(finalEditButton, newEditButton); // Replace the save button with the clone

            // The event listener for 'click' on newEditButton (which was clickSaveListener) is now gone from finalEditButton.
            // Add the listener to make it an edit button again.
            finalEditButton.addEventListener('click', () => {
                enableEditMode(taskCard, titleElement, descriptionElement, taskDateElement, timeSpentElement, finalEditButton);
            });
            // Note: The original `newEditButton` variable in `enableEditMode` scope still refers to the button *before* this save.
            // This part is tricky with listener management. The key is that `finalEditButton` is the one now in the DOM.

            // Prepare data for the API call
            const updateData = {
                title: newTitle,
                description: newDescription,
                task_date: newTaskDate, // Send YYYY-MM-DD string
                time_spent_hours: parseFloat(newTimeSpent) // Convert to float for API
            };
            console.log(`Task ${taskCard.dataset.taskId} updated with data:`, updateData);
            updateTaskDetailsAPI(taskCard.dataset.taskId, updateData);

            // Clean up the keypress listener attached to the original titleInput
            // (currentTitleInput is the same as titleInput in this context)
            currentTitleInput.removeEventListener('keypress', tempKeyListener);
        }

        // This is the listener for the save button.
        const clickSaveListener = () => {
            saveChanges(titleInput, descriptionTextarea, taskDateInput, timeSpentInput);
            // The listener itself should be removed from newEditButton.
            // This is complex because newEditButton is replaced inside saveChanges.
            // The most robust way is that saveChanges replaces newEditButton with finalEditButton,
            // which implicitly removes the clickSaveListener.
            // No explicit removeEventListener(clickSaveListener) needed here if button is replaced.
        };

        newEditButton.addEventListener('click', clickSaveListener); // This listener is on `newEditButton`
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
