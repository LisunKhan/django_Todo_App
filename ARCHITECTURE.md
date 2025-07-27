# Project Architecture

This is a monolithic Django web application. It follows a standard Django project structure:

- **`myproject/myproject`**: This is the main project directory.
    - **`settings.py`**: Contains all the project settings, including database configuration, installed apps, middleware, and template settings. It's configured to use a SQLite database by default. It also includes `crispy_forms` for form styling.
    - **`urls.py`**: The main URL configuration file. It includes the URLs from the `users` app.
    - **`wsgi.py` and `asgi.py`**: Standard files for deploying the application.

- **`myproject/users`**: This is a Django app that contains the core logic of the application.
    - **`models.py`**: Defines the data models.
    - **`views.py`**: Contains the view functions and classes that handle HTTP requests and render templates.
    - **`urls.py`**: Defines the URL patterns for the `users` app.
    - **`forms.py`**: Contains the forms used in the application.
    - **`templates`**: Contains the HTML templates for the application.
    - **`static`**: Contains static files like CSS and JavaScript.

# Model Architecture

The data model is centered around the `User`, `Project`, and `TodoItem` models:

- **`User`**: The standard Django `User` model is used for authentication.
- **`UserProfile`**: A one-to-one relationship with the `User` model to store additional user information.
- **`Project`**: A project can have one owner (`User`) and multiple members (`User`).
- **`ProjectMembership`**: This model links users to projects, creating a many-to-many relationship.
- **`TodoItem`**: Each to-do item belongs to a `User` and can optionally be associated with a `Project`.

# API List and Dependencies

The application exposes a few API endpoints, primarily for the Kanban board functionality:

- **`GET /api/kanban_tasks/`**:
    - **Description**: Fetches all tasks for projects the logged-in user is a part of. It can be filtered by `project_id`.
    - **Dependencies**: Requires the user to be authenticated. It depends on the `Project` and `TodoItem` models.
    - **View**: `api_get_kanban_tasks` in `users/views.py`.

- **`POST /todo/inline_edit/<int:todo_id>/`**:
    - **Description**: Updates a `TodoItem` inline. This is used by the Kanban board to update task details like title, description, status, project, and time.
    - **Dependencies**: Requires the user to be authenticated and to be the owner of the `TodoItem`. It depends on the `TodoItem` and `Project` models.
    - **View**: `inline_edit_todo` in `users/views.py`.

- **`POST /add_todo/` (AJAX)**:
    - **Description**: Adds a new `TodoItem`. It can be called via AJAX from the to-do list or Kanban board.
    - **Dependencies**: Requires the user to be authenticated. It depends on the `TodoItem` model.
    - **View**: `add_todo` in `users/views.py`.

- **`POST /delete_todo/<int:todo_id>/` (AJAX)**:
    - **Description**: Deletes a `TodoItem`.
    - **Dependencies**: Requires the user to be authenticated and to be the owner of the `TodoItem`. It depends on the `TodoItem` model.
    - **View**: `delete_todo` in `users/views.py`.
