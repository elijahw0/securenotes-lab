--User schema table. notes.owner_id should be the foreign key for users.id
CREATE TABLE users(
	id		INTEGER PRIMARY KEY,
	username	TEXT UNIQUE NOT NULL,
	password_hash	TEXT NOT NULL,
	role		TEXT NOT NULL DEFAULT 'user',
	created_at	TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE notes(
	id		INTEGER PRIMARY KEY,
	title		TEXT,
	body		TEXT NOT NULL,
	owner_id 	INTEGER NOT NULL,
	created_at	TEXT NOT NULL DEFAULT (datetime('now')),
	FOREIGN KEY (owner_id) REFERENCES users(id)
);
