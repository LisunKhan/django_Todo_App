# Project Architecture

This document outlines the architecture of the Django Todo App.

## Overview

The project is a Django-based web application that allows users to manage their todo lists. It follows a standard Django project structure.

## Project Structure

* `myproject/`: This is the main Django project directory.
    * `settings.py`: Contains the project settings, including database configuration, installed apps, and middleware.
    * `urls.py`: The main URL configuration for the project. It includes the URLs for the `users` app.
    * `wsgi.py` and `asgi.py`: Entry points for the WSGI and ASGI compatible web servers.
* `users/`: This is a Django app that contains the core logic for the todo list functionality.
    * `models.py`: Defines the database models, including `TodoItem` and `UserProfile`.
    * `views.py`: Contains the views that handle user requests and render templates.
    * `urls.py`: The URL configuration for the `users` app.
    * `templates/`: Contains the HTML templates for the application.
    * `static/`: Contains the static files, such as CSS and JavaScript.
* `manage.py`: A command-line utility that lets you interact with this Django project.
* `db.sqlite3`: The SQLite database file.
* `media/`: A directory to store user-uploaded files.

## Authentication and Authorization

The application uses Django's built-in authentication system to manage user accounts. Users can register, log in, and log out.

## Todo Functionality

The core functionality of the application is the todo list. Users can create, edit, and delete todo items. Each todo item has a title, description, and status.

## Data Models

The application uses the following models to store data:

*   **TodoItem**: Represents a single todo item.
    *   `user`: A foreign key to the `User` model, representing the user who owns the todo item.
    *   `title`: The title of the todo item.
    *   `description`: A detailed description of the todo item.
    *   `project`: A foreign key to the `Project` model, representing the project that the todo item belongs to.
    *   `time_spent`: The time spent on the todo item, in minutes.
    *   `estimation_time`: The estimated time to complete the todo item, in minutes.
    *   `created_at`: The date and time when the todo item was created.
    *   `updated_at`: The date and time when the todo item was last updated.
    *   `status`: The current status of the todo item. Can be "To Do", "In Progress", or "Done".
*   **TodoLog**: Represents a log entry for a todo item.
    *   `todo_item`: A foreign key to the `TodoItem` model, representing the todo item that the log entry belongs to.
    *   `log_time`: The time spent on the todo item for this log entry, in hours.
    *   `task_date`: The date of the log entry.
    *   `notes`: Any notes for the log entry.
*   **Project**: Represents a project that can contain multiple todo items.
    *   `name`: The name of the project.
    *   `description`: A detailed description of the project.
    *   `owner`: A foreign key to the `User` model, representing the user who owns the project.
    *   `members`: A many-to-many relationship with the `User` model, representing the members of the project.
    *   `created_at`: The date and time when the project was created.
    *   `updated_at`: The date and time when the project was last updated.
*   **ProjectMembership**: Represents the relationship between a user and a project.
    *   `user`: A foreign key to the `User` model.
    *   `project`: A foreign key to the `Project` model.
    *   `date_joined`: The date and time when the user joined the project.
*   **UserProfile**: Represents a user's profile.
    *   `user`: A one-to-one relationship with the `User` model.
    *   `bio`: A short biography of the user.
    *   `profile_picture`: The user's profile picture.

## Future Improvements

* Implement user roles and permissions.
* Add support for multiple todo lists per user.
* Integrate a third-party API for notifications.
