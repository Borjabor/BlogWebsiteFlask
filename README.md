# Blog Website Flask App
=========================

A RESTful Flask application for a blog website, allowing users to view, edit, delete, and create new posts with image support.

## Features

* View posts from a database
* Edit existing posts
* Delete posts
* Create new posts with image upload (URL or local file)
* RESTful API architecture
* Possible to create users with hashed and salted passwords
* Users have 3 roles: user, admin, and maintainer
  	+ Users can comment on posts
  	+ Admins can also create, edit, and delete posts, as well as delete user comments
  	+ Maintainer can to the same as Admins, plus grant or revoke Admin status, and delete Users
  

## Installation

1. Clone the repository: `git clone https://github.com/your-username/your-repo-name.git`
2. Install dependencies: `pip install -r requirements.txt`
3. Run the application: `flask run`

## Environment Variables
Some variables are shown in the code for ease of testing, but for security reasons they should be made hidden by use of environment variables
* SECRET KEY
* Maintainer user credentials:
    + Email
    + Password

## API Endpoints

* `GET /posts`: Retrieve a list of all posts
* `GET /posts/<int:post_id>`: Retrieve a single post by ID
* `POST /posts`: Create a new post
* `PUT /posts/<int:post_id>`: Update an existing post
* `DELETE /posts/<int:post_id>`: Delete a post

## Image Upload

* Images can be uploaded from a URL or a local file
* Accepted formats: png, jpg, jpeg, gif

## Database Schema

The project uses a SQLite database with the following schema:

### Users Table

| Column Name | Data Type | Constraints |
|-------------|-----------|-------------|
| id          | Integer   | Primary Key, Auto Increment |
| name        | String    | Not Null |
| email       | String    | Unique, Not Null |
| password    | String    | Not Null |
| role        | Integer   | Not Null, Default: 1 (USER) |

### Blog Posts Table

| Column Name | Data Type | Constraints |
|-------------|-----------|-------------|
| id          | Integer   | Primary Key, Auto Increment |
| title       | String    | Not Null |
| subtitle    | String    | Not Null |
| date        | DateTime  | Not Null |
| body        | Text      | Not Null |
| author_id   | Integer   | Foreign Key (users.id) |
| img_url     | String    | Not Null |

### Comments Table

| Column Name | Data Type | Constraints |
|-------------|-----------|-------------|
| id          | Integer   | Primary Key, Auto Increment |
| text        | Text      | Not Null |
| author_id   | Integer   | Foreign Key (users.id) |
| post_id     | Integer   | Foreign Key (blog_posts.id) |
| date        | DateTime  | Not Null |

### Relationships

- A User can have many Blog Posts (One-to-Many)
- A User can have many Comments (One-to-Many)
- A Blog Post can have many Comments (One-to-Many)

### Role Enumeration

| Role Value | Role Name  |
|------------|------------|
| 1          | USER       |
| 2          | ADMIN      |
| 3          | MAINTAINER |

