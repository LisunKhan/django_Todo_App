new Vue({
    el: '#dashboard-app',
    delimiters: ['${', '}'],
    data: {
        users: [],
        tasks: [],
        logs: [],
        blockers: [],
        yesterdayLogs: [],
        todayLogs: [],
        newTaskTitle: '',
        selectedTask: {},
        logTime: 0,
        logNotes: ''
    },
    methods: {
        isTaskInToday(taskId) {
            return this.todayLogs.some(log => log.todo_item.id === taskId);
        },
        handleDrop(target, event) {
            const task = JSON.parse(event.dataTransfer.getData('text/plain'));
            if (target === 'pool') {
                // Remove from today's tasks
                const logIndex = this.todayLogs.findIndex(log => log.todo_item.id === task.id);
                if (logIndex !== -1) {
                    this.todayLogs.splice(logIndex, 1);
                }
            } else {
                // Add to today's tasks
                if (!this.isTaskInToday(task.id)) {
                    this.todayLogs.push({
                        todo_item: task,
                        log_time: 0,
                        notes: '',
                        task_date: new Date().toISOString().slice(0, 10)
                    });
                }
            }
        },
        openLogTimeModal(task) {
            this.selectedTask = task;
            $('#logTimeModal').modal('show');
        },
        logTime() {
            const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');
            fetch('/api/dashboard/log/create/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                },
                body: JSON.stringify({
                    todo_item: this.selectedTask.id,
                    log_time: this.logTime,
                    notes: this.logNotes,
                    task_date: new Date().toISOString().slice(0, 10)
                })
            })
            .then(response => response.json())
            .then(data => {
                this.todayLogs.push(data);
                this.logTime = 0;
                this.logNotes = '';
                $('#logTimeModal').modal('hide');
            });
        },
        createTask(userId) {
            const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');
            fetch('/api/dashboard/task/create/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                },
                body: JSON.stringify({
                    title: this.newTaskTitle,
                    user: userId,
                    project: projectId
                })
            })
            .then(response => response.json())
            .then(data => {
                this.tasks.push(data);
                this.newTaskTitle = '';
            });
        },
        fetchUsers(projectId) {
            fetch(`/api/dashboard/project/${projectId}/users/`)
                .then(response => response.json())
                .then(data => {
                    this.users = data;
                });
        },
        fetchTasks(projectId) {
            fetch(`/api/dashboard/project/${projectId}/tasks/`)
                .then(response => response.json())
                .then(data => {
                    this.tasks = data;
                });
        },
        fetchLogs(projectId, date) {
            fetch(`/api/dashboard/project/${projectId}/logs/?date=${date}`)
                .then(response => response.json())
                .then(data => {
                    if (date === 'yesterday') {
                        this.yesterdayLogs = data;
                    } else {
                        this.todayLogs = data;
                    }
                });
        },
        fetchBlockers(projectId) {
            fetch(`/api/dashboard/project/${projectId}/blockers/`)
                .then(response => response.json())
                .then(data => {
                    this.blockers = data;
                });
        },
        getYesterdayTasks(userId) {
            return this.yesterdayLogs.filter(log => log.todo_item.user === userId).map(log => log.todo_item);
        },
        getTodayTasks(userId) {
            return this.todayLogs.filter(log => log.todo_item.user === userId).map(log => log.todo_item);
        },
        getTotalTime(userId) {
            return this.todayLogs.filter(log => log.todo_item.user === userId).reduce((total, log) => total + log.log_time, 0);
        },
        getBlockers(userId) {
            return this.blockers.filter(task => task.user === userId);
        }
    },
    mounted() {
        this.fetchUsers(projectId);
        this.fetchTasks(projectId);
        this.fetchLogs(projectId, 'yesterday');
        this.fetchLogs(projectId, 'today');
        this.fetchBlockers(projectId);
    }
});
