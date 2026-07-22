--User schema table. notes.owner_id should be the foreign key for users.id
CREATE TABLE users(
	id		INTEGER PRIMARY KEY,
	username	TEXT UNIQUE NOT NULL,
	password_hash	TEXT NOT NULL,
	role		TEXT NOT NULL DEFAULT 'user',
	created_at	TEXT NOT NULL DEFAULT (datetime('now'))
);
