# Admin Manual - Todo Application with Project Management

This document provides guidance for administrators on managing users, projects, and tasks within the application.

## 1. Becoming a Superuser (Initial Admin Setup)

The first administrator account, known as a **Superuser**, has unrestricted access to all parts of the application and the Django admin interface.

To create a Superuser (if one doesn't exist yet):
1.  Open your terminal or command prompt.
2.  Navigate to the `myproject` directory (where `manage.py` is located).
3.  Run the following command:
    ```bash
    python manage.py createsuperuser
    ```
4.  Follow the prompts to set a username, email (optional), and password for the Superuser.

Once created, the Superuser can log in to the Django admin interface, typically available at `/admin/` on your site (e.g., `http://localhost:8000/admin/`).

## 2. Understanding Admin Roles

There are two primary administrative roles:

*   **Superuser:**
    *   Has all permissions by default.
    *   Can manage users, groups, projects, tasks, and all other aspects of the application.
    *   Can assign other users to be "Project Admins" or even other Superusers.

*   **Project Admin:**
    *   A regular user who has been granted specific permissions to manage projects.
    *   This is achieved by adding the user to the **"Project Admins"** group.
    *   Project Admins can:
        *   Create new projects.
        *   Edit existing project details (name, description, owner).
        *   Delete projects.
        *   Add users to projects (manage project memberships).
        *   Remove users from projects.
    *   They access these functionalities through the Django admin interface.

## 3. Managing Users

User management is typically done by Superusers.

### 3.1. Creating Users
1.  Log in to the Django admin interface (`/admin/`) as a Superuser.
2.  Navigate to **Users** (under the "AUTHENTICATION AND AUTHORIZATION" section or similar).
3.  Click "Add user +".
4.  Fill in the username and password. Click "Save".
5.  On the next page ("Change user"), you can fill in optional details like email, first name, last name.
6.  **Important:** For a user to access the admin panel (even as a Project Admin), they must have **"Staff status"** checked under the "Permissions" section.

### 3.2. Assigning "Project Admin" Role
To allow a regular user to manage projects, a Superuser must add them to the "Project Admins" group:
1.  Log in to the Django admin interface as a Superuser.
2.  Go to **Users**.
3.  Select the user you want to designate as a Project Admin.
4.  In the "Permissions" section:
    *   Ensure **"Staff status"** is checked (so they can log into the admin panel).
    *   In the "Groups" subsection, select "Project Admins" from the "Available groups" list and move it to the "Chosen groups" list using the arrow.
5.  Click "Save" at the bottom of the page.

This user can now log into `/admin/` and will see options to manage Projects and Project Memberships.

## 4. Managing Projects

Projects can be managed by Superusers and members of the "Project Admins" group.

1.  Log in to the Django admin interface.
2.  Navigate to **Projects** (usually under an app section like "USERS" or your specific app name).
    *   The direct URL might be `/admin/users/project/`.

### 4.1. Creating a New Project
1.  On the "Projects" list page, click "Add project +".
2.  Fill in the project details:
    *   **Name:** (Required, must be unique) The name of the project.
    *   **Description:** (Optional) A brief description of the project.
    *   **Owner:** (Optional) You can assign a user as the owner of the project. This is for informational purposes or future permission enhancements.
3.  Click "Save".

### 4.2. Editing an Existing Project
1.  From the "Projects" list, click on the name of the project you want to edit.
2.  Modify the fields as needed.
3.  Click "Save".

### 4.3. Deleting a Project
1.  From the "Projects" list, you can select projects using the checkboxes and choose "Delete selected projects" from the "Actions" dropdown.
2.  Alternatively, when editing a single project, there's usually a "Delete" button at the bottom.
3.  **Note:** Deleting a project will **not** delete associated tasks (`TodoItem`). Instead, the `project` field on those tasks will be set to `NULL` (become unassigned).

## 5. Managing Project Memberships

Project memberships define which users are part of a project. This can be managed by Superusers and "Project Admins".

The primary way to manage members is when editing a specific Project:
1.  Navigate to the **Projects** list in the admin panel.
2.  Click on the project you want to manage members for.
3.  Scroll down to the **"Project Memberships"** inline section.
    *   To add a new member, select a user from the "User" dropdown in an empty row and click "Save". You can add multiple members at once using "Add another Project Membership".
    *   To remove a member, check the "Delete?" box next to their membership entry and click "Save".

Alternatively, you can view all memberships:
1.  Navigate to **Project Memberships** in the admin panel (e.g., `/admin/users/projectmembership/`).
2.  Here you can see all user-project links. You can add new ones or delete existing ones.

## 6. Linking Tasks to Projects

Tasks (`TodoItem` instances) can be linked to projects either through the admin interface or the main application UI.

### 6.1. Via Django Admin
1.  Navigate to **Todo items** in the admin panel.
2.  When adding a new task or editing an existing one:
    *   You will see a **"Project"** field (dropdown).
    *   Select the desired project from the list.
    *   If no project is selected, the task will not be associated with any project.
3.  Save the task.

### 6.2. Via Application UI
1.  When creating a new task or editing an existing task using the application's forms (e.g., "Add Todo" page):
    *   An optional **"Project"** dropdown will be available.
    *   Users can select a project to associate the task with.
    *   If left blank, the task remains unassigned to a project.

This manual should cover the main administrative functions related to the new project management features. For general Django admin usage, please refer to the official Django documentation.
