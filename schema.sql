--User schema table. notes.owner_id should be the foreign key for users.id
CREATE TABLE users(
	id		INTEGER PRIMARY KEY,
	username	TEXT UNIQUE NOT NULL,
	password_hash	TEXT NOT NULL,
	role		TEXT NOT NULL DEFAULT 'user',
	created_at	TEXT NOT NULL DEFAULT (datetime('now'))
);

--Notes schema table. owner_id connects back to user.id (foreign key) notes must come from a user, one user can have multiple notes
CREATE TABLE notes(
	id		INTEGER PRIMARY KEY,
	title		TEXT,
	body		TEXT NOT NULL,
	owner_id 	INTEGER NOT NULL,
	created_at	TEXT NOT NULL DEFAULT (datetime('now')),
	FOREIGN KEY (owner_id) REFERENCES users(id)
);

--Token schema table.
CREATE TABLE tokens(
	id		INTEGER PRIMARY KEY,
	token		TEXT NOT NULL UNIQUE,
	user_id		INTEGER NOT NULL,
	created_at	TEXT NOT NULL DEFAULT (datetime('now')),
	expires_at	TEXT NOT NULL,
	FOREIGN KEY (user_id) REFERENCES users(id)
);

--security_events table for logging and audits
CREATE TABLE security_events(
	log_id		INTEGER PRIMARY KEY,
	event_type	TEXT NOT NULL,
	user_id		INTEGER,
	username	TEXT,
	details		TEXT,
	endpoint	TEXT,
	source_ip	TEXT,
	created_at	TEXT NOT NULL DEFAULT (datetime('now'))
);
