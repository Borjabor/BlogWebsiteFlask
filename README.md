# Blog Website Flask App
=========================

A RESTful Flask application for a blog website, allowing users to view, edit, delete, and create new posts with image support.

## Features

* View posts from a database
* Edit existing posts
* Delete posts
* Create new posts with image upload (URL or local file)
* RESTful API architecture

## Requirements

* Python 3.x
* Flask
* [List any other dependencies required by your app]

## Installation

1. Clone the repository: `git clone https://github.com/your-username/your-repo-name.git`
2. Install dependencies: `pip install -r requirements.txt`
3. Run the application: `flask run`

## API Endpoints

* `GET /posts`: Retrieve a list of all posts
* `GET /posts/<int:post_id>`: Retrieve a single post by ID
* `POST /posts`: Create a new post
* `PUT /posts/<int:post_id>`: Update an existing post
* `DELETE /posts/<int:post_id>`: Delete a post

## Image Upload

* Images can be uploaded from a URL or a local file
* [Provide any additional details about image upload, such as supported formats or size limits]

## Database Schema

The project uses a SQLite database with the following schema:

* `blog_post` table:
	+ `id` (primary key)
	+ `title`
	+ `date`
	+ `body`
	+ `author`
	+ `img_url`
	+ `subtitle`
